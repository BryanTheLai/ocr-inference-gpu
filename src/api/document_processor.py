from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel, Field
import json
import base64
from io import BytesIO
from PIL import Image
import litellm
import os
from dotenv import load_dotenv
import asyncio
from src.tasks.processing import run_ocr_processing
from src.tasks.celery_app import celery_app
from celery.result import AsyncResult
import redis
from src.configs.pipelines.settings import settings

load_dotenv()

router = APIRouter(prefix="/api/v1/document", tags=["document"])

litellm.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

class ExtractionSchema(BaseModel):
    schema: Dict[str, Any] = Field(..., description="JSON schema for extraction")
    document_type: str = Field(..., description="Type of document (invoice, contract, medical, etc.)")
    extraction_prompt: Optional[str] = Field(None, description="Custom extraction prompt")

class ProcessingRequest(BaseModel):
    task_id: str
    schema: Dict[str, Any]
    document_type: str
    extraction_prompt: Optional[str] = None

class ExtractionResult(BaseModel):
    task_id: str
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    ocr_detections: Optional[List[Dict]] = None
    error: Optional[str] = None

def create_extraction_prompt(schema: Dict[str, Any], document_type: str, custom_prompt: Optional[str] = None) -> str:
    if custom_prompt:
        return custom_prompt
    
    prompt = f"""You are an expert document analyzer specializing in {document_type} documents.
    
Extract information from the provided document according to this JSON schema:
{json.dumps(schema, indent=2)}

Important instructions:
1. Extract ONLY the fields specified in the schema
2. Maintain the exact structure and field names from the schema
3. For arrays, extract ALL relevant items found in the document
4. For missing fields, use null
5. Ensure all extracted data matches the specified types
6. Include location information (bounding boxes) when possible for each extracted value

Return the extracted data as valid JSON that conforms to the provided schema.
Also include a "metadata" field with:
- confidence scores for each extraction
- page numbers where information was found
- bounding box coordinates for highlighting
"""
    return prompt

async def process_with_llm(ocr_text: str, image_data: Optional[bytes], schema: Dict[str, Any], document_type: str, extraction_prompt: Optional[str] = None) -> Dict[str, Any]:
    try:
        prompt = create_extraction_prompt(schema, document_type, extraction_prompt)
        
        messages = [
            {
                "role": "system",
                "content": "You are a document extraction expert. Extract structured data from documents according to provided schemas."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "text", "text": f"OCR Text:\n{ocr_text}"}
                ]
            }
        ]
        
        if image_data:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        
        response = await litellm.acompletion(
            model="gemini/gemini-2.0-flash-latest",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4096
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        return extracted_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM processing failed: {str(e)}")

@router.post("/process-with-schema", response_model=ExtractionResult)
async def process_document_with_schema(
    file: UploadFile = File(...),
    schema_data: str = Body(..., description="JSON string containing schema and document type")
):
    try:
        schema_info = json.loads(schema_data)
        schema = schema_info.get("schema", {})
        document_type = schema_info.get("document_type", "general")
        extraction_prompt = schema_info.get("extraction_prompt")
        
        contents = await file.read()
        
        task = run_ocr_processing.delay(contents, file.content_type)
        
        max_wait = 60
        wait_interval = 2
        elapsed = 0
        
        while elapsed < max_wait:
            result = AsyncResult(task.id, app=celery_app)
            if result.ready():
                break
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        if not result.ready():
            return ExtractionResult(
                task_id=task.id,
                status="PROCESSING",
                error="OCR processing is taking longer than expected"
            )
        
        if result.successful():
            ocr_result = result.result
            detections = ocr_result.get("detections", [])
            
            ocr_text = "\n".join([d.get("text", "") for d in detections])
            
            image_data = None
            if file.content_type.startswith("image/"):
                await file.seek(0)
                image_data = await file.read()
            
            extracted_data = await process_with_llm(
                ocr_text=ocr_text,
                image_data=image_data,
                schema=schema,
                document_type=document_type,
                extraction_prompt=extraction_prompt
            )
            
            return ExtractionResult(
                task_id=task.id,
                status="SUCCESS",
                extracted_data=extracted_data,
                ocr_detections=detections
            )
        else:
            return ExtractionResult(
                task_id=task.id,
                status="FAILED",
                error=str(result.info)
            )
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON schema data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-batch")
async def extract_batch_documents(
    files: List[UploadFile] = File(...),
    schema_data: str = Body(..., description="JSON string containing schema and document type")
):
    try:
        schema_info = json.loads(schema_data)
        results = []
        
        for file in files:
            result = await process_document_with_schema(file, schema_data)
            results.append({
                "filename": file.filename,
                "result": result.dict()
            })
        
        return {"batch_results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def get_document_templates():
    templates = {
        "invoice": {
            "name": "Invoice",
            "schema": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "date": {"type": "string"},
                    "vendor": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"}
                        }
                    },
                    "customer": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "address": {"type": "string"}
                        }
                    },
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "total": {"type": "number"}
                            }
                        }
                    },
                    "subtotal": {"type": "number"},
                    "tax": {"type": "number"},
                    "total": {"type": "number"}
                }
            }
        },
        "medical_form": {
            "name": "Medical Form",
            "schema": {
                "type": "object",
                "properties": {
                    "patient_info": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "date_of_birth": {"type": "string"},
                            "patient_id": {"type": "string"}
                        }
                    },
                    "diagnosis": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "medications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "dosage": {"type": "string"},
                                "frequency": {"type": "string"}
                            }
                        }
                    },
                    "vital_signs": {
                        "type": "object",
                        "properties": {
                            "blood_pressure": {"type": "string"},
                            "heart_rate": {"type": "number"},
                            "temperature": {"type": "number"}
                        }
                    }
                }
            }
        },
        "bank_statement": {
            "name": "Bank Statement",
            "schema": {
                "type": "object",
                "properties": {
                    "account_holder": {"type": "string"},
                    "account_number": {"type": "string"},
                    "statement_period": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"}
                        }
                    },
                    "beginning_balance": {"type": "number"},
                    "ending_balance": {"type": "number"},
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                                "balance": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }
    }
    return templates

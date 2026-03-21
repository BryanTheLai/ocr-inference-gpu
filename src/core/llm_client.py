"""LiteLLM adapter used for schema-based extraction."""

import json
import logging
from typing import Any, Dict
import litellm

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, model_name: str = "gemini/gemini-3.1-flash-lite-preview"):
        """Store the model name used for structured extraction requests."""
        self.model_name = model_name

    def extract_structured_data(
        self, text: str, json_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the LLM and return a JSON object that matches the schema.

        Args:
            text: OCR text flattened into one prompt string.
            json_schema: JSON Schema used to constrain the response.

        Returns:
            Parsed JSON content from the model response.

        Raises:
            RuntimeError: If the model call fails or returns invalid JSON.
        """
        system_prompt = (
            "You are a structured data extraction assistant. "
            "Extract information from the provided OCR text according to the exact JSON schema provided. "
            "Your response must be valid JSON matching the schema."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the text to extract from:\n\n{text}"},
        ]

        try:
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "extraction", "schema": json_schema},
                },
                temperature=0.0,
            )  # type: ignore
            content = response.choices[0].message.content  # type: ignore
            return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            raise RuntimeError(f"Failed to extract structured data: {e}")

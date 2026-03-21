import json
import logging
from typing import Any, Dict
import litellm

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for interacting with Large Language Models (LLMs) to perform structured data extraction.

    Abstracts away the underlying provider (e.g., via litellm) and enforces strict JSON schema
    compliance on the output.
    """

    def __init__(self, model_name: str = "gemini/gemini-1.5-flash"):
        """
        Initializes the client.

        Args:
            model_name: The target model identifier to use (litellm format).
                        Default: 'gemini/gemini-1.5-flash'.
        """
        self.model_name = model_name

    def extract_structured_data(
        self, text: str, json_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Passes unstructured text to the LLM to extract data matching a given JSON schema.

        Args:
            text: The text corpus to extract data from.
            json_schema: A python dictionary representing the JSON schema to strictly enforce.

        Returns:
            A python dictionary containing the extracted fields mapped to the schema.

        Raises:
            RuntimeError: If the LLM interaction fails or the format cannot be enforced.
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

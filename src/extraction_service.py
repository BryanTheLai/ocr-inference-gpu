"""
Module: extraction_service.py
Provides hybrid extraction by passing serialized OCR text through an LLM,
then recursively grounding the semantic output back to spatial bounding boxes.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

from src.core.llm_client import LLMClient
from src.ocr_service import Detection

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Combines spatial OCR data with an LLM to produce structurally sound, visually grounded representations.

    Acts as a bridge between absolute coordinates extracted via PaddleOCR and relative semantic
    meaning extracted via natural language processing.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initializes the hybrid extraction service.

        Args:
            llm_client: Injected client instance to override the default LLM implementation.
        """
        self.llm_client = llm_client or LLMClient()

    def process_hybrid_extraction(
        self, ocr_results: List[Detection], extraction_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        serialized_text, text_index_map = self._serialize_ocr(ocr_results)
        llm_parsed_data = self.llm_client.extract_structured_data(
            serialized_text, extraction_schema
        )
        grounded_data = self._ground_bboxes(llm_parsed_data, text_index_map)

        return {
            "parsed_data": grounded_data,
            "raw_ocr_summary": [
                {"id": k, "text": v["text"]} for k, v in text_index_map.items()
            ],
        }

    def _serialize_ocr(
        self, ocr_results: List[Detection]
    ) -> Tuple[str, Dict[str, Dict[str, Any]]]:
        """
        Converts array of OCR block dictionaries into a flat numbered text sequence.

        Args:
            ocr_results: List of block dictionaries with 'text', 'box', 'page_number'.

        Returns:
            Tuple of (formatted block string for LLM context, dict mapping block IDs to original block data).
        """
        lines = []
        text_index_map = {}

        for idx, block in enumerate(ocr_results):
            block_id = f"B{idx}"
            text = block.get("text", "").strip()
            if not text:
                continue

            text_index_map[block_id] = {
                "text": text,
                "box": block.get("box", []),
                "page_number": block.get("page_number", 1),
            }
            lines.append(f"[{block_id}] {text}")

        return chr(10).join(lines), text_index_map

    def _ground_bboxes(
        self, parsed_data: Any, text_index_map: Dict[str, Dict[str, Any]]
    ) -> Any:
        """
        Recursively walks JSON output and attaches bounding boxes to values.

        Args:
            parsed_data: Arbitrary JSON output extracted by the LLM.
            text_index_map: Map of block IDs to their original bounding box/page locations.

        Returns:
            The identical JSON structure, leaf-nodes enhanced with `bbox` and `page_number` properties.
        """
        if isinstance(parsed_data, dict):
            return {
                k: self._ground_bboxes(v, text_index_map)
                for k, v in parsed_data.items()
            }
        if isinstance(parsed_data, list):
            return [self._ground_bboxes(item, text_index_map) for item in parsed_data]

        return self._find_best_match(str(parsed_data), text_index_map)

    def _find_best_match(
        self, value_str: str, text_index_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates longest sequence match between an LLM field and the original OCR blocks.

        Args:
            value_str: The primitive numeric or string value extracted.
            text_index_map: Map of block IDs to their original source chunks.

        Returns:
            Dictionary containing the value, matching bbox coordinates, page number, and confidence.
        """
        if not value_str or len(value_str) < 2:
            return {
                "value": value_str,
                "bbox": None,
                "page_number": None,
                "confidence": 0.0,
            }

        best_match_id = None
        best_ratio = 0.0

        for block_id, block_data in text_index_map.items():
            ocr_text = block_data["text"]
            matcher = SequenceMatcher(None, value_str.lower(), ocr_text.lower())
            match = matcher.find_longest_match(0, len(value_str), 0, len(ocr_text))
            ratio = match.size / len(value_str) if len(value_str) > 0 else 0.0

            if ratio > best_ratio:
                best_ratio = ratio
                best_match_id = block_id

        if best_match_id and best_ratio > 0.6:
            matched_block = text_index_map[best_match_id]
            return {
                "value": value_str,
                "bbox": matched_block["box"],
                "page_number": matched_block["page_number"],
                "confidence": round(best_ratio, 2),
            }

        return {
            "value": value_str,
            "bbox": None,
            "page_number": None,
            "confidence": 0.0,
        }

# Hybrid Extraction Architecture

This document explains why the OCR engine uses a hybrid approach (PaddleOCR + LLM) rather than a pure Vision-Language Model (VLM) or raw LLM PDF ingestion.

## The Problem

Standard LLMs (like Gemini or GPT-4) can parse basic text from PDFs and return structured JSON. However, they fail at spatial grounding: mapping the extracted data back to exact pixel coordinates `[x1, y1, x2, y2]`. Enterprise use cases require exact bounding boxes for auditability and UI highlighting.

Pure VLMs suffer from hallucination on dense documents and perform slower than standard layout-parsing models.

## The Solution: Spatial-Semantic Hybrid 

We separate the extraction into two distinct responsibilities:

1. **Spatial Truth (PaddleOCR)**: Scans the rasterized image and outputs deterministic bounding boxes and raw text chunks.
2. **Semantic Understanding (LLM)**: Reads the flattened text chunks against a provided JSON schema and outputs strictly formatted JSON. 

## The Re-Grounding Mechanism

The `ExtractionService` joins these two layers:

1. **Serialize**: OCR blocks are assigned a unique ID (e.g., `[B0] Invoice: 1234`).
2. **Extract**: The LLM processes this text and returns a JSON object.
3. **Ground**: The service recursively crawls the LLM's JSON. For every primitive value, it performs fuzzy string matching (`difflib.SequenceMatcher`) against the original indexed OCR blocks to retrieve the exact bounding box and page number.

## Tradeoffs
- **Added latency**: Requires two sequential model passes (PaddleOCR -> LLM).
- **Matching failure**: If the LLM heavily mutates the text (e.g., correcting spelling), fuzzy matching may fail to confidently map the bounding box, returning `null` coordinates. 

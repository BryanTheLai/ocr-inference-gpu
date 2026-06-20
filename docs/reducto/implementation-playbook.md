# Applying the Reducto Corpus to `ocr-inference-gpu`

This repo currently exposes asynchronous OCR over PDFs/images using FastAPI, Celery, Redis, and PaddleOCR PP-StructureV3. The Reducto corpus suggests a path from "OCR detections" to "document intelligence infrastructure."

## Current Baseline

Observed from the repo:

- FastAPI endpoint queues OCR jobs at `/api/v1/ocr/process`.
- Celery/Redis handle async execution and task results.
- `OCRService` converts PDFs to page images, runs a PaddleX PP-StructureV3 pipeline on GPU, and returns detections.
- Current output shape is text, box, confidence, and page number.
- The README positions the system as GPU-accelerated OCR with layout/table extraction models available in the underlying pipeline.

The strongest near-term opportunity is to preserve more structure from PP-StructureV3 instead of collapsing results to text detections.

## Product North Star

Build toward a self-hosted document ingestion engine:

1. Parse pages into layout-aware blocks with citations.
2. Chunk documents into LLM-ready units.
3. Extract JSON fields with schemas.
4. Verify extraction against document evidence.
5. Feed downstream search, RAG, analytics, and workflow tools.

The system does not need to copy Reducto feature-for-feature. The durable lesson is the stack shape: OCR -> structure -> chunks -> citations -> schemas -> verification -> connectors.

## Capability Roadmap

### 1. Preserve Full Parse Structure

Why:

- Reducto's repeated claim is that flattened OCR is insufficient for RAG, legal evidence, healthcare, insurance, finance, and compliance.
- Tables, layout types, figure regions, checkbox states, and reading order are correctness-critical.

Recommended output model:

```json
{
  "document_id": "string",
  "pages": [
    {
      "page_number": 1,
      "width": 1700,
      "height": 2200,
      "blocks": [
        {
          "block_id": "p1-b12",
          "type": "table|text|title|figure|header|footer|checkbox|form_field",
          "text": "string",
          "bbox": [[0, 0], [1, 0], [1, 1], [0, 1]],
          "confidence": 0.98,
          "reading_order": 12,
          "children": [],
          "metadata": {}
        }
      ]
    }
  ]
}
```

Implementation note:

- First inspect raw PP-StructureV3 result objects and retain all layout/table fields before reducing them.
- Keep the existing detection-only response as a compatibility mode if needed.

### 2. Add Citation-Ready Normalized Bounding Boxes

Why:

- Citations/bounding boxes are required across legal, clinical, insurance, finance, compliance, and public-sector cases.
- Current boxes appear pixel-based; downstream UIs benefit from normalized coordinates and page dimensions.

Recommended:

- Return both pixel and normalized boxes.
- Include page width/height after rendering.
- Include original page number and render scale.

### 3. Add Chunking

Why:

- Reducto's RAG guidance repeatedly centers on chunk quality.
- Chunks should preserve semantic structure and metadata.

Modes to support:

- `page`: one chunk per page.
- `block`: one chunk per layout block.
- `variable`: combine adjacent blocks until target character range.
- `section`: group by headings when available.

Chunk fields:

```json
{
  "chunk_id": "string",
  "text": "markdown or canonical text",
  "page_start": 1,
  "page_end": 2,
  "block_ids": ["p1-b12", "p1-b13"],
  "bbox_refs": [],
  "metadata": {
    "layout_types": ["title", "text", "table"],
    "source_file": "..."
  }
}
```

Default:

- Use variable chunking for RAG-style use cases, mirroring the Reducto recommendation.

### 4. Add Table and Form Semantics

Why:

- Tables are the most repeated hard case: flattened tables, shifted rows, wrong headers, financial statements, claims, spreadsheets.
- Checkboxes and forms are high-stakes in healthcare and insurance.

Recommended:

- Preserve row/column structure when PP-StructureV3 provides it.
- Return table as HTML/Markdown/CSV-like data plus cell bboxes.
- Detect checkbox state explicitly: checked, unchecked, ambiguous.
- Keep template labels and filled-in values separate.

### 5. Add Schema Extraction as a Separate Endpoint

Why:

- Reducto's Extract API is a separate layer above Parse.
- Schema quality is a major accuracy determinant.

Suggested endpoint:

- `POST /api/v1/extract/process`
- Inputs:
  - file or existing parse task id
  - JSON schema
  - system prompt
  - extraction options
- Outputs:
  - structured JSON
  - field citations
  - missing/ambiguous/null states

Schema linting rules from the corpus:

- Reject or warn on fields without descriptions.
- Warn on generic keys like `id_32`.
- Suggest enums for small finite value sets.
- Warn when descriptions ask the model to do math.
- Require a system prompt for complex documents.

### 6. Add Verification Loops

Why:

- Deep Extract and Agentic OCR are the main quality leap.
- Single-pass extraction silently drops rows and fabricates structure.

Start simple:

- Schema-level required-field completeness checks.
- Citation existence checks for every extracted field.
- Numeric reconciliation hooks:
  - invoice lines sum to total
  - assets equal liabilities plus equity
  - count extracted table rows against detected table rows
- Regex/domain validators:
  - dates
  - currency codes
  - account numbers
  - NPI/HCPCS/NDC style identifiers when relevant

Then add model-based verification:

- Generate a checklist from the schema/system prompt.
- Re-read cited chunks only.
- Flag unsupported fields.
- Re-run extraction for missing/unsupported fields.

### 7. Add Webhooks

Why:

- August moved from polling to webhooks as volume grew.
- Long document processing and enterprise workflows should not require polling loops.

Recommended:

- Accept optional `webhook_url` on process endpoints.
- Send signed completion payload.
- Retry with backoff.
- Include task id, status, output URL or result summary.

### 8. Add Evaluation Harness

Why:

- Reducto's corpus stresses holdout datasets, real customer edge cases, and benchmark mismatch.
- Quality cannot be inferred from visual demos alone.

Test sets to build:

- Dense financial tables.
- Multi-page invoices with totals.
- Forms with checkboxes and handwriting.
- Rotated/off-angle scans.
- Low-contrast scans/faxes.
- Multi-column reports.
- Long spreadsheets.
- PowerPoint-like screenshot pages.
- Charts with bars, lines, negative values, and dense series.

Metrics:

- Character/text accuracy.
- Block completeness.
- Layout class accuracy.
- Reading-order accuracy.
- Table cell accuracy.
- Checkbox state accuracy.
- Field extraction accuracy.
- Citation IoU / citation correctness.
- SLA percentiles.
- Queue time vs processing time.

### 9. Add Connectors and Data Outputs

Why:

- Reducto value often appears downstream: Elasticsearch, Databricks, Delta Lake, vector DBs, document vaults, no-code workflows.

Useful exports:

- JSON parse result.
- JSONL chunks for vector indexing.
- Markdown document.
- CSV tables.
- HTML tables with bbox metadata.
- Parquet/Delta-friendly flat records.

Connector targets:

- Elasticsearch sparse/vector search.
- Weaviate or another vector DB.
- Databricks/Spark batch output.
- S3-compatible object store.

## Architecture Guardrails

- Keep OCR parse, chunking, extraction, and verification as separate stages.
- Store intermediate artifacts by job id so later stages can run without re-OCR.
- Make page complexity visible; route simple pages cheaply and hard pages through heavier processing.
- Treat citations as first-class fields in every output object.
- Never discard raw model output until normalization code is stable.
- Maintain compatibility for existing `text + box + confidence + page_number` clients.

## High-Value Use Cases for This Repo

1. RAG ingestion:
   - Parse -> chunk -> embed/index -> answer with citations.
2. Financial statements and invoices:
   - Tables, line items, totals, reconciliation.
3. Healthcare/insurance forms:
   - Checkboxes, handwritten notes, field extraction, exact citations.
4. Legal discovery:
   - Multilingual OCR, table preservation, chunk-level bounding boxes.
5. Compliance evidence:
   - Screenshot/document parsing, evidence completeness checks.
6. Wealth-management document ops:
   - Document classification, renaming fields, custodian statement extraction.

## Immediate Next Implementation Slice

Smallest useful code change:

1. Add a richer internal parse model with pages and blocks.
2. Modify `OCRService` to capture page dimensions and normalized bboxes.
3. Return both existing `detections` and new `pages[].blocks[]` in task result.
4. Add a `chunking` utility that creates page/block/variable chunks from blocks.
5. Add tests for bbox normalization and chunk grouping.

This gives the project a foundation for extraction, RAG, citations, and verification without immediately adding LLM dependencies.

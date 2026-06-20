# What Matters From The Reducto Corpus

For `ocr-inference-gpu`, keep the engineering patterns and discard the marketing/archive detail.

## Keep

- Preserve layout structure, not only OCR text. The current service returns text boxes; the next useful step is pages, blocks, reading order, tables, figures, and normalized citations.
- Treat bounding boxes as a first-class API contract. Legal, healthcare, insurance, finance, and RAG workflows all need traceability back to the source page.
- Add chunking as a separate stage after OCR. Support page, block, and variable semantic chunks so downstream search/RAG can index useful units.
- Preserve table/form semantics. Rows, columns, headers, checkboxes, and filled values are where OCR systems often fail in production.
- Add schema extraction later, but only after parse/chunk output is solid. Good schema descriptions, enums, null handling, and system prompts matter more than clever prompts.
- Add verification loops for high-stakes extraction. Start with deterministic checks: required fields, citations exist, totals reconcile, row counts match, checkbox state is present.
- Build an evaluation set from hard documents: dense tables, forms, handwriting, rotated scans, fax artifacts, multi-column reports, long spreadsheets, charts, and checkboxes.
- Keep async jobs and add webhooks when volume grows. Polling is fine for demos; webhooks are better for real document pipelines.
- Store intermediate parse artifacts by job id so extraction, chunking, and verification can run without rerunning OCR.
- Route by page complexity when possible. Simple pages should stay cheap; hard pages can use heavier multi-pass logic.

## Do Not Keep

- Funding announcements, valuation, investor names, and marketplace/procurement copy.
- Long customer narratives except as use-case examples.
- Reducto-specific SDK snippets unless this repo is integrating with Reducto directly.
- AWS Marketplace, Studio, sales/demo, and pricing links.
- Company positioning like "most accurate" unless backed by local benchmarks.
- Case-study metrics that do not translate into repo tests or product requirements.
- Zero-downtime Postgres migration details unless this repo later grows a database that needs that exact migration pattern.
- Full source URL inventory. Keep source provenance outside durable repo docs unless citations are required.
- Competitor score tables except as inspiration for local eval datasets.

## Translate Into This Repo

Immediate useful sequence:

1. Return richer parse results while preserving the existing detection output.
2. Add normalized bounding boxes and page dimensions.
3. Add chunk generation from parse blocks.
4. Add table/form-preserving output where PaddleOCR exposes it.
5. Add a small hard-document evaluation harness.
6. Add extraction and verification only after the parse model is stable.

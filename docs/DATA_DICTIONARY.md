# Candidate data dictionary

All field meanings below describe storage and provenance, not validated business rules.

| Family | Key fields | Interpretation |
| --- | --- | --- |
| Zones | `code_zone`, `search_name_fr`, `price_decimal`, `original`, `quality_flags` | SQL-derived zone ID and candidate name/price. The original row remains nested; `price_decimal` does not override published plot prices. |
| Lots | `lot_id`, `zone_id`, `lot_number`, `surface_lotis_decimal`, `status_code_raw`, `status_meaning`, `quality_flags` | SQL-derived lot. Internal status-code semantics remain unknown; no availability assertion follows from a status field. |
| Public plot observation | `capture_time`, `fields`, `observed_map_label`, `state`, `source_snapshot_sha256` | A dated captured search result. `unknown` and `conflicting` states must remain explicit. |
| GIS | `kind`, `geometry`, `geometry_status`, `crs`, `source`, `attributes` | Original coordinate values are preserved. An unknown CRS is not assigned a guessed SRID. Invalid or missing geometry stays flagged. |
| OCR checkpoint | `source_sha256`, `page`, `text`, `text_sha256`, `version_id`, `capture_times`, `review_status` | Page candidate extracted by provisional OCR. Original source hash and extraction method identify provenance. |
| Article | `document_sha256`, `source_page`, `article_number`, `original_text_candidate`, `extraction_method`, `review_status` | Page-local regulatory fragment; legal applicability and text accuracy remain pending review. |
| Institutional passage | `passage_id`, `passage`, `sources`, `source_body_sha256`, `review_status` | Cleaned captured-web text with source references; claims are not validated. |
| Retrieval chunk | `chunk_id`, `kind`, `text`, `text_sha256`, source fields, `review_status` | One article fragment or passage. Candidate-only retrieval, no dense embedding claim. |
| RDF instances | `candidate.ttl` | Named candidate graph; ontology schema is separately in `ontology/`. No production knowledge graph is published. |

JSONL is UTF-8, one JSON object per line. The exact per-record schemas and source fields can be inspected locally after authorization. Published JSON schemas in `schemas/` cover regulatory article candidates and evaluation cases. A field appearing in a source row is not by itself a permission to publish it.

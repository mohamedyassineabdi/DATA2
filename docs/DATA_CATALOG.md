# Data catalog

DATA2 separates public project-owned files from the protected local candidate corpus. Paths below are relative to the repository root. The `local_only/` tree is ignored by Git and is available only after an approved local transfer installed with `setup_data.ps1 -Archive` (or, for the historical source tree, `build_local_workspace.py`). The [root README](../README.md) has the measured sizes, source/access status and complete installation workflow.

| Local path | Format | Measured quantity | Status |
| --- | --- | ---: | --- |
| `local_only/data/original/pdfs/` and `original/web/` | PDF | 114 unique; 3,396 pages | Original, reuse pending |
| `local_only/data/original/sql/afi.sql` | SQL | 13 tables; 15,841 rows | Original, privacy and reuse pending |
| `local_only/data/original/ocr_pilot/images/` | PNG | 30 pages | Original review evidence, local only |
| `local_only/data/processed/ocr/best/pages/` | JSON | 2,996 checkpoints | Unvalidated OCR |
| `local_only/data/processed/ocr/empty_alternatives/` | JSON and text | 12 empty outcomes with alternatives | Unvalidated OCR |
| `local_only/data/processed/regulations_and_institutional/article_candidates.jsonl` | JSONL | 7,587 | Unvalidated regulatory fragments |
| `local_only/data/processed/regulations_and_institutional/institutional_passages.jsonl` | JSONL | 2,794 | Unvalidated institutional passages |
| `local_only/data/processed/retrieval/chunks.jsonl` | JSONL | 10,381 | Candidate lexical corpus |
| `local_only/data/processed/relational/zones.jsonl` | JSONL | 185 | Derived SQL candidates |
| `local_only/data/processed/relational/lots.jsonl` | JSONL | 6,579 | Derived SQL candidates |
| `local_only/data/processed/public_plot_observation/records.jsonl` | JSONL | 720 | Dated public-search observation; not live availability |
| `local_only/data/processed/gis/candidates/candidates.jsonl` | JSONL | 12,006 | Candidate coordinates and geometry |
| `local_only/data/processed/knowledge_graph/candidate.ttl` | Turtle | 93,495 triples | Unvalidated RDF instances |
| `local_only/data/processed/institutional/pages/pages.jsonl` | JSONL | 345 | Cleaned web candidates |
| `local_only/data/processed/institutional/structured/candidates.jsonl` | JSONL | 977 | Structured web candidates |
| `local_only/data/review/document_identities/matrix.json` | JSON | 106 references | Identity review pending |
| `local_only/data/review/prioritized_packets/packets.jsonl` | JSONL | 6,905 | Human review pending |
| `schemas/examples/multilingual-evaluation-drafts.json` | JSON | 224 | Public synthetic drafts, no gold answers |

The full local file inventory, source-to-canonical migration map, SHA-256 values and record counts are in `local_only/audit/`. The public `manifests/` directory describes publication status without exposing source records. Source URLs, capture times and extraction configurations remain in the original records and frozen manifest. No material in `local_only/` is approved for external AI transmission or GitHub upload.

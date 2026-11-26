# Reproducibility verification

Performed locally on 2026-11-26. The old Dalila services and frozen manifest were preserved.

| Check | Result |
| --- | --- |
| Original workspace inventory | 5,472 files; 6,981,930,590 bytes; 4,670 distinct SHA-256 values |
| Exact duplicate detection | 315 groups; 802 extra source paths; 3 duplicate PDF copies removed from new workspace |
| Canonical local copy | 3,377 source mappings → 3,374 physical files, 1,250,493,051 bytes; every mapped checksum passed |
| JSON/JSONL and CSV | 3,159 JSON/JSONL files and 2 CSV files parsed without errors |
| PDFs and document links | 114 PDFs opened; 3,396 pages; zero missing/out-of-range OCR and article PDF references |
| Knowledge candidates | 7,587 articles, 2,794 passages, 10,381 chunks, 93,495 RDF triples; zero chunk-hash or article-page link failures |
| Quality flags retained | 352 native-text articles without OCR checkpoints; 24 lot-zone misses; 13 invalid and 2,037 missing geometries |
| Isolated MariaDB import | 13 tables, 15,841 rows; representative `lots` query returned 6,579 |
| Isolated PostGIS import | 12,006 geometry records, 9,945 staged geometries, zero nonzero SRIDs; 185 zones, 6,579 lots, 24 unmatched lot-zone references |
| Isolated Fuseki import | Candidate graph loaded; SPARQL count returned 93,495 triples |
| Isolated Qdrant import | 10,381 sparse candidate points; all 10,381 chunk IDs matched by full scroll; sample lexical query returned three results |
| Negative tests | All four loaders refused an existing target; MariaDB/PostGIS wrong passwords and Fuseki/Qdrant wrong credentials were denied |
| Public Git audit | No raw/processed/local-only path, source binary, email-shaped string, token or private key in tracked files |
| Fresh public clone | Manifest SHA-256 verification and five unit tests passed; remote main matched local commit |
| Regression suites | Five DATA2 unit tests and 117 existing Dalila foundation tests passed |

The isolated database project used alternate loopback ports and separate persistent volumes. `docker compose config --quiet` passed. The first PostGIS test exposed implicit GeoJSON SRID 4326; the loader was corrected to set SRID 0, the isolated candidate schema was reset, and the clean import then passed. The first Fuseki test exposed an `internal` Docker network that suppressed host port publishing on this host; the Compose template now uses a private project bridge with loopback-bound ports. No source data was sent to an external service.

After recording aggregate results, the `dalila-data2-verify` containers and their four test-only volumes were removed. The pre-existing `dalila-foundation-*` containers remained healthy throughout.

The public clone cannot pass the protected-corpus checks or load candidate databases without a separately authorized local source transfer. The owner confirmed no written redistribution permission exists. The absent AFI capture archive and pending human review also prevent a complete public data-release claim.

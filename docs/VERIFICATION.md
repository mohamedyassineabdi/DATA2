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
| Fresh virtual environment | Dependencies installed with pip 24.0 `--use-feature=truststore`; five tests passed; ontology parsed to 157 triples and SHACL shapes to 69 triples |
| Regression suites | Five DATA2 unit tests and 117 existing Dalila foundation tests passed |

## Fresh-clone onboarding test

On 2026-11-26, a new remote clone at `DATA2_onboarding_verify` started without protected data or access to the historical workspace. The first attempt detected two CRLF-derived manifest mismatches after Git checkout; the manifest writer now rejects CRLF and the corrected remote clone passed public setup. Python dependencies installed using the Windows system trust store. `setup_data.ps1` reported `public_only` and started no empty databases.

The same clone then installed the existing verified v2 archive through `setup_data.ps1 -Archive` into ignored `local_only/`. Its 3,383 ZIP entries, archive SHA-256, 3,377 canonical source mappings and all structural record checks passed. The isolated project `dalila-data2-onboard-verify` generated fresh local credentials, selected loopback ports, started MariaDB/PostGIS/Fuseki/Qdrant and optional Redis, and loaded 13 SQL tables/15,841 rows, 12,006 GIS candidates (9,945 staged, SRID 0), 185 zones, 6,579 lots, 93,495 RDF triples and 10,381 Qdrant sparse points. Aggregate SQL, PostGIS, SPARQL and lexical retrieval queries passed; Redis returned `PONG` through its ACL. Nine DATA2 unit tests passed in that clone.

The README's PowerShell here-string SQL command returned 6,579. The generated `.env` and Redis ACL inherited filesystem ACLs limited to the current user, local administrators and SYSTEM on this Windows host. `docker compose config --quiet` passed for the generated environment. This local ACL check does not establish a portable production secret-management design.

The unauthenticated GitHub repository API reported `private=false`, `visibility=public` and default branch `main`. That confirms the public access boundary; it does not confer redistribution rights on source material.

A second `complete` run verified the same corpus and found all four database targets complete without reimport. `verify`, `data-only`, `db-only` and each `load-mariadb`, `load-postgis`, `load-fuseki`, `load-qdrant` mode ran against the already-populated project and passed without reimporting. The old `db-only` summary misleadingly said `initialized_empty_no_import` even for populated services; it now reports only that services started without importing or overwriting. An approved HTTPS download was **not** tested because no approved endpoint exists. A new empty-project `db-only` run and the Linux/macOS wrapper were not tested on this Windows machine. The original Dalila workspace and services were not used by this clone.

The isolated database project used alternate loopback ports and separate persistent volumes. `docker compose config --quiet` passed. The first PostGIS test exposed implicit GeoJSON SRID 4326; the loader was corrected to set SRID 0, the isolated candidate schema was reset, and the clean import then passed. The first Fuseki test exposed an `internal` Docker network that suppressed host port publishing on this host; the Compose template now uses a private project bridge with loopback-bound ports. No source data was sent to an external service.

After recording aggregate results, the `dalila-data2-verify` containers and their four test-only volumes were removed. The pre-existing `dalila-foundation-*` containers remained healthy throughout.

The public clone cannot pass the protected-corpus checks or load candidate databases without a separately authorized local source transfer. The owner confirmed no written redistribution permission exists. The absent AFI capture archive and pending human review also prevent a complete public data-release claim.

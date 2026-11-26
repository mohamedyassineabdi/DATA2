# Dalila DATA2

DATA2 is a clean, public home for Dalila's data-foundation tooling, ontology, schemas, and **224 synthetic multilingual evaluation drafts**. It is not a publication of the AFI source corpus. Source-bearing datasets are consolidated locally under the ignored `local_only/` directory until redistribution rights and record-level privacy review are documented.

## Available in this repository

| Path | Contents | Status |
| --- | --- | --- |
| `ontology/` | RDF/OWL vocabulary, SHACL shapes and query examples | Project-authored schema; no validated instance graph |
| `schemas/` | Regulatory and evaluation schemas; 224 eight-language evaluation drafts | Synthetic drafts; factual answers and relevance judgments pending |
| `infrastructure/` | Local candidate database Compose template | Configuration only; no database data |
| `scripts/` | Reversible local consolidation, deduplication and checksum verification | Requires separately authorized source tree |
| `manifests/` | Public release inventory and local dataset-family summary | Metadata only |

No source text, AFI SQL records, PDFs, OCR, institutional captures, GIS geometries, retrieval chunks or RDF instances are committed here. Their absence is a publication boundary, not an indication that they do not exist.

## Reconstruct the local candidate workspace

An authorized teammate with a separately transferred copy of the original Dalila data tree can run:

```powershell
git clone https://github.com/mohamedyassineabdi/DATA2.git
cd DATA2
python scripts/build_local_workspace.py --source 'C:\path\to\dalila_data'
python scripts/deduplicate_local_pdfs.py
python scripts/verify_local_workspace.py
```

The build copies bytes without editing the source, records source-relative paths, SHA-256 hashes, formats and record counts in `local_only/audit/`, and keeps all candidate content out of Git. The source tree must be supplied through an approved local transfer; this repository does not provide it.

Database configuration is in `infrastructure/env.example` and `infrastructure/compose.yaml`. Run `docker compose --env-file infrastructure/env.example -f infrastructure/compose.yaml config --quiet` to validate the template. Do not load local candidates into validated or production stores. The old, frozen 30-dataset candidate manifest remains in the original protected workspace; DATA2 does not replace its checksums.

For the optional Redis coordination profile, set a unique `REDIS_COORDINATION_PASSWORD`, run `python scripts/prepare_redis_acl.py`, and keep `infrastructure/redis-users.local.acl` local. Replace every placeholder in a private environment file before starting services.

See [DATA_STATUS.md](DATA_STATUS.md) and [publication decision](docs/PUBLICATION_BOUNDARY.md) for measured counts and the specific permission needed to publish the remaining real datasets.

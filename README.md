# Dalila DATA2

Dalila prepares industrial-land, regulatory and institutional information for a future multilingual investor assistant. DATA2 is its clean, public data-foundation workspace: tooling, ontology, schemas, and **224 synthetic multilingual evaluation drafts**. It is not a publication of the AFI source corpus. Source-bearing datasets are consolidated locally under the ignored `local_only/` directory until redistribution rights and record-level privacy review are documented.

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

`python scripts/package_local_candidate.py` creates a self-contained ZIP in `local_only/transfer_pending/` and tests its ZIP integrity. **It is not encrypted or approved for transfer.** Encrypt it for named, authorized recipients only after source redistribution and privacy decisions are recorded.

Database configuration is in `infrastructure/env.example` and `infrastructure/compose.yaml`. Run `docker compose --env-file infrastructure/env.example -f infrastructure/compose.yaml config --quiet` to validate the template. Do not load local candidates into validated or production stores. The old, frozen 30-dataset candidate manifest remains in the original protected workspace; DATA2 does not replace its checksums.

For the optional Redis coordination profile, set a unique `REDIS_COORDINATION_PASSWORD`, run `python scripts/prepare_redis_acl.py`, and keep `infrastructure/redis-users.local.acl` local. Replace every placeholder in a private environment file before starting services.

See [DATA_STATUS.md](DATA_STATUS.md) and [publication decision](docs/PUBLICATION_BOUNDARY.md) for measured counts and the specific permission needed to publish the remaining real datasets.

For the dataset tree, field definitions, architecture, tested setup commands, structural checks and actual isolated database results, see [catalog](docs/DATA_CATALOG.md), [dictionary](docs/DATA_DICTIONARY.md), [architecture](docs/ARCHITECTURE.md), [quickstart](docs/QUICKSTART.md), [quality](docs/DATA_QUALITY.md) and [verification](docs/VERIFICATION.md). The full file-level migration and checksum manifest is in `local_only/audit/`; public metadata is in `manifests/`.

The current public files are small enough for ordinary Git. GitHub enforces a [100 MB regular-Git object limit](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits), and [Git LFS has metered storage/bandwidth beyond its allowance](https://docs.github.com/en/billing/concepts/product-billing/git-lfs). No LFS objects or paid artifact storage were created. Large source files remain local while publication rights are unresolved.

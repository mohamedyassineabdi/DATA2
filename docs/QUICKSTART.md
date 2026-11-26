# Teammate quickstart

The [root README](../README.md) is the complete onboarding guide. The tested entry point is `setup_data.ps1` (or `setup_data.sh` on Linux/macOS). A clone alone contains public tooling and synthetic evaluation drafts; it does **not** contain the real candidate corpus.

```powershell
git clone https://github.com/mohamedyassineabdi/DATA2.git
cd DATA2
.\setup_data.ps1
```

This public-only command was tested from a fresh clone. On the verification Windows machine, pip 24 needed a retry with its `--use-feature=truststore` option; the script used the system certificate store and completed. For actual candidate data, obtain a separately approved, encrypted transfer of the existing archive, decrypt it locally and run:

```powershell
.\setup_data.ps1 -Archive 'C:\approved\DATA2_local_candidate_v2.zip'
```

The v2 archive has SHA-256 `0addeb821a93e0d96bf40bc2edf893e184b221ec81d665cfbfc52514a3f0b1a2`. It is not on GitHub; the owner's local ZIP is unencrypted and not approved for transfer. The complete installation from that ZIP was tested in an isolated fresh clone. Other supported modes and troubleshooting are in the README.

The public clone includes the ontology and 224 synthetic evaluation drafts. It cannot read AFI PDFs, articles, lots or GIS without an approved source transfer. If an authorized teammate has the **historical source workspace instead of the v2 archive**, the older reconstruction path remains available:

```powershell
.venv\Scripts\python scripts/build_local_workspace.py --source 'C:\approved\dalila_data'
.venv\Scripts\python scripts/deduplicate_local_pdfs.py
.venv\Scripts\python scripts/verify_local_workspace.py
.venv\Scripts\python scripts/verify_candidate_data.py
.venv\Scripts\python scripts/write_local_dataset_manifest.py
```

For isolated candidate databases, copy `infrastructure/env.example` to `infrastructure/.env`, replace all placeholder secrets, and set unused loopback ports if the original Dalila stack is running. Then run:

```powershell
docker compose --env-file infrastructure/.env -f infrastructure/compose.yaml -p dalila-data2-local up -d --wait mariadb postgis qdrant fuseki
.venv\Scripts\python scripts/load_candidate_stack.py
.venv\Scripts\python scripts/load_candidate_stack.py --apply --project dalila-data2-local --mariadb
.venv\Scripts\python scripts/load_candidate_stack.py --apply --project dalila-data2-local --postgis
.venv\Scripts\python scripts/load_candidate_stack.py --apply --project dalila-data2-local --fuseki
.venv\Scripts\python scripts/load_candidate_stack.py --apply --project dalila-data2-local --qdrant
.venv\Scripts\python scripts/query_candidate_stack.py --project dalila-data2-local
```

All imports are candidate-only. The loader refuses to overwrite pre-existing candidate tables or collections. `docker compose ... down` stops services without deleting persistent volumes; retain backups before intentional volume removal.

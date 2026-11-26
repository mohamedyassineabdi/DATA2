# Teammate quickstart

```powershell
git clone https://github.com/mohamedyassineabdi/DATA2.git
cd DATA2
python -m venv .venv
.venv\Scripts\python -m pip install --use-feature=truststore -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -q
```

The `--use-feature=truststore` option was needed with pip 24.0 on the verification Windows machine to use its trusted certificate store. If your pip already uses the system trust store or no longer supports this option, run `pip install -r requirements.txt` with your normal organization-approved certificate configuration.

The public clone includes the ontology and 224 synthetic evaluation drafts. It cannot read AFI PDFs, articles, lots or GIS because those bytes are intentionally not public. To reconstruct them, first obtain explicit source reuse and access approval, then receive a separately encrypted source tree from the owner. After local extraction:

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

# DATA2 data status

As of 2026-11-26, the local source tree was inventoried without modifying it. The inventory covers **5,472 files / 6,981,930,590 bytes**, with **4,670 distinct SHA-256 values** and **802 extra exact duplicate files in 315 groups**. The protected canonical copy maps **3,272 source files / 1,225,020,909 source bytes**; 117 PDF source paths reduce to **114 distinct PDF hashes and 114 physical PDF copies**. These counts exclude Git worktrees, backups, model caches and temporary artifacts from the canonical copy.

Verified candidate row counts in the local copy: **2,996 OCR page JSON checkpoints**, **7,587 regulatory article candidates**, **2,794 institutional passages**, **10,381 retrieval chunks**, **6,579 normalized lots**, **185 normalized zones**, **12,006 GIS source candidates**, **345 institutional page candidates**, and **977 structured web candidates**. The public repository contains **224 synthetic multilingual evaluation drafts** across eight required languages. These are preparation counts, not accuracy or legal validation claims.

The original 30-dataset frozen candidate release remains in the source workspace. Its manifest SHA-256 is `85e1cc56941f2b960ed364bd02068adfdbce1035f059df736cee847dfba1a11e`. DATA2 does not modify or supersede it.

**Publication status:** project-authored tooling, ontology/schema and synthetic drafts are eligible. AFI SQL/PDF/web captures and source-derived OCR, knowledge, GIS, relational, retrieval and RDF instance records remain **local only pending redistribution evidence and privacy review**. The project owner confirmed no written source redistribution permission exists. No records are labeled validated or production-ready.

**Verification:** `scripts/verify_local_workspace.py` checks every mapped local file by size and SHA-256. `docker compose config --quiet` passed for the infrastructure template. Public Git audit and remote clone results are recorded in `manifests/public_release.json` after publication.

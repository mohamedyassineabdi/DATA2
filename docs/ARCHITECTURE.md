# Data architecture

The original AFI and institutional source bytes remain immutable in the old workspace and in the protected local copy. Reproducible scripts produce candidate SQL projections, OCR page checkpoints, article/passages, GIS records, RDF instances and retrieval chunks. Each step retains source hashes, IDs and review status. The frozen 30-dataset Phase 2 candidate manifest remains the reference for the original preparation run.

MariaDB holds the isolated original SQL import. PostGIS stages source geometry as JSONB and assigns no unsupported SRID. Fuseki holds the unvalidated RDF in a candidate named graph. Qdrant uses a candidate lexical sparse collection keyed to the chunk corpus hash. Redis is optional for local coordination. The Compose template binds database interfaces to loopback and uses persistent volumes; it does not provide a production security posture.

The access boundary is `original → extracted candidate → reviewed → validated → published`. DATA2 currently contains the first two states only in ignored local storage; the public repository contains project-authored schemas and draft evaluation data. The `load_candidate_stack.py` command requires a separate `dalila-data2-*` Compose project and refuses existing MariaDB/PostGIS targets. Nothing loads into validated namespaces. A future backend must enforce candidate/validated access separation and cite source evidence before investor-facing claims.

The original project repository and frozen release are retained. The new Git history begins at DATA2's own root commit and contains no previous worktrees, raw source bytes or protected archives.

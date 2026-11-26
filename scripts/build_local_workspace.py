"""Create a reversible, checksum-verified local Dalila consolidation.

No source-bearing artifact is added to Git: outputs live under ignored local_only/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path


SOURCE_DIRS = ("raw", "processed", "reports", "evaluation", "manifests", "scripts", "schemas", "ontology", "infrastructure", "docs")
SKIP_PARTS = {".git", "__pycache__", ".venv", "worktrees", "backups", "artifacts", "model_cache"}
CANONICAL = {
    "raw/documents": "original/pdfs",
    "raw/web": "original/web",
    "raw/restricted/sql": "original/sql",
    "processed/ocr/best_candidate_v1": "processed/ocr/best",
    "processed/ocr/empty_retry_v1": "processed/ocr/empty_alternatives",
    "processed/ocr/quarantine_v1": "processed/ocr/standard_and_native",
    "processed/knowledge/candidates_v7": "processed/regulations_and_institutional",
    "processed/knowledge/rdf_candidates_v7": "processed/knowledge_graph",
    "processed/retrieval/candidate_chunks_v2": "processed/retrieval",
    "processed/relational/clean_candidates_v1": "processed/relational",
    "processed/relational/snapshot_read_model_v2": "processed/public_plot_observation",
    "processed/gis/candidates_v1": "processed/gis/candidates",
    "processed/gis/quality_candidates_v1": "processed/gis/quality",
    "processed/web/institutional_candidates_v2": "processed/institutional/pages",
    "processed/web/structured_candidates_v2": "processed/institutional/structured",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix.lower() not in {".jsonl", ".csv"}:
        return None
    with path.open("rb") as stream:
        count = 0
        last = b""
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += block.count(b"\n")
            last = block[-1:]
        if last and last != b"\n":
            count += 1
    return count - (1 if path.suffix.lower() == ".csv" and count else 0)


def walk_source(root: Path):
    for dirname in SOURCE_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and not any(part.lower() in SKIP_PARTS for part in path.relative_to(base).parts):
                yield path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    source = args.source.resolve()
    dest = args.destination.resolve()
    if source == dest or source in dest.parents:
        raise SystemExit("Destination must be separate from source")
    audit = dest / "local_only" / "audit"
    audit.mkdir(parents=True, exist_ok=True)
    inventory_path = audit / "full_inventory.jsonl"
    mapping_path = audit / "canonical_mapping.jsonl"
    hashes = defaultdict(list)
    counters = Counter()
    copied_hashes = {}
    with inventory_path.open("w", encoding="utf-8") as inventory, mapping_path.open("w", encoding="utf-8") as mapping:
        for path in walk_source(source):
            rel = path.relative_to(source).as_posix()
            digest = sha256(path)
            size = path.stat().st_size
            rows = row_count(path)
            record = {"source_path": rel, "sha256": digest, "bytes": size, "format": path.suffix.lower().lstrip("."), "record_count": rows}
            inventory.write(json.dumps(record, ensure_ascii=False) + "\n")
            counters["inventory_files"] += 1
            counters["inventory_bytes"] += size
            hashes[digest].append(rel)
            for prefix, target in CANONICAL.items():
                if rel.startswith(prefix + "/"):
                    suffix = rel[len(prefix) + 1:]
                    output = dest / "local_only" / "data" / target / suffix
                    if output.exists() and sha256(output) == digest:
                        pass
                    else:
                        output.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, output)
                    if sha256(output) != digest:
                        raise RuntimeError(f"Copy checksum mismatch: {rel}")
                    mapped = {**record, "local_path": output.relative_to(dest).as_posix(), "sharing": "local_only_pending_source_rights_and_content_review"}
                    mapping.write(json.dumps(mapped, ensure_ascii=False) + "\n")
                    copied_hashes[digest] = True
                    counters["canonical_files"] += 1
                    counters["canonical_bytes"] += size
                    break
    duplicates = [paths for paths in hashes.values() if len(paths) > 1]
    summary = {**counters, "distinct_sha256": len(hashes), "duplicate_groups": len(duplicates), "duplicate_extra_files": sum(len(group) - 1 for group in duplicates), "source_root": str(source), "publication_status": "local_only_pending_rights_review"}
    (audit / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (audit / "duplicates.jsonl").open("w", encoding="utf-8") as stream:
        for group in duplicates:
            stream.write(json.dumps({"sha256": sha256(source / group[0]), "paths": group}, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

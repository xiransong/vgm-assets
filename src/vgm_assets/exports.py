from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .catalog import _sha256
from .protocol import repo_root


def export_scene_engine_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    category_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    asset_catalog_out = output_dir / "asset_catalog.json"
    category_index_out = output_dir / "category_index.json"
    manifest_out = output_dir / "asset_catalog_manifest.json"

    shutil.copy2(catalog_path, asset_catalog_out)
    shutil.copy2(category_index_path, category_index_out)
    shutil.copy2(manifest_path, manifest_out)

    metadata = {
        "export_id": export_id,
        "consumer": "vgm-scene-engine",
        "source_catalog_id": source_catalog_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "producer": {
            "repo": "vgm-assets",
            "version": "0.1.0-dev",
            "commit": "working_tree",
        },
        "files": {
            "asset_catalog": {
                "path": asset_catalog_out.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(asset_catalog_out),
            },
            "category_index": {
                "path": category_index_out.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(category_index_out),
            },
            "asset_catalog_manifest": {
                "path": manifest_out.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(manifest_out),
            },
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "asset_catalog": str(asset_catalog_out.resolve()),
        "category_index": str(category_index_out.resolve()),
        "asset_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
    }

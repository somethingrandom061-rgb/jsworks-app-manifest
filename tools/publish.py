#!/usr/bin/env python3
# JSWORKS PUBLISH SCRIPT — FS20 / FS24 SCHEMA (NO name / NO download_url)

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVERIES_DIR = REPO_ROOT / "liveries"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


def is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def has_any_download(meta: Dict[str, Any]) -> bool:
    # FS20 / FS24 fields
    if is_nonempty_string(meta.get("download_fs20")):
        return True
    if is_nonempty_string(meta.get("download_fs2020")):
        return True
    if is_nonempty_string(meta.get("download_fs24")):
        return True
    if is_nonempty_string(meta.get("download_fs2024")):
        return True

    # downloads array
    downloads = meta.get("downloads", [])
    if isinstance(downloads, list):
        for d in downloads:
            if isinstance(d, dict) and is_nonempty_string(d.get("url")):
                return True

    return False


def validate_meta(file: Path, meta: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not is_nonempty_string(meta.get("id")):
        errors.append("missing required field: id")

    if not is_nonempty_string(meta.get("version")):
        errors.append("missing required field: version")

    if not has_any_download(meta):
        errors.append(
            "missing downloads (provide download_fs20 / download_fs24 or downloads[] with url)"
        )

    return errors


def main() -> int:
    print("JSWORKS publish.py — FS20 / FS24 schema active")

    if not LIVERIES_DIR.exists():
        print("ERROR: liveries/ folder not found")
        return 1

    items: List[Dict[str, Any]] = []
    failed = False

    for meta_file in sorted(LIVERIES_DIR.glob("*.meta.json")):
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"{meta_file.name}: invalid JSON ({e})")
            failed = True
            continue

        if not isinstance(meta, dict):
            print(f"{meta_file.name}: root JSON value must be an object")
            failed = True
            continue

        errors = validate_meta(meta_file, meta)
        if errors:
            for err in errors:
                print(f"{meta_file.name}: {err}")
            failed = True
            continue

        items.append(meta)

    if failed:
        print("Publish failed due to validation errors.")
        return 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest.json with {len(items)} item(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())

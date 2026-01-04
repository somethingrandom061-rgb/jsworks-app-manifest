#!/usr/bin/env python3
# JSWORKS publish.py — LEGACY SCHEMA (REVERTED)
# Expects:
#   - version
#   - download_fs20 / download_fs24
#   - package_folders_fs20 / package_folders_fs24
# Outputs manifest.json consumed by the app

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIVERIES_DIR = REPO_ROOT / "liveries"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


def validate_meta(meta: dict, fname: str):
    errors = []

    for field in ["id", "title_line", "developer", "aircraft", "author", "version"]:
        if not meta.get(field):
            errors.append(f"{fname}: missing required field: {field}")

    if not meta.get("download_fs20") and not meta.get("download_fs24"):
        errors.append(
            f"{fname}: missing downloads (download_fs20 / download_fs24 required)"
        )

    return errors


def main():
    print("JSWORKS publish.py — LEGACY SCHEMA ACTIVE")

    if not LIVERIES_DIR.exists():
        print("ERROR: liveries/ folder not found")
        return 1

    items = []
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

        errors = validate_meta(meta, meta_file.name)
        if errors:
            for err in errors:
                print(err)
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

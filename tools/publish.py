#!/usr/bin/env python3
# JSWORKS PUBLISH SCRIPT — FS20 / FS24 SCHEMA
# PATCH: supports BOTH legacy meta schema and new schema:
#   - legacy: version + download_fs20/download_fs24 (or downloads[] with url)
#   - new: latest_version + releases[] (with releases[].downloads.{fs20,fs24}.url)
#
# Output manifest.json stays compatible with the app by deriving:
#   version, download_fs20, download_fs24, package_folders_fs20, package_folders_fs24, changelog

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVERIES_DIR = REPO_ROOT / "liveries"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


def is_nonempty_string(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _pick_latest_release(meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    releases = meta.get("releases")
    if not isinstance(releases, list) or not releases:
        return None

    latest = meta.get("latest_version")
    if is_nonempty_string(latest):
        for r in releases:
            if isinstance(r, dict) and r.get("version") == latest:
                return r

    # fall back to first (assume newest first)
    first = releases[0]
    return first if isinstance(first, dict) else None


def normalize_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Derive legacy fields from new schema so downstream logic + app stay compatible."""
    if "latest_version" in meta and "releases" in meta and not is_nonempty_string(meta.get("version")):
        rel = _pick_latest_release(meta)
        if rel is None:
            raise ValueError("missing releases[] entries (new schema requires releases[])")

        latest = meta.get("latest_version")
        if not is_nonempty_string(latest):
            # If caller didn't set latest_version, fall back to chosen release's version
            latest = rel.get("version")

        if not is_nonempty_string(latest):
            raise ValueError("missing latest_version (or releases[0].version)")

        # Derive canonical 'version' for compatibility
        meta["version"] = latest

        downloads = rel.get("downloads", {})
        if not isinstance(downloads, dict):
            downloads = {}

        fs20 = downloads.get("fs20", {})
        fs24 = downloads.get("fs24", {})
        if not isinstance(fs20, dict):
            fs20 = {}
        if not isinstance(fs24, dict):
            fs24 = {}

        if is_nonempty_string(fs20.get("url")) and not is_nonempty_string(meta.get("download_fs20")):
            meta["download_fs20"] = fs20["url"]
        if is_nonempty_string(fs24.get("url")) and not is_nonempty_string(meta.get("download_fs24")):
            meta["download_fs24"] = fs24["url"]

        if isinstance(fs20.get("package_folders"), list) and not isinstance(meta.get("package_folders_fs20"), list):
            meta["package_folders_fs20"] = fs20.get("package_folders", [])
        if isinstance(fs24.get("package_folders"), list) and not isinstance(meta.get("package_folders_fs24"), list):
            meta["package_folders_fs24"] = fs24.get("package_folders", [])

        # Build app-friendly changelog from releases (newest first)
        releases = meta.get("releases", [])
        changelog: List[Dict[str, Any]] = []
        if isinstance(releases, list):
            for r in releases:
                if not isinstance(r, dict):
                    continue
                v = r.get("version")
                if not is_nonempty_string(v):
                    continue
                changelog.append(
                    {
                        "version": v,
                        "date": r.get("date", ""),
                        "changes": r.get("changes", []) if isinstance(r.get("changes", []), list) else [],
                    }
                )
        if changelog and not isinstance(meta.get("changelog"), list):
            meta["changelog"] = changelog

    return meta


def has_any_download(meta: Dict[str, Any]) -> bool:
    # Normalize so new schema counts as having downloads
    meta = normalize_meta(meta)

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

    # Normalize first (lets new schema satisfy legacy requirements)
    try:
        meta = normalize_meta(meta)
    except Exception as e:
        errors.append(str(e))
        return errors

    if not is_nonempty_string(meta.get("id")):
        errors.append("missing required field: id")

    if not is_nonempty_string(meta.get("version")):
        errors.append("missing required field: version (or latest_version + releases[])")

    if not has_any_download(meta):
        errors.append(
            "missing downloads (provide download_fs20 / download_fs24, downloads[] with url, OR latest_version + releases[].downloads.{fs20,fs24}.url)"
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

        # Store normalized meta so manifest stays app-compatible
        meta = normalize_meta(meta)
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

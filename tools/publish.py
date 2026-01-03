#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVERIES_DIR = REPO_ROOT / "liveries"
MANIFEST_PATH = REPO_ROOT / "manifest.json"


@dataclass
class ValidationError:
    file: Path
    message: str


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _get_download_fs20(meta: Dict[str, Any]) -> str:
    v = meta.get("download_fs20")
    if not _is_nonempty_str(v):
        v = meta.get("download_fs2020")
    return v.strip() if _is_nonempty_str(v) else ""


def _get_download_fs24(meta: Dict[str, Any]) -> str:
    v = meta.get("download_fs24")
    if not _is_nonempty_str(v):
        v = meta.get("download_fs2024")
    return v.strip() if _is_nonempty_str(v) else ""


def _get_downloads_list(meta: Dict[str, Any]) -> List[Dict[str, str]]:
    downloads = meta.get("downloads")
    if not isinstance(downloads, list):
        return []
    out: List[Dict[str, str]] = []
    for d in downloads:
        if not isinstance(d, dict):
            continue
        label = d.get("label", "")
        url = d.get("url", "")
        if _is_nonempty_str(url):
            out.append(
                {
                    "label": str(label).strip() if label is not None else "",
                    "url": str(url).strip(),
                }
            )
    return out


def _has_any_download(meta: Dict[str, Any]) -> bool:
    if _get_download_fs20(meta):
        return True
    if _get_download_fs24(meta):
        return True
    if _get_downloads_list(meta):
        return True
    return False


def validate_meta(file: Path, meta: Dict[str, Any]) -> List[ValidationError]:
    errs: List[ValidationError] = []

    # Required minimal fields
    if not _is_nonempty_str(meta.get("id")):
        errs.append(ValidationError(file, "missing required field: id (non-empty string)"))

    if not _is_nonempty_str(meta.get("version")):
        errs.append(ValidationError(file, "missing required field: version (non-empty string)"))

    # Must have at least one download method
    if not _has_any_download(meta):
        errs.append(
            ValidationError(
                file,
                "missing downloads: provide download_fs20 and/or download_fs24 "
                "(or downloads: [{label,url}, ...] with at least one non-empty url)",
            )
        )

    # Optional sanity checks (non-fatal style can be added later)
    return errs


def load_all_meta() -> Tuple[List[Dict[str, Any]], List[ValidationError]]:
    if not LIVERIES_DIR.exists():
        return [], [ValidationError(LIVERIES_DIR, "liveries/ folder not found")]

    metas: List[Dict[str, Any]] = []
    errors: List[ValidationError] = []

    for file in sorted(LIVERIES_DIR.glob("*.meta.json")):
        try:
            meta = json.loads(file.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                errors.append(ValidationError(file, "meta file must contain a JSON object"))
                continue
        except Exception as e:
            errors.append(ValidationError(file, f"failed to parse JSON: {e}"))
            continue

        errors.extend(validate_meta(file, meta))
        metas.append(meta)

    return metas, errors


def build_manifest(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Keep item objects mostly as-is so the app can evolve without constant tool changes.
    # We do normalize/augment a couple of fields.
    out_items: List[Dict[str, Any]] = []

    for it in items:
        # Shallow copy to avoid mutating source object
        item = dict(it)

        # Normalize optional download aliases (keep originals too)
        if "download_fs20" not in item and "download_fs2020" in item:
            item["download_fs20"] = item.get("download_fs2020")
        if "download_fs24" not in item and "download_fs2024" in item:
            item["download_fs24"] = item.get("download_fs2024")

        # Ensure downloads list is clean if present
        if "downloads" in item:
            item["downloads"] = _get_downloads_list(item)

        out_items.append(item)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": out_items,
    }
    return manifest


def main() -> int:
    metas, errors = load_all_meta()

    if errors:
        for e in errors:
            rel = e.file.relative_to(REPO_ROOT) if e.file.exists() or e.file.is_absolute() else e.file
            print(f"{rel}: {e.message}")
        return 1

    manifest = build_manifest(metas)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)} with {len(metas)} item(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

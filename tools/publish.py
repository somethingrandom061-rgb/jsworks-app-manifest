import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LIVERIES_DIR = ROOT / "liveries"
MANIFEST_PATH = ROOT / "manifest.json"
BRAND = "JSWorks"

REQUIRED = ["id", "name", "version", "download_url"]
OPTIONAL = ["aircraft", "changelog", "photos"]

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    if not LIVERIES_DIR.exists():
        raise SystemExit(f"Missing folder: {LIVERIES_DIR}")

    items = []
    meta_files = sorted(LIVERIES_DIR.glob("*.meta.json"))

    if not meta_files:
        raise SystemExit("No *.meta.json files found in liveries/")

    for meta_path in meta_files:
        data = load_json(meta_path)

        missing = [k for k in REQUIRED if not data.get(k)]
        if missing:
            raise SystemExit(f"{meta_path.name} missing required fields: {missing}")

        item = {k: data.get(k) for k in REQUIRED + OPTIONAL if k in data}

        if "photos" in item:
            if not isinstance(item["photos"], list):
                raise SystemExit(f"{meta_path.name}: 'photos' must be a list of URLs")
            # normalize empty strings
            item["photos"] = [p for p in item["photos"] if isinstance(p, str) and p.strip()]

        items.append(item)

    # Stable sort by name then version
    items.sort(key=lambda x: (str(x.get("name","")).lower(), str(x.get("version",""))))

    manifest = {
        "brand": BRAND,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH} with {len(items)} items")

if __name__ == "__main__":
    main()

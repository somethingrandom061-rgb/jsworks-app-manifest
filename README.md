# JSWorks Livery Manifest (GitHub Pages)

This repo generates and hosts `manifest.json` for the **JSWorks Livery Manager** app.

## Enable GitHub Pages
- Settings → Pages → Deploy from a branch
- Branch: `main`
- Folder: `/ (root)`

Manifest URL:
`https://<org-or-user>.github.io/<repo>/manifest.json`

## Add a livery
Create a new `*.meta.json` in `liveries/` and push.
GitHub Actions will regenerate `manifest.json`.

### Meta fields
Required:
- `id`, `name`, `version`, `download_url`

Recommended (for the gallery-card UI):
- `variant` (e.g. "Standard", "New")
- `registration` (or `reg`)
- `year`
- `tags` (list of small badges, e.g. ["GR", "IAEV2500", "WTF"])
- `photos` (list of URLs; first URL is used as the card thumbnail)

Optional:
- `downloads`: list of { "label": "FS20", "url": "..." } objects.
  If provided, the card shows up to 2 buttons (like the reference screenshot).
  If not provided, it falls back to a single "DOWNLOAD" button using `download_url`.

# JSWorks Livery Manifest (GitHub Pages)

This repo generates and hosts `manifest.json` for the **JSWorks Livery Manager** app.

## How to add a livery
1. Create a new `*.meta.json` in `liveries/` (copy the sample).
2. Commit + push.
3. GitHub Actions will regenerate `manifest.json`.

## Enable GitHub Pages
- Settings → Pages → Deploy from a branch
- Branch: `main`
- Folder: `/ (root)`

Your manifest URL will be:
`https://<org-or-user>.github.io/<repo>/manifest.json`

## Meta file format
Required fields:
- `id`, `name`, `version`, `download_url`

Optional:
- `aircraft`, `changelog`, `photos` (list of URLs)

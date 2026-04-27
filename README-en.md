# Forma

Forma is an AI thesis formatting entry: paste formatting requirements, upload a thesis file, then let an Agent-driven flow precheck, prepare fixes, and export a Word document.

It is not a thesis-writing service and not an official university system. The public entry focuses on existing `.docx` files or existing thesis text, visible precheck results, and normalized `.docx` export. Remote AI providers are disabled on the public site by default.

## Product Direction

Forma is moving from a single-school thesis portal toward a general thesis formatting platform. The SCNU undergraduate export implementation remains in the repository as a specialized rule profile and legacy verification baseline, but it is no longer the public product identity.

The intended path is:

1. Paste school, faculty, journal, or advisor formatting requirements.
2. Upload a `.docx` thesis file.
3. Review grouped format and structure issues.
4. Confirm candidate fixes.
5. Export a Word document.

Requirement parsing, automatic format repair, and diff reports are still prepared as integration points for a future formatting Agent / ruleset API.

## Local Development

```bash
uv sync --extra dev
npm install --prefix web
uv run uvicorn backend.app.main:app --reload --port 8000
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev --prefix web
```

Open:

- Forma: `http://127.0.0.1:5173/`
- Guide: `http://127.0.0.1:5173/#/guide`
- Workbench demo: `http://127.0.0.1:5173/#/workbench-demo`

Public Vercel preview: [forma-rosy.vercel.app](https://forma-rosy.vercel.app)

## Verification

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
npm run build --prefix web
uv run python scripts/build_web_public.py
```

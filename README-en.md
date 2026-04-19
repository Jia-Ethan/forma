# SCNU Thesis Agent Workbench

SCNU Thesis Agent Workbench is an unofficial tool for SCNU undergraduate thesis format precheck, proposal review, version tracking, and Word export.

It is not a thesis-writing service and not an official university system. The public entry only supports existing `.docx` or existing thesis text precheck and normalized `.docx` export. Remote AI providers are disabled on the public site.

## Production Direction

The primary production site should run on a mainland China cloud server with a custom domain, ICP filing, Docker Compose, Caddy HTTPS, FastAPI, Postgres, and local temporary export storage.

Vercel is kept only as a static preview or mirror. It should not host the stateful FastAPI Workbench backend.

## Local Development

```bash
uv sync --extra dev
npm install --prefix web
uv run uvicorn backend.app.main:app --reload --port 8000
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev --prefix web
```

## Verification

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
npm run build --prefix web
uv run python scripts/build_web_public.py
```

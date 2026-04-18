# Contributing

SC-TH keeps the fast `.docx` export path stable while Workbench evolves in small phases.

## Branches

- Use `main` for released baseline.
- Use `codex/<feature-name>` for feature work.
- Keep each PR focused on one phase or one user-facing capability.

## Commits

Use:

```text
<type>(scope): <summary>
```

Allowed types:

- `feat`
- `fix`
- `docs`
- `test`
- `refactor`
- `chore`
- `security`

Examples:

```text
feat(workbench): add project wizard and privacy consent
security(provider): verify base urls before saving provider configs
docs(api): document access code guard
```

## Required Checks

Run before opening a PR:

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
npm run build --prefix web
uv run python scripts/build_web_public.py
uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx
uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx
```

If UI changed, include a screenshot. If export changed, include the compliance script result.

## Product Boundary

This project is an AI-assisted thesis workbench and formatter. It must not present itself as a thesis ghostwriting system, fabricate data, fabricate references, or bypass user approval for AI-generated正文.

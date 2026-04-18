## Summary

- 

## User Scenarios

- 

## Data / API Impact

- [ ] No schema or API change
- [ ] Schema change
- [ ] API change
- [ ] Migration or compatibility handling included

## Export / Privacy Impact

- [ ] No export behavior change
- [ ] Export behavior changed
- [ ] No privacy or Provider behavior change
- [ ] Privacy or Provider behavior changed

## Verification

```bash
uv run pytest tests -q
npm run test:smoke --prefix web
npm run build --prefix web
uv run python scripts/build_web_public.py
uv run python scripts/export_compliance_fixture.py tmp/fixture-export.docx
uv run python scripts/check_docx_compliance.py tmp/fixture-export.docx
```

## Screenshots

Add screenshots for UI changes.

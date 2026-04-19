# API Reference

This document covers the Workbench-facing API surface. All endpoints are under `/api`.

## Access Code

When `SCNU_ACCESS_CODE` is set, all `/api/*` routes require the access cookie except:

- `GET /api/health`
- `POST /api/public/precheck/docx`
- `POST /api/public/precheck/text`
- `POST /api/public/exports/docx`
- `GET /api/public/exports/{id}/download`
- `GET /api/public/exports/{id}/report`
- `GET /api/access-code/status`
- `POST /api/access-code/verify`

## Public Quick Export

### `POST /api/public/precheck/docx`

Multipart fields:

- `file`: `.docx`, max 20 MB
- `privacy_accepted`: must be `true`
- `turnstile_token`: required in production

Returns `PrecheckResponse` with `export_token` and `expires_at`.

### `POST /api/public/precheck/text`

JSON request:

```json
{
  "text": "已有论文正文",
  "privacy_accepted": true,
  "turnstile_token": "..."
}
```

Text input is limited to 80,000 characters. The endpoint is for existing thesis text precheck only.

### `POST /api/public/exports/docx`

JSON request:

```json
{
  "thesis": {},
  "export_token": "..."
}
```

Returns a retained export with `download_url`, `report_url`, and `expires_at`. Public exports are kept for 30 minutes.

### `GET /api/access-code/status`

Returns:

```json
{
  "required": true,
  "verified": false
}
```

### `POST /api/access-code/verify`

Request:

```json
{
  "access_code": "..."
}
```

On success, the backend sets an HttpOnly cookie and returns `verified=true`.

## Projects

### `POST /api/projects`

Creates an SCNU undergraduate project. The server defaults are:

- `school=scnu`
- `degree_level=undergraduate`
- `template_profile=scnu-undergraduate`
- `rule_set_id=scnu-undergraduate-2025`
- `privacy_mode=local_only`
- `remote_provider_allowed=false`

Request fields:

- `title`
- `department`
- `major`
- `advisor`
- `student_name`
- `student_id`
- `writing_stage`: `topic`, `proposal`, `draft`, `revision`, `final_check`
- `privacy_mode`: `local_only`, `remote_allowed`
- `remote_provider_allowed`

### `PATCH /api/projects/{id}`

Updates project metadata and privacy settings. If `privacy_mode=local_only`, the server forces `remote_provider_allowed=false`.

## Provider Configs

### `GET /api/providers`

Returns Provider metadata only. API keys are never included.

### `GET /api/provider-configs`

Returns saved Provider configs with:

- `provider`
- `model`
- `base_url`
- `allow_local`
- `has_api_key`
- `verification_status`
- `verification_message`

Raw API keys are never returned.

### `POST /api/provider-configs`

Stores a Provider config and seals `api_key` server-side.

Remote Providers reject private, loopback, link-local, reserved, and multicast `base_url` targets. Ollama can use local loopback/private addresses only when `allow_local=true`; link-local, reserved, and multicast targets remain blocked.

### `POST /api/provider-configs/{id}/verify`

Runs metadata verification only. It does not call a remote LLM and does not send论文正文.

- Remote Providers require a model and saved API key.
- Ollama may perform a short local `/api/tags` probe when a base URL is configured.

### `DELETE /api/provider-configs/{id}`

Soft-deletes the Provider config.

## Existing Workbench APIs

- `POST /api/projects/{id}/files`
- `GET /api/projects/{id}/files`
- `POST /api/projects/{id}/parse-jobs`
- `GET /api/jobs/{id}`
- `GET /api/jobs/{id}/events`
- `GET /api/jobs/{id}/events/stream`
- `GET /api/projects/{id}/versions`
- `GET /api/projects/{id}/issues`
- `GET /api/projects/{id}/proposals`
- `POST /api/proposals/{id}/accept`
- `POST /api/proposals/{id}/reject`
- `POST /api/proposals/{id}/stash`
- `POST /api/projects/{id}/exports`
- `GET /api/projects/{id}/exports`
- `GET /api/exports/{id}/download`

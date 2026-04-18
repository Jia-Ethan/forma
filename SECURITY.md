# Security

## Supported Scope

The current Workbench is designed for private or local deployments. It is not a multi-tenant SaaS permission system.

## Access Code

Set `SCNU_ACCESS_CODE` to protect API routes in private deployments.

- `/api/health`
- `/api/access-code/status`
- `/api/access-code/verify`

remain public so the app can verify access. Other `/api/*` routes require the access cookie when `SCNU_ACCESS_CODE` is set.

## Provider Secrets

Provider API keys are accepted only by the backend and are never returned to the frontend. Responses expose only `has_api_key`.

Set `SCNU_SECRET_KEY` in real deployments. Development mode derives an explicitly insecure local key only so the app can run without extra setup.

## SSRF Guard

Custom Provider `base_url` values are validated before storage and verification.

- Remote providers reject loopback and private addresses.
- Link-local, reserved, and multicast addresses are always rejected.
- Ollama can use local addresses only when `allow_local=true`.

## Reporting

Open a private issue or contact the maintainer if a bug could expose thesis content, Provider keys, local files, or internal network access.

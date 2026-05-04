# Brain

Cognee-native local memory evaluation harness.

## Quick Start

```bash
cp .env.gemini.example .env
make setup
make up
make check
make smoke
make eval
```

Profiles are selected through `PROFILE` and provider-specific environment variables:

- `gemini` for the Google challenger lane
- `openai` for the quality-ceiling lane
- `local` for the Ollama/Fastembed no-cloud lane

The HTTP service for production verification includes:

- `GET /healthz`
- `GET|POST /mcp`
- `GET /.well-known/oauth-protected-resource/mcp`
- `GET /.well-known/oauth-authorization-server`
- `POST /register`
- `GET|POST /authorize`
- `POST /token`
- `POST /revoke`

The production Cognee web UI is published separately at:

- `https://brain.dceb.net/ui`
- local proxy: `http://127.0.0.1:8002`
- local Cognee frontend: `http://127.0.0.1:3000`
- local Cognee backend API: `http://127.0.0.1:8001`

The UI does not use the MCP OAuth authorization-code resource directly. The
browser app and Cognee backend have their own local auth assumptions, so Brain
puts a small reverse proxy in front of them and gates `/ui`, `/ui-api`, and
Next.js app routes with the same Brain auth password file used by MCP OAuth
approval.

Run it locally with:

```bash
make mcp-http
```

Run only the UI proxy locally with:

```bash
make ui-proxy
```

Production deployment is Phase 5 work and uses `/Volumes/xpg_usb4/prod/brain`.
When production auth is enabled, the OAuth password is stored at
`/Volumes/xpg_usb4/prod/brain/shared/secrets/brain-auth-password`.

Production request/response refinement logs are JSONL records written to:

```text
/Volumes/xpg_usb4/prod/brain/shared/logs/requests.jsonl
```

The log captures HTTP metadata plus request and response bodies. OAuth passwords,
authorization headers, auth codes, client secrets, and issued tokens are redacted.

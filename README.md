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

Run it locally with:

```bash
make mcp-http
```

Production deployment is Phase 5 work and uses `/Volumes/xpg_usb4/prod/brain`.

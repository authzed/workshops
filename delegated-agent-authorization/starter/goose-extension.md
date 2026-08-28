# Registering the deploybot extension in goose

## Option A — edit `~/.config/goose/config.yaml`

Add under `extensions:` (use ABSOLUTE paths to this repo's venv python and server):

```yaml
extensions:
  deploybot:
    type: stdio
    name: deploybot
    enabled: true
    cmd: /ABSOLUTE/PATH/delegated-agent-authorization/starter/.venv/bin/python
    args:
      - /ABSOLUTE/PATH/delegated-agent-authorization/starter/deploybot_server.py
    env_keys: []
    envs:
      SPICEDB_ENDPOINT: localhost:50051
      SPICEDB_TOKEN: devtoken
      AGENT_SUBJECT: agent:goose_alice
    timeout: 300
```

## Option B — interactive

```bash
goose configure
# -> Add Extension -> Command-line Extension
# name: deploybot
# command: /ABSOLUTE/PATH/delegated-agent-authorization/starter/.venv/bin/python /ABSOLUTE/PATH/delegated-agent-authorization/starter/deploybot_server.py
# add env vars: SPICEDB_ENDPOINT, SPICEDB_TOKEN, AGENT_SUBJECT
```

> Verify the exact key names (`envs` vs `env_keys`, `type: stdio`) against your installed
> goose version with `goose configure` — the schema has been stable but confirm once.

## Manually verifying the goose integration

This step is inherently manual: it drives goose through a live LLM-backed session, which is
outside what an automated test can exercise. Running goose is optional for this workshop — you
do not need it (or an LLM API key) installed. The same decisions are available without goose in the
web UI (`python web.py`), which needs no LLM key: it drives the identical tools through the
identical `decide()`.

If you do have goose installed and an LLM key configured, here is the checklist to confirm the
wiring end to end:

```bash
# Ensure SpiceDB is seeded and the extension is registered, then:
goose session
```

Drive these prompts and confirm the deploybot tool output:
1. "Deploy checkout to staging." → **✅ ALLOWED**, version bumps.
2. "Deploy checkout to production." → **⏸️ NEEDS APPROVAL**.
3. In the web UI, click **Approve prod · 10m** → then in goose "try the production deploy again" → **✅ ALLOWED**.
4. "Tear down the production environment." → **🚫 BLOCKED**.
5. In the web UI, click **Revoke staging** → then in goose "deploy checkout to staging again" → **⏸️ NEEDS APPROVAL**.

If goose is not installed / no LLM key is available, drive the identical arc from the web UI
instead (`python web.py`) — same tools, same buttons, same decisions, no LLM.

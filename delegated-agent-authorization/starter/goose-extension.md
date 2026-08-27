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
outside what an automated test can exercise. **We did not install goose or run this checklist
as part of building this repo — no goose install and no LLM API key were used.** The identical
decision sequence is instead proven deterministically and repeatably by `tests/test_arc.py`,
which calls `authz.decide` (the same function `deploybot_server.py` calls on every tool
invocation) directly against a real SpiceDB instance.

If you do have goose installed and an LLM key configured, here is the checklist to confirm the
wiring end to end:

```bash
# Ensure SpiceDB is seeded and the extension is registered, then:
goose session
```

Drive these prompts and confirm the deploybot tool output:
1. "Deploy checkout to staging." → **✅ ALLOWED**, version bumps.
2. "Deploy checkout to production." → **⏸️ NEEDS APPROVAL**.
3. In another terminal: `python approve.py --approver alice --env production` → then in goose "try the production deploy again" → **✅ ALLOWED**.
4. "Tear down the production environment." → **🚫 BLOCKED**.
5. In another terminal: `python revoke.py --env staging` → then in goose "deploy checkout to staging again" → **⏸️ NEEDS APPROVAL**.

If goose is not installed / no LLM key is available, this step is skipped and the arc is
covered by `tests/test_arc.py` (which exercises the identical decision sequence deterministically).

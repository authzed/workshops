# Setup

In this workshop you build a DevOps deploy agent on [goose](https://github.com/aaif-goose/goose)
(the open-source agent from the Agentic AI Foundation), then gate its every action with
delegated, fine-grained authorization from SpiceDB — scoped grants, time-bound windows, instant
revocation, and a permission hierarchy where revoking a base grant cascades to what depends on
it. The `starter/` folder in this repo is stubbed on purpose: the plumbing (MCP extension,
docker-compose, seed/approve/revoke scripts, web UI) is provided, and you'll write the schema and
the decision engine yourself across the checkpoints.

## Get the code

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/delegated-agent-authorization/starter
```

## Option A - Run locally with Docker

Copy the example `.env` file:

```bash
cp .env.example .env
```

`.env` holds the SpiceDB connection details the app itself needs — endpoint, preshared token,
and which agent identity the deploy bot acts as. Nothing in this repo talks to an LLM directly,
so there's no LLM key in here. The LLM key only comes into play later, and only if you use the
goose path (see [Install goose](#install-goose-and-register-the-extension) below) — the
deterministic path (`scripts/verify.py` and the web UI, introduced in later checkpoints) needs no
LLM at all.

Start the infrastructure:

```bash
docker compose up -d --wait
```

This brings up two containers — `postgres` (SpiceDB's datastore) and `spicedb` — plus a
short-lived `spicedb-migrate` container that runs SpiceDB's own datastore migration (setting up
its Postgres tables — not the `schema.zed` you'll write later) and exits. SpiceDB serves
on `localhost:50051` with a preshared key of `devtoken` (not recommended for prod, obviously) and
`--enable-experimental-relationship-expiration` turned on, which later checkpoints use for
time-bound grants.

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

## Option B - Run in GitHub Codespaces

For anyone who can't run Docker locally, Codespaces is the path. The repo ships with a
`.devcontainer/` config that handles everything automatically.

1. On the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**
2. On startup the devcontainer creates the `.venv`, installs dependencies into it, and runs
   `docker compose up -d` — so the `.venv/bin/python` path the goose step below relies on exists
   here too
3. Once the Codespace is ready, `cd delegated-agent-authorization/starter` and copy `.env.example`
   to `.env` as in Option A

## Install goose and register the extension

Installing goose is optional for this workshop. Every checkpoint has a second, deterministic way
to see the same decisions — `scripts/verify.py` plus a web UI, neither of which needs goose or an
LLM key. Install goose if you want to drive the agent with natural language ("Deploy checkout to
staging") and watch its tool calls resolve through SpiceDB live.

If you do want the goose path:

1. Install goose by following the [Agentic AI Foundation goose](https://github.com/aaif-goose/goose)
   project's own install instructions, then run `goose configure` to pick an LLM provider and set
   its API key — this is where the "LLM key" lives, in goose's own config, not in this project's
   `.env`.
2. Register the `deploybot` MCP extension so goose can call into this repo's deploy tools. Follow
   `goose-extension.md` — it walks through editing `~/.config/goose/config.yaml` (or running
   `goose configure` interactively) with **absolute paths** to this repo's `.venv/bin/python` and
   `deploybot_server.py`, plus three env vars the extension needs to reach SpiceDB:
   `SPICEDB_ENDPOINT=localhost:50051`, `SPICEDB_TOKEN=devtoken`, `AGENT_SUBJECT=agent:goose_alice`.

`goose-extension.md` also has a manual verification checklist for once goose is wired up — worth
skimming now, but there's nothing to run yet: SpiceDB has no authorization schema until
Checkpoint 2, where you write it and the agent's decisions (via goose or the web UI) first come
online.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up — Docker (`docker compose up -d --wait`) or Codespaces
- [ ] `.venv` created and dependencies installed — manually in Option A, automatically by the
      devcontainer in Option B
- [ ] (Goose path only) goose installed with an LLM provider configured, and the `deploybot`
      extension registered per `goose-extension.md`

Next: [Checkpoint 1 — Run the agent](1-run-the-agent.md)

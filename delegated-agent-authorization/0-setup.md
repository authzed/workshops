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

<!-- TODO: verify on a live Codespace before the conference -->

For anyone who can't run Docker locally, Codespaces is the path. This repo's devcontainer config
lives at `delegated-agent-authorization/starter/.devcontainer/devcontainer.json` — nested under
`starter/`, not at the repo root — which most Codespaces-creation flows don't auto-detect. Be
explicit about which folder you're opening:

1. On the repo page, click **Code ▸ Codespaces ▸ Create codespace on main**. Because the
   devcontainer config isn't at the repo root, this may open a plain Codespace at the repo root
   with no devcontainer applied, rather than the Python image this workshop expects.
2. Once the Codespace is up, check whether `delegated-agent-authorization/starter/.venv` already
   exists. If it does, the devcontainer ran and did its job — skip to step 4.
3. If it doesn't, the devcontainer wasn't picked up automatically. In VS Code, open the Command
   Palette and run **Dev Containers: Reopen in Container**, pointing it at
   `delegated-agent-authorization/starter` (or open that folder directly and let VS Code prompt
   you to reopen in its container). That runs the same `postCreateCommand` — creating `.venv`,
   installing dependencies, and running `docker compose up -d --wait` — so the `.venv/bin/python`
   path the goose step below relies on exists.
4. Once dependencies are installed and infra is up, `cd delegated-agent-authorization/starter` (if
   you're not already there) and copy `.env.example` to `.env` as in Option A.

In short: Codespaces gets you most of the way there, but don't assume it's zero-config — confirm
`.venv` and `docker compose ps` both look right before moving on, and fall back to the manual
Dev Containers step above if they don't.

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

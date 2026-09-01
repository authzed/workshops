# Introduction

In this workshop you will build a DevOps deploy Agent with fine-grained authorization: scoped grants, time-bound windows, instant
revocation, and a permission hierarchy where revoking a base grant cascades to everything that
depends on it. The purpose of the workshop is to understand why fine-grained authorization is required for AI Agents, 
and how it can be implemented using ReBAC. 

The `starter/` folder in this repo is stubbed on purpose: the plumbing (MCP
extension, docker-compose, the seed script, the web UI) is already there, and you'll
write the schema and the decision engine yourself across the parts to learn each of the concepts.

![Architecture diagram of the project](/delegated-agent-authorization/images/fig1-permission-check.svg)

## Two ways to drive the agent

As a reminder, you can complete every part in this workshop with just the web UI — no LLM key, no goose
install required. That's the primary path, and it's all you need. 

Each part page also ends with an optional *drive it with goose* step: the same requests in natural language, through a real
LLM, hitting the exact same authorization boundary. Use this if you want to watch the agent work with a live LLM; skip it and you miss nothing, because the authorization decision is identical either way.

## Get the code

```bash
git clone https://github.com/authzed/workshops.git
cd workshops/delegated-agent-authorization/starter
```

## Installation

#### Option A - Run locally with Docker

1. Copy the example `.env` file:

```bash
cp .env.example .env
```

`.env` holds the SpiceDB connection details the app itself needs: endpoint, and preshared-token,
and which agent identity the deploy bot acts as. 

2. Start the infrastructure:

```bash
docker compose up -d --wait
```

This brings up two containers, `postgres` (SpiceDB's datastore) and `spicedb`, plus a
short-lived `spicedb-migrate` container that runs SpiceDB's own datastore migration (setting up
its Postgres tables, not the `schema.zed` you'll write later) and exits. SpiceDB serves
on `localhost:50051` with a preshared key of `devtoken` (not recommended for prod, obviously).

3. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

#### Option B - Run in GitHub Codespaces

<!-- TODO: verify on a live Codespace before the conference -->

For anyone who can't run Docker locally, Codespaces is the path. This repo's devcontainer config
lives at `delegated-agent-authorization/starter/.devcontainer/devcontainer.json` (nested under
`starter/`, not at the repo root), which most Codespaces-creation flows don't auto-detect. Be
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

Codespaces gets you most of the way there. It isn't zero-config: confirm `.venv` and
`docker compose ps` both look right before moving on, and fall back to the manual Dev Containers
step above if they don't.

## Install goose and register the extension (optional)

Installing goose is optional for this workshop. Install goose if you want to drive the agent with natural language
("Deploy checkout to staging") and watch its tool calls resolve through SpiceDB live.

If you do want the goose path:

1. Install goose by following the [Agentic AI Foundation goose](https://github.com/aaif-goose/goose)
   project's own install instructions, then run `goose configure` to pick an LLM provider and set
   its API key — this is where the "LLM key" lives, in goose's own config, not in this project's
   `.env`.
2. Register the `deploybot` MCP extension so goose can call this repo's deploy tools. goose launches
   `deploybot_server.py` with your virtualenv's Python, so it needs the **absolute path** to both.
   From `starter/`, print that path once:

   ```bash
   pwd
   ```

   Then run `goose configure` and answer the prompts (exact wording varies slightly by goose
   version):

   - **What would you like to configure?** → `Add Extension`
   - **What type of extension would you like to add?** → `Command-line Extension`
   - **What would you like to call this extension?** → `deploybot`
   - **What command should be run?** → your venv Python and the server script, both as absolute
     paths — take the `pwd` output above and append `/.venv/bin/python` and `/deploybot_server.py`:

     ```
     /ABSOLUTE/PATH/to/starter/.venv/bin/python /ABSOLUTE/PATH/to/starter/deploybot_server.py
     ```

   - **Please set the timeout for this tool (in secs):** → `300`
   - **Would you like to add a description?** → `No`
   - **Would you like to add environment variables?** → `Yes`, then add these three (goose asks for
     a name, then a value, then "add another?" after each):

     | Name | Value |
     | --- | --- |
     | `SPICEDB_ENDPOINT` | `localhost:50051` |
     | `SPICEDB_TOKEN` | `devtoken` |
     | `AGENT_SUBJECT` | `agent:goose_alice` |

   `AGENT_SUBJECT` pins the agent's identity: every authorization check goose triggers runs as
   `agent:goose_alice`. goose writes all of this into `~/.config/goose/config.yaml` — see
   `goose-extension.md` for the equivalent YAML if you'd rather edit it by hand.

`goose-extension.md` also has a manual verification checklist for once goose is wired up. Worth
skimming now, but there's nothing to verify yet: SpiceDB has no authorization schema until
Part 2, where you write it and the agent's decisions (via goose or the web UI) first come
online. Part 1 is next, and it drives the agent from the web UI to watch it over-reach.

---

## Completion Milestone: Setup

- [ ] Cloned the repo
- [ ] Infrastructure is up — Docker (`docker compose up -d --wait`) or Codespaces
- [ ] `.venv` created and dependencies installed — manually in Option A, automatically by the
      devcontainer in Option B
- [ ] (Goose path only) goose installed with an LLM provider configured, and the `deploybot`
      extension registered per `goose-extension.md`

Next: [Part 1 — Run the agent](1-run-the-agent.md)

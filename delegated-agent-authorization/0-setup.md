# Introduction

In this workshop you will build a DevOps deploy Agent with fine-grained authorization. 
The learning objective of the workshop is to understand why fine-grained authorization is required for AI Agents, 
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

Everything runs from `delegated-agent-authorization/starter`. Pick an environment, then run the
same three steps.

- **Local** — install Docker (Desktop or Engine) and Python 3.11+, then
  `cd delegated-agent-authorization/starter`.
- **GitHub Codespaces** — on the repo page, **Code ▸ Codespaces ▸ Create codespace on main**. It
  auto-detects this workshop's devcontainer and builds a Python + Docker image with dependencies
  pre-installed (step 3 is a no-op in a codespace). When the terminal is ready,
  `cd delegated-agent-authorization/starter`. **Before running step 2, apply the host-networking
  edit in the Codespaces note below** — the default bridge networking hangs under Codespaces'
  Docker-in-Docker.

  > **Codespace didn't pick up the devcontainer?** (no `.venv`, `docker` missing) — open the Command
  > Palette → **Dev Containers: Reopen in Container** and point it at
  > `delegated-agent-authorization/starter`.

Then, from `starter/`:

1. Copy the example env file:

```bash
cp .env.example .env
```

`.env` holds the SpiceDB connection details the app needs: endpoint, preshared token, and which
agent identity the deploy bot acts as.

2. Start SpiceDB and its Postgres datastore:

```bash
docker compose up -d --wait
```

This brings up `postgres`, a short-lived `spicedb-migrate` container (runs SpiceDB's datastore
migration and exits), and `spicedb` on `localhost:50051` with a preshared key of `devtoken`.

> **On GitHub Codespaces**, edit `docker-compose.yml` for **host networking** before running this —
> Docker-in-Docker's bridge can't reliably route container-to-container, so `spicedb-migrate` hangs
> connecting to `postgres`. Three edits:
> - add `network_mode: host` to all three services (`postgres`, `spicedb-migrate`, `spicedb`)
> - in both `SPICEDB_DATASTORE_CONN_URI` values, change `@postgres:5432` to `@127.0.0.1:5432`
>   (host networking has no Compose DNS, so `postgres` won't resolve)
> - delete the `ports:` and `networks:` blocks — both are no-ops under host networking
>
> Leave the file unchanged for local Docker, where bridge networking works.

3. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

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
- [ ] `.venv` created and dependencies installed (automatic in a Codespace via the devcontainer)
- [ ] (Goose path only) goose installed with an LLM provider configured, and the `deploybot`
      extension registered per `goose-extension.md`

Next: [Part 1 — Run the agent](1-run-the-agent.md)

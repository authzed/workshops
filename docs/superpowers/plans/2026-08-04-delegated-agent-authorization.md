# Delegated Authorization for AI Agents — Workshop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-guided, 90-minute hands-on workshop where attendees add delegated, fine-grained authorization (SpiceDB/ReBAC) to a goose DevOps deploy agent — learning scoped delegation, expiring grants, revocation, and hierarchical/cascading permissions.

**Architecture:** A `starter/` app (goose MCP extension + web UI + SpiceDB via Docker) with two pieces stubbed — `schema.zed` and `authz.decide()`. Four checkpoint markdown files walk attendees through *run → watch it fail → implement → re-run → why*, growing the schema and implementing the decision engine. Provided plumbing is copied (with modifications) from the tested solution repo; the exact fill-in code lives in the checkpoints.

**Tech Stack:** Python 3.10+, goose (MCP), SpiceDB (Docker Compose), FastAPI web UI, `authzed` async client, pytest-style `verify.py`.

**Spec:** `docs/superpowers/specs/2026-08-04-delegated-agent-authorization-workshop-design.md`

**Solution source (tested, on disk):** `/Users/sohan/code-samples/goose-spicedb-delegation/` — the finished reference. Provided files are copied from here with the modifications each task specifies.

## Global Constraints

- **Location:** everything under `delegated-agent-authorization/` in the `authzed/workshops` repo, on branch `workshop/delegated-agent-authorization`.
- **SpiceDB token:** `devtoken` everywhere (docker-compose `SPICEDB_GRPC_PRESHARED_KEY`, `.env.example` `SPICEDB_TOKEN`, `spicedb_client` default). This differs from the solution repo's `somerandomkeyhere` — change it on copy.
- **SpiceDB image/flags:** `authzed/spicedb:latest`, `serve --enable-experimental-relationship-expiration`, `SPICEDB_GRPC_NO_TLS=true`, endpoint `localhost:50051`, postgres datastore.
- **Python 3.10+.** Provided modules keep the solution's async `authzed.api.v1.Client` patterns (all calls awaited).
- **Agent identity:** `agent:goose_alice`, delegator `user:alice`.
- **Tools exposed by the extension (trimmed for teaching):** `list_environments`, `deploy`, `destroy`. (The solution also has `rollback`; omit it here to reduce surface — note this in Next Steps.)
- **`decide()` signature (workshop, simpler than the solution):** `async def decide(client, agent_id, permission, environment_id) -> AuthzResult` — no `action` parameter.
- **`revoke.py` is an ungated operator CLI in the workshop** (no `manage`/`view` permissions — those are solution-only hardening). Call this out in Next Steps as a production follow-up.
- **`list_environments` is ungated** in the workshop (no `view` permission). Next-Steps follow-up.
- **Build-time:** only one SpiceDB can bind `localhost:50051`. Before testing, ensure no other local SpiceDB (e.g. the solution repo's) is running: `docker ps --filter publish=50051`.
- **Checkpoint stub convention:** stubbed files carry a `WORKSHOP STUB` docstring and `# TODO(Checkpoint N):` markers, matching the reference workshop.
- **Match the reference workshop's tone/structure** for all markdown: read `../agentic-rag-authorization/{0-setup,1-agentic-rag,2-secure-it,3-nextsteps}.md` before authoring. Declarative headings; each checkpoint ends with a `## Completion Milestone` checkbox list; both a goose path and a deterministic (`verify.py` + web UI) path.

---

### Task 1: Scaffold folder, provided plumbing, CP1 stubs, and verify.py

**Files:**
- Create dir: `delegated-agent-authorization/starter/`
- Copy (with mods below) from solution → `starter/`: `docker-compose.yml`, `spicedb_client.py`, `relationships.py`, `deploybot_server.py`, `web.py`, `static/index.html`, `requirements.txt`, `.env.example`, `goose-extension.md`
- Create: `starter/schema.zed` (CP1 stub), `starter/authz.py` (provided helpers + `decide()` stub), `starter/bootstrap.py`, `starter/approve.py`, `starter/revoke.py`, `starter/scripts/verify.py`, `starter/.devcontainer/devcontainer.json`

**Interfaces:**
- Produces (provided, used by later tasks and the extension):
  - `authz.check(client, sub_type, sub_id, permission, res_type, res_id) -> bool`
  - `authz.read_delegator(client, agent_id) -> str | None`
  - `authz.expiry_from_now(minutes) -> Timestamp`
  - `authz.Decision` (str Enum ALLOWED/NEEDS_APPROVAL/BLOCKED), `authz.AuthzResult(decision, reason)`
  - `authz.decide(client, agent_id, permission, environment_id) -> AuthzResult` (STUB in CP1)
  - `bootstrap.write_schema(client)`, `bootstrap.seed(client, window_minutes=60)`, `bootstrap.AGENT_ID="goose_alice"`
  - `deploybot_server.do_list_environments/do_deploy/do_destroy`, `STATE_PATH`, `AGENT_ID`
  - `spicedb_client.make_client()`

- [ ] **Step 1: Create the folder and copy provided files with modifications**

Copy these from `/Users/sohan/code-samples/goose-spicedb-delegation/` into `starter/`, applying mods:
- `spicedb_client.py` — change token default `somerandomkeyhere` → `devtoken`.
- `relationships.py` — copy verbatim (`rel(...)`, `agent_deployer_filter(...)`).
- `docker-compose.yml` — copy; set `SPICEDB_GRPC_PRESHARED_KEY: "${SPICEDB_TOKEN:-devtoken}"`; keep `serve --enable-experimental-relationship-expiration`.
- `deploybot_server.py` — copy, then: remove the `do_rollback`/`rollback` tool and its wrapper; remove the `check`-based gating in `do_list_environments` (make it ungated — just list all envs); ensure imports are `from authz import Decision, decide` (drop `check`); each mutating tool calls `decide(make_client(), AGENT_ID, "deploy"|"destroy", environment)` and mutates only on ALLOWED (keep the solution's `_decide_and_mutate` helper but drop the `action=` argument to match the workshop `decide()` signature).
- `web.py` — copy, then in `/api/state` compute `effective = await check(client, "agent", AGENT_ID, "deploy", environment)` (NOT `agent_deploy` — `deploy` routes through the cascade automatically once CP4 rewires it, and exists from CP2). Keep the delegation/expiry reads. Remove any `agent_deploy` references.
- `static/index.html` — copy verbatim (includes the walking-goose indicator and authority bar).
- `requirements.txt` — copy (authzed, grpcio, mcp, fastapi, uvicorn, python-dotenv, pytest, pytest-asyncio).
- `.env.example` — set `SPICEDB_TOKEN=devtoken`, `SPICEDB_ENDPOINT=localhost:50051`, `AGENT_SUBJECT=agent:goose_alice`.
- `goose-extension.md` — copy; update the absolute-path examples to `.../delegated-agent-authorization/starter/...`.

- [ ] **Step 2: Write `starter/schema.zed` (CP1 stub)**

```zed
// WORKSHOP STUB — you will build this schema up across Checkpoints 2–4.
// It defines the object types but grants the agent nothing. Combined with the
// authz.decide() stub, the deploy agent runs UNGATED in Checkpoint 1.
// TODO(Checkpoint 2): model delegated authorization here.

definition user {}

definition agent {
    relation delegator: user
}

definition environment {}
```

- [ ] **Step 3: Write `starter/authz.py` (provided helpers + `decide()` stub)**

```python
"""authz.py — SpiceDB helpers (provided) + the decision engine (you implement)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from google.protobuf.timestamp_pb2 import Timestamp
from authzed.api.v1 import (
    CheckPermissionRequest,
    CheckPermissionResponse,
    Consistency,
    ObjectReference,
    ReadRelationshipsRequest,
    RelationshipFilter,
    SubjectReference,
)


class Decision(str, Enum):
    ALLOWED = "ALLOWED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass
class AuthzResult:
    decision: Decision
    reason: str


def expiry_from_now(minutes: int) -> Timestamp:
    """A protobuf Timestamp `minutes` from now, for a relationship's optional_expires_at."""
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc) + timedelta(minutes=minutes))
    return ts


async def check(client, sub_type, sub_id, permission, res_type, res_id) -> bool:
    """Does `subject` have `permission` on `resource`? A single SpiceDB CheckPermission."""
    resp = await client.CheckPermission(
        CheckPermissionRequest(
            consistency=Consistency(fully_consistent=True),
            resource=ObjectReference(object_type=res_type, object_id=res_id),
            permission=permission,
            subject=SubjectReference(
                object=ObjectReference(object_type=sub_type, object_id=sub_id)
            ),
        )
    )
    return resp.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION


async def read_delegator(client, agent_id) -> str | None:
    """The user this agent acts for (agent:<id>#delegator), or None."""
    req = ReadRelationshipsRequest(
        consistency=Consistency(fully_consistent=True),
        relationship_filter=RelationshipFilter(
            resource_type="agent",
            optional_resource_id=agent_id,
            optional_relation="delegator",
        ),
    )
    async for resp in client.ReadRelationships(req):
        return resp.relationship.subject.object.object_id
    return None


async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    # WORKSHOP STUB — Checkpoint 1.
    # Returns ALLOWED for everything WITHOUT consulting SpiceDB. This is exactly why
    # the agent over-reaches in Checkpoint 1. You implement the real, SpiceDB-backed
    # three-way decision in Checkpoint 2.
    # TODO(Checkpoint 2): replace this stub.
    return AuthzResult(Decision.ALLOWED, "no authorization configured (workshop stub)")
```

- [ ] **Step 4: Write `starter/bootstrap.py`**

Copy the solution's `bootstrap.py` structure, but the seed is the CP2 set with NO expiration and NO gated_by yet (those are added by CP3/CP4 checkpoints):

```python
"""bootstrap.py — write the schema and seed the delegation graph."""
import argparse
import asyncio
from pathlib import Path

from authzed.api.v1 import (
    DeleteRelationshipsRequest,
    WriteRelationshipsRequest,
    WriteSchemaRequest,
)

from relationships import agent_deployer_filter, rel
from spicedb_client import make_client

SCHEMA_PATH = Path(__file__).parent / "schema.zed"
AGENT_ID = "goose_alice"


async def write_schema(client) -> None:
    await client.WriteSchema(WriteSchemaRequest(schema=SCHEMA_PATH.read_text()))


async def _reset_agent_grants(client) -> None:
    await client.DeleteRelationships(
        DeleteRelationshipsRequest(relationship_filter=agent_deployer_filter(AGENT_ID))
    )


async def seed(client, window_minutes: int = 60) -> None:
    await _reset_agent_grants(client)
    updates = [
        rel("environment", "staging", "direct_deployer", "user", "alice"),
        rel("environment", "production", "direct_deployer", "user", "alice"),
        rel("environment", "production", "approver", "user", "alice"),
        rel("environment", "staging", "destroyer", "user", "sre_admin"),
        rel("environment", "production", "destroyer", "user", "sre_admin"),
        rel("agent", AGENT_ID, "delegator", "user", "alice"),
        # Checkpoint 2: staging-only delegation (no expiration yet).
        rel("environment", "staging", "agent_deployer", "agent", AGENT_ID),
    ]
    await client.WriteRelationships(WriteRelationshipsRequest(updates=updates))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the delegated-agent-authorization workshop.")
    parser.add_argument("--window-minutes", type=int, default=60,
                        help="Minutes the agent's staging delegation stays valid (Checkpoint 3+).")
    args = parser.parse_args()
    client = make_client()
    print("Writing schema...")
    await write_schema(client)
    print(f"Seeding delegation graph (window = {args.window_minutes} min)...")
    await seed(client, window_minutes=args.window_minutes)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
```

Note: `seed()` ignores `window_minutes` until Checkpoint 3 (added there). `_reset_agent_grants` makes reseeding idempotent.

- [ ] **Step 5: Write `starter/approve.py` (CP2 version — no expiry) and `starter/revoke.py` (ungated)**

`approve.py` (CP2 — writes an `agent_deployer` grant with NO expiration; Checkpoint 3 upgrades it):
```python
"""approve.py — human-in-the-loop: grant the agent deploy on an environment."""
import argparse
import asyncio

from authzed.api.v1 import WriteRelationshipsRequest

from authz import check, read_delegator
from relationships import rel
from spicedb_client import make_client


async def approve(approver: str, environment: str, agent_id: str, minutes: int) -> int:
    client = make_client()
    if not await check(client, "user", approver, "approve", "environment", environment):
        print(f"❌ Refused: user:{approver} is not an approver on environment:{environment}")
        return 1
    delegator = await read_delegator(client, agent_id)
    if not (delegator and await check(client, "user", delegator, "deploy", "environment", environment)):
        who = f"user:{delegator}" if delegator else "(no delegator)"
        print(f"❌ Refused: agent:{agent_id}'s delegator {who} may not deploy environment:{environment}")
        return 1
    update = rel("environment", environment, "agent_deployer", "agent", agent_id)
    await client.WriteRelationships(WriteRelationshipsRequest(updates=[update]))
    print(f"✅ Approved: agent:{agent_id} may deploy environment:{environment}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Approve an agent deploy grant.")
    p.add_argument("--approver", default="alice")
    p.add_argument("--env", default="production")
    p.add_argument("--agent", default="goose_alice")
    p.add_argument("--minutes", type=int, default=10)
    a = p.parse_args()
    raise SystemExit(asyncio.run(approve(a.approver, a.env, a.agent, a.minutes)))
```

`revoke.py` (ungated operator CLI, unchanged across checkpoints):
```python
"""revoke.py — delete an agent's deploy grant on an environment (operator CLI)."""
import argparse
import asyncio

from authzed.api.v1 import DeleteRelationshipsRequest

from relationships import agent_deployer_filter
from spicedb_client import make_client


async def revoke(environment: str, agent_id: str) -> int:
    client = make_client()
    await client.DeleteRelationships(
        DeleteRelationshipsRequest(
            relationship_filter=agent_deployer_filter(agent_id, environment)
        )
    )
    print(f"✅ Revoked: agent:{agent_id} agent_deployer on environment:{environment}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Revoke an agent deploy grant.")
    p.add_argument("--env", default="staging")
    p.add_argument("--agent", default="goose_alice")
    a = p.parse_args()
    raise SystemExit(asyncio.run(revoke(a.env, a.agent)))
```

- [ ] **Step 6: Write `starter/scripts/verify.py` (per-checkpoint deterministic verifier)**

```python
"""verify.py — deterministic checks for the current checkpoint. No LLM needed.

Usage: python scripts/verify.py --checkpoint N
Run from the starter/ directory with SpiceDB up.
"""
import argparse
import asyncio
import sys

from authz import Decision, decide
import bootstrap
from approve import approve
from revoke import revoke
from spicedb_client import make_client

AGENT = "goose_alice"


def _ok(label, got, want):
    mark = "✅" if got == want else "❌"
    print(f"  {mark} {label}: got {got}, want {want}")
    return got == want


async def checkpoint_1():
    # The stub decides ALLOWED for everything — the over-reach.
    r = await decide(make_client(), AGENT, "destroy", "production")
    return _ok("stub allows destroy production (over-reach)", r.decision, Decision.ALLOWED)


async def checkpoint_2(client):
    await bootstrap.write_schema(client)
    await bootstrap.seed(client)
    passed = True
    passed &= _ok("agent deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.ALLOWED)
    passed &= _ok("agent deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.NEEDS_APPROVAL)
    passed &= _ok("agent destroy production", (await decide(client, AGENT, "destroy", "production")).decision, Decision.BLOCKED)
    await approve("alice", "production", AGENT, 10)
    passed &= _ok("after approve: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.ALLOWED)
    return passed


async def checkpoint_3(client):
    # Expired window -> staging autonomy gone (falls back to NEEDS_APPROVAL).
    await bootstrap.write_schema(client)
    await bootstrap.seed(client, window_minutes=0)
    passed = _ok("expired staging grant", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    # Revocation on a fresh window.
    await bootstrap.seed(client, window_minutes=60)
    await revoke("staging", AGENT)
    passed &= _ok("after revoke: deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    return passed


async def checkpoint_4(client):
    await bootstrap.write_schema(client)
    await bootstrap.seed(client, window_minutes=60)
    await approve("alice", "production", AGENT, 10)
    passed = _ok("with both grants: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.ALLOWED)
    await revoke("staging", AGENT)  # revoke the BASE
    passed &= _ok("cascade: deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    passed &= _ok("cascade: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.NEEDS_APPROVAL)
    return passed


async def main(n):
    print(f"Verifying Checkpoint {n}...")
    if n == 1:
        passed = await checkpoint_1()
    else:
        client = make_client()
        passed = await {2: checkpoint_2, 3: checkpoint_3, 4: checkpoint_4}[n](client)
    print("PASS ✅" if passed else "FAIL ❌")
    return 0 if passed else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=int, required=True, choices=[1, 2, 3, 4])
    raise SystemExit(asyncio.run(main(p.parse_args().checkpoint)))
```

- [ ] **Step 7: Write `starter/.devcontainer/devcontainer.json`**

```json
{
  "name": "delegated-agent-authorization",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": { "ghcr.io/devcontainers/features/docker-in-docker:2": {} },
  "postCreateCommand": "pip install -r requirements.txt && docker compose up -d",
  "forwardPorts": [8000, 50051]
}
```

- [ ] **Step 8: Smoke test — infra up + CP1 over-reach**

Run from `starter/` (ensure nothing else holds :50051):
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
docker compose up -d --wait
python -c "import deploybot_server, web, authz, bootstrap, approve, revoke"   # imports resolve
python scripts/verify.py --checkpoint 1
```
Expected: imports succeed; verify prints `✅ stub allows destroy production (over-reach)` and `PASS ✅`.

- [ ] **Step 9: Commit**

```bash
cd ~/authzed-branches/workshops
git add delegated-agent-authorization/starter
git commit -m "feat(workshop): starter scaffolding, provided plumbing, CP1 stubs, verify.py"
```

---

### Task 2: `0-setup.md`

**Files:** Create `delegated-agent-authorization/0-setup.md`

- [ ] **Step 1: Author the setup doc** — model it on `../agentic-rag-authorization/0-setup.md`. Cover, in this order:
  1. One-paragraph framing: build a goose deploy agent, then add delegated authorization with SpiceDB; the `starter/` is stubbed on purpose.
  2. Get the code: `git clone https://github.com/authzed/workshops.git` → `cd workshops/delegated-agent-authorization/starter`.
  3. Option A — local Docker: `cp .env.example .env`, add an LLM key for goose (note: only needed for the goose path; the `verify.py`/web-UI path needs no LLM), `docker compose up -d` (brings up postgres + SpiceDB with the expiration flag on `devtoken`), venv + `pip install -r requirements.txt`.
  4. Option B — Codespaces: the `.devcontainer/` runs compose + installs deps on create.
  5. Install goose and register the deploy-bot extension: reference `goose-extension.md` (absolute paths to `.venv/bin/python` and `deploybot_server.py`, env `SPICEDB_ENDPOINT`/`SPICEDB_TOKEN=devtoken`/`AGENT_SUBJECT=agent:goose_alice`).
  6. `## Completion Milestone: Setup` checklist: repo cloned; infra up (Docker or Codespaces); `.env` has an LLM key (goose path); extension registered in goose.
  7. Ends: `Next: [Checkpoint 1 — Run the agent](1-run-the-agent.md)`.

- [ ] **Step 2: Verify** — from a clean read, the commands are copy-pasteable and consistent with Task 1's files (token `devtoken`, port 50051, paths). Confirm `docker compose up -d --wait` succeeds and goose config keys match `goose-extension.md`.

- [ ] **Step 3: Commit** `docs(workshop): 0-setup`.

---

### Task 3: `1-run-the-agent.md` (Checkpoint 1 — watch it over-reach)

**Files:** Create `delegated-agent-authorization/1-run-the-agent.md`

- [ ] **Step 1: Author the checkpoint** — model on `../agentic-rag-authorization/1-agentic-rag.md`. Cover:
  1. The flow: goose calls the deploy-bot MCP extension; every tool routes through `authz.decide()` before acting.
  2. Show the `decide()` stub (quote the `WORKSHOP STUB` block from `authz.py`) and explain: it returns ALLOWED without consulting SpiceDB.
  3. **Watch it over-reach (goose path):** in a `goose session`, ask *"Deploy checkout to production"*, then *"Tear down the production environment."* Both execute — the agent has no authorization boundary.
  4. **Deterministic path:** `python scripts/verify.py --checkpoint 1` → shows the stub allows `destroy production`.
  5. Why: an agent runs with its host's ambient authority; with no authorization boundary, it can do anything the credentials can. Putting the rule in the prompt is not enough — a prompt can be bypassed.
  6. `## Completion Milestone: Checkpoint 1` — ran the agent; reproduced the over-reach via goose and/or `verify.py`; can explain why ambient authority is the problem.
  7. `Next: [Checkpoint 2 — Delegated authorization](2-delegated-authorization.md)`.

- [ ] **Step 2: Verify** — the quoted stub matches `authz.py` exactly; `verify.py --checkpoint 1` output matches what the doc claims.

- [ ] **Step 3: Commit** `docs(workshop): CP1 run-the-agent`.

---

### Task 4: `2-delegated-authorization.md` (Checkpoint 2 — the core)

**Files:** Create `delegated-agent-authorization/2-delegated-authorization.md`

**Interfaces:** the fill-in code here must reproduce the CP2 state that `verify.py --checkpoint 2` asserts (staging ALLOWED, prod NEEDS_APPROVAL, destroy BLOCKED, post-approve prod ALLOWED).

- [ ] **Step 1: Author the checkpoint** — model on `../agentic-rag-authorization/2-secure-it.md`. Cover:
  1. **Concepts (inline):** ReBAC vs. RBAC; Google Zanzibar; why the decision must be a deterministic check, not the prompt.
  2. **Write the schema** — attendee replaces `schema.zed` with (this exact block):
     ```zed
     definition user {}
     definition agent { relation delegator: user }
     definition environment {
         relation direct_deployer: user
         relation agent_deployer: agent
         relation approver: user
         relation destroyer: user
         permission deploy  = direct_deployer + agent_deployer
         permission approve = approver
         permission destroy = destroyer
     }
     ```
     Explain each relation/permission and the delegation idea (`agent.delegator`).
  3. **Seed it:** `python bootstrap.py` (writes schema + relationships: alice deploys both envs + approves prod; sre_admin is the only destroyer; the agent is delegated staging-only).
  4. **Implement `decide()`** — attendee replaces the stub with (this exact block):
     ```python
     async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
         if await check(client, "agent", agent_id, permission, "environment", environment_id):
             return AuthzResult(Decision.ALLOWED,
                 f"agent:{agent_id} holds delegated '{permission}' on environment:{environment_id}")
         delegator = await read_delegator(client, agent_id)
         if delegator and await check(client, "user", delegator, permission, "environment", environment_id):
             return AuthzResult(Decision.NEEDS_APPROVAL,
                 f"agent:{agent_id} lacks '{permission}'; delegator user:{delegator} holds it — human approval required")
         return AuthzResult(Decision.BLOCKED,
             f"neither agent:{agent_id} nor its delegator may '{permission}' environment:{environment_id}")
     ```
     Explain the three-way logic: agent's own grant → ALLOWED; else the human it acts for could → NEEDS APPROVAL; else BLOCKED.
  5. **See it (both paths):** start the web UI (`python web.py`, open `http://127.0.0.1:8000`) — deploy staging ✅, deploy prod ⏸, destroy 🚫; run `python approve.py --approver alice --env production` then retry prod → ✅. And in goose, the same prompts. Deterministic: `python scripts/verify.py --checkpoint 2` → `PASS ✅`.
  6. Why the check (not the prompt) is the boundary — deterministic, unbypassable, the agent only ever gets an answer SpiceDB computed.
  7. `## Completion Milestone: Checkpoint 2` — wrote the schema; seeded; implemented `decide()`; `verify.py --checkpoint 2` passes; saw the three-way decision in the UI and/or goose; can explain ReBAC.
  8. `Next: [Checkpoint 3 — Time-bound and revocable](3-time-bound-and-revocable.md)`.

- [ ] **Step 2: Verify the fill-ins reach the CP2 state** — from `starter/`, apply the schema + `decide()` blocks from the doc, then:
  ```bash
  python scripts/verify.py --checkpoint 2
  ```
  Expected `PASS ✅`. (Restore the stubs afterward so `starter/` ships stubbed: `git checkout starter/schema.zed starter/authz.py`.)

- [ ] **Step 3: Commit** `docs(workshop): CP2 delegated-authorization`.

---

### Task 5: `3-time-bound-and-revocable.md` (Checkpoint 3)

**Files:** Create `delegated-agent-authorization/3-time-bound-and-revocable.md`

**Interfaces:** fill-ins must reach the CP3 state `verify.py --checkpoint 3` asserts (window 0 → NEEDS_APPROVAL; revoke → NEEDS_APPROVAL). Requires the schema `agent_deployer: agent with expiration`, `seed()`/`approve.py` writing `optional_expires_at`.

- [ ] **Step 1: Author the checkpoint.** Cover:
  1. Concept: temporary access — incident windows. SpiceDB's built-in relationship expiration (preferred over a caveat; evaluated server-side; garbage-collected).
  2. **Schema edit:** add `use expiration` at the top and change the relation to `relation agent_deployer: agent with expiration`. (Show the exact diff.)
  3. **Update the seed** — in `bootstrap.py`, change the staging grant line to carry an expiry:
     ```python
     from authz import expiry_from_now
     # ...
     rel("environment", "staging", "agent_deployer", "agent", AGENT_ID,
         expires_at=expiry_from_now(window_minutes)),
     ```
  4. **Update `approve.py`** — write the grant with an expiry:
     ```python
     from authz import check, read_delegator, expiry_from_now
     # ...
     update = rel("environment", environment, "agent_deployer", "agent", agent_id,
                  expires_at=expiry_from_now(minutes))
     ```
  5. **See expiry without waiting:** `python bootstrap.py --window-minutes 0` seeds an already-expired staging grant → the agent's autonomous staging deploy drops to NEEDS APPROVAL. Then **revocation:** `python revoke.py --env staging` → same effect, instantly. Both visible in the web UI (grant disappears / countdown) and via `python scripts/verify.py --checkpoint 3`.
  6. Why contingent evaluation beats a cron job that deletes grants.
  7. `## Completion Milestone: Checkpoint 3` — added expiration to schema + seed + approve; demoed the window and revoke; `verify.py --checkpoint 3` passes.
  8. `Next: [Checkpoint 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md)`.

- [ ] **Step 2: Verify the fill-ins** — apply CP2 fill-ins + CP3 edits, then `python scripts/verify.py --checkpoint 3` → `PASS ✅`. Restore stubs after (`git checkout starter/`).

- [ ] **Step 3: Commit** `docs(workshop): CP3 time-bound-and-revocable`.

---

### Task 6: `4-relationship-based-hierarchy.md` (Checkpoint 4 — the payoff)

**Files:** Create `delegated-agent-authorization/4-relationship-based-hierarchy.md`

**Interfaces:** fill-ins must reach the CP4 state `verify.py --checkpoint 4` asserts (both grants → prod ALLOWED; revoke staging → staging AND production NEEDS_APPROVAL — the cascade). Requires `gated_by`, `agent_deploy = agent_deployer & gated_by->agent_deployer`, `deploy = direct_deployer + agent_deploy`, and gated_by seed.

- [ ] **Step 1: Author the checkpoint.** Cover:
  1. Concept: hierarchical/contingent authority — production autonomy should depend on staging autonomy. RBAC can't express this without a role-per-combination explosion.
  2. **Schema edit** (show exact additions):
     ```zed
     // inside definition environment:
     relation gated_by: environment
     permission agent_deploy = agent_deployer & gated_by->agent_deployer
     permission deploy = direct_deployer + agent_deploy
     ```
     Explain the intersection + arrow: the agent may deploy here only if it holds this env's grant AND the gating env's grant. Staging gates itself (base); production is gated by staging.
  3. **Seed gated_by** — add to `bootstrap.seed()`:
     ```python
     rel("environment", "staging", "gated_by", "environment", "staging"),
     rel("environment", "production", "gated_by", "environment", "staging"),
     ```
  4. **See the cascade:** re-seed; `python approve.py --approver alice --env production` (agent now deploys both). Then `python revoke.py --env staging` — production autonomy suspends automatically, no second delete. Web UI shows production as a dashed *suspended* grant. `python scripts/verify.py --checkpoint 4` → `PASS ✅`.
  5. Why: it's contingent *evaluation*, not a delete — so it's suspend-not-erase (re-granting staging revives production while its window lasts). This is the ReBAC superpower.
  6. `## Completion Milestone: Checkpoint 4` — added `gated_by` + `agent_deploy`; seeded the hierarchy; demoed the staging→production cascade; `verify.py --checkpoint 4` passes; can explain why RBAC can't do this.
  7. `Next: [Next steps](5-nextsteps.md)`.

- [ ] **Step 2: Verify the fill-ins** — apply CP2+CP3+CP4 edits, then `python scripts/verify.py --checkpoint 4` → `PASS ✅`. Confirm the resulting schema matches the tested solution's `schema.zed` behavior. Restore stubs after (`git checkout starter/`).

- [ ] **Step 3: Commit** `docs(workshop): CP4 relationship-based-hierarchy`.

---

### Task 7: `README.md`, `5-nextsteps.md`, and full end-to-end validation

**Files:** Create `delegated-agent-authorization/README.md`, `delegated-agent-authorization/5-nextsteps.md`

- [ ] **Step 1: Author `README.md`** — model on `../agentic-rag-authorization/README.md`. Include: the title + abstract (from the conference listing); "Why this matters" (agents run with credentials that touch everything); "What you'll build" (bulleted); prerequisites (Docker/Codespaces, Python 3.10+, goose + an LLM key for the goose path); the **90-minute module map** with the per-checkpoint timing from the spec (Setup 15 · CP1 10 · CP2 25 · CP3 15 · CP4 20 · Next Steps 5); a link to the full reference solution `https://github.com/sohanmaheshwar/goose-spicedb-delegation`; and the ordered module links. End with "Let's get started with [Setup](0-setup.md)."

- [ ] **Step 2: Author `5-nextsteps.md`.** Cover: modeling authority once as relationships for a whole platform; `CheckBulk` for "which of these N resources may this agent touch"; on-behalf-of vs. advisory enforcement; production hardening the workshop deliberately skipped (gate `revoke`/admin actions behind a `manage` permission; gate `list_environments` behind a `view` permission — point to the solution repo which does both); scaling ReBAC with SpiceDB (Zanzibar lineage, Kubernetes — link the other AuthZed workshop). Keep it a short zoom-out.

- [ ] **Step 3: Full end-to-end validation (the integration test).** From a fresh `starter/` (stubs in place), walk the entire workshop in order, applying each checkpoint's fill-in code from the markdown and running its verifier:
  ```bash
  cd delegated-agent-authorization/starter
  docker compose up -d --wait
  python scripts/verify.py --checkpoint 1            # stub over-reach: PASS
  # apply CP2 schema + decide() from 2-delegated-authorization.md
  python scripts/verify.py --checkpoint 2            # PASS
  # apply CP3 edits from 3-time-bound-and-revocable.md
  python scripts/verify.py --checkpoint 3            # PASS
  # apply CP4 edits from 4-relationship-based-hierarchy.md
  python scripts/verify.py --checkpoint 4            # PASS
  git checkout schema.zed authz.py bootstrap.py approve.py   # restore ship-state stubs
  ```
  All four must PASS. This proves the checkpoints' embedded code is correct and complete. Fix any checkpoint whose fill-ins don't reach its verifier state.

- [ ] **Step 4: Confirm `starter/` ships stubbed** — `git status` clean; `schema.zed` and `authz.decide()` are the CP1 stubs; `bootstrap.py`/`approve.py` are the CP2 versions (no expiry).

- [ ] **Step 5: Commit** `docs(workshop): README, next steps, end-to-end validated`.

---

## Self-Review

**Spec coverage:**
- Folder/structure → Task 1 + doc tasks. ✓
- Guided-implement (schema + decide) → CP2 (Task 4), grown in CP3/CP4 (Tasks 5/6); everything else provided in Task 1. ✓
- goose headline + deterministic verifier → both paths in every checkpoint; `verify.py` (Task 1) + web UI (copied Task 1). ✓
- CP1 over-reach → Task 3 + `decide()` stub + `verify.py --checkpoint 1`. ✓
- Delegation / 3-way → CP2 (Task 4). ✓
- Time-bound + revoke → CP3 (Task 5). ✓
- ReBAC hierarchy/cascade → CP4 (Task 6). ✓
- Setup (Docker + Codespaces) → Task 2 + devcontainer (Task 1). ✓
- README + module map + timing + next steps → Task 7. ✓
- Prereqs, non-goals (no manage/view/rollback; revoke ungated) → Global Constraints + Next Steps follow-ups. ✓
- Success criteria (clean clone → all checkpoints pass) → Task 7 Step 3 end-to-end validation. ✓

**Placeholder scan:** All code blocks are complete and exact. `# TODO(Checkpoint N):` markers are intentional workshop-stub content, not plan placeholders. Doc-authoring steps specify exact embedded code + the reference file to match for tone (not "write prose").

**Type consistency:** `decide(client, agent_id, permission, environment_id)` (no `action`) is consistent across authz.py, deploybot_server.py (Task 1 mod drops `action=`), verify.py, and the CP2 fill-in. `check`/`read_delegator`/`expiry_from_now`/`rel`/`agent_deployer_filter` signatures match the solution's and are used consistently. `deploy` (not `agent_deploy`) is the permission checked by web.py `/api/state` and verify.py — works CP2→CP4 because CP4 rewires `deploy` through `agent_deploy`.

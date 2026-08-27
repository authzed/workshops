# Delegated Authorization for AI Agents — Workshop Design

**Date:** 2026-08-04
**Status:** Approved design, ready for implementation plan
**Folder:** `delegated-agent-authorization/` (in `authzed/workshops`)
**Branch:** `workshop/delegated-agent-authorization`

## What this is

A self-guided, hands-on workshop that teaches technical attendees how to add
**delegated, fine-grained authorization** to AI agents. Attendees build a DevOps
deploy agent on **goose** (the open-source agent from the Agentic AI Foundation) and
gate its every action with **SpiceDB** using **Relationship-Based Access Control
(ReBAC)**. By the end they understand scoped delegation, time-bound (expiring) grants,
instant revocation, and hierarchical permissions where revoking a base grant cascades
to dependents — something role-based systems can't express cleanly.

Delivered first at a conference (Fri Sep 11, 2026, JST), then published to
`authzed/workshops`.

## Audience, duration, learning goals

- **Audience:** technical — AI engineers and programmers. Comfortable with a terminal,
  Python, Docker. No prior authorization background assumed.
- **Duration:** 90 minutes, self-guided (works both live and after the fact).
- **Learning goals:** by the end, an attendee can explain and has hands-on built:
  1. **Delegated authorization** — an agent acts on a human's behalf with a scoped
     subset of their authority; decisions resolve to ALLOWED / NEEDS APPROVAL / BLOCKED.
  2. **Time-bound expiration** — grants that expire on their own (incident windows),
     plus instant revocation.
  3. **ReBAC / hierarchy** — relationship- and hierarchy-aware permissions, incl. a
     cascade (revoking staging autonomy suspends production autonomy automatically).

## Format (follows the reference workshop)

Matches `agentic-rag-authorization`: a `starter/` app with intentionally-stubbed
authorization pieces, checkpoint markdown files that go *run it → watch it fail →
implement the fix → re-run → why this is the right design*, each ending in a
**Completion Milestone** checklist, plus a setup doc (local Docker **and** a Codespaces
devcontainer) and a web UI to see decisions live.

**Pedagogy — guided implement:** attendees write the two pedagogically valuable things
themselves from `# TODO(Checkpoint N):` stubs — **the SpiceDB schema** (grown across
CP2→CP4) and **the `decide()` decision engine** (CP2). Everything else is provided
plumbing: the goose MCP extension, docker-compose, seed harness, approve/revoke scripts,
web UI, devcontainer. The exact code-to-write is embedded in each checkpoint (the
reference's own pattern). The complete reference solution is the published
`github.com/sohanmaheshwar/goose-spicedb-delegation` repo, linked from the workshop.

**Two ways to see every checkpoint:** goose is the headline — attendees register the
MCP extension and talk to it in natural language ("Deploy checkout to production"). The
**web UI** + `python scripts/verify.py` are the deterministic verifier, so every
checkpoint is confirmable in a room without depending on an LLM key. The deterministic
path never needs an LLM.

## Artifact structure

```
delegated-agent-authorization/
  README.md                          # overview, "what you'll build", prereqs, 90-min module map, solution link
  0-setup.md                         # Docker + Codespaces devcontainer, register goose extension, seed, verify
  1-run-the-agent.md                 # CP1: run the UNGATED agent, watch it over-reach
  2-delegated-authorization.md       # CP2: write delegation schema + implement decide() (3-way); ReBAC concepts
  3-time-bound-and-revocable.md      # CP3: expiring grants (incident window) + instant revoke
  4-relationship-based-hierarchy.md  # CP4: gated_by cascade — revoke staging suspends prod
  5-nextsteps.md                     # scale: ReBAC in prod, CheckBulk, on-behalf-of, real platform teams
  starter/
    docker-compose.yml               # postgres + spicedb (+ expiration flag)
    schema.zed                       # STUB — grown by learners across CP2→CP4
    authz.py                         # decide() + helpers STUB — implemented in CP2
    bootstrap.py                     # seed harness (grant-writing evolves with the schema)
    deploybot_server.py              # goose MCP extension — provided plumbing; calls decide()
    spicedb_client.py                # provided
    relationships.py                 # provided TOUCH/filter helpers
    approve.py, revoke.py            # provided lifecycle scripts
    web.py, static/index.html        # provided web UI (chat + authority bar + decision states)
    scripts/verify.py                # per-checkpoint deterministic verifier
    requirements.txt, .env.example
    goose-extension.md               # how to register the extension in goose
    .devcontainer/devcontainer.json  # Codespaces
  images/                            # authority-chain + decision-flow diagrams
```

## The checkpoint arc (the schema grows as they learn)

Each checkpoint adds exactly one concept by editing the schema and re-running. The
naive → fix → why loop drives every one.

### CP1 — Run it, watch it over-reach (~10 min)
`decide()` is a stub returning ALLOWED for everything (clear `# TODO(Checkpoint 2)`
docstring warning, mirroring the reference). Attendees register the extension, talk to
goose, and watch it deploy to production and tear down environments with no guardrail —
all green in the web UI. Takeaway: an agent runs with its host's ambient authority; with
no authorization boundary it can do anything the credentials can.

### CP2 — Delegated authorization (~25 min, includes ReBAC concepts)
Attendees **write `schema.zed`**:
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
and **implement `decide()`**: check the agent for the permission → ALLOWED; else read the
agent's `delegator` and check the delegator → NEEDS APPROVAL (a human could authorize);
else BLOCKED. Seed grants the agent staging-only deploy. Results: staging ✅, production
⏸ (with the `approve.py` human-in-the-loop flow), destroy 🚫. ReBAC and the Google
Zanzibar model are taught inline here (relationships, not flat roles; why the decision
lives in a deterministic check, not the prompt).

### CP3 — Time-bound & revocable (~15 min)
Attendees add expiration to the schema (`use expiration`;
`agent_deployer: agent with expiration`) and grants carry `optional_expires_at`.
Demonstrate the incident window and — because it's contingent evaluation — show expiry
without waiting (`bootstrap.py --window-minutes 0`), then instant `revoke.py`. Note this
uses SpiceDB's built-in relationship expiration (preferred over a caveat for expiry).

### CP4 — Relationship-based hierarchy (~20 min)
Attendees add the cascade to the schema:
```zed
relation gated_by: environment          // production -> staging; staging -> itself
permission agent_deploy = agent_deployer & gated_by->agent_deployer
permission deploy = direct_deployer + agent_deploy
```
Production autonomy becomes contingent on staging autonomy. Revoke staging → production
`agent_deploy` evaluates false automatically, no second delete. This is the payoff: the
thing RBAC can't express cleanly. The web UI shows the suspended production grant as a
dashed chip.

### 5 — Next steps (~5 min)
How this maps to a real platform team: modeling authority once as relationships,
`CheckBulk` for "which of these N resources may this agent touch", on-behalf-of vs.
advisory enforcement, and scaling ReBAC with SpiceDB (Zanzibar lineage). Links to the
full solution repo and SpiceDB docs.

## Verification

- `starter/scripts/verify.py` asserts the expected decision matrix for the **current**
  checkpoint (so a learner confirms their schema/`decide()` is correct before moving on),
  mirroring the reference's `verify_permissions.py`. It runs against live SpiceDB, no LLM.
- The web UI shows each decision (ALLOWED / NEEDS APPROVAL / BLOCKED) and the live
  authority state (delegation chain + expiry countdown).
- goose provides the natural-language "for real" path.

## Prerequisites (stated in README/setup)

- Docker (or a GitHub Codespace via the provided devcontainer)
- Python 3.10+
- goose installed, plus an API key for any LLM goose supports (only needed for the
  goose path; the deterministic verifier + web UI need no LLM)

## Decisions & defaults

- **Language:** Python (matches the demo and the authzed/langchain workshop stack).
- **SpiceDB:** local via Docker Compose, `authzed/spicedb:latest`, insecure preshared key
  (`somerandomkeyhere` or `devtoken`), expiration enabled via
  `--enable-experimental-relationship-expiration`.
- **Solution source:** adapt the tested `goose-spicedb-delegation` repo — the `starter/`
  is that code with `schema.zed` and `authz.decide()` stubbed; checkpoints contain the
  exact code to fill in.
- **Provided vs. implemented:** implemented by learner = schema + `decide()`; provided =
  everything else.

## Non-goals

- Not a goose internals or prompt-engineering workshop.
- Not production deployment of SpiceDB (Kubernetes/Operator) — that's a different
  workshop; touched only in Next Steps.
- No cloud accounts or paid services beyond an optional LLM key.
- Not multi-agent fleets (mentioned in Next Steps only).

## To verify at build time

- Exact goose custom-extension config (config.yaml stanza / `goose configure`) — reuse
  the demo's verified `goose-extension.md`.
- Codespaces devcontainer that runs `docker compose up -d` + installs deps on create.
- `scripts/verify.py` output format and the per-checkpoint assertions matching each
  schema state.

## Success criteria

- A learner starting from a clean clone completes setup, then all four checkpoints, with
  `scripts/verify.py` passing at each, on Docker or Codespaces.
- CP1 visibly over-reaches; CP2 produces the three-way decision; CP3 shows expiry +
  revoke; CP4 shows the staging→production cascade.
- The goose path and the web-UI/CLI path both demonstrate each checkpoint's behavior.
- Total content paces to ~90 minutes.

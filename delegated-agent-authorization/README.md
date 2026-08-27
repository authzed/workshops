# Delegated Authorization for AI Agents: Build an Agent with Fine-Grained Permissions

An AI agent doesn't ask permission before it acts — it inherits whatever its host process can
do. Point an agent at a set of credentials and "deploy checkout to staging" and "tear down
production" look identical to it: both are just tool calls that return `ALLOWED`, because nothing
downstream of the prompt is checking. In this hands-on workshop you build a DevOps deploy agent on
[goose](https://github.com/aaif-goose/goose) (the open-source agent from the Agentic AI
Foundation), watch it over-reach with no guardrail in place, then gate its every action with
delegated, fine-grained authorization from SpiceDB. By the end you'll have scoped grants, a
three-way decision (`ALLOWED` / `NEEDS_APPROVAL` / `BLOCKED`), time-bound windows with instant
revocation, and a relationship hierarchy where revoking one grant cascades to what depends on it —
the kind of policy a role-based system can't express without a synchronization job to keep it
honest.

---

## Why this matters

An agent process holds one set of credentials, and every tool call it makes runs with the full
weight of those credentials behind it — there's no built-in notion of *this specific action, for
this specific reason, scoped to this specific window*. That's **ambient authority**: authority
that comes along for free with the environment an agent runs in, rather than being granted for a
specific act. It's the same failure mode as a script running as root because it happened to be
launched by root, not because anyone decided it should have root.

The instinct to fix this in the system prompt — "never destroy production without approval" —
doesn't hold up. A prompt is a suggestion to a language model, not a control the system enforces;
it lives in the same channel as everything else the model reads, which means it can be argued
with, reworded around, or forgotten three turns into a longer conversation. An authorization
boundary has to live *outside* the model's judgment, in code that runs whether or not the agent
"remembers" the rule. That's what this workshop builds: a decision that's fully determined by a
relationship graph the agent has no way to write to, so the same question gets the same answer no
matter how many different ways — or how many different agents — ask it.

## What you'll build

- A goose MCP extension (`deploybot`) exposing three tools — `list_environments`, `deploy`,
  `destroy` — against a small deploy-agent backend
- A SpiceDB [ReBAC](https://authzed.com/blog/exploring-rebac) schema
  that models delegation directly: an `agent` acts for a `user` through one relation, `delegator`
- A three-way decision engine, `decide()`, that turns every mutating tool call into `ALLOWED`,
  `NEEDS_APPROVAL`, or `BLOCKED` — never a silent yes
- Time-bound grants that expire on their own, for incident-style access windows, plus a
  `revoke.py` for instant, on-demand revocation
- A relationship hierarchy (`gated_by`) where revoking one environment's autonomy automatically
  suspends what depends on it — contingent evaluation, not a cascading delete
- A web UI and a deterministic CLI verifier (`scripts/verify.py`) so every checkpoint is
  confirmable without an LLM in the loop

## Prerequisites

- **Docker**, or a GitHub Codespace — the repo ships a `.devcontainer/` that handles setup for you
- **Python 3.10+**
- **goose, plus an API key for any LLM it supports** — only needed if you want to drive the agent
  in natural language. Every checkpoint also has a deterministic path
  (`scripts/verify.py` and a web UI) that needs no LLM at all.

No prior authorization background is assumed. Comfort with a terminal, Python, and Docker is
enough.

## The 90-minute module map

| Module | Time | What you do |
| --- | --- | --- |
| [Setup](0-setup.md) | 15 min | Bring up Docker (or Codespaces), install dependencies, optionally register the goose extension |
| [Checkpoint 1 — Run the agent](1-run-the-agent.md) | 10 min | Run the agent ungated and watch it destroy production on request |
| [Checkpoint 2 — Delegated authorization](2-delegated-authorization.md) | 25 min | Write the ReBAC schema and implement the three-way `decide()` |
| [Checkpoint 3 — Time-bound and revocable](3-time-bound-and-revocable.md) | 15 min | Add expiring grants for incident windows, plus instant revocation |
| [Checkpoint 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md) | 20 min | Make production's autonomy contingent on staging's, and watch the cascade |
| [Next steps](5-nextsteps.md) | 5 min | Zoom out to a real platform: bulk checks, on-behalf-of enforcement, scaling ReBAC |

That's 90 minutes end to end, self-guided — it works equally well live or worked through on your
own afterward.

## The full reference solution

Everything you write in this workshop — the schema, `decide()`, the checkpoint progression — is a
guided version of a complete, tested implementation:
[`github.com/sohanmaheshwar/goose-spicedb-delegation`](https://github.com/sohanmaheshwar/goose-spicedb-delegation).
Use it if you get stuck, or to see the production-hardening this workshop deliberately skips (more
on that in [Next steps](5-nextsteps.md)).

## Modules

0. [Setup](0-setup.md)
1. [Checkpoint 1 — Run the agent](1-run-the-agent.md)
2. [Checkpoint 2 — Delegated authorization](2-delegated-authorization.md)
3. [Checkpoint 3 — Time-bound and revocable](3-time-bound-and-revocable.md)
4. [Checkpoint 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md)
5. [Next steps](5-nextsteps.md)

Let's get started with [Setup](0-setup.md).

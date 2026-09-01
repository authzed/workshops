# Delegated Authorization for AI Agents: Build an Agent with Fine-Grained Permissions

DevOps and Platform teams now work with hundreds of AI Agents in their internal systems. These
Agents usually run with credentials that can touch everything, including your production servers, which is less than ideal.

This workshop teaches you how to add delegated authorization to your AI Agents, at scale.

We'll build a DevOps deploy agent on goose, the open-source agent from the Agentic AI Foundation,
and give it fine-grained permissions using Relationship-Based Access Control (ReBAC). Along the
way you'll get hands-on with the Google Zanzibar model behind it, and why it fits AI agents:
scoped delegation, expiring grants, instant revocation, and hierarchical permissions where
revoking staging access automatically suspends production too, something role-based systems
can't express cleanly.

It's self-guided and hands-on, and everything runs locally with open-source tooling. Here's a high-level diagram of the workshop.

![Architecture diagram of the project](/delegated-agent-authorization/images/fig1-permission-check.svg)

---

## Why this matters

An agent process holds one set of credentials, and every tool call it makes runs with the full
weight of those credentials behind it — there's no built-in notion of *this specific action, for
this specific reason, scoped to this specific window*. That's **ambient authority**: authority
that comes along with the environment an agent runs in, rather than being granted for a
specific act. It's the same failure mode as a script running as root because it happened to be
launched by root, not because anyone decided it should have root.

The instinct to fix this in the prompt (example: "never destroy production without approval") but this is an anti-pattern. 
A prompt is a suggestion to a language model, not a control that a system enforces;
it lives in the same channel as everything else the model reads, which means it can be argued
with, reworded around, or bypassed via prompt injection. An authorization
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
  `NEEDS_APPROVAL`, or `BLOCKED`
- Time-bound grants that expire on their own, for incident-style access windows, plus instant,
  on-demand revocation for when you need to pull a grant early
- A relationship hierarchy (`gated_by`) where revoking one environment's autonomy automatically
  suspends what depends on it — contingent evaluation, not a cascading delete
- A web UI that drives every action — request, approve, revoke, watch a grant expire live — and
  shows exactly what SpiceDB decides, so every part is confirmable without an LLM in the loop

## Prerequisites

- **Docker**, or a GitHub Codespace — the repo ships a `.devcontainer/` that handles setup for you
- **Python 3.10+**
- **goose, plus an API key for any LLM it supports** — only needed if you want to drive the agent
  in natural language. The web UI drives every part without an LLM, so goose is optional
  throughout.

No prior authorization background is assumed. Comfort with a terminal, Python, and Docker is
enough.

## The full reference solution

Everything you write in this workshop — the schema, `decide()`, the part progression — is a
guided version of a complete, tested implementation:
[`github.com/sohanmaheshwar/goose-spicedb-delegation`](https://github.com/sohanmaheshwar/goose-spicedb-delegation).
Use it if you get stuck, or to see the production-hardening this workshop deliberately skips (more
on that in [Next steps](5-nextsteps.md)).

## Modules

0. [Setup](0-setup.md)
1. [Part 1 — Run the agent](1-run-the-agent.md)
2. [Part 2 — Delegated authorization](2-delegated-authorization.md)
3. [Part 3 — Time-bound and revocable](3-time-bound-and-revocable.md)
4. [Part 4 — Relationship-based hierarchy](4-relationship-based-hierarchy.md)
5. [Next steps](5-nextsteps.md)

Let's get started with [Setup](0-setup.md).

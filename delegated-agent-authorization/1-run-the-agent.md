# Checkpoint 1 — Run the Agent (and Watch It Over-Reach)

The goal here is simple: get the deploy agent running, then catch it doing something it should
never have been allowed to do — tearing down production — because right now nothing stops it.

---

## The flow — goose calls deploybot

`deploybot_server.py` is a goose MCP extension. It exposes three tools:

- **`list_environments`** — lists every environment and the service versions deployed to it.
  Read-only, and — by design, for this workshop — not authorization-checked. The code says so
  directly:

  ```python
  # UNGATED in this workshop: list_environments is not authorization-checked.
  ```

- **`deploy(service, environment)`** — deploys a service to an environment.
- **`destroy(environment)`** — tears down an entire environment. Its own docstring says
  *"Destructive; requires elevated authority."* No rollback tool exists; destroy is a one-way
  door.

`deploy` and `destroy` are mutating, and both are gated: before either touches anything, it calls
`authz.decide()` to get a ruling, and only proceeds on `ALLOWED`. That's the boundary this
workshop is about. In Checkpoint 1, the boundary is a stub that never says no.

---

## `decide()` is a deliberate stub

Open `authz.py`. `decide()` is the one function every mutating tool call goes through, and right
now it is honest about doing nothing:

```python
async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    # WORKSHOP STUB — Checkpoint 1.
    # Returns ALLOWED for everything WITHOUT consulting SpiceDB. This is exactly why
    # the agent over-reaches in Checkpoint 1. You implement the real, SpiceDB-backed
    # three-way decision in Checkpoint 2.
    # TODO(Checkpoint 2): replace this stub.
    return AuthzResult(Decision.ALLOWED, "no authorization configured (workshop stub)")
```

It takes a `client` — a live connection to SpiceDB — and ignores it. Every argument that should
matter (which agent, which permission, which environment) is ignored too. `decide()` always
returns `ALLOWED`. There is no schema yet for it to consult even if it wanted to — that arrives in
Checkpoint 2. Right now, an authorization call is just a formality the code performs on its way to
doing whatever it was asked.

---

## Watch it over-reach (goose path)

If you registered the `deploybot` extension in setup, open a session:

```bash
goose session
```

Ask it to do something reasonable:

> Deploy checkout to production.

goose calls `deploy(service="checkout", environment="production")`. It comes back
**✅ ALLOWED**, and the version bumps. Fine so far — that's a real deploy engineer's job.

Now ask it to do something no agent should be able to decide on its own:

> Tear down the production environment.

goose calls `destroy(environment="production")`. It comes back **✅ ALLOWED**, and production is
gone. No pause, no approval step, no distinction between "deploy a service" and "delete an entire
environment." The tool's own docstring says destroying "requires elevated authority" — but that's
just a comment for humans reading the code. Nothing enforces it. The stub doesn't look at
`permission` or `environment_id` at all, so it can't tell a deploy from a destroy any more than it
can tell staging from production.

Nothing about the *prompt* told the agent to be reckless. Nothing about the *user's* request was
malicious — "deploy checkout to production" and "tear down the production environment" are both
plausible things an operator might type into a chat window, adversarially or by mistake, or an
agent might decide to do on its own mid-task. The problem isn't the prompt. It's that nothing
downstream of the prompt is checking.

---

## Deterministic path

Don't have goose installed, or want a repeatable check instead of a live LLM session? From
`starter/`, with SpiceDB up:

```bash
python scripts/verify.py --checkpoint 1
```

Output:

```
Verifying Checkpoint 1...
  ✅ stub allows destroy production (over-reach): got Decision.ALLOWED, want Decision.ALLOWED
PASS ✅
```

This calls the exact same `authz.decide()` that `deploybot_server.py` calls on every tool
invocation — `decide(client, "goose_alice", "destroy", "production")` — no LLM involved, no goose
required. It asks the stub the most dangerous question in the workshop, "can this agent destroy
production," and the stub says yes. That's the whole bug, isolated to one deterministic assertion.

---

## Why this happens: ambient authority

The agent process holds one set of credentials — the `SPICEDB_TOKEN` and `AGENT_SUBJECT` in its
environment — and every tool call runs with the full weight of those credentials behind it.
There's no notion of *this specific action, for this specific reason, scoped to this specific
window*. The agent can do anything its host process could do, because as far as the code is
concerned, there is no difference between "deploy a service" and "destroy production." Both are
just tool calls that return `ALLOWED`.

This is **ambient authority**: authority that comes along for free with the environment an agent
runs in, rather than being granted for a specific act. It's the same failure mode as a script
running with root because it happened to be launched by root — not because anyone decided it
should have root.

You might be tempted to fix this by editing the tool's docstring, or telling the agent in its
system prompt "never destroy production without approval." Don't reach for that — a prompt is a
suggestion to a language model, not a control the system enforces. Nothing stops a differently
worded request, a longer conversation that talks the model out of its own guardrail, or a chain of
reasoning that convinces the agent this particular destroy is the exception. The instruction lives
in the same channel as everything else the model reads, which means it can be argued with. An
authorization boundary has to live *outside* the model's judgment, in code that runs whether or
not the agent "remembers" the rule. That boundary is what Checkpoint 2 builds.

---

## Completion Milestone: Checkpoint 1

- [ ] Ran the agent — via `goose session`, `scripts/verify.py --checkpoint 1`, or both
- [ ] Reproduced the over-reach: `destroy production` returns `ALLOWED` with no schema, no check,
      no pause
- [ ] Can point to the exact line in `authz.py` that makes this happen
- [ ] Can explain why ambient authority is the problem, and why fixing it in the prompt wouldn't
      be enough

Next: [Checkpoint 2 — Delegated authorization](2-delegated-authorization.md)

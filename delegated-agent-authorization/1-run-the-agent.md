# Part 1 — Run the Agent (and Watch It Over-Reach)

In this section we'll get the deploy agent running, try a few actions and catch it doing something it should
never be allowed to do. For example: this agent can tear down production servers since there are no permission checks to stop it from doing so.

---

## Going Live

The web UI is how you drive the agent throughout this workshop. It needs no LLM key: it turns your
text into the same tool calls goose would, and hands them to the same gated backend. From
`starter/`, with SpiceDB up:

```bash
python web.py
```

Open `http://127.0.0.1:8000`. Type something reasonable into the request box (or click one of the buttons)

> Deploy checkout to production.

The UI calls `deploy(service="checkout", environment="production")`. It comes back
**✅ ALLOWED**, and the version bumps. So far so good.

Now ask it to do something the agent should **not** be able to decide on its own:

> Tear down the production environment.

The UI calls `destroy(environment="production")`. It comes back **✅ ALLOWED**, and production environment is
gone. The tool's own docstring says destroying "requires elevated authority" — but there's no permission check to enforce it. 
The stub doesn't look at `permission` or `environment_id` at all, so it can't tell a deploy from a destroy any more than it
can tell staging from production.

Nothing about the *prompt* told the agent to be reckless. Nothing about the *user's* request was
malicious: "deploy checkout to production" and "tear down the production environment" are both
plausible things an operator might type into a chat window, adversarially or by mistake, or an
agent might decide to do on its own mid-task. This is the consequence of a lack of permission checks before performing an action.

---

## Or drive it with goose (optional)

If you installed goose and registered the `deploybot` extension in setup, open a session and give
it the same two requests:

```bash
goose session
```
And type the following and see what happens:

> Deploy checkout to production.
>
> Tear down the production environment.

goose calls the identical `deploy` / `destroy` tools the web UI calls, gated by the identical
stubbed `decide()`, so you get the identical **✅ ALLOWED** both times. Same error caused by a real
LLM instead of the request box.

---

## The backend

`deploybot_server.py` is a goose MCP extension (MCP — the Model Context Protocol — is how goose
calls external tools). It exposes three tools:

- **`list_environments`** — read-only; not authorization-checked in this workshop.
- **`deploy(service, environment)`** — deploys a service to an environment.
- **`destroy(environment)`** — tears down an entire environment; a one-way door.

`deploy` and `destroy` are mutating: before either touches anything it calls `authz.decide()` and
only proceeds on `ALLOWED`. That's the boundary this workshop is about.

---

## `decide()` is a deliberate stub

Open `authz.py` and look for the `decide()` method. It's the one function every mutating tool call goes through, and right
now there are no permission checks. 

```python
async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    # WORKSHOP STUB — Part 1.
    # Returns ALLOWED for everything. This is exactly why
    # the agent over-reaches in Part 1. You implement the real, SpiceDB-backed
    # three-way decision in Part 2.
    # TODO(Part 2): replace this stub.
    return AuthzResult(Decision.ALLOWED, "no authorization configured (workshop stub)")
```

It takes a live SpiceDB `client` and ignores it — along with which agent, permission, and
environment are involved. `decide()` always returns `ALLOWED`. That's the bug.

---

## Why this happens: ambient authority

The agent runs with one set of credentials, and every tool call carries their full weight — there's
no notion of *this specific action, for this specific reason, scoped to this specific window*. As
far as the code is concerned there's no difference between "deploy a service" and "destroy
production"; both are just calls that return `ALLOWED`. This is **ambient authority**: authority that
comes free with the environment an agent runs in, rather than being granted for a specific act.

You can't fix this in the prompt — a prompt is a suggestion to a model, not a control the system
enforces. The boundary has to live *outside* the model's judgment, in code that runs whether or not
the agent "remembers" the rule. That's what Part 2 builds.

---

## Completion Milestone: Part 1

- [ ] Ran the agent — via the web UI (`python web.py`), a `goose session`, or both
- [ ] Reproduced the over-reach: `destroy production` returns `ALLOWED` with no schema, no check,
      no pause
- [ ] Can point to the exact line in `authz.py` that makes this happen
- [ ] Can explain why ambient authority is the problem, and why fixing it in the prompt wouldn't
      be enough

Next: [Part 2 — Delegated authorization](2-delegated-authorization.md)

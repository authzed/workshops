"""deploybot_server.py — goose MCP extension; every mutating action is authorized by SpiceDB."""
import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from authz import Decision, decide
from spicedb_client import make_client

AGENT_SUBJECT = os.getenv("AGENT_SUBJECT", "agent:goose_alice")
AGENT_ID = AGENT_SUBJECT.split(":", 1)[-1]
STATE_PATH = Path(os.getenv("INFRA_STATE_PATH", str(Path(__file__).parent / "infra_state.json")))

mcp = FastMCP("deploybot")


def _load_state() -> dict:
    return json.loads(STATE_PATH.read_text())


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _format(result, action: str) -> str:
    icon = {
        Decision.ALLOWED: "✅ ALLOWED",
        Decision.NEEDS_APPROVAL: "⏸️  NEEDS APPROVAL",
        Decision.BLOCKED: "🚫 BLOCKED",
    }[result.decision]
    return f"{icon} — {action}\n{result.reason}"


async def do_list_environments() -> str:
    # UNGATED in this workshop: list_environments is not authorization-checked.
    state = _load_state()
    lines = [
        f"{env}: " + ", ".join(f"{svc} v{ver}" for svc, ver in svcs.items())
        for env, svcs in state.items()
    ]
    return "\n".join(lines) if lines else "(no environments)"


async def _decide_and_mutate(permission, environment, label, apply):
    """Authorize `permission` on the environment; on ALLOWED run apply(state) -> (changed, detail),
    persist iff changed, and format. On denial, format the reason against `label`."""
    result = await decide(make_client(), AGENT_ID, permission, environment)
    if result.decision is not Decision.ALLOWED:
        return _format(result, label)
    state = _load_state()
    changed, detail = apply(state)
    if changed:
        _save_state(state)
    return _format(result, f"{label} ({detail})" if changed else f"{label} — {detail}")


async def do_deploy(service: str, environment: str) -> str:
    def apply(state):
        state.setdefault(environment, {})
        state[environment][service] = state[environment].get(service, 0) + 1
        return True, f"now v{state[environment][service]}"

    return await _decide_and_mutate("deploy", environment, f"deploy {service} -> {environment}", apply)


async def do_destroy(environment: str) -> str:
    def apply(state):
        state.pop(environment, None)
        return True, "removed"

    return await _decide_and_mutate("destroy", environment, f"destroy {environment}", apply)


@mcp.tool()
async def list_environments() -> str:
    """List all deployment environments and their current service versions."""
    return await do_list_environments()


@mcp.tool()
async def deploy(service: str, environment: str) -> str:
    """Deploy a service to an environment (e.g. 'staging' or 'production')."""
    return await do_deploy(service, environment)


@mcp.tool()
async def destroy(environment: str) -> str:
    """Tear down an entire environment. Destructive; requires elevated authority."""
    return await do_destroy(environment)


if __name__ == "__main__":
    mcp.run()

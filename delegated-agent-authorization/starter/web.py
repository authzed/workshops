"""web.py — a goose-style chat front end for the SpiceDB delegation demo.

A thin FastAPI shell: it parses a natural-language request into a tool call and
delegates to the SAME code the MCP server uses (deploybot_server.do_*, approve,
revoke, bootstrap) against the live SpiceDB. The front end holds no authorization
logic of its own — what you see is exactly what SpiceDB decides.

Run:  python web.py   (then open http://127.0.0.1:8000)
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from google.protobuf.timestamp_pb2 import Timestamp
from authzed.api.v1 import Consistency, ReadRelationshipsRequest, WriteRelationshipsRequest

import bootstrap
import deploybot_server
from approve import approve
from authz import check, read_delegator
from relationships import agent_deployer_filter, rel
from revoke import revoke
from spicedb_client import make_client

BASE = Path(__file__).parent
AGENT_ID = deploybot_server.AGENT_ID
DELEGATOR = "alice"  # the human the demo agent acts for
BASELINE_STATE = {
    "staging": {"checkout": 3, "payments": 5},
    "production": {"checkout": 2, "payments": 4},
}

app = FastAPI(title="deploybot")

SERVICES = ("checkout", "payments")


def parse_intent(text: str):
    """Map a natural-language request to (op, service, environment). No LLM needed."""
    t = text.lower()
    env = (
        "production" if "prod" in t
        else "staging" if ("staging" in t or "stage" in t)
        else None
    )
    service = next((s for s in SERVICES if s in t), "checkout")
    if any(w in t for w in ("destroy", "tear down", "teardown", "delete", "nuke")):
        return "destroy", None, env or "production"
    if any(w in t for w in ("deploy", "ship", "release", "push")):
        return "deploy", service, env or "staging"
    if any(w in t for w in ("list", "environment", "status", "what can", "show", "see")):
        return "list", None, None
    return None, None, None


def _decision_of(out: str):
    if "NEEDS APPROVAL" in out:
        return "NEEDS_APPROVAL"
    if "BLOCKED" in out:
        return "BLOCKED"
    if "ALLOWED" in out:
        return "ALLOWED"
    return None


class RequestBody(BaseModel):
    text: str


class ApproveBody(BaseModel):
    environment: str = "production"
    minutes: int = 10


class RevokeBody(BaseModel):
    environment: str = "staging"


class GrantBody(BaseModel):
    environment: str = "staging"
    seconds: int = 30


@app.get("/")
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/api/request")
async def request_action(body: RequestBody):
    op, service, env = parse_intent(body.text)
    if op is None:
        return {
            "understood": False,
            "reply": "I can deploy or destroy a service in staging or "
                     'production — or list what you can see. Try "Deploy checkout to staging".',
        }
    if op == "list":
        listing = await deploybot_server.do_list_environments()
        return {"understood": True, "op": "list", "tool_call": "list_environments()",
                "decision": None, "reply": listing}

    if op == "deploy":
        out = await deploybot_server.do_deploy(service, env)
        tool_call = f"deploy({service}, {env})"
    else:  # destroy
        out = await deploybot_server.do_destroy(env)
        tool_call = f"destroy({env})"

    head, _, reason = out.partition("\n")
    _, sep, action = head.partition("— ")
    return {
        "understood": True,
        "op": op,
        "tool_call": tool_call,
        "decision": _decision_of(out),
        "action": action.strip() if sep else head.strip(),
        "reason": reason.strip(),
    }


@app.get("/api/state")
async def state():
    # Defensive throughout: in Checkpoint 1 no schema exists yet, so the delegator
    # read / relationship read / permission checks below all error. We degrade to an
    # empty "no delegation configured" view so the web UI still loads and the chat
    # (which routes through the stubbed decide()) shows the agent over-reaching.
    client = make_client()
    try:
        delegator = await read_delegator(client, AGENT_ID)
    except Exception:
        delegator = None
    grants = []
    try:
        req = ReadRelationshipsRequest(
            consistency=Consistency(fully_consistent=True),
            relationship_filter=agent_deployer_filter(AGENT_ID),
        )
        async for resp in client.ReadRelationships(req):
            r = resp.relationship
            env = r.resource.object_id
            expires_at = None
            if r.HasField("optional_expires_at"):
                dt = r.optional_expires_at.ToDatetime().replace(tzinfo=timezone.utc)
                expires_at = dt.isoformat()
            # A grant tuple can exist yet be suspended by the cascade (e.g. a prod grant
            # after staging was revoked). `effective` is the actual deploy verdict.
            try:
                effective = await check(client, "agent", AGENT_ID, "deploy", "environment", env)
            except Exception:
                effective = False
            grants.append({"environment": env, "expires_at": expires_at, "effective": effective})
    except Exception:
        grants = []  # no schema yet (Checkpoint 1)
    try:
        versions = deploybot_server._load_state()
    except Exception:
        versions = {}
    return {"agent": AGENT_ID, "delegator": delegator, "grants": grants, "versions": versions}


@app.post("/api/approve")
async def approve_action(body: ApproveBody):
    code = await approve(DELEGATOR, body.environment, AGENT_ID, body.minutes)
    return {"ok": code == 0, "environment": body.environment, "minutes": body.minutes}


@app.post("/api/revoke")
async def revoke_action(body: RevokeBody):
    code = await revoke(body.environment, AGENT_ID)
    return {"ok": code == 0, "environment": body.environment}


@app.post("/api/grant-short")
async def grant_short(body: GrantBody):
    """Grant the agent a short-lived deploy window so you can watch it expire live in the
    authority bar (used in Checkpoint 3). An operator/demo action: it writes the
    agent_deployer grant directly with a seconds-scale expiration. Requires the schema to
    allow expiration (`agent_deployer: agent with expiration`, from Checkpoint 3)."""
    client = make_client()
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc) + timedelta(seconds=body.seconds))
    update = rel("environment", body.environment, "agent_deployer", "agent", AGENT_ID, expires_at=ts)
    try:
        await client.WriteRelationships(WriteRelationshipsRequest(updates=[update]))
        return {"ok": True, "environment": body.environment, "seconds": body.seconds}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


@app.post("/api/reset")
async def reset():
    client = make_client()
    await bootstrap.write_schema(client)
    await bootstrap.seed(client, window_minutes=60)
    deploybot_server._save_state(dict(BASELINE_STATE))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

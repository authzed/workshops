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

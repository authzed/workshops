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

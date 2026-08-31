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
        # Part 2: staging-only delegation (no expiration yet).
        rel("environment", "staging", "agent_deployer", "agent", AGENT_ID),
    ]
    await client.WriteRelationships(WriteRelationshipsRequest(updates=updates))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the delegated-agent-authorization workshop.")
    parser.add_argument("--window-minutes", type=int, default=60,
                        help="Minutes the agent's staging delegation stays valid (Part 3+).")
    args = parser.parse_args()
    client = make_client()
    print("Writing schema...")
    await write_schema(client)
    print(f"Seeding delegation graph (window = {args.window_minutes} min)...")
    await seed(client, window_minutes=args.window_minutes)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

"""verify.py — deterministic checks for the current checkpoint. No LLM needed.

Usage: python scripts/verify.py --checkpoint N
Run from the starter/ directory with SpiceDB up.
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Invoked as `python scripts/verify.py`, so Python puts scripts/ (not starter/) on
# sys.path — add the parent directory so the top-level modules below resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authz import Decision, decide
import bootstrap
from approve import approve
from revoke import revoke
from spicedb_client import make_client

AGENT = "goose_alice"


def _ok(label, got, want):
    mark = "✅" if got == want else "❌"
    print(f"  {mark} {label}: got {got}, want {want}")
    return got == want


async def checkpoint_1():
    # The stub decides ALLOWED for everything — the over-reach.
    r = await decide(make_client(), AGENT, "destroy", "production")
    return _ok("stub allows destroy production (over-reach)", r.decision, Decision.ALLOWED)


async def checkpoint_2(client):
    await bootstrap.write_schema(client)
    await bootstrap.seed(client)
    passed = True
    passed &= _ok("agent deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.ALLOWED)
    passed &= _ok("agent deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.NEEDS_APPROVAL)
    passed &= _ok("agent destroy production", (await decide(client, AGENT, "destroy", "production")).decision, Decision.BLOCKED)
    await approve("alice", "production", AGENT, 10)
    passed &= _ok("after approve: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.ALLOWED)
    return passed


async def checkpoint_3(client):
    # Expired window -> staging autonomy gone (falls back to NEEDS_APPROVAL).
    await bootstrap.write_schema(client)
    await bootstrap.seed(client, window_minutes=0)
    passed = _ok("expired staging grant", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    # Revocation on a fresh window.
    await bootstrap.seed(client, window_minutes=60)
    await revoke("staging", AGENT)
    passed &= _ok("after revoke: deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    return passed


async def checkpoint_4(client):
    await bootstrap.write_schema(client)
    await bootstrap.seed(client, window_minutes=60)
    await approve("alice", "production", AGENT, 10)
    passed = _ok("with both grants: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.ALLOWED)
    await revoke("staging", AGENT)  # revoke the BASE
    passed &= _ok("cascade: deploy staging", (await decide(client, AGENT, "deploy", "staging")).decision, Decision.NEEDS_APPROVAL)
    passed &= _ok("cascade: deploy production", (await decide(client, AGENT, "deploy", "production")).decision, Decision.NEEDS_APPROVAL)
    return passed


async def main(n):
    print(f"Verifying Checkpoint {n}...")
    if n == 1:
        passed = await checkpoint_1()
    else:
        client = make_client()
        passed = await {2: checkpoint_2, 3: checkpoint_3, 4: checkpoint_4}[n](client)
    print("PASS ✅" if passed else "FAIL ❌")
    return 0 if passed else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=int, required=True, choices=[1, 2, 3, 4])
    raise SystemExit(asyncio.run(main(p.parse_args().checkpoint)))

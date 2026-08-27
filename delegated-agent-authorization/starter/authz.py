"""authz.py — SpiceDB helpers (provided) + the decision engine (you implement)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from google.protobuf.timestamp_pb2 import Timestamp
from authzed.api.v1 import (
    CheckPermissionRequest,
    CheckPermissionResponse,
    Consistency,
    ObjectReference,
    ReadRelationshipsRequest,
    RelationshipFilter,
    SubjectReference,
)


class Decision(str, Enum):
    ALLOWED = "ALLOWED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    BLOCKED = "BLOCKED"


@dataclass
class AuthzResult:
    decision: Decision
    reason: str


def expiry_from_now(minutes: int) -> Timestamp:
    """A protobuf Timestamp `minutes` from now, for a relationship's optional_expires_at."""
    ts = Timestamp()
    ts.FromDatetime(datetime.now(timezone.utc) + timedelta(minutes=minutes))
    return ts


async def check(client, sub_type, sub_id, permission, res_type, res_id) -> bool:
    """Does `subject` have `permission` on `resource`? A single SpiceDB CheckPermission."""
    resp = await client.CheckPermission(
        CheckPermissionRequest(
            consistency=Consistency(fully_consistent=True),
            resource=ObjectReference(object_type=res_type, object_id=res_id),
            permission=permission,
            subject=SubjectReference(
                object=ObjectReference(object_type=sub_type, object_id=sub_id)
            ),
        )
    )
    return resp.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION


async def read_delegator(client, agent_id) -> str | None:
    """The user this agent acts for (agent:<id>#delegator), or None."""
    req = ReadRelationshipsRequest(
        consistency=Consistency(fully_consistent=True),
        relationship_filter=RelationshipFilter(
            resource_type="agent",
            optional_resource_id=agent_id,
            optional_relation="delegator",
        ),
    )
    async for resp in client.ReadRelationships(req):
        return resp.relationship.subject.object.object_id
    return None


async def decide(client, agent_id, permission, environment_id) -> AuthzResult:
    # WORKSHOP STUB — Checkpoint 1.
    # Returns ALLOWED for everything WITHOUT consulting SpiceDB. This is exactly why
    # the agent over-reaches in Checkpoint 1. You implement the real, SpiceDB-backed
    # three-way decision in Checkpoint 2.
    # TODO(Checkpoint 2): replace this stub.
    return AuthzResult(Decision.ALLOWED, "no authorization configured (workshop stub)")

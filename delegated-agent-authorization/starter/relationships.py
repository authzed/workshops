"""relationships.py — shared SpiceDB relationship builders.

Used by bootstrap (seed + reset), approve (grant), and revoke (delete) so the
TOUCH-relationship shape and the agent_deployer filter live in exactly one place.
"""
from authzed.api.v1 import (
    ObjectReference,
    Relationship,
    RelationshipFilter,
    RelationshipUpdate,
    SubjectFilter,
    SubjectReference,
)


def rel(res_type, res_id, relation, sub_type, sub_id, expires_at=None):
    """A TOUCH RelationshipUpdate, optionally carrying a relationship expiration."""
    return RelationshipUpdate(
        operation=RelationshipUpdate.OPERATION_TOUCH,
        relationship=Relationship(
            resource=ObjectReference(object_type=res_type, object_id=res_id),
            relation=relation,
            subject=SubjectReference(
                object=ObjectReference(object_type=sub_type, object_id=sub_id)
            ),
            optional_expires_at=expires_at,
        ),
    )


def agent_deployer_filter(agent_id, environment=None):
    """Filter matching an agent's agent_deployer grants — one environment, or all if None."""
    return RelationshipFilter(
        resource_type="environment",
        optional_resource_id=environment or "",
        optional_relation="agent_deployer",
        optional_subject_filter=SubjectFilter(
            subject_type="agent", optional_subject_id=agent_id
        ),
    )

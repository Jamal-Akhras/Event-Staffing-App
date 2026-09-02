from __future__ import annotations

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository


def worker_can_see_shift(
    shift: Shift, worker_id: str, relationships: WorkerRelationshipRepository
) -> bool:
    if shift.origin == "market":
        return True
    if shift.origin == "assigned":
        return shift.assigned_worker_id == worker_id
    if not shift.account_id:
        return False
    relationship = relationships.get_for_venue_worker(shift.account_id, worker_id)
    return (
        relationship is not None
        and relationship.status in ("active", "invited")
        and relationship.relationship_type != "one_off"
    )

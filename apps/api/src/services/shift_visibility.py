from __future__ import annotations

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository


def worker_can_see_shift(
    shift: Shift, worker_id: str, relationships: WorkerRelationshipRepository
) -> bool:
    if shift.rota_state == "draft" or shift.needs_attention:
        return False
    if shift.origin == "market":
        return True
    if shift.origin == "assigned":
        return shift.assigned_worker_id == worker_id
    if not shift.account_id:
        return False
    relationship = relationships.get_for_venue_worker(shift.account_id, worker_id)
    if relationship is None or relationship.status not in ("active", "invited"):
        return False
    if shift.origin == "team":
        return relationship.relationship_type in EMPLOYED_TYPES
    return relationship.relationship_type != "one_off"

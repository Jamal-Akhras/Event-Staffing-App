from __future__ import annotations

from datetime import datetime

from apps.api.src.models.worker_relationship import EMPLOYED_TYPES, WorkerRelationship
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)


def relationship_type_as_of(
    relationships: WorkerRelationshipRepository,
    transitions: RelationshipTransitionRepository,
    venue_id: str,
    worker_id: str,
    at: datetime,
) -> str:
    relationship = relationships.get_for_venue_worker(venue_id, worker_id)
    if relationship is None:
        return "one_off"
    recorded = transitions.list_for_relationship(relationship.relationship_id)
    if not recorded:
        if relationship.created_at <= at and relationship.status in ("active", "invited"):
            return relationship.relationship_type
        return "one_off"
    state_type = recorded[0].from_relationship_type
    state_status = recorded[0].from_status
    for transition in recorded:
        if transition.occurred_at > at:
            break
        if transition.to_status == "invited":
            continue
        state_type = transition.to_relationship_type
        state_status = transition.to_status
    if state_type is None or state_status != "active":
        return "one_off"
    return state_type


def sibling_employed_venue_as_of(
    organisations: OrganisationRepository,
    relationships: WorkerRelationshipRepository,
    transitions: RelationshipTransitionRepository,
    venue_id: str,
    worker_id: str,
    at: datetime,
) -> str | None:
    venue = organisations.get_venue(venue_id)
    if venue is None:
        return None
    for sibling in organisations.list_venues_for_organisation(venue.organisation_id):
        if sibling.venue_id == venue_id:
            continue
        state = relationship_type_as_of(
            relationships, transitions, sibling.venue_id, worker_id, at
        )
        if state in EMPLOYED_TYPES:
            return sibling.venue_id
    return None


def sibling_employed_now(
    organisations: OrganisationRepository,
    relationships: WorkerRelationshipRepository,
    venue_id: str,
    worker_id: str,
) -> WorkerRelationship | None:
    venue = organisations.get_venue(venue_id)
    if venue is None:
        return None
    for sibling in organisations.list_venues_for_organisation(venue.organisation_id):
        if sibling.venue_id == venue_id:
            continue
        relationship = relationships.get_for_venue_worker(sibling.venue_id, worker_id)
        if (
            relationship is not None
            and relationship.status == "active"
            and relationship.relationship_type in EMPLOYED_TYPES
        ):
            return relationship
    return None

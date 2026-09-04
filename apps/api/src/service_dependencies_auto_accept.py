from __future__ import annotations

from fastapi import Depends

from apps.api.src.deps import get_shift_offer_service
from apps.api.src.repositories.shift_offer_repository import ShiftOfferRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import (
    WorkerRelationshipRepository,
)
from apps.api.src.repository_dependencies import (
    get_auto_accept_attempt_repo,
    get_auto_accept_rule_repo,
    get_shift_offer_repo,
    get_shift_repo,
)
from apps.api.src.repository_dependencies_workforce import get_worker_relationship_repo
from apps.api.src.services.auto_accept_service import AutoAcceptService
from apps.api.src.services.shift_offer_service import ShiftOfferService


def get_auto_accept_service(
    rules=Depends(get_auto_accept_rule_repo),
    attempts=Depends(get_auto_accept_attempt_repo),
    offers: ShiftOfferRepository = Depends(get_shift_offer_repo),
    shifts: ShiftRepository = Depends(get_shift_repo),
    relationships: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    offer_service: ShiftOfferService = Depends(get_shift_offer_service),
) -> AutoAcceptService:
    return AutoAcceptService(rules, attempts, offers, shifts, relationships, offer_service)

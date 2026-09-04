from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from apps.api.src.repositories.sqlalchemy_organisation_repository import (
    SqlAlchemyOrganisationRepository,
)
from apps.api.src.repositories.sqlalchemy_auto_accept_repository import (
    SqlAlchemyAutoAcceptAttemptRepository,
    SqlAlchemyWorkerAutoAcceptRuleRepository,
)
from apps.api.src.repositories.sqlalchemy_booking_allocator import (
    SqlAlchemyBookingAllocator,
)
from apps.api.src.repositories.sqlalchemy_booking_transition_repository import (
    SqlAlchemyBookingTransitionRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_offer_repository import (
    SqlAlchemyShiftOfferRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_certification_repository import (
    SqlAlchemyWorkerCertificationRepository,
)
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyWorkerRelationshipRepository,
)
from apps.api.src.services.auto_accept_service import AutoAcceptService
from apps.api.src.services.certification_gate import CertificationGate
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher
from apps.api.src.services.shift_offer_service import ShiftOfferService

log = logging.getLogger(__name__)


def sweep_auto_accept(service: AutoAcceptService, now: datetime) -> int:
    return _sweep_auto_accept(service, now, lambda offer: service.evaluate_offer(offer, now))


def _sweep_auto_accept(
    service: AutoAcceptService,
    now: datetime,
    evaluate: Callable,
) -> int:
    evaluated = 0
    for offer in service.claim_candidates(now):
        if not service.has_enabled_rule(offer):
            continue
        try:
            evaluate(offer)
        except Exception:
            log.exception("auto-accept evaluation failed for offer %s", offer.offer_id)
            continue
        evaluated += 1
    return evaluated


def run(now: datetime | None = None) -> int:
    with SessionLocal() as session, session.begin():
        shifts = SqlAlchemyShiftRepository(session)
        offers = SqlAlchemyShiftOfferRepository(session)
        relationships = SqlAlchemyWorkerRelationshipRepository(session)
        outbox = SqlAlchemyOutboxPublisher(session)
        offer_service = ShiftOfferService(
            offers,
            shifts,
            SqlAlchemyBookingAllocator(session),
            relationships,
            SqlAlchemyBookingTransitionRepository(session),
            EscalationService(
                shifts,
                relationships,
                SqlAlchemyAccountRepository(session),
                outbox,
                offers=offers,
            ),
            outbox,
            CertificationGate(SqlAlchemyWorkerCertificationRepository(session)),
            SqlAlchemyOrganisationRepository(session),
        )
        service = AutoAcceptService(
            SqlAlchemyWorkerAutoAcceptRuleRepository(session),
            SqlAlchemyAutoAcceptAttemptRepository(session),
            offers,
            shifts,
            relationships,
            offer_service,
        )
        evaluated_at = now or utc_now()

        def evaluate(offer) -> None:
            with session.begin_nested():
                service.evaluate_offer(offer, evaluated_at)

        return _sweep_auto_accept(service, evaluated_at, evaluate)


if __name__ == "__main__":
    print(f"Auto-accept sweep evaluated {run()} offer(s).")

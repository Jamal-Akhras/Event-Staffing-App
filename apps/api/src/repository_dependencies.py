from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.application_decision_repository import ApplicationDecisionRepository
from apps.api.src.repositories.application_message_history_repository import ApplicationMessageHistoryRepository
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.in_memory_application_decision_repository import InMemoryApplicationDecisionRepository
from apps.api.src.repositories.in_memory_application_message_history_repository import InMemoryApplicationMessageHistoryRepository
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_message_repository import InMemoryMessageRepository
from apps.api.src.repositories.in_memory_market_repository import InMemoryMarketRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.repositories.in_memory_report_repository import InMemoryReportRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.in_memory_booking_charge_repository import InMemoryBookingChargeRepository
from apps.api.src.repositories.in_memory_booking_transition_repository import InMemoryBookingTransitionRepository
from apps.api.src.repositories.sqlalchemy_booking_charge_repository import SqlAlchemyBookingChargeRepository
from apps.api.src.repositories.sqlalchemy_booking_transition_repository import SqlAlchemyBookingTransitionRepository
from apps.api.src.repositories.in_memory_event_repository import InMemoryEventRepository
from apps.api.src.repositories.event_repository import EventRepository
from apps.api.src.repositories.sqlalchemy_event_repository import SqlAlchemyEventRepository
from apps.api.src.repositories.in_memory_partner_code_repository import InMemoryPartnerCodeRepository
from apps.api.src.repositories.partner_code_repository import PartnerCodeRepository
from apps.api.src.repositories.sqlalchemy_partner_code_repository import SqlAlchemyPartnerCodeRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_template_repository import InMemoryTemplateRepository
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_worker_feed_state_repository import InMemoryWorkerFeedStateRepository
from apps.api.src.repositories.in_memory_worker_feed_query_repository import InMemoryWorkerFeedQueryRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.rating_repository import RatingRepository
from apps.api.src.repositories.report_repository import ReportRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
from apps.api.src.repositories.sqlalchemy_application_decision_repository import SqlAlchemyApplicationDecisionRepository
from apps.api.src.repositories.sqlalchemy_application_message_history_repository import SqlAlchemyApplicationMessageHistoryRepository
from apps.api.src.repositories.sqlalchemy_application_repository import SqlAlchemyApplicationRepository
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_message_repository import SqlAlchemyMessageRepository
from apps.api.src.repositories.sqlalchemy_market_repository import SqlAlchemyMarketRepository
from apps.api.src.repositories.sqlalchemy_notification_repository import SqlAlchemyNotificationRepository
from apps.api.src.repositories.sqlalchemy_organisation_repository import SqlAlchemyOrganisationRepository
from apps.api.src.repositories.sqlalchemy_rating_repository import SqlAlchemyRatingRepository
from apps.api.src.repositories.sqlalchemy_report_repository import SqlAlchemyReportRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_template_repository import SqlAlchemyTemplateRepository
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from apps.api.src.repositories.sqlalchemy_worker_feed_state_repository import SqlAlchemyWorkerFeedStateRepository
from apps.api.src.repositories.sqlalchemy_worker_feed_query_repository import SqlAlchemyWorkerFeedQueryRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import SqlAlchemyWorkerProfileRepository
from apps.api.src.repositories.template_repository import TemplateRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.email import get_email_transport
from apps.api.src.services.outbox_publisher import (
    InMemoryOutboxPublisher,
    OutboxPublisher,
    SqlAlchemyOutboxPublisher,
)
from apps.api.src.repositories.worker_feed_query_repository import WorkerFeedQueryRepository
from apps.api.src.unit_of_work import RequestUnitOfWork

_BOOKINGS = InMemoryBookingRepository()
_APPLICATIONS = InMemoryApplicationRepository()
_SHIFTS = InMemoryShiftRepository(_BOOKINGS)
_BOOKINGS.attach_shift_repo(_SHIFTS)
_APPLICATIONS.attach_shift_repo(_SHIFTS)
_WORKERS = InMemoryWorkerProfileRepository()
_USERS = InMemoryUserRepository()
_TEMPLATES = InMemoryTemplateRepository()
_MESSAGES = InMemoryMessageRepository()
_FEED_STATES = InMemoryWorkerFeedStateRepository()
_MESSAGE_HISTORY = InMemoryApplicationMessageHistoryRepository()
_ACCOUNTS = InMemoryAccountRepository()
_ORGANISATIONS = InMemoryOrganisationRepository(_ACCOUNTS)
_MARKETS = InMemoryMarketRepository()
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository as _RelationshipRepo,
)

_RELATIONSHIPS = _RelationshipRepo()
from apps.api.src.repositories.in_memory_rota_publication_repository import (
    InMemoryRotaPublicationRepository as _RotaPublicationRepo,
)

_ROTA_PUBLICATIONS = _RotaPublicationRepo()
from apps.api.src.repositories.in_memory_booking_charge_adjustment_repository import (
    InMemoryBookingChargeAdjustmentRepository as _ChargeAdjustmentRepo,
)

_CHARGE_ADJUSTMENTS = _ChargeAdjustmentRepo()


def shared_booking_charge_adjustment_repository():
    return _CHARGE_ADJUSTMENTS


from apps.api.src.repositories.in_memory_shift_offer_repository import (
    InMemoryShiftOfferRepository as _ShiftOfferRepo,
)

_SHIFT_OFFERS = _ShiftOfferRepo()


def shared_shift_offer_repository():
    return _SHIFT_OFFERS


from apps.api.src.repositories.in_memory_shift_change_request_repository import (
    InMemoryShiftChangeRequestRepository as _ShiftChangeRepo,
    InMemoryShiftChangeTransitionRepository as _ShiftChangeTransitionRepo,
)

_SHIFT_CHANGES = _ShiftChangeRepo()
_SHIFT_CHANGE_TRANSITIONS = _ShiftChangeTransitionRepo()


def shared_shift_change_request_repository():
    return _SHIFT_CHANGES


def shared_shift_change_transition_repository():
    return _SHIFT_CHANGE_TRANSITIONS


from apps.api.src.repositories.in_memory_worker_certification_repository import (
    InMemoryWorkerCertificationRepository as _CertRepo,
)

_WORKER_CERTIFICATIONS = _CertRepo()


def shared_worker_certification_repository():
    return _WORKER_CERTIFICATIONS

_FEED_QUERY = InMemoryWorkerFeedQueryRepository(
    _SHIFTS,
    _ORGANISATIONS,
    _APPLICATIONS,
    _FEED_STATES,
    _RELATIONSHIPS,
)
_NOTIFICATIONS = InMemoryNotificationRepository()
_REPORTS = InMemoryReportRepository()
_PARTNER_CODES = InMemoryPartnerCodeRepository()
_EVENTS = InMemoryEventRepository()
_BOOKING_CHARGES = InMemoryBookingChargeRepository()
_BOOKING_TRANSITIONS = InMemoryBookingTransitionRepository()
_DECISIONS = InMemoryApplicationDecisionRepository(_APPLICATIONS, _BOOKINGS, _SHIFTS)


def get_request_unit_of_work() -> Generator[RequestUnitOfWork, None, None]:
    unit_of_work = RequestUnitOfWork(None if use_in_memory_repositories() else SessionLocal())
    try:
        yield unit_of_work
        unit_of_work.commit()
    except BaseException:
        unit_of_work.rollback()
        raise
    finally:
        unit_of_work.close()


def get_request_session(
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> Session | None:
    return unit_of_work.session


def _session(value: Session | None) -> Session:
    if value is None:
        raise RuntimeError("A database-backed repository requires a request session.")
    return value


def get_booking_repo(session: Session | None = Depends(get_request_session)) -> BookingRepository:
    return _BOOKINGS if use_in_memory_repositories() else SqlAlchemyBookingRepository(_session(session))


def get_application_repo(session: Session | None = Depends(get_request_session)) -> ApplicationRepository:
    return _APPLICATIONS if use_in_memory_repositories() else SqlAlchemyApplicationRepository(_session(session))


def get_application_decision_repo(
    session: Session | None = Depends(get_request_session),
) -> ApplicationDecisionRepository:
    return _DECISIONS if use_in_memory_repositories() else SqlAlchemyApplicationDecisionRepository(_session(session))


def get_shift_repo(session: Session | None = Depends(get_request_session)) -> ShiftRepository:
    return _SHIFTS if use_in_memory_repositories() else SqlAlchemyShiftRepository(_session(session))


def get_worker_profile_repo(
    session: Session | None = Depends(get_request_session),
) -> WorkerProfileRepository:
    return _WORKERS if use_in_memory_repositories() else SqlAlchemyWorkerProfileRepository(_session(session))


def get_user_repo(session: Session | None = Depends(get_request_session)) -> UserRepository:
    return _USERS if use_in_memory_repositories() else SqlAlchemyUserRepository(_session(session))


def get_template_repo(session: Session | None = Depends(get_request_session)) -> TemplateRepository:
    return _TEMPLATES if use_in_memory_repositories() else SqlAlchemyTemplateRepository(_session(session))


def get_message_repo(session: Session | None = Depends(get_request_session)) -> MessageRepository:
    return _MESSAGES if use_in_memory_repositories() else SqlAlchemyMessageRepository(_session(session))


def get_application_message_history_repo(
    session: Session | None = Depends(get_request_session),
) -> ApplicationMessageHistoryRepository:
    return _MESSAGE_HISTORY if use_in_memory_repositories() else SqlAlchemyApplicationMessageHistoryRepository(_session(session))


def get_worker_feed_state_repo(session: Session | None = Depends(get_request_session)):
    return _FEED_STATES if use_in_memory_repositories() else SqlAlchemyWorkerFeedStateRepository(_session(session))


def get_account_repo(session: Session | None = Depends(get_request_session)) -> AccountRepository:
    return _ACCOUNTS if use_in_memory_repositories() else SqlAlchemyAccountRepository(_session(session))


def get_organisation_repo(
    session: Session | None = Depends(get_request_session),
) -> OrganisationRepository:
    return _ORGANISATIONS if use_in_memory_repositories() else SqlAlchemyOrganisationRepository(_session(session))


def get_market_repo(session: Session | None = Depends(get_request_session)) -> MarketRepository:
    return _MARKETS if use_in_memory_repositories() else SqlAlchemyMarketRepository(_session(session))


def get_worker_feed_query_repo(
    session: Session | None = Depends(get_request_session),
) -> WorkerFeedQueryRepository:
    return _FEED_QUERY if use_in_memory_repositories() else SqlAlchemyWorkerFeedQueryRepository(_session(session))


def get_notification_repo(
    session: Session | None = Depends(get_request_session),
) -> NotificationRepository:
    return _NOTIFICATIONS if use_in_memory_repositories() else SqlAlchemyNotificationRepository(_session(session))


def get_outbox_publisher(
    session: Session | None = Depends(get_request_session),
    notification_repo: NotificationRepository = Depends(get_notification_repo),
) -> OutboxPublisher:
    if use_in_memory_repositories():
        return InMemoryOutboxPublisher(notification_repo, get_email_transport())
    return SqlAlchemyOutboxPublisher(_session(session))


def get_rating_repo(session: Session | None = Depends(get_request_session)) -> RatingRepository:
    if use_in_memory_repositories():
        raise RuntimeError("RatingRepository requires a database-backed request session.")
    return SqlAlchemyRatingRepository(_session(session))


def get_report_repo(session: Session | None = Depends(get_request_session)) -> ReportRepository:
    return _REPORTS if use_in_memory_repositories() else SqlAlchemyReportRepository(_session(session))


def get_partner_code_repo(session: Session | None = Depends(get_request_session)) -> PartnerCodeRepository:
    return _PARTNER_CODES if use_in_memory_repositories() else SqlAlchemyPartnerCodeRepository(_session(session))


def shared_booking_charge_repository() -> InMemoryBookingChargeRepository:
    return _BOOKING_CHARGES


def get_booking_charge_repo(session: Session | None = Depends(get_request_session)) -> BookingChargeRepository:
    if use_in_memory_repositories():
        return _BOOKING_CHARGES
    return SqlAlchemyBookingChargeRepository(_session(session))


def shared_booking_transition_repository() -> InMemoryBookingTransitionRepository:
    return _BOOKING_TRANSITIONS


def get_booking_transition_repo(
    session: Session | None = Depends(get_request_session),
) -> BookingTransitionRepository:
    if use_in_memory_repositories():
        return _BOOKING_TRANSITIONS
    return SqlAlchemyBookingTransitionRepository(_session(session))


def shared_event_repository() -> InMemoryEventRepository:
    return _EVENTS


def get_event_repo(session: Session | None = Depends(get_request_session)) -> EventRepository:
    return _EVENTS if use_in_memory_repositories() else SqlAlchemyEventRepository(_session(session))


def get_rota_publication_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_rota_publication_repository import (
        SqlAlchemyRotaPublicationRepository,
    )

    if use_in_memory_repositories():
        return _ROTA_PUBLICATIONS
    return SqlAlchemyRotaPublicationRepository(_session(session))


def get_booking_allocator(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
    from apps.api.src.repositories.sqlalchemy_booking_allocator import SqlAlchemyBookingAllocator

    if use_in_memory_repositories():
        return InMemoryBookingAllocator(_BOOKINGS, _SHIFTS)
    return SqlAlchemyBookingAllocator(_session(session))


def get_booking_charge_adjustment_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_booking_charge_adjustment_repository import (
        SqlAlchemyBookingChargeAdjustmentRepository,
    )

    if use_in_memory_repositories():
        return _CHARGE_ADJUSTMENTS
    return SqlAlchemyBookingChargeAdjustmentRepository(_session(session))


def get_shift_offer_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_shift_offer_repository import (
        SqlAlchemyShiftOfferRepository,
    )

    if use_in_memory_repositories():
        return _SHIFT_OFFERS
    return SqlAlchemyShiftOfferRepository(_session(session))


def get_shift_change_request_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_shift_change_request_repository import (
        SqlAlchemyShiftChangeRequestRepository,
    )

    if use_in_memory_repositories():
        return _SHIFT_CHANGES
    return SqlAlchemyShiftChangeRequestRepository(_session(session))


def get_shift_change_transition_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_shift_change_request_repository import (
        SqlAlchemyShiftChangeTransitionRepository,
    )

    if use_in_memory_repositories():
        return _SHIFT_CHANGE_TRANSITIONS
    return SqlAlchemyShiftChangeTransitionRepository(_session(session))


def get_worker_certification_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_worker_certification_repository import (
        SqlAlchemyWorkerCertificationRepository,
    )

    if use_in_memory_repositories():
        return _WORKER_CERTIFICATIONS
    return SqlAlchemyWorkerCertificationRepository(_session(session))


from apps.api.src.repositories.in_memory_auto_accept_repository import (
    InMemoryAutoAcceptAttemptRepository as _AutoAcceptAttemptRepo,
    InMemoryWorkerAutoAcceptRuleRepository as _AutoAcceptRuleRepo,
)

_AUTO_ACCEPT_RULES = _AutoAcceptRuleRepo()
_AUTO_ACCEPT_ATTEMPTS = _AutoAcceptAttemptRepo(_SHIFT_OFFERS)


def shared_auto_accept_rule_repository():
    return _AUTO_ACCEPT_RULES


def shared_auto_accept_attempt_repository():
    return _AUTO_ACCEPT_ATTEMPTS


def get_auto_accept_rule_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_auto_accept_repository import (
        SqlAlchemyWorkerAutoAcceptRuleRepository,
    )

    if use_in_memory_repositories():
        return _AUTO_ACCEPT_RULES
    return SqlAlchemyWorkerAutoAcceptRuleRepository(_session(session))


def get_auto_accept_attempt_repo(session: Session | None = Depends(get_request_session)):
    from apps.api.src.repositories.sqlalchemy_auto_accept_repository import (
        SqlAlchemyAutoAcceptAttemptRepository,
    )

    if use_in_memory_repositories():
        return _AUTO_ACCEPT_ATTEMPTS
    return SqlAlchemyAutoAcceptAttemptRepository(_session(session))

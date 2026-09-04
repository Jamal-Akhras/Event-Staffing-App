from __future__ import annotations

from fastapi import Depends

from apps.api.src.repositories.application_decision_repository import ApplicationDecisionRepository
from apps.api.src.repositories.application_message_history_repository import ApplicationMessageHistoryRepository
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.message_thread_repository import MessageThreadRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.template_repository import TemplateRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_feed_query_repository import WorkerFeedQueryRepository
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_booking_allocator,
    get_booking_charge_adjustment_repo,
    get_commercial_agreement_repo,
    get_consent_repo,
    get_manager_invitation_repo,
    get_shift_boost_repo,
    get_subscription_charge_repo,
    get_shift_change_request_repo,
    get_shift_change_transition_repo,
    get_worker_certification_repo,
    get_shift_offer_repo,
    get_rota_publication_repo,
    get_application_decision_repo,
    get_application_message_history_repo,
    get_application_repo,
    get_booking_repo,
    get_booking_charge_repo,
    get_booking_transition_repo,
    get_event_repo,
    get_message_repo,
    get_message_thread_repo,
    get_market_repo,
    get_notification_repo,
    get_outbox_publisher,
    get_organisation_repo,
    get_partner_code_repo,
    get_rating_repo,
    get_report_repo,
    get_request_session,
    get_request_unit_of_work,
    get_shift_repo,
    get_template_repo,
    get_user_repo,
    get_worker_feed_state_repo,
    get_worker_feed_query_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies_workforce import (
    get_relationship_transition_repo,
    get_venue_join_code_repo,
    get_worker_relationship_repo,
)
from apps.api.src.repository_dependencies_availability import (
    get_availability_exception_repo,
    get_availability_rule_repo,
    get_time_off_repo,
)
from apps.api.src.config import get_platform_fee_percent
from apps.api.src.repositories.partner_code_repository import PartnerCodeRepository
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.event_repository import EventRepository
from apps.api.src.repositories.worker_relationship_repository import (
    RelationshipTransitionRepository,
    WorkerRelationshipRepository,
)
from apps.api.src.repositories.venue_join_code_repository import VenueJoinCodeRepository
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.services.join_code_service import JoinCodeService
from apps.api.src.services.people_service import PeopleService
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.rota_service import RotaService
from apps.api.src.services.availability_gate import AvailabilityGate
from apps.api.src.services.organisation_service import OrganisationService
from apps.api.src.services.certification_gate import CertificationGate
from apps.api.src.services.availability_service import AvailabilityService
from apps.api.src.services.shift_change_service import ShiftChangeService
from apps.api.src.services.shift_offer_service import ShiftOfferService
from apps.api.src.services.rota_revisions import RotaRevisionService
from apps.api.src.services.timesheet_service import TimesheetService
from apps.api.src.services.relationship_service import RelationshipService
from apps.api.src.services.billing_service import BillingService
from apps.api.src.services.charge_recorder import ChargeRecorder
from apps.api.src.services.venue_analytics_service import VenueAnalyticsService
from apps.api.src.services.venue_insights_service import VenueInsightsService
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.message_service import MessageService
from apps.api.src.services.shift_service import ShiftService
from apps.api.src.services.shift_lifecycle_service import ShiftLifecycleService
from apps.api.src.services.template_service import TemplateService
from apps.api.src.services.worker_feed_service import WorkerFeedService
from apps.api.src.services.worker_shift_feed_service import WorkerShiftFeedService
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.idempotency import IdempotencyService
from apps.api.src.repositories.booking_charge_adjustment_repository import BookingChargeAdjustmentRepository

__all__ = [
    "get_account_repo",
    "get_application_decision_repo",
    "get_application_message_history_repo",
    "get_application_repo",
    "get_application_service",
    "get_billing_service",
    "get_booking_lifecycle_service",
    "get_booking_repo",
    "get_booking_charge_repo",
    "get_booking_transition_repo",
    "get_event_repo",
    "get_event_recorder",
    "get_message_repo",
    "get_message_thread_repo",
    "get_message_service",
    "get_idempotency_service",
    "get_market_repo",
    "get_notification_repo",
    "get_outbox_publisher",
    "get_organisation_repo",
    "get_rating_repo",
    "get_report_repo",
    "get_request_session",
    "get_request_unit_of_work",
    "get_shift_repo",
    "get_shift_service",
    "get_shift_lifecycle_service",
    "get_template_repo",
    "get_template_service",
    "get_user_repo",
    "get_worker_feed_service",
    "get_worker_feed_query_repo",
    "get_worker_shift_feed_service",
    "get_worker_feed_state_repo",
    "get_worker_profile_repo",
    "get_availability_exception_repo",
    "get_availability_rule_repo",
    "get_time_off_repo",
]


def get_event_recorder(repo: EventRepository = Depends(get_event_repo)) -> EventRecorder:
    return EventRecorder(repo)


def get_shift_service(repo: ShiftRepository = Depends(get_shift_repo)) -> ShiftService:
    return ShiftService(repo)


def get_billing_service(
    booking_repo: BookingRepository = Depends(get_booking_repo),
    charge_repo: BookingChargeRepository = Depends(get_booking_charge_repo),
    adjustment_repo: BookingChargeAdjustmentRepository = Depends(get_booking_charge_adjustment_repo),
    partner_code_repo: PartnerCodeRepository = Depends(get_partner_code_repo),
    subscription_repo=Depends(get_subscription_charge_repo),
    boost_repo=Depends(get_shift_boost_repo),
    organisation_repo=Depends(get_organisation_repo),
    agreement_repo=Depends(get_commercial_agreement_repo),
) -> BillingService:
    return BillingService(
        booking_repo, charge_repo, adjustment_repo, partner_code_repo, get_platform_fee_percent(),
        subscription_repo, boost_repo, organisation_repo, agreement_repo,
    )


def get_charge_recorder(
    charge_repo: BookingChargeRepository = Depends(get_booking_charge_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    partner_code_repo: PartnerCodeRepository = Depends(get_partner_code_repo),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    relationship_transition_repo: RelationshipTransitionRepository = Depends(get_relationship_transition_repo),
    organisation_repo=Depends(get_organisation_repo),
    agreement_repo=Depends(get_commercial_agreement_repo),
) -> ChargeRecorder:
    return ChargeRecorder(
        charge_repo,
        shift_repo,
        worker_repo,
        partner_code_repo,
        get_platform_fee_percent(),
        relationship_repo,
        relationship_transition_repo,
        organisation_repo,
        agreement_repo,
    )


def get_relationship_service(
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    transition_repo: RelationshipTransitionRepository = Depends(get_relationship_transition_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
) -> RelationshipService:
    return RelationshipService(relationship_repo, transition_repo, worker_repo)


def get_certification_gate(
    certification_repo=Depends(get_worker_certification_repo),
) -> CertificationGate:
    return CertificationGate(certification_repo)


def get_availability_service(
    rule_repo=Depends(get_availability_rule_repo),
    exception_repo=Depends(get_availability_exception_repo),
    time_off_repo=Depends(get_time_off_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
) -> AvailabilityService:
    return AvailabilityService(rule_repo, exception_repo, time_off_repo, booking_repo)


def get_availability_gate(
    time_off_repo=Depends(get_time_off_repo),
) -> AvailabilityGate:
    return AvailabilityGate(time_off_repo)


def get_people_service(
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    charge_repo: BookingChargeRepository = Depends(get_booking_charge_repo),
    availability: AvailabilityService = Depends(get_availability_service),
) -> PeopleService:
    return PeopleService(relationship_repo, worker_repo, charge_repo, availability)


def get_escalation_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    offer_repo=Depends(get_shift_offer_repo),
) -> EscalationService:
    return EscalationService(shift_repo, relationship_repo, account_repo, outbox, offers=offer_repo)


def get_join_code_service(
    code_repo: VenueJoinCodeRepository = Depends(get_venue_join_code_repo),
    relationships: RelationshipService = Depends(get_relationship_service),
    account_repo: AccountRepository = Depends(get_account_repo),
) -> JoinCodeService:
    return JoinCodeService(code_repo, relationships, account_repo)


def get_idempotency_service(
    session=Depends(get_request_session),
) -> IdempotencyService:
    return IdempotencyService(session)


def get_shift_lifecycle_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> ShiftLifecycleService:
    return ShiftLifecycleService(shift_repo, application_repo, booking_repo, outbox)


def get_application_service(
    application_repo: ApplicationRepository = Depends(get_application_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    decision_repo: ApplicationDecisionRepository = Depends(get_application_decision_repo),
    history_repo: ApplicationMessageHistoryRepository = Depends(get_application_message_history_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    certifications: CertificationGate = Depends(get_certification_gate),
) -> ApplicationService:
    return ApplicationService(
        application_repo, shift_repo, decision_repo, history_repo, outbox, relationship_repo,
        certifications,
    )


def get_booking_lifecycle_service(
    booking_repo: BookingRepository = Depends(get_booking_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    escalations: EscalationService = Depends(get_escalation_service),
) -> BookingLifecycleService:
    return BookingLifecycleService(booking_repo, worker_repo, shift_repo, outbox, transitions, escalations)


def get_venue_insights_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
) -> VenueInsightsService:
    return VenueInsightsService(shift_repo, booking_repo, application_repo)


def get_venue_analytics_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
) -> VenueAnalyticsService:
    return VenueAnalyticsService(shift_repo, booking_repo, application_repo)


def get_template_service(
    template_repo: TemplateRepository = Depends(get_template_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    escalations: EscalationService = Depends(get_escalation_service),
) -> TemplateService:
    return TemplateService(template_repo, shift_repo, escalations)


def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repo),
    thread_repo: MessageThreadRepository = Depends(get_message_thread_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    organisation_repo=Depends(get_organisation_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> MessageService:
    return MessageService(
        message_repo,
        thread_repo,
        shift_repo,
        application_repo,
        booking_repo,
        relationship_repo,
        organisation_repo,
        outbox,
    )


def get_worker_feed_service(
    repo=Depends(get_worker_feed_state_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> WorkerFeedService:
    return WorkerFeedService(repo, shift_repo)


def get_worker_shift_feed_service(
    profile_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    query_repo: WorkerFeedQueryRepository = Depends(get_worker_feed_query_repo),
) -> WorkerShiftFeedService:
    return WorkerShiftFeedService(profile_repo, market_repo, query_repo)


def get_shift_offer_service(
    offer_repo=Depends(get_shift_offer_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    allocator=Depends(get_booking_allocator),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    escalations: EscalationService = Depends(get_escalation_service),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    certifications: CertificationGate = Depends(get_certification_gate),
    organisation_repo=Depends(get_organisation_repo),
) -> ShiftOfferService:
    return ShiftOfferService(
        offer_repo,
        shift_repo,
        allocator,
        relationship_repo,
        transitions,
        escalations,
        outbox,
        certifications,
        organisation_repo,
    )


def get_rota_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
    publications=Depends(get_rota_publication_repo),
    allocator=Depends(get_booking_allocator),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    lifecycle: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    escalations: EscalationService = Depends(get_escalation_service),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    account_repo: AccountRepository = Depends(get_account_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    offers: ShiftOfferService = Depends(get_shift_offer_service),
    gate: AvailabilityGate = Depends(get_availability_gate),
    certifications: CertificationGate = Depends(get_certification_gate),
    organisation_repo=Depends(get_organisation_repo),
) -> RotaService:
    return RotaService(
        shift_repo,
        booking_repo,
        application_repo,
        allocator,
        publications,
        relationship_repo,
        transitions,
        lifecycle,
        escalations,
        outbox,
        account_repo,
        market_repo,
        offers,
        gate,
        certifications,
        organisation_repo,
    )


def get_timesheet_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    charge_repo: BookingChargeRepository = Depends(get_booking_charge_repo),
    adjustment_repo=Depends(get_booking_charge_adjustment_repo),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
) -> TimesheetService:
    return TimesheetService(
        shift_repo,
        booking_repo,
        worker_repo,
        relationship_repo,
        charge_repo,
        adjustment_repo,
        transitions,
        account_repo,
        market_repo,
    )


def get_shift_change_service(
    request_repo=Depends(get_shift_change_request_repo),
    change_transition_repo=Depends(get_shift_change_transition_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    allocator=Depends(get_booking_allocator),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    lifecycle: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    escalations: EscalationService = Depends(get_escalation_service),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    publications=Depends(get_rota_publication_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    gate: AvailabilityGate = Depends(get_availability_gate),
    certifications: CertificationGate = Depends(get_certification_gate),
) -> ShiftChangeService:
    return ShiftChangeService(
        request_repo,
        change_transition_repo,
        shift_repo,
        booking_repo,
        allocator,
        relationship_repo,
        transitions,
        lifecycle,
        escalations,
        outbox,
        RotaRevisionService(shift_repo, booking_repo, publications, outbox, account_repo, market_repo),
        gate,
        certifications,
    )


def get_organisation_service(
    organisation_repo=Depends(get_organisation_repo),
    invitation_repo=Depends(get_manager_invitation_repo),
    user_repo=Depends(get_user_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> OrganisationService:
    return OrganisationService(
        organisation_repo, invitation_repo, user_repo, market_repo, outbox
    )


def get_commercial_service(
    agreement_repo=Depends(get_commercial_agreement_repo),
    subscription_repo=Depends(get_subscription_charge_repo),
    boost_repo=Depends(get_shift_boost_repo),
    organisation_repo=Depends(get_organisation_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> "CommercialService":
    from apps.api.src.services.commercial_service import CommercialService

    return CommercialService(
        agreement_repo, subscription_repo, boost_repo, organisation_repo, shift_repo
    )


def get_consent_service(
    consent_repo=Depends(get_consent_repo),
) -> "ConsentService":
    from apps.api.src.services.consent_service import ConsentService

    return ConsentService(consent_repo)

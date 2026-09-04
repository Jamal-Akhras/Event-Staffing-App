from __future__ import annotations

from typing import Any, Callable

from apps.api.src import repository_dependencies as rd
from apps.api.src import repository_dependencies_workforce as rdw
from apps.api.src import repository_dependencies_availability as rda
from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
from apps.api.src.services.email import LoggingEmailTransport
from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher


def in_memory_repositories() -> dict[Callable[..., Any], Any]:
    return {
        rd.get_booking_repo: rd._BOOKINGS,
        rd.get_application_repo: rd._APPLICATIONS,
        rd.get_application_decision_repo: rd._DECISIONS,
        rd.get_shift_repo: rd._SHIFTS,
        rd.get_worker_profile_repo: rd._WORKERS,
        rd.get_user_repo: rd._USERS,
        rd.get_template_repo: rd._TEMPLATES,
        rd.get_message_repo: rd._MESSAGES,
        rd.get_application_message_history_repo: rd._MESSAGE_HISTORY,
        rd.get_worker_feed_state_repo: rd._FEED_STATES,
        rd.get_account_repo: rd._ACCOUNTS,
        rd.get_organisation_repo: rd._ORGANISATIONS,
        rd.get_market_repo: rd._MARKETS,
        rd.get_worker_feed_query_repo: rd._FEED_QUERY,
        rd.get_notification_repo: rd._NOTIFICATIONS,
        rd.get_report_repo: rd._REPORTS,
        rd.get_partner_code_repo: rd._PARTNER_CODES,
        rd.get_event_repo: rd._EVENTS,
        rd.get_booking_charge_repo: rd._BOOKING_CHARGES,
        rd.get_booking_transition_repo: rd._BOOKING_TRANSITIONS,
        rdw.get_worker_relationship_repo: rdw._RELATIONSHIPS,
        rdw.get_relationship_transition_repo: rdw._RELATIONSHIP_TRANSITIONS,
        rdw.get_venue_join_code_repo: rdw._JOIN_CODES,
        rd.get_rota_publication_repo: rd._ROTA_PUBLICATIONS,
        rd.get_booking_allocator: InMemoryBookingAllocator(rd._BOOKINGS, rd._SHIFTS),
        rd.get_outbox_publisher: InMemoryOutboxPublisher(rd._NOTIFICATIONS, LoggingEmailTransport()),
        rd.get_booking_charge_adjustment_repo: rd._CHARGE_ADJUSTMENTS,
        rd.get_shift_offer_repo: rd._SHIFT_OFFERS,
        rd.get_shift_change_request_repo: rd._SHIFT_CHANGES,
        rd.get_shift_change_transition_repo: rd._SHIFT_CHANGE_TRANSITIONS,
        rd.get_worker_certification_repo: rd._WORKER_CERTIFICATIONS,
        rd.get_manager_invitation_repo: rd._MANAGER_INVITATIONS,
        rd.get_commercial_agreement_repo: rd._COMMERCIAL_AGREEMENTS,
        rd.get_subscription_charge_repo: rd._SUBSCRIPTION_CHARGES,
        rd.get_shift_boost_repo: rd._SHIFT_BOOSTS,
        rd.get_auto_accept_rule_repo: rd._AUTO_ACCEPT_RULES,
        rd.get_auto_accept_attempt_repo: rd._AUTO_ACCEPT_ATTEMPTS,
        rd.get_message_thread_repo: rd._MESSAGE_THREADS,
        rda.get_availability_rule_repo: rda._AVAILABILITY_RULES,
        rda.get_availability_exception_repo: rda._AVAILABILITY_EXCEPTIONS,
        rda.get_time_off_repo: rda._TIME_OFF,
    }


def _provide(repository: Any) -> Callable[[], Any]:
    def provider() -> Any:
        return repository

    return provider


def install_in_memory_repositories(app: Any) -> dict[Callable[..., Any], Any]:
    repositories = in_memory_repositories()
    for provider, repository in repositories.items():
        app.dependency_overrides.setdefault(provider, _provide(repository))
    return repositories


def clear_in_memory_repositories() -> None:
    for repository in in_memory_repositories().values():
        clear = getattr(repository, "clear", None)
        if clear is not None:
            clear()

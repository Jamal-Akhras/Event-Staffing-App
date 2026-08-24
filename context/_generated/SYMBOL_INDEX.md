# Symbol Index

Generated: 2026-08-24 22:44:35
Python files: 259

## apps/api/alembic/env.py (62 lines)
  L26 def _database_url
  L30 def run_migrations_offline
  L43 def run_migrations_online

## apps/api/alembic/versions/001_create_bookings.py (38 lines)
  L14 def upgrade
  L35 def downgrade

## apps/api/alembic/versions/002_create_core_tables.py (66 lines)
  L12 def upgrade
  L63 def downgrade

## apps/api/alembic/versions/003_create_users_table.py (29 lines)
  L12 def upgrade
  L27 def downgrade

## apps/api/alembic/versions/004_add_workers_needed_to_shifts.py (20 lines)
  L12 def upgrade
  L18 def downgrade

## apps/api/alembic/versions/005_add_shift_templates.py (50 lines)
  L12 def upgrade
  L48 def downgrade

## apps/api/alembic/versions/006_add_messages.py (38 lines)
  L12 def upgrade
  L34 def downgrade

## apps/api/alembic/versions/007_add_application_message_history.py (29 lines)
  L12 def upgrade
  L27 def downgrade

## apps/api/alembic/versions/008_add_integrity_constraints.py (170 lines)
  L11 def upgrade
  L122 def downgrade

## apps/api/alembic/versions/009_add_worker_feed_state.py (31 lines)
  L12 def upgrade
  L28 def downgrade

## apps/api/alembic/versions/010_add_accounts.py (106 lines)
  L18 def _has_column
  L22 def _has_index
  L26 def _add_account_link
  L60 def _drop_account_link
  L82 def upgrade
  L101 def downgrade

## apps/api/alembic/versions/011_add_shift_currency.py (31 lines)
  L18 def _has_column
  L22 def upgrade
  L28 def downgrade

## apps/api/alembic/versions/012_add_media_fields.py (48 lines)
  L18 def _has_column
  L22 def upgrade
  L40 def downgrade

## apps/api/alembic/versions/013_add_notifications.py (48 lines)
  L18 def _has_table
  L22 def _has_index
  L26 def upgrade
  L44 def downgrade

## apps/api/alembic/versions/014_add_ratings.py (49 lines)
  L18 def _has_table
  L22 def upgrade
  L45 def downgrade

## apps/api/alembic/versions/015_add_worker_recontact.py (34 lines)
  L18 def _has_column
  L22 def upgrade
  L31 def downgrade

## apps/api/alembic/versions/016_add_shift_coordinates.py (35 lines)
  L18 def _has_column
  L22 def upgrade
  L30 def downgrade

## apps/api/alembic/versions/017_add_password_changed_at.py (31 lines)
  L18 def _has_column
  L22 def upgrade
  L28 def downgrade

## apps/api/alembic/versions/018_add_account_notification_preferences.py (31 lines)
  L18 def _has_column
  L22 def upgrade
  L28 def downgrade

## apps/api/alembic/versions/019_add_email_verification.py (47 lines)
  L18 def _has_column
  L22 def upgrade
  L41 def downgrade

## apps/api/alembic/versions/020_time_money_deletion_integrity.py (198 lines)
  L45 def upgrade
  L55 def downgrade
  L65 def _upgrade_postgresql_types
  L83 def _downgrade_postgresql_types
  L101 def _replace_shift_foreign_keys
  L105 def _restore_shift_foreign_keys
  L109 def _set_shift_foreign_keys
  L126 def _upgrade_sqlite_types_and_foreign_keys
  L136 def _downgrade_sqlite_types_and_foreign_keys
  L146 def _batch_set_shift_foreign_keys
  L163 def _add_notification_shift_foreign_key
  L192 def _drop_notification_shift_foreign_key

## apps/api/alembic/versions/021_organisation_venue_separation.py (192 lines)
  L18 def upgrade
  L27 def downgrade
  L37 def _create_organisation_tables
  L64 def _copy_accounts_to_venues
  L83 def _create_memberships
  L112 def _create_accounts_table
  L124 def _copy_venues_to_accounts
  L135 def _venue_detail_columns
  L147 def _replace_link

## apps/api/alembic/versions/022_markets_and_worker_feed_indexes.py (108 lines)
  L17 def upgrade
  L52 def downgrade
  L59 def _add_market_link
  L83 def _drop_market_link
  L95 def _backfill_bath

## apps/api/alembic/versions/023_secure_rating_identity.py (47 lines)
  L12 def upgrade
  L39 def downgrade

## apps/api/alembic/versions/024_operational_recovery.py (108 lines)
  L12 def upgrade
  L62 def downgrade

## apps/api/alembic/versions/025_transactional_outbox.py (180 lines)
  L12 def upgrade
  L151 def downgrade

## apps/api/alembic/versions/026_auth_session_version.py (36 lines)
  L12 def upgrade
  L28 def downgrade

## apps/api/alembic/versions/027_account_privacy_and_reports.py (54 lines)
  L12 def upgrade
  L48 def downgrade

## apps/api/alembic/versions/028_direct_payment_attestation.py (46 lines)
  L12 def upgrade
  L34 def downgrade

## apps/api/alembic/versions/029_idempotency_records.py (31 lines)
  L12 def upgrade
  L29 def downgrade

## apps/api/scripts/create_dev_accounts.py (112 lines)
  L41 def main

## apps/api/scripts/create_operator.py (133 lines)
  L29 def create_operator
  L99 def main

## apps/api/scripts/prepare_demo_accounts.py (174 lines)
  L27 def prepare_demo_accounts
  L129 def _upsert_user
  L156 def main

## apps/api/scripts/seed_demo_data.py (251 lines)
  L54 def main
  L72 def delete_demo_data
  L100 def seed_workers
  L128 def seed_shifts
  L154 def seed_applications
  L183 def seed_bookings
  L212 def seed_templates
  L232 def seed_messages
  L242 def next_saturday

## apps/api/scripts/smoke.py (142 lines)
  L22 def call
  L40 def _decode
  L49 def probe
  L59 def main

## apps/api/src/api_errors.py (78 lines)
  L22 def error_content
  L37 async def http_exception_handler
  L46 async def validation_exception_handler
  L70 async def rate_limit_exception_handler

## apps/api/src/auth.py (25 lines)
  L8 class ActorRole (str, Enum)
  L14 def get_actor_role
  L23 def require_role

## apps/api/src/auth/dependencies.py (259 lines)
  L21 class ActorRole (str, Enum)
  L30 class ActorContext
  L39   def venue_id
  L43 async def get_current_user
  L79 async def get_actor_role
  L131 async def get_actor_context
  L200 def _require_current_session
  L206 def require_verified_actor
  L216 def require_role
  L233 def require_worker_owner
  L240 def require_operator_owner
  L246 def extract_user_id_from_token

## apps/api/src/auth/jwt.py (104 lines)
  L21 class ResetTokenClaims
  L26 def create_access_token
  L45 def decode_access_token
  L64 def revoke_access_token
  L86 def create_reset_token
  L93 def decode_reset_token

## apps/api/src/auth/password.py (30 lines)
  L8 def hash_password
  L20 def verify_password

## apps/api/src/auth/schemas.py (97 lines)
  L8 class UserRegisterRequest (BaseModel)
  L15 class OperatorRegisterRequest (BaseModel)
  L25 class UserLoginRequest (BaseModel)
  L32 class TokenResponse (BaseModel)
  L48 class LogoutResponse (BaseModel)
  L52 class VerifyEmailRequest (BaseModel)
  L56 class ResendVerificationRequest (BaseModel)
  L60 class EmailVerificationResponse (BaseModel)
  L65 class SessionResponse (BaseModel)
  L75 class UserResponse (BaseModel)
  L86 class ForgotPasswordRequest (BaseModel)
  L90 class ResetPasswordRequest (BaseModel)
  L95 class PasswordResetResponse (BaseModel)

## apps/api/src/auth/token_denylist.py (78 lines)
  L22 class TokenDenylist (Protocol)
  L23   def revoke
  L27   def is_revoked
  L31 class InMemoryTokenDenylist
  L32   def __init__
  L35   def revoke
  L40   def is_revoked
  L49   def clear
  L53 class RedisTokenDenylist
  L54   def __init__
  L59   def revoke
  L64   def is_revoked
  L68 def _build_denylist
  L77 def get_token_denylist

## apps/api/src/config.py (177 lines)
  L17 def get_env
  L21 def get_database_url
  L37 def normalize_database_url
  L45 def resolve_sqlite_file_url
  L57 def get_bool_env
  L64 def get_cors_origins
  L87 def get_environment
  L91 def is_development
  L95 def get_web_base_url
  L105 def use_in_memory_repositories
  L119 def use_in_memory_backends
  L136 def get_redis_url
  L157 def trust_forwarded_for
  L167 def ensure_safe_startup_config

## apps/api/src/datetime_utils.py (13 lines)
  L6 def utc_now
  L10 def normalize_utc

## apps/api/src/db/database.py (25 lines)
  L17   def _enable_sqlite_foreign_keys

## apps/api/src/db/idempotency_models.py (23 lines)
  L9 class IdempotencyRecordModel (Base)

## apps/api/src/db/models.py (299 lines)
  L35 class BookingModel (Base)
  L65 class ShiftModel (Base)
  L103 class ApplicationModel (Base)
  L129 class WorkerProfileModel (Base)
  L161 class UserModel (Base)
  L182 class ShiftTemplateModel (Base)
  L205 class RecurringScheduleModel (Base)
  L234 class MessageModel (Base)
  L259 class ApplicationMessageHistoryModel (Base)
  L273 class RatingModel (Base)
  L289 class WorkerFeedStateModel (Base)

## apps/api/src/db/notification_models.py (100 lines)
  L9 class NotificationModel (Base)
  L30 class OutboxEventModel (Base)
  L52 class NotificationDeliveryModel (Base)
  L76 class UserNotificationPreferenceModel (Base)
  L85 class PushTokenModel (Base)

## apps/api/src/db/schema_guard.py (22 lines)
  L10 def ensure_schema_current

## apps/api/src/db/tenancy_models.py (84 lines)
  L10 class MarketModel (Base)
  L26 class OrganisationModel (Base)
  L36 class VenueModel (Base)
  L66 class OrganisationMembershipModel (Base)

## apps/api/src/db/trust_models.py (40 lines)
  L9 class ReportModel (Base)

## apps/api/src/db/types.py (23 lines)
  L12 class UtcDateTime (TypeDecorator[datetime])
  L16   def load_dialect_impl
  L19   def process_bind_param
  L22   def process_result_value

## apps/api/src/deps.py (148 lines)
  L81 def get_shift_service
  L85 def get_idempotency_service
  L91 def get_shift_lifecycle_service
  L100 def get_application_service
  L110 def get_booking_lifecycle_service
  L119 def get_template_service
  L126 def get_message_service
  L136 def get_worker_feed_service
  L143 def get_worker_shift_feed_service

## apps/api/src/helpers.py (74 lines)
  L22 def _now
  L26 def _now_or
  L30 def _get_worker_profile
  L37 def _save_worker_profile
  L41 def _booking_view
  L50 def _shift_view
  L55 def _application_view
  L60 def _worker_public_view
  L71 def _worker_private_view

## apps/api/src/jobs/run_no_show_sweep.py (45 lines)
  L21 def run

## apps/api/src/jobs/run_outbox_dispatch.py (24 lines)
  L15 def run_outbox_dispatch

## apps/api/src/main.py (125 lines)
  L37 async def lifespan
  L60 async def unhandled_exception_handler
  L115 def health
  L120 def ready

## apps/api/src/models/account.py (33 lines)
  L15 class Account
  L32   def venue_id

## apps/api/src/models/application.py (21 lines)
  L8 class Application

## apps/api/src/models/application_message_history.py (12 lines)
  L8 class ApplicationMessageHistory

## apps/api/src/models/message.py (18 lines)
  L7 class Message (BaseModel)

## apps/api/src/models/notification.py (20 lines)
  L8 class Notification

## apps/api/src/models/organisation.py (64 lines)
  L14 class OrganisationRole (str, Enum)
  L21 class Market
  L33 class Organisation
  L42 class Venue
  L60 class OrganisationMembership

## apps/api/src/models/rating.py (15 lines)
  L8 class Rating

## apps/api/src/models/report.py (19 lines)
  L8 class Report

## apps/api/src/models/shift.py (30 lines)
  L9 class Shift

## apps/api/src/models/shift_template.py (38 lines)
  L8 class ShiftTemplate (BaseModel)
  L25 class RecurringSchedule (BaseModel)

## apps/api/src/models/user.py (25 lines)
  L8 class User

## apps/api/src/models/worker_feed_query.py (35 lines)
  L12 class FeedPosition
  L18 class WorkerFeedQuery
  L33 class WorkerFeedItem

## apps/api/src/models/worker_feed_state.py (15 lines)
  L8 class WorkerFeedState (BaseModel)

## apps/api/src/models/worker_profile.py (28 lines)
  L9 class WorkerProfile

## apps/api/src/money.py (11 lines)
  L10 def money

## apps/api/src/observability.py (31 lines)
  L10 def init_sentry

## apps/api/src/rate_limit.py (66 lines)
  L29 def client_ip
  L39 def actor_or_ip
  L54 def _build_limiter

## apps/api/src/repositories/account_repository.py (13 lines)
  L8 class AccountRepository (ABC)
  L10   def get
  L13   def save

## apps/api/src/repositories/application_decision_repository.py (49 lines)
  L13 class ApplicationApprovalResult
  L19 class ApplicationDecisionError (Exception)
  L23 class ApplicationDecisionNotFoundError (ApplicationDecisionError)
  L27 class ApplicationAlreadyDecidedError (ApplicationDecisionError)
  L31 class ShiftAlreadyFullError (ApplicationDecisionError)
  L35 class ApplicationDecisionConflictError (ApplicationDecisionError)
  L39 class ApplicationDecisionRepository (Protocol)
  L40   def approve
  L48   def reject

## apps/api/src/repositories/application_message_history_repository.py (13 lines)
  L8 class ApplicationMessageHistoryRepository (Protocol)
  L9   def save
  L12   def list_by_application

## apps/api/src/repositories/application_repository.py (61 lines)
  L8 class DuplicateApplicationError (Exception)
  L12 class ApplicationRepository (Protocol)
  L13   def get
  L16   def save
  L19   def list_recent
  L27   def list_by_worker
  L37   def list_by_operator
  L47   def list_for_account
  L57   def find_by_worker_and_shift
  L60   def list_by_shift

## apps/api/src/repositories/booking_repository.py (47 lines)
  L9 class BookingRepository (Protocol)
  L10   def get
  L13   def save
  L16   def list_recent
  L19   def list_by_worker
  L27   def list_by_operator
  L35   def list_for_account
  L43   def list_by_state
  L46   def list_by_shift

## apps/api/src/repositories/in_memory_account_repository.py (21 lines)
  L9 class InMemoryAccountRepository (AccountRepository)
  L10   def __init__
  L13   def get
  L16   def save
  L20   def clear

## apps/api/src/repositories/in_memory_application_decision_repository.py (85 lines)
  L21 class InMemoryApplicationDecisionRepository
  L22   def __init__
  L33   def approve
  L72   def reject
  L79   def _get_applied_application

## apps/api/src/repositories/in_memory_application_message_history_repository.py (23 lines)
  L6 class InMemoryApplicationMessageHistoryRepository
  L7   def __init__
  L10   def save
  L14   def list_by_application
  L22   def clear

## apps/api/src/repositories/in_memory_application_repository.py (119 lines)
  L10 class InMemoryApplicationRepository
  L11   def __init__
  L15   def attach_shift_repo
  L18   def get
  L21   def save
  L28   def list_recent
  L36   def list_by_worker
  L52   def list_by_operator
  L68   def list_for_account
  L89   def find_by_worker_and_shift
  L95   def list_by_shift
  L98   def clear
  L101   def _list

## apps/api/src/repositories/in_memory_booking_repository.py (82 lines)
  L10 class InMemoryBookingRepository
  L11   def __init__
  L15   def attach_shift_repo
  L18   def get
  L21   def save
  L25   def list_recent
  L30   def list_by_worker
  L38   def list_by_operator
  L46   def list_for_account
  L61   def list_by_state
  L64   def list_by_shift
  L67   def clear
  L70   def _list

## apps/api/src/repositories/in_memory_market_repository.py (30 lines)
  L9 class InMemoryMarketRepository
  L10   def __init__
  L23   def get
  L26   def list_active

## apps/api/src/repositories/in_memory_message_repository.py (54 lines)
  L9 class InMemoryMessageRepository
  L10   def __init__
  L13   def get
  L16   def save
  L20   def list_by_shift
  L26   def list_by_application
  L32   def list_by_booking
  L38   def mark_as_read
  L47   def clear
  L51   def _sorted

## apps/api/src/repositories/in_memory_notification_repository.py (64 lines)
  L8 class InMemoryNotificationRepository
  L9   def __init__
  L12   def list_for_worker
  L15   def list_for_recipient
  L30   def unread_count
  L33   def mark_read
  L41   def save
  L45   def mark_all_read
  L48   def mark_all_read_for_recipient
  L57   def clear
  L61 def _mark_read

## apps/api/src/repositories/in_memory_organisation_repository.py (70 lines)
  L9 class InMemoryOrganisationRepository (OrganisationRepository)
  L10   def __init__
  L16   def get_organisation
  L19   def get_venue
  L22   def get_membership
  L25   def list_venues_for_user
  L36   def save_organisation
  L40   def save_venue
  L63   def save_membership
  L67   def clear

## apps/api/src/repositories/in_memory_report_repository.py (26 lines)
  L6 class InMemoryReportRepository
  L7   def __init__
  L10   def get
  L13   def save
  L17   def list_by_reporter
  L21   def list_by_status
  L25   def clear

## apps/api/src/repositories/in_memory_shift_repository.py (43 lines)
  L9 class InMemoryShiftRepository
  L10   def __init__
  L14   def get
  L17   def get_for_update
  L20   def save
  L24   def list_recent
  L29   def list_for_account
  L34   def list_by_worker
  L42   def clear

## apps/api/src/repositories/in_memory_template_repository.py (64 lines)
  L6 class InMemoryTemplateRepository
  L7   def __init__
  L11   def get_template
  L14   def save_template
  L18   def list_templates
  L27   def delete_template
  L33   def get_schedule
  L36   def save_schedule
  L40   def list_schedules
  L49   def list_active_schedules
  L56   def delete_schedule
  L62   def clear

## apps/api/src/repositories/in_memory_user_repository.py (42 lines)
  L8 class InMemoryUserRepository
  L11   def __init__
  L15   def get
  L19   def get_by_email
  L23   def get_by_verification_token
  L30   def save
  L39   def clear

## apps/api/src/repositories/in_memory_worker_feed_query_repository.py (61 lines)
  L12 class InMemoryWorkerFeedQueryRepository
  L13   def __init__
  L25   def list_page

## apps/api/src/repositories/in_memory_worker_feed_state_repository.py (30 lines)
  L6 class InMemoryWorkerFeedStateRepository
  L7   def __init__
  L10   def list_for_worker
  L15   def get
  L18   def save
  L22   def delete
  L29   def clear

## apps/api/src/repositories/in_memory_worker_profile_repository.py (20 lines)
  L8 class InMemoryWorkerProfileRepository
  L9   def __init__
  L12   def get
  L15   def save
  L19   def clear

## apps/api/src/repositories/market_repository.py (13 lines)
  L8 class MarketRepository (Protocol)
  L9   def get
  L12   def list_active

## apps/api/src/repositories/message_repository.py (25 lines)
  L8 class MessageRepository (Protocol)
  L9   def get
  L12   def save
  L15   def list_by_shift
  L18   def list_by_application
  L21   def list_by_booking
  L24   def mark_as_read

## apps/api/src/repositories/notification_repository.py (21 lines)
  L8 class NotificationRepository (Protocol)
  L9   def list_for_worker
  L10   def list_for_recipient
  L17   def unread_count
  L18   def mark_read
  L19   def save
  L20   def mark_all_read
  L21   def mark_all_read_for_recipient

## apps/api/src/repositories/organisation_repository.py (28 lines)
  L8 class OrganisationRepository (ABC)
  L10   def get_organisation
  L13   def get_venue
  L16   def get_membership
  L19   def list_venues_for_user
  L22   def save_organisation
  L25   def save_venue
  L28   def save_membership

## apps/api/src/repositories/rating_repository.py (62 lines)
  L10 class UnratedBooking
  L11   def __init__
  L20 class PendingRating
  L32 class DuplicateRatingError (Exception)
  L36 class RatingRepository (Protocol)
  L37   def save
  L40   def get_by_booking_and_role
  L43   def avg_operator_rating_for_worker
  L47   def avg_worker_rating_for_venue
  L50   def unrated_bookings_for_operator
  L54   def completed_bookings_for_account
  L58   def pending_for_worker
  L61   def pending_for_account

## apps/api/src/repositories/report_repository.py (15 lines)
  L8 class ReportRepository (Protocol)
  L9   def get
  L11   def save
  L13   def list_by_reporter
  L15   def list_by_status

## apps/api/src/repositories/shift_repository.py (25 lines)
  L8 class ShiftRepository (Protocol)
  L9   def get
  L12   def get_for_update
  L15   def save
  L18   def list_recent
  L21   def list_for_account
  L24   def list_by_worker

## apps/api/src/repositories/sqlalchemy_account_repository.py (60 lines)
  L11 class SqlAlchemyAccountRepository (AccountRepository)
  L12   def __init__
  L15   def get
  L19   def save
  L44 def _to_domain

## apps/api/src/repositories/sqlalchemy_application_decision_repository.py (175 lines)
  L24 class SqlAlchemyApplicationDecisionRepository
  L25   def __init__
  L28   def approve
  L75   def reject
  L84   def _load_application_for_update
  L94   def _load_shift_for_update
  L105 def _booking_to_model
  L125 def _booking_to_domain
  L145 def _application_to_domain
  L161 def _shift_to_domain

## apps/api/src/repositories/sqlalchemy_application_message_history_repository.py (40 lines)
  L9 class SqlAlchemyApplicationMessageHistoryRepository
  L10   def __init__
  L13   def save
  L24   def list_by_application
  L34 def _to_domain

## apps/api/src/repositories/sqlalchemy_application_repository.py (166 lines)
  L12 class SqlAlchemyApplicationRepository
  L13   def __init__
  L16   def get
  L22   def save
  L35   def list_recent
  L43   def list_by_worker
  L59   def list_by_operator
  L75   def list_for_account
  L91   def find_by_worker_and_shift
  L104   def list_by_shift
  L111   def _list
  L136 def _to_domain
  L154 def _apply_domain

## apps/api/src/repositories/sqlalchemy_booking_repository.py (144 lines)
  L11 class SqlAlchemyBookingRepository
  L12   def __init__
  L15   def get
  L21   def save
  L30   def list_recent
  L39   def list_by_worker
  L47   def list_by_operator
  L55   def list_for_account
  L63   def list_by_state
  L72   def list_by_shift
  L78   def _list
  L100 def _to_domain
  L125 def _apply_domain

## apps/api/src/repositories/sqlalchemy_market_repository.py (38 lines)
  L11 class SqlAlchemyMarketRepository
  L12   def __init__
  L15   def get
  L19   def list_active
  L28 def _to_domain

## apps/api/src/repositories/sqlalchemy_message_repository.py (91 lines)
  L11 class SqlAlchemyMessageRepository
  L12   def __init__
  L15   def get
  L21   def save
  L30   def list_by_shift
  L40   def list_by_application
  L50   def list_by_booking
  L60   def mark_as_read
  L69 def _to_domain
  L83 def _apply_domain

## apps/api/src/repositories/sqlalchemy_notification_repository.py (119 lines)
  L10 class SqlAlchemyNotificationRepository
  L11   def __init__
  L14   def list_for_worker
  L17   def list_for_recipient
  L45   def unread_count
  L52   def mark_read
  L64   def save
  L84   def mark_all_read
  L87   def mark_all_read_for_recipient
  L97   def _recipient_filter
  L105 def _to_domain

## apps/api/src/repositories/sqlalchemy_organisation_repository.py (132 lines)
  L21 class SqlAlchemyOrganisationRepository (OrganisationRepository)
  L22   def __init__
  L25   def get_organisation
  L29   def get_venue
  L33   def get_membership
  L37   def list_venues_for_user
  L49   def save_organisation
  L61   def save_venue
  L82   def save_membership
  L97 def _organisation
  L107 def _venue
  L126 def _membership

## apps/api/src/repositories/sqlalchemy_rating_repository.py (199 lines)
  L24 class SqlAlchemyRatingRepository
  L25   def __init__
  L28   def save
  L45   def get_by_booking_and_role
  L55   def avg_operator_rating_for_worker
  L69   def avg_worker_rating_for_venue
  L84   def unrated_bookings_for_operator
  L110   def completed_bookings_for_account
  L130   def pending_for_worker
  L158   def pending_for_account
  L186   def _rated_booking_ids
  L190 def _to_domain

## apps/api/src/repositories/sqlalchemy_report_repository.py (48 lines)
  L10 class SqlAlchemyReportRepository
  L11   def __init__
  L14   def get
  L18   def save
  L29   def list_by_reporter
  L39   def list_by_status
  L47 def _to_domain

## apps/api/src/repositories/sqlalchemy_shift_repository.py (116 lines)
  L11 class SqlAlchemyShiftRepository
  L12   def __init__
  L15   def get
  L21   def get_for_update
  L30   def save
  L39   def list_recent
  L48   def list_for_account
  L58   def list_by_worker
  L70 def _to_domain
  L96 def _apply_domain

## apps/api/src/repositories/sqlalchemy_template_repository.py (145 lines)
  L11 class SqlAlchemyTemplateRepository
  L12   def __init__
  L15   def get_template
  L21   def save_template
  L30   def list_templates
  L39   def delete_template
  L47   def get_schedule
  L53   def save_schedule
  L62   def list_schedules
  L71   def list_active_schedules
  L79   def delete_schedule
  L88 def _template_to_domain
  L105 def _apply_template_domain
  L119 def _schedule_to_domain
  L135 def _apply_schedule_domain

## apps/api/src/repositories/sqlalchemy_user_repository.py (91 lines)
  L10 class SqlAlchemyUserRepository
  L13   def __init__
  L16   def get
  L23   def get_by_email
  L31   def get_by_verification_token
  L38   def save
  L49 def _to_domain
  L70 def _apply_domain

## apps/api/src/repositories/sqlalchemy_worker_feed_query_repository.py (84 lines)
  L14 class SqlAlchemyWorkerFeedQueryRepository
  L15   def __init__
  L18   def list_page
  L64 def _passed_exists
  L74 def _application_exists
  L83 def _escape_search

## apps/api/src/repositories/sqlalchemy_worker_feed_state_repository.py (56 lines)
  L10 class SqlAlchemyWorkerFeedStateRepository
  L11   def __init__
  L14   def list_for_worker
  L23   def get
  L29   def save
  L40   def delete
  L49 def _to_domain

## apps/api/src/repositories/sqlalchemy_worker_profile_repository.py (97 lines)
  L11 class SqlAlchemyWorkerProfileRepository
  L12   def __init__
  L15   def get
  L21   def save
  L30   def list_all
  L33   def list_for_account
  L55 def _to_domain
  L79 def _apply_domain

## apps/api/src/repositories/template_repository.py (34 lines)
  L8 class TemplateRepository (Protocol)
  L9   def get_template
  L12   def save_template
  L15   def list_templates
  L18   def delete_template
  L21   def get_schedule
  L24   def save_schedule
  L27   def list_schedules
  L30   def list_active_schedules
  L33   def delete_schedule

## apps/api/src/repositories/user_repository.py (53 lines)
  L8 class UserRepository (Protocol)
  L11   def get
  L22   def get_by_email
  L33   def get_by_verification_token
  L44   def save

## apps/api/src/repositories/worker_feed_query_repository.py (10 lines)
  L8 class WorkerFeedQueryRepository (Protocol)
  L9   def list_page

## apps/api/src/repositories/worker_feed_state_repository.py (19 lines)
  L8 class WorkerFeedStateRepository (Protocol)
  L9   def list_for_worker
  L12   def get
  L15   def save
  L18   def delete

## apps/api/src/repositories/worker_profile_repository.py (19 lines)
  L8 class WorkerProfileRepository (Protocol)
  L9   def get
  L12   def save
  L15   def list_all
  L18   def list_for_account

## apps/api/src/repository_dependencies.py (208 lines)
  L92 def _use_in_memory
  L96 def get_request_unit_of_work
  L108 def get_request_session
  L114 def _session
  L120 def get_booking_repo
  L124 def get_application_repo
  L128 def get_application_decision_repo
  L134 def get_shift_repo
  L138 def get_worker_profile_repo
  L144 def get_user_repo
  L148 def get_template_repo
  L152 def get_message_repo
  L156 def get_application_message_history_repo
  L162 def get_worker_feed_state_repo
  L166 def get_account_repo
  L170 def get_organisation_repo
  L176 def get_market_repo
  L180 def get_worker_feed_query_repo
  L186 def get_notification_repo
  L192 def get_outbox_publisher
  L201 def get_rating_repo
  L207 def get_report_repo

## apps/api/src/request_middleware.py (52 lines)
  L19 class RequestContextMiddleware (BaseHTTPMiddleware)
  L20   async def dispatch

## apps/api/src/routes/accounts.py (112 lines)
  L23 def _account_view
  L43 def _get_account
  L50 @GET /accounts/me
  L51 @GET /venues/me
  L52 def get_my_account
  L62 @PUT /accounts/me
  L63 @PUT /venues/me
  L64 def update_my_account

## apps/api/src/routes/applications.py (193 lines)
  L36 @POST /applications
  L38 def create_application
  L74 @GET /applications
  L75 def list_applications
  L95 @POST /applications/{application_id}/approve
  L96 def approve_application
  L111 @POST /applications/{application_id}/reject
  L112 def reject_application
  L127 @POST /applications/{application_id}/withdraw
  L128 def withdraw_application
  L143 @PUT /applications/{application_id}/message
  L144 def update_application_message
  L157 @GET /applications/{application_id}/message-history
  L158 def get_application_message_history
  L179 def _require_application_access

## apps/api/src/routes/auth.py (300 lines)
  L49 @POST /register
  L51 def register
  L133 @POST /register/operator
  L135 def register_operator
  L236 @POST /login
  L238 def login
  L290 @GET /me
  L291 def me

## apps/api/src/routes/auth_account.py (174 lines)
  L50 @POST /logout
  L51 def logout
  L60 @POST /logout-all
  L61 def logout_all
  L78 @POST /account-export
  L80 def export_account
  L98 @DELETE /account
  L100 def delete_account
  L125 @POST /verify-email
  L126 def verify_email
  L143 @POST /resend-verification
  L145 def resend_verification

## apps/api/src/routes/auth_password.py (78 lines)
  L26 @POST /forgot-password
  L28 def forgot_password
  L52 @POST /reset-password
  L54 def reset_password

## apps/api/src/routes/bookings.py (205 lines)
  L26 @GET /bookings/{booking_id}
  L27 def get_booking
  L40 @GET /bookings
  L41 def list_bookings
  L59 @POST /bookings/{booking_id}/confirm
  L60 def confirm_booking
  L70 @POST /bookings/{booking_id}/check-in
  L71 def check_in_booking
  L81 @POST /bookings/{booking_id}/check-out
  L82 def check_out_booking
  L92 @POST /bookings/{booking_id}/approve
  L93 def approve_booking
  L103 @POST /bookings/{booking_id}/pay
  L104 @POST /bookings/{booking_id}/record-payment
  L106 def pay_booking
  L117 @POST /bookings/{booking_id}/no-show
  L118 def no_show_booking
  L128 @POST /bookings/{booking_id}/cancel/worker
  L129 def cancel_by_worker
  L139 @POST /bookings/{booking_id}/cancel/operator
  L140 def cancel_by_operator
  L150 @POST /system/no-show-sweep
  L151 def sweep_no_shows
  L161 def _transition
  L189 def _require_booking_access

## apps/api/src/routes/markets.py (16 lines)
  L12 @GET /markets
  L13 def list_markets

## apps/api/src/routes/messages.py (99 lines)
  L16 def _thread_actor_id
  L22 @POST /shifts/{shift_id}/messages
  L24 def send_message
  L66 @GET /shifts/{shift_id}/messages
  L67 def get_shift_messages
  L89 @POST /messages/{message_id}/read
  L90 def mark_message_as_read

## apps/api/src/routes/notifications.py (181 lines)
  L28 @GET /notifications
  L29 def list_actor_notifications
  L55 @POST /notifications/{notification_id}/read
  L56 def mark_notification_read
  L67 @POST /notifications/read-all
  L68 def mark_actor_notifications_read
  L76 @GET /notification-preferences
  L77 def read_notification_preferences
  L85 @PUT /notification-preferences
  L86 def update_notification_preferences
  L103 @POST /devices/push-tokens
  L104 def create_push_token
  L126 @DELETE /devices/push-tokens/{push_token_id}
  L127 def remove_push_token
  L137 @GET /workers/{worker_id}/notifications
  L138 def list_worker_notifications_legacy
  L148 @POST /workers/{worker_id}/notifications/read-all
  L149 def mark_worker_notifications_read_legacy
  L158 def _recipient
  L166 def _view

## apps/api/src/routes/payments.py (125 lines)
  L37 class PaymentQuoteRequest (BaseModel)
  L45 class PaymentQuoteResponse (BaseModel)
  L60 @POST /quote
  L61 def quote_payment
  L95 def _processing_fee
  L109 def _capped_fee
  L121 def _decimal_env

## apps/api/src/routes/ratings.py (189 lines)
  L29 @POST /bookings/{booking_id}/rate
  L31 def rate_booking
  L79 @GET /ratings/pending
  L80 def list_pending_ratings
  L96 @GET /workers/{worker_id}/rating-summary
  L97 def get_worker_rating_summary
  L124 @GET /venues/{venue_id}/rating-summary
  L125 def get_venue_rating_summary
  L142 @GET /accounts/me/completed-shifts
  L143 def list_completed_shifts
  L167 def _get_worker_id
  L172 def _require_rating_access

## apps/api/src/routes/reports.py (121 lines)
  L34 @POST /reports
  L36 def create_report
  L81 @GET /reports/me
  L82 def list_my_reports
  L91 @GET /system/reports
  L92 def list_reports_for_review
  L102 @PATCH /system/reports/{report_id}
  L103 def review_report

## apps/api/src/routes/service_errors.py (25 lines)
  L16 def raise_service_error

## apps/api/src/routes/shifts.py (251 lines)
  L39 def _geocode_and_update
  L66 def _geocode_repo
  L70 def _require_verified_operator
  L86 @POST /shifts
  L88 def create_shift
  L136 @GET /shifts
  L137 def list_shifts
  L152 @GET /shifts/{shift_id}
  L153 def get_shift_by_id
  L166 @POST /shifts/{shift_id}/clone
  L167 def clone_shift
  L182 @PUT /shifts/{shift_id}
  L183 def update_shift
  L210 @POST /shifts/{shift_id}/close
  L211 def close_shift
  L225 @POST /shifts/{shift_id}/cancel
  L226 def cancel_shift
  L240 def _require_shift_access
  L248 def _require_shift_management

## apps/api/src/routes/templates.py (94 lines)
  L23 @POST /templates
  L24 def create_template
  L33 @GET /templates
  L34 def list_templates
  L42 @GET /templates/{template_id}
  L43 def get_template
  L55 @PUT /templates/{template_id}
  L56 def update_template
  L69 @DELETE /templates/{template_id}
  L70 def delete_template
  L83 @POST /templates/{template_id}/generate
  L84 def generate_shifts_from_template

## apps/api/src/routes/tenancy.py (53 lines)
  L13 @GET /organisations/me
  L14 def get_my_organisation
  L35 @GET /venues
  L36 def list_my_venues

## apps/api/src/routes/uploads.py (121 lines)
  L28 @POST /uploads/avatar
  L30 async def upload_worker_avatar
  L60 @POST /uploads/venue-photo
  L62 async def upload_venue_photo
  L91 @POST /uploads/venue-avatar
  L93 async def upload_venue_avatar

## apps/api/src/routes/worker_feed.py (118 lines)
  L31 @GET /workers/me/feed
  L32 def list_worker_feed
  L78 @GET /workers/{worker_id}/feed-state
  L79 def list_feed_state
  L93 def save_feed_state
  L109 @DELETE /workers/{worker_id}/feed-state/{shift_id}
  L110 def delete_feed_state

## apps/api/src/routes/workers.py (164 lines)
  L36 @GET /workers
  L37 def list_all_workers
  L49 @GET /workers/{worker_id}
  L50 def get_worker_profile
  L65 @GET /workers/{worker_id}/earnings
  L66 def get_worker_earnings
  L124 @PUT /workers/{worker_id}
  L125 def update_worker_profile

## apps/api/src/scheduler.py (120 lines)
  L13 def run_no_show_sweep
  L41 def run_recurring_generation
  L105 def create_scheduler

## apps/api/src/schemas.py (276 lines)
  L8 class BookingTransitionRequest (BaseModel)
  L12 class BookingResponse (BaseModel)
  L36 class ShiftCreateRequest (BaseModel)
  L47   def validate_time_order
  L53 class ShiftResponse (BaseModel)
  L76 class ApplicationCreateRequest (BaseModel)
  L83 class ApplicationDecisionRequest (BaseModel)
  L87 class ApplicationMessageUpdateRequest (BaseModel)
  L92 class ApplicationResponse (BaseModel)
  L108 class ApplicationMessageHistoryResponse (BaseModel)
  L115 class WorkerProfileUpdateRequest (BaseModel)
  L133 class WorkerProfilePublicResponse (BaseModel)
  L148 class WorkerProfilePrivateResponse (WorkerProfilePublicResponse)
  L158 class ErrorResponse (BaseModel)
  L162 class TemplateCreateRequest (BaseModel)
  L172 class TemplateUpdateRequest (BaseModel)
  L182 class TemplateResponse (BaseModel)
  L196 class GenerateShiftsRequest (BaseModel)
  L203 class RecurringScheduleCreateRequest (BaseModel)
  L212 class RecurringScheduleResponse (BaseModel)
  L226 class MessageSendRequest (BaseModel)
  L232 class MessageResponse (BaseModel)
  L244 class EarningsEntryResponse (BaseModel)
  L258 class EarningsSummaryResponse (BaseModel)
  L266 class WorkerFeedStateUpdateRequest (BaseModel)
  L271 class WorkerFeedStateResponse (BaseModel)

## apps/api/src/schemas_account.py (37 lines)
  L9 class AccountResponse (BaseModel)
  L27 class AccountUpdateRequest (BaseModel)

## apps/api/src/schemas_market.py (21 lines)
  L11 class MarketResponse (BaseModel)
  L20   def from_domain

## apps/api/src/schemas_notifications.py (43 lines)
  L8 class NotificationActionResponse (BaseModel)
  L13 class NotificationResponse (BaseModel)
  L23 class NotificationPageResponse (BaseModel)
  L29 class NotificationPreferencesResponse (BaseModel)
  L34 class PushTokenRequest (BaseModel)
  L40 class PushTokenResponse (BaseModel)

## apps/api/src/schemas_privacy.py (26 lines)
  L10 class AccountExportRequest (BaseModel)
  L14 class AccountExportResponse (BaseModel)
  L20 class AccountDeactivateRequest (BaseModel)
  L25 class AccountDeactivateResponse (BaseModel)

## apps/api/src/schemas_ratings.py (52 lines)
  L8 class RatingCreateRequest (BaseModel)
  L13 class PendingRatingResponse (BaseModel)
  L25 class WorkerRatingSummaryResponse (BaseModel)
  L31 class VenueRatingSummaryResponse (BaseModel)
  L37 class UnratedBookingResponse (BaseModel)
  L45 class CompletedShiftResponse (BaseModel)

## apps/api/src/schemas_recovery.py (40 lines)
  L10 class CancellationRequest (BaseModel)
  L15 class ShiftLifecycleRequest (BaseModel)
  L19 class PaymentRecordRequest (BaseModel)
  L26 class ShiftUpdateRequest (BaseModel)
  L37   def validate_time_order

## apps/api/src/schemas_reports.py (37 lines)
  L14 class ReportCreateRequest (BaseModel)
  L21 class ReportReviewRequest (BaseModel)
  L26 class ReportResponse (BaseModel)

## apps/api/src/schemas_tenancy.py (25 lines)
  L8 class OrganisationResponse (BaseModel)
  L17 class VenueSummaryResponse (BaseModel)

## apps/api/src/schemas_uploads.py (8 lines)
  L6 class UploadResponse (BaseModel)

## apps/api/src/schemas_worker_feed.py (22 lines)
  L9 class FeedVenueResponse (BaseModel)
  L15 class WorkerFeedItemResponse (ShiftResponse)
  L19 class WorkerFeedPageResponse (BaseModel)

## apps/api/src/services/account_privacy.py (204 lines)
  L30 def build_account_export
  L91 def deactivate_account
  L146 def _shift_query
  L161 def _applications
  L169 def _bookings
  L177 def _model_or_none
  L181 def _model
  L189 def _values
  L193 def _json_value

## apps/api/src/services/application_service.py (211 lines)
  L34 class ApplicationService
  L35   def __init__
  L49   def create_application
  L91   def list_applications
  L108   def approve_application
  L120   def reject_application
  L130   def update_message
  L148   def withdraw
  L180   def list_message_history
  L184   def get_application
  L187   def application_belongs_to_venue
  L191   def _get_application
  L197   def _publish_decision

## apps/api/src/services/booking_lifecycle_service.py (147 lines)
  L26 class BookingLifecycleService
  L27   def __init__
  L39   def get_booking
  L45   def booking_belongs_to_venue
  L49   def list_bookings
  L64   def transition
  L130   def sweep_no_shows

## apps/api/src/services/booking_ops.py (81 lines)
  L16 def refresh_reliability
  L47 def sweep_no_shows
  L68 def _decrement_workers_filled

## apps/api/src/services/email.py (114 lines)
  L28 class Email
  L34 class EmailTransport (Protocol)
  L35   def send
  L39 class LoggingEmailTransport
  L40   def send
  L50 class SmtpSettings
  L58   def from_env
  L77 class SmtpEmailTransport
  L78   def __init__
  L81   def send
  L95 def _select_transport
  L113 def get_email_transport

## apps/api/src/services/email_verification.py (43 lines)
  L17 def generate_verification_token
  L21 def _verification_link
  L26 def send_verification_email
  L30 def build_verification_email

## apps/api/src/services/errors.py (21 lines)
  L4 class ServiceError (Exception)
  L8 class NotFoundError (ServiceError)
  L12 class ValidationError (ServiceError)
  L16 class ConflictError (ServiceError)
  L20 class ForbiddenError (ServiceError)

## apps/api/src/services/expo_push.py (34 lines)
  L9 def send_expo_push

## apps/api/src/services/geocoding.py (65 lines)
  L19 def geocode
  L53 def _fetch

## apps/api/src/services/health.py (99 lines)
  L16 def record_worker_heartbeat
  L22 def readiness_snapshot
  L33 def _database_status
  L49 def _redis_status
  L62 def _outbox_status
  L87 def _worker_status
  L96 def _redis_client

## apps/api/src/services/idempotency.py (116 lines)
  L16 class IdempotencyConflict (Exception)
  L21 class IdempotencyStart
  L26 class IdempotencyService
  L27   def __init__
  L30   def start
  L70   def finish
  L82   def _find
  L95 def _memory_start
  L109 def _request_hash
  L114 def clear_in_memory_idempotency

## apps/api/src/services/image_processing.py (65 lines)
  L24 class ProcessedImage
  L32 def process_image
  L52 def _encode
  L63 def _flatten_mode

## apps/api/src/services/message_service.py (163 lines)
  L17 class MessageService
  L18   def __init__
  L32   def send_message
  L60   def list_messages
  L77   def mark_as_read
  L92   def _get_shift
  L98   def _require_thread_access
  L120   def _application_worker_id
  L126   def _booking_worker_id
  L132   def _publish_message

## apps/api/src/services/notification_cursor.py (21 lines)
  L7 def encode_notification_cursor
  L12 def decode_notification_cursor

## apps/api/src/services/notification_preferences.py (36 lines)
  L15 def default_notification_preferences
  L19 def normalize_notification_preferences
  L30 def operator_notification_enabled

## apps/api/src/services/notification_settings.py (151 lines)
  L25 class PushToken
  L33 def get_preferences
  L46 def save_preferences
  L68 def register_push_token
  L117 def delete_push_token
  L133 def _normalize
  L142 def _validate_complete
  L150 def _to_push_token

## apps/api/src/services/operator_invites.py (22 lines)
  L14 def _valid_invite_codes
  L19 def is_valid_invite_code

## apps/api/src/services/outbox_dispatcher.py (270 lines)
  L27 class DispatchStats
  L33 def dispatch_outbox_once
  L56 def _claim_events
  L79 def _fan_out_event
  L122 def _claim_deliveries
  L147 def _deliver
  L180 def _deliver_in_app
  L219 def _mark_delivery_success
  L226 def _mark_delivered
  L234 def _record_event_failure
  L249 def _record_delivery_failure
  L269 def _retry_delay

## apps/api/src/services/outbox_publisher.py (212 lines)
  L17 class OutboxPublisher (Protocol)
  L18   def publish_notification
  L33   def publish_email
  L44 class SqlAlchemyOutboxPublisher
  L45   def __init__
  L48   def publish_notification
  L86   def publish_email
  L105   def _save
  L145 class InMemoryOutboxPublisher
  L146   def __init__
  L155   def publish_notification
  L194   def publish_email
  L210 def _idempotency_key

## apps/api/src/services/outbox_recipients.py (60 lines)
  L10 def channel_enabled
  L26 def push_tokens
  L46 def _recipient_users
  L54 def _normalized

## apps/api/src/services/password_reset_email.py (38 lines)
  L14 def _reset_link
  L19 def send_password_reset_email
  L23 def build_password_reset_email

## apps/api/src/services/recovery_notifications.py (25 lines)
  L6 def notify_worker

## apps/api/src/services/report_access.py (94 lines)
  L12 def require_report_subject_access
  L60 def _require_shift_access
  L81 def _require_participant

## apps/api/src/services/shift_lifecycle_service.py (175 lines)
  L26 class ShiftLifecycleService
  L27   def __init__
  L39   def update
  L74   def close
  L80   def cancel
  L133   def _manageable_shift
  L151   def _reject_pending_applications
  L166   def _contract_terms_changed

## apps/api/src/services/shift_service.py (86 lines)
  L12 class ShiftService
  L13   def __init__
  L16   def create_shift
  L45   def list_shifts
  L59   def get_shift
  L65   def clone_shift

## apps/api/src/services/stored_upload.py (71 lines)
  L15 def avatar_key
  L19 def avatar_prefix
  L23 def venue_photo_key
  L27 def venue_photo_prefix
  L31 async def store_image
  L53 def retire_objects_after_commit
  L68 def _safe_segment

## apps/api/src/services/template_service.py (134 lines)
  L19 class TemplateService
  L20   def __init__
  L28   def create_template
  L46   def list_templates
  L49   def get_template
  L52   def update_template
  L75   def delete_template
  L79   def generate_shifts
  L101   def _get_owned_template
  L107   def _parse_start_time
  L115 def _shift_from_template

## apps/api/src/services/upload_validation.py (62 lines)
  L15 def validate_extension
  L22 async def read_capped_image
  L39 async def read_processed_image
  L44 def image_content_type

## apps/api/src/services/worker_feed_cursor.py (85 lines)
  L15 class FeedCursorError (ValueError)
  L19 def filter_fingerprint
  L32 def encode_feed_cursor
  L52 def decode_feed_cursor
  L79 def _encode
  L83 def _decode

## apps/api/src/services/worker_feed_service.py (47 lines)
  L11 class WorkerFeedService
  L12   def __init__
  L20   def list_state
  L23   def save_state
  L46   def delete_state

## apps/api/src/services/worker_shift_feed_service.py (100 lines)
  L21 class WorkerMarketMissingError (ValueError)
  L26 class WorkerFeedPage
  L32 class WorkerShiftFeedService
  L33   def __init__
  L43   def list_page
  L96 def _today_bounds

## apps/api/src/storage/config.py (62 lines)
  L10 class StorageSettings
  L21 def get_storage_settings
  L57 def _local_directory

## apps/api/src/storage/local_object_storage.py (45 lines)
  L10 class LocalObjectStorage
  L11   def __init__
  L16   def put
  L28   def delete
  L31   def key_from_url
  L39   def _path_for_key

## apps/api/src/storage/object_storage.py (18 lines)
  L8 class StoredObject
  L13 class ObjectStorage (Protocol)
  L14   def put
  L16   def delete
  L18   def key_from_url

## apps/api/src/storage/s3_object_storage.py (47 lines)
  L9 class S3ObjectStorage
  L10   def __init__
  L18   def put
  L29   def delete
  L32   def key_from_url

## apps/api/src/storage_dependencies.py (29 lines)
  L14 def get_object_storage

## apps/api/src/unit_of_work.py (51 lines)
  L11 class RequestUnitOfWork
  L12   def __init__
  L17   def after_commit
  L20   def after_rollback
  L23   def commit
  L31   def rollback
  L41   def close
  L46   def _run_callbacks

## apps/api/src/worker.py (38 lines)
  L15 def main
  L21   def request_stop

## apps/api/tests/conftest.py (146 lines)
  L20 def _database_backend
  L37 def _assert_disposable_database
  L49 def _delete_all_rows
  L75 def pytest_runtest_setup
  L89 def clean_database_tables
  L96 def reset_rate_limiter
  L105 def restore_dependency_overrides
  L115 def reset_in_memory_idempotency
  L124 def repo_session

## apps/api/tests/test_account_preferences.py (154 lines)
  L19 class FakeAccountRepository
  L20   def __init__
  L23   def get
  L26   def save
  L32 def account_repo
  L52 def override_account_repo
  L58 def test_get_account_returns_default_notification_preferences
  L71 def test_update_account_persists_notification_preferences
  L97 def test_update_account_drops_unknown_notification_keys
  L121 def test_update_account_rejects_non_bool_notification_values
  L137 def test_account_profile_update_still_preserves_existing_fields

## apps/api/tests/test_application_endpoints.py (123 lines)
  L22 def _client
  L41 def test_application_approve_creates_booking
  L92 def test_worker_cannot_create_application_for_another_worker

## apps/api/tests/test_application_service_filters.py (61 lines)
  L21 def test_list_applications_by_worker_filters_before_limit
  L49 def _application

## apps/api/tests/test_auth.py (226 lines)
  L20 def user_repo
  L28 def worker_profile_repo
  L35 def override_repos
  L43 def test_register_worker_success
  L65 def test_register_duplicate_email
  L92 def test_short_password_rejection
  L117 def test_login_success
  L148 def test_login_rate_limit_response
  L164 def test_login_invalid_email
  L175 def test_login_invalid_password
  L202 def test_login_inactive_user

## apps/api/tests/test_auth_startup_guard.py (87 lines)
  L8 def _run_import
  L21 def test_guard_raises_in_production_with_dev_mode
  L35 def test_guard_raises_in_production_with_short_secret
  L49 def test_guard_raises_in_production_with_default_secret
  L63 def test_guard_is_noop_in_development
  L76 def test_guard_rejects_in_memory_backends_in_production

## apps/api/tests/test_booking_endpoints.py (194 lines)
  L18 def _client
  L48 def _create_booking
  L68 def test_direct_booking_creation_is_not_exposed
  L74 def test_booking_lifecycle_happy_path
  L127 def test_invalid_transition_returns_400
  L139 def test_no_show_requires_window_closed
  L166 def test_list_bookings_returns_recent
  L176 def test_role_required
  L182 def test_booking_access_is_limited_to_owner

## apps/api/tests/test_config.py (93 lines)
  L13 def test_resolve_sqlite_file_url_anchors_relative_paths_to_project_root
  L20 def test_resolve_sqlite_file_url_leaves_external_urls_unchanged
  L26 def test_normalize_database_url_uses_psycopg_for_postgres_urls
  L32 def test_normalize_database_url_accepts_postgres_scheme_alias
  L38 def test_get_cors_origins_parses_comma_separated_env
  L51 def test_get_cors_origins_falls_back_to_default_when_blank
  L61 def test_production_requires_database_url
  L72 def test_production_rejects_sqlite_database
  L80 def test_production_requires_cors_origins
  L88 def test_production_rejects_insecure_cors_origin

## apps/api/tests/test_email_verification.py (129 lines)
  L26 def user_repo
  L33 def override_repos
  L44 def test_worker_registers_unverified_with_token
  L57 def test_verify_email_marks_verified
  L73 def test_verify_email_rejects_unknown_token
  L78 def test_resend_verification_issues_new_token
  L93 def test_resend_verification_unknown_email_is_opaque
  L98 def _operator_user
  L114 def test_unverified_operator_cannot_create_shift
  L124 def test_verified_operator_can_create_shift

## apps/api/tests/test_health.py (10 lines)
  L6 def test_health_check

## apps/api/tests/test_health_and_errors.py (59 lines)
  L11 def test_liveness_and_development_readiness
  L22 def test_request_id_is_validated_and_security_headers_are_set
  L33 def test_production_responses_enable_transport_security
  L42 def test_validation_errors_have_stable_machine_readable_shape
  L55 def test_http_errors_have_stable_machine_readable_shape

## apps/api/tests/test_idempotency.py (62 lines)
  L17 def test_in_memory_idempotency_replays_and_rejects_payload_changes
  L33 def test_shift_creation_replays_same_response

## apps/api/tests/test_image_processing.py (99 lines)
  L18 def _encode
  L24 def _png_header_claiming
  L35 def test_jpeg_is_reencoded_without_exif_metadata
  L50 def test_png_keeps_alpha_and_drops_text_chunks
  L65 def test_webp_roundtrip
  L73 def test_oversized_image_is_downscaled_to_max_edge
  L80 def test_valid_magic_bytes_with_garbage_body_are_rejected
  L87 def test_decompression_bomb_header_is_rejected_before_decode
  L95 def test_unsupported_format_is_rejected

## apps/api/tests/test_message_endpoints.py (127 lines)
  L21 def _client
  L66 def test_worker_can_message_own_application_thread
  L86 def test_message_threads_are_limited_to_participants
  L110 def test_linked_worker_account_uses_profile_id_for_message_access

## apps/api/tests/test_no_show_sweep_entrypoints.py (112 lines)
  L15 class _DummySession
  L16   def close
  L19   def commit
  L23 def _seed_confirmed_no_show
  L65 def test_scheduler_run_no_show_sweep_end_to_end
  L96 def test_job_run_no_show_sweep_end_to_end

## apps/api/tests/test_no_show_sweep_service.py (61 lines)
  L14 def test_sweep_no_shows_updates_booking_and_reliability

## apps/api/tests/test_notification_contract.py (94 lines)
  L14 def test_worker_inbox_cursor_read_and_tenant_isolation
  L70 def test_preferences_and_push_token_are_actor_scoped

## apps/api/tests/test_object_storage.py (66 lines)
  L11 class FakeS3Client
  L12   def __init__
  L16   def put_object
  L19   def delete_object
  L23 def test_local_storage_writes_resolves_and_deletes_object
  L36 def test_local_storage_rejects_keys_outside_root
  L43 def test_s3_storage_sets_public_cache_metadata_and_builds_url

## apps/api/tests/test_operator_invite_gating.py (67 lines)
  L20 def configure_invite_codes
  L26 def override_repos
  L38 def _payload
  L51 def test_operator_register_rejects_bad_invite_code
  L57 def test_operator_register_requires_invite_code_field
  L62 def test_operator_register_accepts_valid_invite_code

## apps/api/tests/test_outbox_dispatcher.py (113 lines)
  L20 class RecordingTransport
  L21   def __init__
  L24   def send
  L28 class FailingTransport
  L29   def send
  L33 def _session_factory
  L44 def test_domain_rollback_removes_outbox_event
  L60 def test_replay_is_idempotent_and_materializes_one_notification
  L78 def test_failed_email_is_released_for_retry
  L101 def _publish_worker_notification

## apps/api/tests/test_password_reset_tokens.py (185 lines)
  L23 class RecordingTransport
  L24   def __init__
  L27   def send
  L32 def user_repo
  L39 def override_user_repo
  L45 def test_reset_token_works_once
  L62 def test_password_reset_revokes_existing_sessions
  L87 def test_reset_token_rejected_after_use
  L107 def test_reset_token_expires_after_one_hour
  L111 class ExpiredDateTime (datetime)
  L113   def now
  L131 def test_forgot_password_emails_working_reset_link
  L156 def test_forgot_password_unknown_email_sends_nothing_with_identical_response
  L172 def _save_user

## apps/api/tests/test_postgres_concurrency.py (138 lines)
  L24 def _session_factory
  L30 def _seed_shift_with_applications
  L66 def _approve_concurrently
  L72   def approve
  L99 def _shift_state
  L109 def test_concurrent_approvals_cannot_overfill_last_slot
  L125 def test_same_application_cannot_be_approved_twice_concurrently

## apps/api/tests/test_postgres_flows.py (257 lines)
  L30 def client
  L36 def _db_session
  L42 def _auth
  L46 def _register_worker
  L52 def _register_verified_operator
  L75 def _create_shift
  L93 def test_created_shift_geocoding_is_committed
  L105 def _apply
  L120 def _approve
  L128 def _approved_booking
  L140 def test_backend_is_actually_postgresql
  L153 def test_registration_persists_user_account_and_profile
  L177 def test_approval_creates_booking_and_fills_shift
  L196 def test_approving_second_application_on_full_shift_fails
  L219 def test_worker_cancellation_reopens_shift
  L240 def test_operator_no_show_reopens_shift_and_updates_reliability

## apps/api/tests/test_postgres_market_schema.py (25 lines)
  L11 def test_postgres_has_market_and_open_feed_indexes

## apps/api/tests/test_postgres_outbox.py (209 lines)
  L25 class FailingTransport
  L26   def send
  L30 def test_two_dispatchers_materialize_one_in_app_notification
  L39   def dispatch
  L59 def test_concurrent_producers_share_one_idempotent_event
  L65   def publish
  L84 def test_stale_event_lease_is_reclaimed
  L101 def test_actor_notification_preferences_and_devices_are_tenant_scoped
  L158 def test_email_delivery_reaches_dead_letter_after_max_attempts
  L184 def _publish_notification

## apps/api/tests/test_postgres_phase2a.py (184 lines)
  L49 def _shift
  L67 def test_postgres_schema_uses_timestamptz_and_exact_numeric
  L81 def test_postgres_round_trips_decimal_money_and_utc
  L110 def test_postgres_prevents_deleting_shift_with_booking
  L137 def test_postgres_shift_delete_retains_notification
  L163 def test_postgres_foreign_keys_encode_deletion_policy

## apps/api/tests/test_postgres_ratings.py (212 lines)
  L31 def _seed_booking
  L107 def test_pending_prompts_are_personalised_for_each_side
  L120 def test_rating_requires_booking_participation_and_venue_access
  L138 def test_rating_requires_completed_shift
  L151 def test_rating_records_rater_and_clears_only_that_sides_prompt
  L169 def test_worker_ratings_are_exposed_as_venue_reputation
  L188 def test_each_side_can_rate_once
  L205 def test_rating_comment_is_bounded

## apps/api/tests/test_postgres_recovery.py (137 lines)
  L28 def client
  L34 def _db_session
  L40 def _staffed_shift
  L51 def test_shift_cancellation_persists_audit_and_related_updates
  L89 def test_notification_failure_rolls_back_whole_shift_cancellation
  L92 class FailingOutboxPublisher
  L93   def publish_notification
  L96   def publish_email
  L119 def test_worker_withdrawal_is_persisted_with_reason

## apps/api/tests/test_postgres_security_hardening.py (188 lines)
  L30 def client
  L36 def _verify_user
  L43 def test_account_export_and_deletion_persist_and_revoke_access
  L83 def test_report_persists_and_cross_venue_operator_is_denied
  L123 def test_same_idempotency_key_is_serialized_across_connections
  L130   def attempt
  L168 def test_expired_idempotency_key_can_be_reused

## apps/api/tests/test_postgres_tenancy.py (151 lines)
  L24 def client
  L30 def _session
  L36 def _headers
  L40 def _register
  L57 def _verify
  L64 def test_registration_creates_one_organisation_venue_and_owner_membership
  L84 def test_operator_can_read_organisation_and_all_its_venues
  L110 def test_separate_registrations_are_isolated_organisations_and_venues
  L139 def test_operator_scope_requires_membership

## apps/api/tests/test_postgres_transactions.py (111 lines)
  L21 def client
  L26 def _operator_payload
  L37 def test_registration_repositories_share_one_request_session
  L43   def capture_market
  L47   def capture_organisation
  L51   def capture_user
  L69 def test_registration_rolls_back_every_repository_write
  L70   def fail_user_save
  L92 def test_verification_email_is_committed_atomically_with_user

## apps/api/tests/test_postgres_worker_feed_query.py (287 lines)
  L21 def client
  L30 def _session
  L36 def _register_worker
  L48 def _select_bath
  L66 def _seed_venues
  L108 def _shift
  L136 def test_market_contract_and_profile_assignment
  L179 def test_feed_filters_in_postgres_and_excludes_ineligible_rows
  L246 def test_keyset_cursor_is_stable_signed_and_filter_bound

## apps/api/tests/test_prepare_demo_accounts.py (59 lines)
  L16 def test_prepare_demo_accounts_is_complete_and_idempotent

## apps/api/tests/test_recovery_endpoints.py (212 lines)
  L34 def _client
  L52 def _create_shift
  L71 def _apply
  L87 def _approve
  L97 def test_worker_can_withdraw_only_their_pending_application
  L121 def test_closing_shift_rejects_pending_applications_but_preserves_bookings
  L139 def test_shift_edit_locks_contract_terms_after_booking_but_allows_notes_and_capacity
  L163 def test_cancelling_shift_is_atomic_and_audited
  L191 def test_worker_booking_cancellation_requires_reason_and_records_actor

## apps/api/tests/test_red_team_security.py (166 lines)
  L18 def _register_worker
  L27 def test_actor_headers_cannot_bypass_auth_when_dev_mode_is_disabled
  L39 def test_jwt_role_and_tenant_claims_cannot_escalate_database_identity
  L73 def test_tampered_jwt_is_rejected
  L88 def test_unverified_worker_cannot_apply_in_production_mode
  L126 def test_account_deletion_requires_password_and_exact_confirmation
  L148 def test_oversized_inputs_and_unbounded_limits_are_rejected

## apps/api/tests/test_reliability_and_sweep.py (153 lines)
  L18 def _client
  L26 def _create_profile
  L49 def _create_booking
  L73 def test_reliability_updates_from_outcomes
  L116 def test_no_show_sweep_marks_expired_bookings

## apps/api/tests/test_report_endpoints.py (72 lines)
  L14 def test_report_submission_status_and_system_review
  L56 def test_report_rejects_unknown_subject

## apps/api/tests/test_shift_endpoints.py (107 lines)
  L14 def _client
  L20 def test_shift_create_and_list
  L57 def test_shift_create_rejects_timezone_less_timestamps
  L74 def test_shift_create_normalizes_offset_timestamps_to_utc
  L93 def test_shift_create_rejects_fractional_pennies

## apps/api/tests/test_sqlalchemy_repositories.py (174 lines)
  L22 def test_sqlalchemy_shift_repository_round_trip
  L47 def test_sqlalchemy_application_repository_round_trip
  L86 def test_sqlalchemy_worker_profile_repository_round_trip
  L114 def test_sqlalchemy_application_repository_rejects_duplicate_worker_shift
  L126 def test_sqlalchemy_application_decision_approve_is_single_write_path
  L145 def _shift
  L162 def _application

## apps/api/tests/test_sqlite_migrations.py (198 lines)
  L11 def test_sqlite_migrations_reach_head
  L101 def test_organisation_migration_backfills_and_reverses
  L138 def test_market_migration_backfills_bath_and_reverses

## apps/api/tests/test_storage_config.py (61 lines)
  L17 def test_local_storage_is_allowed_in_development
  L28 def test_local_storage_is_rejected_outside_development
  L36 def test_s3_storage_requires_complete_configuration
  L46 def test_s3_storage_configuration_is_provider_portable

## apps/api/tests/test_template_endpoints.py (73 lines)
  L12 def _client
  L19 def test_template_create_list_update_delete_round_trip
  L70 def test_default_template_dependency_uses_in_memory

## apps/api/tests/test_token_revocation.py (128 lines)
  L22 def user_repo
  L29 def override_repos
  L39 def clear_denylist
  L46 def test_access_token_has_jti
  L52 def test_decode_rejects_revoked_token
  L62 def test_logout_revokes_token
  L78 def test_logout_requires_token
  L83 def test_logout_all_revokes_every_session
  L103 def test_account_deletion_anonymizes_user_and_revokes_session

## apps/api/tests/test_unit_of_work_callbacks.py (48 lines)
  L8 class FakeSession
  L9   def __init__
  L14   def commit
  L18   def rollback
  L21   def close
  L25 def test_commit_runs_commit_callbacks_and_discards_rollback_callbacks
  L37 def test_failed_commit_preserves_cleanup_for_rollback

## apps/api/tests/test_upload_endpoints.py (246 lines)
  L20 def _image_bytes
  L36 class FakeStorage
  L37   def __init__
  L42   def put
  L47   def delete
  L51   def key_from_url
  L56 class FakeWorkerRepository
  L57   def __init__
  L60   def get
  L63   def save
  L68 class FakeAccountRepository
  L69   def __init__
  L73   def get
  L76   def save
  L84 def upload_dependencies
  L125 def test_worker_avatar_upload_updates_profile_and_retires_previous_object
  L142 def test_venue_photo_upload_appends_public_object_url
  L156 def test_upload_rejects_extension_content_mismatch
  L169 def test_failed_database_write_removes_new_object
  L184 def test_removing_venue_photo_retires_object_after_account_commit
  L200 def test_account_update_cannot_attach_or_delete_another_venues_media
  L219 def test_account_update_cannot_replace_avatar_url_directly
  L234 def test_legacy_foreign_photo_is_not_deleted_by_venue_update

## apps/api/tests/test_user_repository.py (153 lines)
  L10 def test_in_memory_user_repository_save_and_get
  L37 def test_in_memory_user_repository_get_by_email
  L61 def test_in_memory_user_repository_get_by_email_case_insensitive
  L84 def test_in_memory_user_repository_get_nonexistent
  L95 def test_in_memory_user_repository_update
  L131 def test_in_memory_user_repository_clear

## apps/api/tests/test_worker_feed_endpoints.py (76 lines)
  L13 def _client
  L22 def test_worker_feed_state_round_trip_and_delete
  L48 def test_worker_feed_state_is_worker_owned
  L61 def _create_shift

## apps/api/tests/test_worker_profile_endpoints.py (61 lines)
  L16 def _client
  L22 def test_worker_profile_update_and_public_view

## apps/api/tests/test_workers_needed.py (198 lines)
  L32 def repos
  L53 def override_repos
  L57 def test_create_shift_with_default_workers_needed
  L67 def test_create_shift_with_multiple_workers_needed
  L77 def test_approve_application_increments_workers_filled
  L89 def test_shift_status_changes_to_filled_when_capacity_reached
  L104 def test_cannot_approve_application_when_shift_fully_staffed
  L117 def test_cannot_apply_to_fully_staffed_shift
  L128 def test_multiple_workers_for_large_shift
  L154 def create_shift
  L175 def apply_to_shift
  L183 def approve_application
  L191 def get_shift
  L196 def assert_fully_staffed_or_closed

## packages/domain/src/booking.py (92 lines)
  L15 class Booking
  L37   def transition_to
  L84 def _within_check_in_window
  L90 def _check_in_window_expired

## packages/domain/src/booking_state.py (13 lines)
  L4 class BookingState (str, Enum)

## packages/domain/src/booking_state_machine.py (54 lines)
  L10 class Transition
  L15 class TransitionError (ValueError)
  L34 def allowed_next_states
  L41 def is_valid_transition
  L47 def require_transition
  L52 def transition

## packages/domain/src/reliability.py (30 lines)
  L9 def compute_reliability

## packages/domain/tests/test_booking.py (98 lines)
  L10 def _base_booking
  L25 def test_confirm_sets_timestamp
  L33 def test_check_in_window_enforced
  L44 def test_check_in_window_boundaries
  L52 def test_check_out_requires_check_in
  L58 def test_no_show_requires_window_expired
  L69 def test_no_show_requires_confirmed
  L76 def test_worker_cancel_requires_before_start
  L83 def test_operator_cancel_rejected_after_start
  L90 def test_paid_requires_approved
  L96 def test_idempotent_same_state

## packages/domain/tests/test_booking_state.py (52 lines)
  L12 def test_paid_is_terminal
  L15 def test_allowed_transitions
  L23 def test_no_show_only_from_confirmed
  L28 def test_cancel_is_allowed_only_before_work_starts
  L46 def test_cancel_not_allowed_from_paid
  L50 def test_invalid_transition_raises

## packages/domain/tests/test_reliability.py (40 lines)
  L8 def _booking
  L22 def test_reliability_empty_returns_zero
  L26 def test_reliability_completed_only
  L34 def test_reliability_mixed_outcomes


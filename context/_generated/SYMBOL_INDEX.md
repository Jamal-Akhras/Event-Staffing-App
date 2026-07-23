# Symbol Index

Generated: 2026-05-02 16:34:05
Python files: 78

## apps/api/alembic/env.py (61 lines)
  L25 def _database_url
  L29 def run_migrations_offline
  L42 def run_migrations_online

## apps/api/alembic/versions/001_create_bookings.py (36 lines)
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

## apps/api/scripts/create_operator.py (84 lines)
  L21 def create_operator
  L60 def main

## apps/api/src/auth.py (25 lines)
  L8 class ActorRole (str, Enum)
  L14 def get_actor_role
  L23 def require_role

## apps/api/src/auth/dependencies.py (141 lines)
  L20 class ActorRole (str, Enum)
  L28 async def get_current_user
  L60 async def get_actor_role
  L111 def require_role
  L128 def extract_user_id_from_token

## apps/api/src/auth/jwt.py (41 lines)
  L13 def create_access_token
  L29 def decode_access_token

## apps/api/src/auth/password.py (30 lines)
  L8 def hash_password
  L20 def verify_password

## apps/api/src/auth/schemas.py (40 lines)
  L8 class UserRegisterRequest (BaseModel)
  L15 class UserLoginRequest (BaseModel)
  L22 class TokenResponse (BaseModel)
  L32 class UserResponse (BaseModel)

## apps/api/src/db/models.py (149 lines)
  L9 class BookingModel (Base)
  L30 class ShiftModel (Base)
  L47 class ApplicationModel (Base)
  L63 class WorkerProfileModel (Base)
  L84 class UserModel (Base)
  L97 class ShiftTemplateModel (Base)
  L113 class RecurringScheduleModel (Base)
  L129 class MessageModel (Base)
  L143 class ApplicationMessageHistoryModel (Base)

## apps/api/src/deps.py (122 lines)
  L40 def _use_in_memory
  L46 def get_booking_repo
  L58 def get_application_repo
  L70 def get_shift_repo
  L82 def get_worker_profile_repo
  L94 def get_user_repo
  L106 def get_template_repo
  L115 def get_message_repo

## apps/api/src/helpers.py (120 lines)
  L29 def _now
  L33 def _now_or
  L37 def _get_booking
  L44 def _save_booking
  L48 def _get_shift
  L55 def _save_shift
  L59 def _get_application
  L66 def _save_application
  L70 def _get_worker_profile
  L77 def _save_worker_profile
  L81 def _booking_view
  L90 def _shift_view
  L95 def _application_view
  L100 def _worker_public_view
  L111 def _worker_private_view
  L116 def _apply_transition

## apps/api/src/jobs/run_no_show_sweep.py (28 lines)
  L15 def run

## apps/api/src/main.py (29 lines)
  L28 def health

## apps/api/src/models/application.py (19 lines)
  L8 class Application

## apps/api/src/models/message.py (19 lines)
  L7 class Message (BaseModel)
  L18 class Config

## apps/api/src/models/shift.py (20 lines)
  L8 class Shift

## apps/api/src/models/shift_template.py (38 lines)
  L7 class ShiftTemplate (BaseModel)
  L20 class Config
  L24 class RecurringSchedule (BaseModel)
  L37 class Config

## apps/api/src/models/user.py (18 lines)
  L8 class User

## apps/api/src/models/worker_profile.py (24 lines)
  L8 class WorkerProfile

## apps/api/src/repositories/application_repository.py (19 lines)
  L8 class ApplicationRepository (Protocol)
  L9   def get
  L12   def save
  L15   def list_recent
  L18   def find_by_worker_and_shift

## apps/api/src/repositories/booking_repository.py (23 lines)
  L9 class BookingRepository (Protocol)
  L10   def get
  L13   def save
  L16   def list_recent
  L19   def list_by_worker
  L22   def list_by_state

## apps/api/src/repositories/in_memory_application_repository.py (31 lines)
  L8 class InMemoryApplicationRepository
  L9   def __init__
  L12   def get
  L15   def save
  L19   def list_recent
  L24   def find_by_worker_and_shift
  L30   def clear

## apps/api/src/repositories/in_memory_booking_repository.py (32 lines)
  L9 class InMemoryBookingRepository
  L10   def __init__
  L13   def get
  L16   def save
  L20   def list_recent
  L25   def list_by_worker
  L28   def list_by_state
  L31   def clear

## apps/api/src/repositories/in_memory_shift_repository.py (25 lines)
  L8 class InMemoryShiftRepository
  L9   def __init__
  L12   def get
  L15   def save
  L19   def list_recent
  L24   def clear

## apps/api/src/repositories/in_memory_user_repository.py (32 lines)
  L8 class InMemoryUserRepository
  L11   def __init__
  L15   def get
  L19   def get_by_email
  L23   def save
  L29   def clear

## apps/api/src/repositories/in_memory_worker_profile_repository.py (20 lines)
  L8 class InMemoryWorkerProfileRepository
  L9   def __init__
  L12   def get
  L15   def save
  L19   def clear

## apps/api/src/repositories/message_repository.py (25 lines)
  L8 class MessageRepository (Protocol)
  L9   def get
  L12   def save
  L15   def list_by_shift
  L18   def list_by_application
  L21   def list_by_booking
  L24   def mark_as_read

## apps/api/src/repositories/shift_repository.py (16 lines)
  L8 class ShiftRepository (Protocol)
  L9   def get
  L12   def save
  L15   def list_recent

## apps/api/src/repositories/sqlalchemy_application_repository.py (78 lines)
  L10 class SqlAlchemyApplicationRepository
  L11   def __init__
  L14   def get
  L20   def save
  L29   def list_recent
  L38   def find_by_worker_and_shift
  L52 def _to_domain
  L68 def _apply_domain

## apps/api/src/repositories/sqlalchemy_booking_repository.py (92 lines)
  L11 class SqlAlchemyBookingRepository
  L12   def __init__
  L15   def get
  L21   def save
  L30   def list_recent
  L39   def list_by_worker
  L48   def list_by_state
  L58 def _to_domain
  L78 def _apply_domain

## apps/api/src/repositories/sqlalchemy_message_repository.py (88 lines)
  L11 class SqlAlchemyMessageRepository
  L12   def __init__
  L15   def get
  L21   def save
  L30   def list_by_shift
  L39   def list_by_application
  L48   def list_by_booking
  L57   def mark_as_read
  L66 def _to_domain
  L80 def _apply_domain

## apps/api/src/repositories/sqlalchemy_shift_repository.py (67 lines)
  L10 class SqlAlchemyShiftRepository
  L11   def __init__
  L14   def get
  L20   def save
  L29   def list_recent
  L39 def _to_domain
  L56 def _apply_domain

## apps/api/src/repositories/sqlalchemy_template_repository.py (142 lines)
  L10 class SqlAlchemyTemplateRepository
  L11   def __init__
  L14   def get_template
  L20   def save_template
  L29   def list_templates
  L38   def delete_template
  L46   def get_schedule
  L52   def save_schedule
  L61   def list_schedules
  L70   def list_active_schedules
  L78   def delete_schedule
  L87 def _template_to_domain
  L103 def _apply_template_domain
  L116 def _schedule_to_domain
  L132 def _apply_schedule_domain

## apps/api/src/repositories/sqlalchemy_user_repository.py (64 lines)
  L10 class SqlAlchemyUserRepository
  L13   def __init__
  L16   def get
  L23   def get_by_email
  L31   def save
  L42 def _to_domain
  L56 def _apply_domain

## apps/api/src/repositories/sqlalchemy_worker_profile_repository.py (65 lines)
  L9 class SqlAlchemyWorkerProfileRepository
  L10   def __init__
  L13   def get
  L19   def save
  L29 def _to_domain
  L50 def _apply_domain

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

## apps/api/src/repositories/user_repository.py (42 lines)
  L8 class UserRepository (Protocol)
  L11   def get
  L22   def get_by_email
  L33   def save

## apps/api/src/repositories/worker_profile_repository.py (13 lines)
  L8 class WorkerProfileRepository (Protocol)
  L9   def get
  L12   def save

## apps/api/src/routes/applications.py (209 lines)
  L40 @POST /applications
  L41 def create_application
  L77 @GET /applications
  L78 def list_applications
  L99 @POST /applications/{application_id}/approve
  L100 def approve_application
  L138 @POST /applications/{application_id}/reject
  L139 def reject_application
  L154 @PUT /applications/{application_id}/message
  L155 def update_application_message
  L184 @GET /applications/{application_id}/message-history
  L185 def get_application_message_history

## apps/api/src/routes/auth.py (99 lines)
  L20 @POST /register
  L21 def register
  L78 @POST /login
  L79 def login

## apps/api/src/routes/bookings.py (212 lines)
  L34 @POST /bookings
  L35 def create_booking
  L54 @GET /bookings/{booking_id}
  L55 def get_booking
  L64 @GET /bookings
  L65 def list_bookings
  L78 @POST /bookings/{booking_id}/confirm
  L79 def confirm_booking
  L91 @POST /bookings/{booking_id}/check-in
  L92 def check_in_booking
  L104 @POST /bookings/{booking_id}/check-out
  L105 def check_out_booking
  L121 @POST /bookings/{booking_id}/approve
  L122 def approve_booking
  L138 @POST /bookings/{booking_id}/pay
  L139 def pay_booking
  L155 @POST /bookings/{booking_id}/no-show
  L156 def no_show_booking
  L172 @POST /bookings/{booking_id}/cancel/worker
  L173 def cancel_by_worker
  L189 @POST /bookings/{booking_id}/cancel/operator
  L190 def cancel_by_operator
  L202 @POST /system/no-show-sweep
  L203 def sweep_no_shows

## apps/api/src/routes/messages.py (74 lines)
  L17 @POST /shifts/{shift_id}/messages
  L18 def send_message
  L49 @GET /shifts/{shift_id}/messages
  L50 def get_shift_messages
  L66 @POST /messages/{message_id}/read
  L67 def mark_message_as_read

## apps/api/src/routes/shifts.py (91 lines)
  L17 @POST /shifts
  L18 def create_shift
  L42 @GET /shifts
  L43 def list_shifts
  L59 @GET /shifts/{shift_id}
  L60 def get_shift_by_id
  L69 @POST /shifts/{shift_id}/clone
  L70 def clone_shift

## apps/api/src/routes/templates.py (159 lines)
  L27 @POST /templates
  L28 def create_template
  L53 @GET /templates
  L54 def list_templates
  L64 @GET /templates/{template_id}
  L65 def get_template
  L77 @PUT /templates/{template_id}
  L78 def update_template
  L104 @DELETE /templates/{template_id}
  L105 def delete_template
  L116 @POST /templates/{template_id}/generate
  L117 def generate_shifts_from_template

## apps/api/src/routes/workers.py (130 lines)
  L32 @GET /workers/{worker_id}
  L33 def get_worker_profile
  L45 @GET /workers/{worker_id}/earnings
  L46 def get_worker_earnings
  L100 @PUT /workers/{worker_id}
  L101 def update_worker_profile

## apps/api/src/schemas.py (245 lines)
  L8 class BookingCreateRequest (BaseModel)
  L17 class BookingTransitionRequest (BaseModel)
  L21 class BookingResponse (BaseModel)
  L40 class ShiftCreateRequest (BaseModel)
  L52 class ShiftResponse (BaseModel)
  L67 class ApplicationCreateRequest (BaseModel)
  L74 class ApplicationDecisionRequest (BaseModel)
  L78 class ApplicationMessageUpdateRequest (BaseModel)
  L83 class ApplicationResponse (BaseModel)
  L97 class ApplicationMessageHistoryResponse (BaseModel)
  L104 class WorkerProfileUpdateRequest (BaseModel)
  L120 class WorkerProfilePublicResponse (BaseModel)
  L133 class WorkerProfilePrivateResponse (WorkerProfilePublicResponse)
  L142 class ErrorResponse (BaseModel)
  L146 class TemplateCreateRequest (BaseModel)
  L156 class TemplateUpdateRequest (BaseModel)
  L166 class TemplateResponse (BaseModel)
  L180 class GenerateShiftsRequest (BaseModel)
  L187 class RecurringScheduleCreateRequest (BaseModel)
  L196 class RecurringScheduleResponse (BaseModel)
  L210 class MessageSendRequest (BaseModel)
  L216 class MessageResponse (BaseModel)
  L228 class EarningsEntryResponse (BaseModel)
  L241 class EarningsSummaryResponse (BaseModel)

## apps/api/src/services/booking_ops.py (61 lines)
  L14 def refresh_reliability
  L45 def sweep_no_shows

## apps/api/tests/test_application_endpoints.py (70 lines)
  L12 def _client
  L22 def test_application_approve_creates_booking

## apps/api/tests/test_auth.py (172 lines)
  L19 def user_repo
  L27 def override_user_repo
  L34 def test_register_worker_success
  L56 def test_register_duplicate_email
  L82 def test_login_success
  L112 def test_login_invalid_email
  L123 def test_login_invalid_password
  L149 def test_login_inactive_user

## apps/api/tests/test_booking_endpoints.py (136 lines)
  L10 def _client
  L16 def _create_booking
  L38 def test_booking_lifecycle_happy_path
  L84 def test_invalid_transition_returns_400
  L96 def test_no_show_requires_window_closed
  L123 def test_list_bookings_returns_recent
  L133 def test_role_required

## apps/api/tests/test_health.py (10 lines)
  L6 def test_health_check

## apps/api/tests/test_no_show_sweep_service.py (59 lines)
  L13 def test_sweep_no_shows_updates_booking_and_reliability

## apps/api/tests/test_reliability_and_sweep.py (148 lines)
  L13 def _client
  L21 def _create_profile
  L44 def _create_booking
  L68 def test_reliability_updates_from_outcomes
  L111 def test_no_show_sweep_marks_expired_bookings

## apps/api/tests/test_shift_endpoints.py (40 lines)
  L10 def _client
  L16 def test_shift_create_and_list

## apps/api/tests/test_sqlalchemy_repositories.py (98 lines)
  L20 def _session
  L27 def test_sqlalchemy_shift_repository_round_trip
  L51 def test_sqlalchemy_application_repository_round_trip
  L73 def test_sqlalchemy_worker_profile_repository_round_trip

## apps/api/tests/test_user_repository.py (161 lines)
  L10 def test_in_memory_user_repository_save_and_get
  L38 def test_in_memory_user_repository_get_by_email
  L63 def test_in_memory_user_repository_get_by_email_case_insensitive
  L87 def test_in_memory_user_repository_get_nonexistent
  L100 def test_in_memory_user_repository_update
  L137 def test_in_memory_user_repository_clear

## apps/api/tests/test_worker_profile_endpoints.py (50 lines)
  L12 def _client
  L18 def test_worker_profile_update_and_public_view

## apps/api/tests/test_workers_needed.py (345 lines)
  L19 def shift_repo
  L27 def application_repo
  L35 def booking_repo
  L43 def override_repos
  L52 def test_create_shift_with_default_workers_needed
  L75 def test_create_shift_with_multiple_workers_needed
  L99 def test_approve_application_increments_workers_filled
  L146 def test_shift_status_changes_to_filled_when_capacity_reached
  L203 def test_cannot_approve_application_when_shift_fully_staffed
  L253 def test_cannot_apply_to_fully_staffed_shift
  L296 def test_multiple_workers_for_large_shift

## packages/domain/src/booking.py (85 lines)
  L15 class Booking
  L32   def transition_to
  L77 def _within_check_in_window
  L83 def _check_in_window_expired

## packages/domain/src/booking_state.py (13 lines)
  L4 class BookingState (str, Enum)

## packages/domain/src/booking_state_machine.py (58 lines)
  L10 class Transition
  L15 class TransitionError (ValueError)
  L34 def allowed_next_states
  L43 def is_valid_transition
  L51 def require_transition
  L56 def transition

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
  L83 def test_operator_cancel_allowed_after_start
  L90 def test_paid_requires_approved
  L96 def test_idempotent_same_state

## packages/domain/tests/test_booking_state.py (49 lines)
  L12 def test_paid_is_terminal
  L15 def test_allowed_transitions
  L23 def test_no_show_only_from_confirmed
  L28 def test_cancel_is_allowed_from_non_terminal_states
  L43 def test_cancel_not_allowed_from_paid
  L47 def test_invalid_transition_raises

## packages/domain/tests/test_reliability.py (40 lines)
  L8 def _booking
  L22 def test_reliability_empty_returns_zero
  L26 def test_reliability_completed_only
  L34 def test_reliability_mixed_outcomes


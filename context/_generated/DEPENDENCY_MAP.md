# Dependency Map

Generated: 2026-08-26 14:49:34
Format: <- means 'imports from'

## apps/api/alembic/env.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/001_create_bookings.py
  <- __future__
  <- alembic
  <- packages.domain.src.booking_state
  <- sqlalchemy

## apps/api/alembic/versions/002_create_core_tables.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/003_create_users_table.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/004_add_workers_needed_to_shifts.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/005_add_shift_templates.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/006_add_messages.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/007_add_application_message_history.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/008_add_integrity_constraints.py
  <- __future__
  <- alembic

## apps/api/alembic/versions/009_add_worker_feed_state.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/020_time_money_deletion_integrity.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/021_organisation_venue_separation.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/022_markets_and_worker_feed_indexes.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/023_secure_rating_identity.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/024_operational_recovery.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/025_transactional_outbox.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/026_auth_session_version.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/027_account_privacy_and_reports.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/028_direct_payment_attestation.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/alembic/versions/029_idempotency_records.py
  <- __future__
  <- alembic
  <- sqlalchemy

## apps/api/scripts/create_dev_accounts.py
  <- __future__
  <- apps.api.src.auth.password
  <- apps.api.src.db.database
  <- apps.api.src.db.models

## apps/api/scripts/prepare_demo_accounts.py
  <- __future__
  <- apps.api.src.auth.password
  <- apps.api.src.config
  <- apps.api.src.db.database
  <- apps.api.src.db.models
  <- sqlalchemy.orm

## apps/api/scripts/seed_demo_data.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.models

## apps/api/src/api_errors.py
  <- __future__
  <- fastapi
  <- fastapi.exceptions
  <- fastapi.responses
  <- slowapi.errors

## apps/api/src/auth.py
  <- __future__
  <- fastapi

## apps/api/src/auth/__init__.py
  <- apps.api.src.auth.dependencies
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password

## apps/api/src/auth/dependencies.py
  <- apps.api.src.auth.jwt
  <- apps.api.src.config
  <- apps.api.src.deps
  <- apps.api.src.models.user
  <- apps.api.src.repositories.organisation_repository
  <- apps.api.src.repositories.user_repository
  <- fastapi
  <- fastapi.security

## apps/api/src/auth/jwt.py
  <- apps.api.src.auth.token_denylist
  <- apps.api.src.config
  <- jose

## apps/api/src/auth/password.py
  <- passlib.context

## apps/api/src/auth/schemas.py
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/config.py
  <- __future__
  <- dotenv

## apps/api/src/datetime_utils.py
  <- __future__

## apps/api/src/db/database.py
  <- __future__
  <- apps.api.src.config
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/db/idempotency_models.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.types
  <- sqlalchemy

## apps/api/src/db/models.py
  <- __future__
  <- sqlalchemy

## apps/api/src/db/notification_models.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.types
  <- sqlalchemy

## apps/api/src/db/schema_guard.py
  <- __future__
  <- alembic.config
  <- alembic.script
  <- apps.api.src.config
  <- sqlalchemy

## apps/api/src/db/tenancy_models.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.types
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/db/trust_models.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.types
  <- sqlalchemy

## apps/api/src/db/types.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- sqlalchemy
  <- sqlalchemy.engine
  <- sqlalchemy.types

## apps/api/src/deps.py
  <- __future__
  <- apps.api.src.repositories.application_decision_repository
  <- apps.api.src.repositories.application_message_history_repository
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.market_repository
  <- apps.api.src.repositories.message_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.template_repository
  <- apps.api.src.repositories.worker_feed_query_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.repository_dependencies
  <- fastapi

## apps/api/src/helpers.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.schemas
  <- fastapi

## apps/api/src/jobs/run_no_show_sweep.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.database
  <- apps.api.src.repositories.sqlalchemy_booking_repository

## apps/api/src/jobs/run_outbox_dispatch.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.services.health
  <- apps.api.src.services.outbox_dispatcher

## apps/api/src/main.py
  <- __future__
  <- apps.api.src.api_errors
  <- fastapi
  <- fastapi.exceptions
  <- fastapi.middleware.cors
  <- fastapi.responses
  <- fastapi.staticfiles
  <- slowapi.errors
  <- slowapi.middleware

## apps/api/src/models/account.py
  <- __future__
  <- apps.api.src.services.notification_preferences

## apps/api/src/models/application.py
  <- __future__

## apps/api/src/models/application_message_history.py
  <- __future__

## apps/api/src/models/message.py
  <- __future__
  <- pydantic

## apps/api/src/models/notification.py
  <- __future__

## apps/api/src/models/organisation.py
  <- __future__
  <- apps.api.src.services.notification_preferences

## apps/api/src/models/rating.py
  <- __future__

## apps/api/src/models/report.py
  <- __future__

## apps/api/src/models/shift.py
  <- __future__

## apps/api/src/models/shift_template.py
  <- __future__
  <- pydantic

## apps/api/src/models/user.py
  <- __future__

## apps/api/src/models/worker_feed_query.py
  <- __future__
  <- apps.api.src.models.organisation
  <- apps.api.src.models.shift

## apps/api/src/models/worker_feed_state.py
  <- __future__
  <- pydantic

## apps/api/src/models/worker_profile.py
  <- __future__

## apps/api/src/money.py
  <- __future__

## apps/api/src/observability.py
  <- __future__
  <- apps.api.src.config

## apps/api/src/repositories/account_repository.py
  <- __future__
  <- apps.api.src.models.account

## apps/api/src/repositories/application_decision_repository.py
  <- __future__
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- packages.domain.src.booking

## apps/api/src/repositories/application_message_history_repository.py
  <- __future__
  <- apps.api.src.models.application_message_history

## apps/api/src/repositories/application_repository.py
  <- __future__
  <- apps.api.src.models.application

## apps/api/src/repositories/booking_repository.py
  <- __future__
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state

## apps/api/src/repositories/in_memory_account_repository.py
  <- __future__
  <- apps.api.src.models.account
  <- apps.api.src.repositories.account_repository

## apps/api/src/repositories/in_memory_application_decision_repository.py
  <- __future__
  <- apps.api.src.models.application
  <- apps.api.src.repositories.application_decision_repository
  <- threading

## apps/api/src/repositories/in_memory_application_message_history_repository.py
  <- __future__
  <- apps.api.src.models.application_message_history

## apps/api/src/repositories/in_memory_application_repository.py
  <- __future__
  <- apps.api.src.models.application
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.shift_repository

## apps/api/src/repositories/in_memory_booking_repository.py
  <- __future__
  <- apps.api.src.repositories.shift_repository
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state

## apps/api/src/repositories/in_memory_market_repository.py
  <- __future__
  <- apps.api.src.models.organisation

## apps/api/src/repositories/in_memory_message_repository.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.models.message

## apps/api/src/repositories/in_memory_notification_repository.py
  <- __future__
  <- apps.api.src.models.notification

## apps/api/src/repositories/in_memory_organisation_repository.py
  <- __future__
  <- apps.api.src.models.account
  <- apps.api.src.models.organisation
  <- apps.api.src.repositories.in_memory_account_repository
  <- apps.api.src.repositories.organisation_repository

## apps/api/src/repositories/in_memory_report_repository.py
  <- __future__
  <- apps.api.src.models.report

## apps/api/src/repositories/in_memory_shift_repository.py
  <- __future__
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.booking_repository

## apps/api/src/repositories/in_memory_template_repository.py
  <- __future__
  <- apps.api.src.models.shift_template

## apps/api/src/repositories/in_memory_user_repository.py
  <- __future__
  <- apps.api.src.models.user

## apps/api/src/repositories/in_memory_worker_feed_query_repository.py
  <- __future__
  <- apps.api.src.models.worker_feed_query
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_organisation_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_worker_feed_state_repository
  <- zoneinfo

## apps/api/src/repositories/in_memory_worker_feed_state_repository.py
  <- __future__
  <- apps.api.src.models.worker_feed_state

## apps/api/src/repositories/in_memory_worker_profile_repository.py
  <- __future__
  <- apps.api.src.models.worker_profile

## apps/api/src/repositories/market_repository.py
  <- __future__
  <- apps.api.src.models.organisation

## apps/api/src/repositories/message_repository.py
  <- __future__
  <- apps.api.src.models.message

## apps/api/src/repositories/notification_repository.py
  <- __future__
  <- apps.api.src.models.notification

## apps/api/src/repositories/organisation_repository.py
  <- __future__
  <- apps.api.src.models.organisation

## apps/api/src/repositories/rating_repository.py
  <- __future__
  <- apps.api.src.models.rating

## apps/api/src/repositories/report_repository.py
  <- __future__
  <- apps.api.src.models.report

## apps/api/src/repositories/shift_repository.py
  <- __future__
  <- apps.api.src.models.shift

## apps/api/src/repositories/sqlalchemy_account_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.account
  <- apps.api.src.repositories.account_repository
  <- apps.api.src.services.notification_preferences
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_application_decision_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.money
  <- apps.api.src.repositories.application_decision_repository
  <- sqlalchemy
  <- sqlalchemy.exc
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_application_message_history_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.application_message_history
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_application_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.application
  <- apps.api.src.repositories.application_repository
  <- sqlalchemy
  <- sqlalchemy.exc
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_booking_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_market_repository.py
  <- __future__
  <- apps.api.src.db.tenancy_models
  <- apps.api.src.models.organisation
  <- apps.api.src.money
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_message_repository.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.models
  <- apps.api.src.models.message
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_notification_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.notification
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_organisation_repository.py
  <- __future__
  <- apps.api.src.db.tenancy_models
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_rating_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.db.tenancy_models
  <- apps.api.src.models.rating
  <- apps.api.src.repositories.rating_repository
  <- sqlalchemy
  <- sqlalchemy.exc
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_report_repository.py
  <- __future__
  <- apps.api.src.db.trust_models
  <- apps.api.src.models.report
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_shift_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.shift
  <- apps.api.src.money
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_template_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.shift_template
  <- apps.api.src.money
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_user_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.user
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_worker_feed_query_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.db.tenancy_models
  <- apps.api.src.models.organisation
  <- apps.api.src.models.worker_feed_query
  <- apps.api.src.repositories.sqlalchemy_organisation_repository
  <- apps.api.src.repositories.sqlalchemy_shift_repository
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_worker_feed_state_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.worker_feed_state
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_worker_profile_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.worker_profile
  <- apps.api.src.money
  <- packages.domain.src.booking_state
  <- sqlalchemy.orm

## apps/api/src/repositories/template_repository.py
  <- __future__
  <- apps.api.src.models.shift_template

## apps/api/src/repositories/user_repository.py
  <- __future__
  <- apps.api.src.models.user

## apps/api/src/repositories/worker_feed_query_repository.py
  <- __future__
  <- apps.api.src.models.worker_feed_query

## apps/api/src/repositories/worker_feed_state_repository.py
  <- __future__
  <- apps.api.src.models.worker_feed_state

## apps/api/src/repositories/worker_profile_repository.py
  <- __future__
  <- apps.api.src.models.worker_profile

## apps/api/src/repository_dependencies.py
  <- __future__
  <- apps.api.src.config
  <- apps.api.src.db.database
  <- apps.api.src.repositories.account_repository
  <- apps.api.src.repositories.application_decision_repository
  <- apps.api.src.repositories.application_message_history_repository
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.in_memory_account_repository
  <- apps.api.src.repositories.in_memory_application_decision_repository
  <- apps.api.src.repositories.in_memory_application_message_history_repository
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_market_repository
  <- apps.api.src.repositories.in_memory_message_repository
  <- apps.api.src.repositories.in_memory_notification_repository
  <- apps.api.src.repositories.in_memory_organisation_repository
  <- apps.api.src.repositories.in_memory_report_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_template_repository
  <- apps.api.src.repositories.in_memory_user_repository
  <- apps.api.src.repositories.in_memory_worker_feed_query_repository
  <- apps.api.src.repositories.in_memory_worker_feed_state_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- apps.api.src.repositories.market_repository
  <- apps.api.src.repositories.message_repository
  <- apps.api.src.repositories.notification_repository
  <- apps.api.src.repositories.organisation_repository
  <- apps.api.src.repositories.rating_repository
  <- apps.api.src.repositories.report_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.sqlalchemy_account_repository
  <- apps.api.src.repositories.sqlalchemy_application_decision_repository
  <- apps.api.src.repositories.sqlalchemy_application_message_history_repository
  <- apps.api.src.repositories.sqlalchemy_application_repository
  <- apps.api.src.repositories.sqlalchemy_booking_repository
  <- apps.api.src.repositories.sqlalchemy_market_repository
  <- apps.api.src.repositories.sqlalchemy_message_repository
  <- apps.api.src.repositories.sqlalchemy_notification_repository
  <- apps.api.src.repositories.sqlalchemy_organisation_repository
  <- apps.api.src.repositories.sqlalchemy_rating_repository
  <- apps.api.src.repositories.sqlalchemy_report_repository
  <- apps.api.src.repositories.sqlalchemy_shift_repository
  <- apps.api.src.repositories.sqlalchemy_template_repository
  <- apps.api.src.repositories.sqlalchemy_user_repository
  <- apps.api.src.repositories.sqlalchemy_worker_feed_query_repository
  <- apps.api.src.repositories.sqlalchemy_worker_feed_state_repository
  <- apps.api.src.repositories.sqlalchemy_worker_profile_repository
  <- apps.api.src.repositories.template_repository
  <- apps.api.src.repositories.user_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.services.email
  <- apps.api.src.services.outbox_publisher
  <- fastapi
  <- sqlalchemy.orm

## apps/api/src/request_middleware.py
  <- __future__
  <- apps.api.src.config
  <- starlette.middleware.base
  <- starlette.requests
  <- starlette.responses

## apps/api/src/routes/accounts.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.models.account
  <- apps.api.src.repositories.account_repository
  <- apps.api.src.repositories.market_repository
  <- apps.api.src.repository_dependencies
  <- apps.api.src.schemas_account
  <- apps.api.src.services.notification_preferences
  <- apps.api.src.services.stored_upload
  <- apps.api.src.storage.object_storage
  <- apps.api.src.storage_dependencies
  <- apps.api.src.unit_of_work
  <- fastapi

## apps/api/src/routes/applications.py
  <- __future__
  <- apps.api.src.auth
  <- fastapi

## apps/api/src/routes/auth.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password
  <- apps.api.src.auth.schemas
  <- fastapi

## apps/api/src/routes/auth_account.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password
  <- apps.api.src.auth.schemas
  <- fastapi
  <- fastapi.security
  <- sqlalchemy.orm

## apps/api/src/routes/auth_password.py
  <- __future__
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password
  <- apps.api.src.auth.schemas
  <- fastapi
  <- jose

## apps/api/src/routes/bookings.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- fastapi

## apps/api/src/routes/markets.py
  <- __future__
  <- apps.api.src.deps
  <- apps.api.src.repositories.market_repository
  <- apps.api.src.schemas_market
  <- fastapi

## apps/api/src/routes/messages.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.rate_limit
  <- apps.api.src.routes.service_errors
  <- apps.api.src.schemas
  <- apps.api.src.services.errors
  <- apps.api.src.services.idempotency
  <- apps.api.src.services.message_service
  <- fastapi

## apps/api/src/routes/notifications.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.repositories.notification_repository
  <- apps.api.src.schemas_notifications
  <- fastapi
  <- sqlalchemy.orm

## apps/api/src/routes/payments.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.config
  <- apps.api.src.money
  <- apps.api.src.validation_types
  <- fastapi
  <- pydantic

## apps/api/src/routes/ratings.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.datetime_utils
  <- apps.api.src.deps
  <- apps.api.src.models.rating
  <- apps.api.src.rate_limit
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.organisation_repository
  <- apps.api.src.repositories.rating_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas_ratings
  <- fastapi

## apps/api/src/routes/reports.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.datetime_utils
  <- apps.api.src.deps
  <- fastapi

## apps/api/src/routes/service_errors.py
  <- __future__
  <- apps.api.src.services.errors
  <- fastapi

## apps/api/src/routes/shifts.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.config
  <- apps.api.src.db.database
  <- apps.api.src.deps
  <- fastapi

## apps/api/src/routes/templates.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- apps.api.src.routes.service_errors
  <- apps.api.src.schemas
  <- fastapi

## apps/api/src/routes/tenancy.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.repositories.organisation_repository
  <- apps.api.src.schemas_tenancy
  <- fastapi

## apps/api/src/routes/uploads.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.rate_limit
  <- apps.api.src.repositories.account_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.repository_dependencies
  <- apps.api.src.schemas_uploads
  <- apps.api.src.services.stored_upload
  <- fastapi

## apps/api/src/routes/worker_feed.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- apps.api.src.routes.service_errors
  <- apps.api.src.schemas
  <- fastapi

## apps/api/src/routes/workers.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.datetime_utils
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- fastapi

## apps/api/src/scheduler.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apscheduler.schedulers.background

## apps/api/src/schemas.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_account.py
  <- __future__
  <- apps.api.src.services.notification_preferences
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_market.py
  <- __future__
  <- apps.api.src.models.organisation
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_notifications.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_privacy.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_ratings.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_recovery.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_reports.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_tenancy.py
  <- __future__
  <- apps.api.src.validation_types
  <- pydantic

## apps/api/src/schemas_uploads.py
  <- __future__
  <- pydantic

## apps/api/src/schemas_worker_feed.py
  <- __future__
  <- apps.api.src.schemas
  <- apps.api.src.schemas_market
  <- pydantic

## apps/api/src/services/account_privacy.py
  <- __future__
  <- apps.api.src.auth.password
  <- apps.api.src.db.models
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/services/application_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.models.application
  <- apps.api.src.models.application_message_history
  <- apps.api.src.repositories.application_decision_repository

## apps/api/src/services/booking_lifecycle_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.schemas
  <- apps.api.src.schemas_recovery
  <- apps.api.src.services.booking_ops
  <- apps.api.src.services.errors
  <- apps.api.src.services.outbox_publisher
  <- apps.api.src.services.recovery_notifications
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine

## apps/api/src/services/booking_ops.py
  <- __future__
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine
  <- packages.domain.src.reliability

## apps/api/src/services/errors.py
  <- __future__

## apps/api/src/services/expo_push.py
  <- __future__
  <- apps.api.src.config

## apps/api/src/services/geocoding.py
  <- __future__
  <- threading

## apps/api/src/services/health.py
  <- __future__
  <- apps.api.src.config
  <- apps.api.src.datetime_utils
  <- sqlalchemy

## apps/api/src/services/idempotency.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.idempotency_models
  <- sqlalchemy.exc
  <- sqlalchemy.orm

## apps/api/src/services/image_processing.py
  <- __future__
  <- fastapi
  <- PIL

## apps/api/src/services/message_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.models.message
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.message_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas
  <- apps.api.src.services.errors
  <- apps.api.src.services.outbox_publisher

## apps/api/src/services/notification_cursor.py
  <- __future__

## apps/api/src/services/notification_preferences.py
  <- __future__

## apps/api/src/services/notification_settings.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.notification_models
  <- sqlalchemy.orm

## apps/api/src/services/outbox_dispatcher.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.notification_models
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/services/outbox_publisher.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.notification_models
  <- apps.api.src.models.notification
  <- apps.api.src.repositories.notification_repository
  <- apps.api.src.services.email
  <- sqlalchemy.dialects.postgresql
  <- sqlalchemy.orm

## apps/api/src/services/outbox_recipients.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.db.notification_models
  <- apps.api.src.services.notification_settings
  <- sqlalchemy.orm

## apps/api/src/services/recovery_notifications.py
  <- __future__
  <- apps.api.src.services.outbox_publisher

## apps/api/src/services/report_access.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.message_repository
  <- apps.api.src.repositories.organisation_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.services.errors

## apps/api/src/services/shift_lifecycle_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas_recovery
  <- apps.api.src.services.errors
  <- apps.api.src.services.outbox_publisher
  <- apps.api.src.services.recovery_notifications
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine

## apps/api/src/services/shift_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas
  <- apps.api.src.services.errors

## apps/api/src/services/stored_upload.py
  <- __future__
  <- apps.api.src.storage.object_storage
  <- apps.api.src.unit_of_work
  <- starlette.concurrency

## apps/api/src/services/template_service.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.helpers
  <- apps.api.src.models.shift
  <- apps.api.src.models.shift_template
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.template_repository
  <- apps.api.src.schemas

## apps/api/src/services/upload_validation.py
  <- __future__
  <- apps.api.src.services.image_processing
  <- fastapi
  <- starlette.concurrency

## apps/api/src/services/worker_feed_cursor.py
  <- __future__
  <- apps.api.src.auth.jwt
  <- apps.api.src.datetime_utils
  <- apps.api.src.models.worker_feed_query

## apps/api/src/services/worker_feed_service.py
  <- __future__
  <- apps.api.src.helpers
  <- apps.api.src.models.worker_feed_state
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.worker_feed_state_repository
  <- apps.api.src.schemas
  <- apps.api.src.services.errors

## apps/api/src/services/worker_shift_feed_service.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.models.organisation
  <- apps.api.src.models.worker_feed_query
  <- apps.api.src.repositories.market_repository
  <- apps.api.src.repositories.worker_feed_query_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.services.worker_feed_cursor
  <- zoneinfo

## apps/api/src/storage/__init__.py
  <- apps.api.src.storage.object_storage

## apps/api/src/storage/config.py
  <- __future__
  <- apps.api.src.config

## apps/api/src/storage/local_object_storage.py
  <- __future__
  <- apps.api.src.storage.object_storage

## apps/api/src/storage/object_storage.py
  <- __future__

## apps/api/src/storage/s3_object_storage.py
  <- __future__
  <- apps.api.src.storage.object_storage

## apps/api/src/storage_dependencies.py
  <- __future__
  <- apps.api.src.storage.config
  <- apps.api.src.storage.local_object_storage
  <- apps.api.src.storage.object_storage
  <- apps.api.src.storage.s3_object_storage
  <- botocore.config

## apps/api/src/unit_of_work.py
  <- __future__
  <- sqlalchemy.orm

## apps/api/src/validation_types.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- pydantic

## apps/api/src/worker.py
  <- __future__
  <- apps.api.src.db.schema_guard
  <- apps.api.src.observability
  <- apps.api.src.scheduler
  <- signal
  <- threading
  <- types

## apps/api/tests/conftest.py
  <- __future__

## apps/api/tests/test_account_preferences.py
  <- __future__
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.account
  <- fastapi.testclient

## apps/api/tests/test_application_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- fastapi.testclient

## apps/api/tests/test_application_service_filters.py
  <- __future__
  <- apps.api.src.models.application
  <- apps.api.src.repositories.in_memory_application_decision_repository

## apps/api/tests/test_auth.py
  <- apps.api.src.auth.password
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_user_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient

## apps/api/tests/test_auth_startup_guard.py
  <- __future__
  <- subprocess

## apps/api/tests/test_booking_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_booking_repository
  <- fastapi.testclient
  <- packages.domain.src.booking

## apps/api/tests/test_config.py
  <- apps.api.src.config

## apps/api/tests/test_email_verification.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_account_repository
  <- apps.api.src.repositories.in_memory_user_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi
  <- fastapi.testclient

## apps/api/tests/test_health.py
  <- apps.api.src.main
  <- fastapi.testclient

## apps/api/tests/test_health_and_errors.py
  <- __future__
  <- apps.api.src.config
  <- apps.api.src.main
  <- fastapi.testclient

## apps/api/tests/test_idempotency.py
  <- __future__
  <- apps.api.src.config
  <- apps.api.src.main
  <- apps.api.src.services.idempotency
  <- apps.api.tests.test_postgres_flows
  <- fastapi.testclient

## apps/api/tests/test_image_processing.py
  <- __future__
  <- apps.api.src.services.image_processing
  <- fastapi
  <- PIL
  <- zlib

## apps/api/tests/test_message_endpoints.py
  <- apps.api.src
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_message_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- fastapi.testclient

## apps/api/tests/test_no_show_sweep_entrypoints.py
  <- __future__
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository

## apps/api/tests/test_no_show_sweep_service.py
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository

## apps/api/tests/test_notification_contract.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.notification
  <- apps.api.src.repositories.in_memory_notification_repository
  <- fastapi.testclient

## apps/api/tests/test_object_storage.py
  <- __future__
  <- apps.api.src.storage.local_object_storage
  <- apps.api.src.storage.s3_object_storage

## apps/api/tests/test_operator_invite_gating.py
  <- __future__
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.repositories.in_memory_account_repository
  <- apps.api.src.repositories.in_memory_organisation_repository
  <- apps.api.src.repositories.in_memory_user_repository
  <- fastapi.testclient

## apps/api/tests/test_outbox_dispatcher.py
  <- __future__
  <- apps.api.src.db
  <- apps.api.src.db.database
  <- apps.api.src.db.notification_models
  <- sqlalchemy
  <- sqlalchemy.orm
  <- sqlalchemy.pool

## apps/api/tests/test_password_reset_tokens.py
  <- __future__
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_notification_repository
  <- apps.api.src.repositories.in_memory_user_repository
  <- apps.api.src.services.email
  <- apps.api.src.services.outbox_publisher
  <- fastapi.testclient

## apps/api/tests/test_postgres_concurrency.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.repositories.application_decision_repository
  <- sqlalchemy
  <- threading

## apps/api/tests/test_postgres_flows.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.db.models
  <- fastapi.testclient
  <- sqlalchemy

## apps/api/tests/test_postgres_market_schema.py
  <- __future__
  <- apps.api.src.db.database
  <- sqlalchemy

## apps/api/tests/test_postgres_outbox.py
  <- __future__
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.notification_models
  <- fastapi.testclient
  <- sqlalchemy
  <- threading

## apps/api/tests/test_postgres_phase2a.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.db.models
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.sqlalchemy_shift_repository
  <- packages.domain.src.booking_state
  <- sqlalchemy
  <- sqlalchemy.exc

## apps/api/tests/test_postgres_ratings.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.db.tenancy_models
  <- apps.api.src.main
  <- fastapi.testclient
  <- packages.domain.src.booking_state

## apps/api/tests/test_postgres_recovery.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.db.models
  <- apps.api.src.deps
  <- apps.api.src.services.outbox_dispatcher
  <- apps.api.tests.test_postgres_flows
  <- fastapi.testclient
  <- sqlalchemy

## apps/api/tests/test_postgres_security_hardening.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.datetime_utils
  <- apps.api.src.db.idempotency_models
  <- apps.api.src.db.models
  <- apps.api.src.db.trust_models
  <- apps.api.src.services.idempotency
  <- apps.api.tests.test_postgres_flows
  <- fastapi.testclient
  <- sqlalchemy
  <- threading

## apps/api/tests/test_postgres_tenancy.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.db.models
  <- fastapi.testclient

## apps/api/tests/test_postgres_transactions.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.db.models
  <- apps.api.src.db.notification_models
  <- apps.api.src.repositories.sqlalchemy_market_repository
  <- apps.api.src.repositories.sqlalchemy_organisation_repository
  <- apps.api.src.repositories.sqlalchemy_user_repository
  <- fastapi.testclient
  <- sqlalchemy

## apps/api/tests/test_postgres_worker_feed_query.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.db.models
  <- apps.api.src.db.tenancy_models
  <- fastapi.testclient

## apps/api/tests/test_prepare_demo_accounts.py
  <- apps.api.scripts.prepare_demo_accounts
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/tests/test_recovery_endpoints.py
  <- __future__
  <- apps.api.src
  <- apps.api.src.deps
  <- fastapi.testclient

## apps/api/tests/test_red_team_security.py
  <- __future__
  <- apps.api.src.auth.dependencies
  <- apps.api.src.auth.jwt
  <- apps.api.src.config
  <- apps.api.src.main
  <- apps.api.tests.test_postgres_flows
  <- fastapi.testclient

## apps/api/tests/test_reliability_and_sweep.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient

## apps/api/tests/test_report_endpoints.py
  <- __future__
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.organisation
  <- apps.api.src.repositories.in_memory_organisation_repository
  <- apps.api.src.repositories.in_memory_report_repository
  <- fastapi.testclient

## apps/api/tests/test_shift_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_shift_repository
  <- fastapi.testclient

## apps/api/tests/test_sqlalchemy_repositories.py
  <- apps.api.src.db.models
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.sqlalchemy_application_decision_repository

## apps/api/tests/test_sqlite_migrations.py
  <- alembic
  <- alembic.config
  <- sqlalchemy

## apps/api/tests/test_storage_config.py
  <- __future__
  <- apps.api.src.storage.config

## apps/api/tests/test_template_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_template_repository
  <- fastapi.testclient

## apps/api/tests/test_token_revocation.py
  <- __future__
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.token_denylist
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.repositories.in_memory_user_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient
  <- jose

## apps/api/tests/test_unit_of_work_callbacks.py
  <- __future__
  <- apps.api.src.unit_of_work

## apps/api/tests/test_upload_endpoints.py
  <- __future__
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.account
  <- apps.api.src.models.worker_profile
  <- apps.api.src.storage.object_storage
  <- apps.api.src.storage_dependencies
  <- fastapi.testclient
  <- PIL

## apps/api/tests/test_user_repository.py
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_user_repository

## apps/api/tests/test_worker_feed_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_worker_feed_state_repository
  <- fastapi.testclient

## apps/api/tests/test_worker_profile_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient

## apps/api/tests/test_workers_needed.py
  <- apps.api.src.deps
  <- fastapi.testclient

## packages/domain/src/booking.py
  <- __future__
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine

## packages/domain/src/booking_state_machine.py
  <- __future__
  <- packages.domain.src.booking_state

## packages/domain/src/reliability.py
  <- __future__
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state

## packages/domain/tests/test_booking.py
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine

## packages/domain/tests/test_booking_state.py
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine

## packages/domain/tests/test_reliability.py
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- packages.domain.src.reliability


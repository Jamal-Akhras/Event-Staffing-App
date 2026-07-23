# Dependency Map

Generated: 2026-05-02 16:34:05
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

## apps/api/src/auth.py
  <- __future__
  <- fastapi

## apps/api/src/auth/__init__.py
  <- apps.api.src.auth.dependencies
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password

## apps/api/src/auth/dependencies.py
  <- apps.api.src.auth.jwt
  <- apps.api.src.deps
  <- apps.api.src.models.user
  <- apps.api.src.repositories.user_repository
  <- fastapi
  <- fastapi.security

## apps/api/src/auth/jwt.py
  <- jose

## apps/api/src/auth/password.py
  <- passlib.context

## apps/api/src/auth/schemas.py
  <- pydantic

## apps/api/src/db/database.py
  <- __future__
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/db/models.py
  <- __future__
  <- apps.api.src.db.database
  <- packages.domain.src.booking_state
  <- sqlalchemy

## apps/api/src/deps.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.sqlalchemy_booking_repository
  <- apps.api.src.repositories.worker_profile_repository

## apps/api/src/helpers.py
  <- __future__
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.application_repository
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- apps.api.src.schemas
  <- fastapi
  <- fastapi.security

## apps/api/src/jobs/run_no_show_sweep.py
  <- __future__
  <- apps.api.src.db.database
  <- apps.api.src.repositories.sqlalchemy_booking_repository

## apps/api/src/main.py
  <- __future__
  <- apps.api.src.routes
  <- fastapi
  <- fastapi.middleware.cors

## apps/api/src/models/application.py
  <- __future__

## apps/api/src/models/message.py
  <- __future__
  <- pydantic

## apps/api/src/models/shift.py
  <- __future__

## apps/api/src/models/shift_template.py
  <- __future__
  <- pydantic

## apps/api/src/models/user.py
  <- __future__

## apps/api/src/models/worker_profile.py
  <- __future__

## apps/api/src/repositories/application_repository.py
  <- __future__
  <- apps.api.src.models.application

## apps/api/src/repositories/booking_repository.py
  <- __future__
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state

## apps/api/src/repositories/in_memory_application_repository.py
  <- __future__
  <- apps.api.src.models.application

## apps/api/src/repositories/in_memory_booking_repository.py
  <- __future__
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state

## apps/api/src/repositories/in_memory_shift_repository.py
  <- __future__
  <- apps.api.src.models.shift

## apps/api/src/repositories/in_memory_user_repository.py
  <- __future__
  <- apps.api.src.models.user

## apps/api/src/repositories/in_memory_worker_profile_repository.py
  <- __future__
  <- apps.api.src.models.worker_profile

## apps/api/src/repositories/message_repository.py
  <- __future__
  <- apps.api.src.models.message

## apps/api/src/repositories/shift_repository.py
  <- __future__
  <- apps.api.src.models.shift

## apps/api/src/repositories/sqlalchemy_application_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.application
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_booking_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_message_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.message
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_shift_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.shift
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_template_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.shift_template
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_user_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.user
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/src/repositories/sqlalchemy_worker_profile_repository.py
  <- __future__
  <- apps.api.src.db.models
  <- apps.api.src.models.worker_profile
  <- sqlalchemy.orm

## apps/api/src/repositories/template_repository.py
  <- __future__
  <- apps.api.src.models.shift_template

## apps/api/src/repositories/user_repository.py
  <- __future__
  <- apps.api.src.models.user

## apps/api/src/repositories/worker_profile_repository.py
  <- __future__
  <- apps.api.src.models.worker_profile

## apps/api/src/routes/applications.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.db.database
  <- apps.api.src.db.models
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- fastapi

## apps/api/src/routes/auth.py
  <- __future__
  <- apps.api.src.auth.jwt
  <- apps.api.src.auth.password
  <- apps.api.src.auth.schemas
  <- apps.api.src.deps
  <- apps.api.src.models.user
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.user_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- fastapi

## apps/api/src/routes/bookings.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- fastapi

## apps/api/src/routes/messages.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- apps.api.src.models.message
  <- apps.api.src.repositories.message_repository
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas
  <- fastapi
  <- fastapi.security

## apps/api/src/routes/shifts.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- apps.api.src.models.shift
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.schemas
  <- fastapi

## apps/api/src/routes/templates.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- apps.api.src.models.shift
  <- apps.api.src.models.shift_template
  <- apps.api.src.repositories.shift_repository
  <- apps.api.src.repositories.template_repository
  <- apps.api.src.schemas
  <- fastapi
  <- fastapi.security

## apps/api/src/routes/workers.py
  <- __future__
  <- apps.api.src.auth
  <- apps.api.src.deps
  <- apps.api.src.helpers
  <- fastapi

## apps/api/src/schemas.py
  <- __future__
  <- pydantic

## apps/api/src/services/booking_ops.py
  <- __future__
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.booking_repository
  <- apps.api.src.repositories.worker_profile_repository
  <- packages.domain.src.booking
  <- packages.domain.src.booking_state
  <- packages.domain.src.booking_state_machine
  <- packages.domain.src.reliability

## apps/api/tests/test_application_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_shift_repository
  <- fastapi.testclient

## apps/api/tests/test_auth.py
  <- apps.api.src.auth.password
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_user_repository
  <- fastapi.testclient

## apps/api/tests/test_booking_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_booking_repository
  <- fastapi.testclient

## apps/api/tests/test_health.py
  <- apps.api.src.main
  <- fastapi.testclient

## apps/api/tests/test_no_show_sweep_service.py
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository

## apps/api/tests/test_reliability_and_sweep.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient

## apps/api/tests/test_shift_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_shift_repository
  <- fastapi.testclient

## apps/api/tests/test_sqlalchemy_repositories.py
  <- apps.api.src.db
  <- apps.api.src.db.database
  <- apps.api.src.models.application
  <- apps.api.src.models.shift
  <- apps.api.src.models.worker_profile
  <- apps.api.src.repositories.sqlalchemy_application_repository
  <- sqlalchemy
  <- sqlalchemy.orm

## apps/api/tests/test_user_repository.py
  <- apps.api.src.models.user
  <- apps.api.src.repositories.in_memory_user_repository

## apps/api/tests/test_worker_profile_endpoints.py
  <- apps.api.src
  <- apps.api.src.deps
  <- apps.api.src.repositories.in_memory_worker_profile_repository
  <- fastapi.testclient

## apps/api/tests/test_workers_needed.py
  <- apps.api.src.deps
  <- apps.api.src.main
  <- apps.api.src.repositories.in_memory_application_repository
  <- apps.api.src.repositories.in_memory_booking_repository
  <- apps.api.src.repositories.in_memory_shift_repository
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


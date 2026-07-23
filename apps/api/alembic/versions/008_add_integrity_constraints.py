from __future__ import annotations

from alembic import op

revision = "008_add_integrity_constraints"
down_revision = "007_message_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.create_check_constraint("ck_shifts_time_order", "end_time > start_time")
        batch.create_check_constraint("ck_shifts_pay_rate_nonnegative", "pay_rate >= 0")
        batch.create_check_constraint("ck_shifts_workers_needed_positive", "workers_needed >= 1")
        batch.create_check_constraint("ck_shifts_workers_filled_nonnegative", "workers_filled >= 0")
        batch.create_check_constraint("ck_shifts_capacity_bounds", "workers_filled <= workers_needed")

    with op.batch_alter_table("bookings") as batch:
        batch.create_foreign_key(
            "fk_bookings_shift_id_shifts",
            "shifts",
            ["shift_id"],
            ["shift_id"],
            ondelete="CASCADE",
        )
        batch.create_unique_constraint("uq_bookings_worker_shift", ["worker_id", "shift_id"])
        batch.create_check_constraint("ck_bookings_time_order", "end_time > start_time")
        batch.create_index("ix_bookings_shift_id", ["shift_id"])
        batch.create_index("ix_bookings_worker_id", ["worker_id"])

    with op.batch_alter_table("applications") as batch:
        batch.create_foreign_key(
            "fk_applications_shift_id_shifts",
            "shifts",
            ["shift_id"],
            ["shift_id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_applications_booking_id_bookings",
            "bookings",
            ["booking_id"],
            ["booking_id"],
            ondelete="SET NULL",
        )
        batch.create_unique_constraint("uq_applications_worker_shift", ["worker_id", "shift_id"])
        batch.create_check_constraint("ck_applications_time_order", "end_time > start_time")
        batch.create_check_constraint("ck_applications_status", "status IN ('applied', 'approved', 'rejected')")
        batch.create_index("ix_applications_shift_id", ["shift_id"])
        batch.create_index("ix_applications_worker_id", ["worker_id"])

    with op.batch_alter_table("worker_profiles") as batch:
        batch.create_check_constraint("ck_worker_profiles_experience_nonnegative", "experience_years >= 0")
        batch.create_check_constraint(
            "ck_worker_profiles_reliability_range",
            "reliability_score >= 0 AND reliability_score <= 1",
        )
        batch.create_check_constraint(
            "ck_worker_profiles_pay_rate_nonnegative",
            "pay_rate IS NULL OR pay_rate >= 0",
        )

    with op.batch_alter_table("shift_templates") as batch:
        batch.create_check_constraint("ck_shift_templates_duration_positive", "duration_hours > 0")
        batch.create_check_constraint("ck_shift_templates_pay_rate_nonnegative", "pay_rate >= 0")
        batch.create_check_constraint("ck_shift_templates_workers_needed_positive", "workers_needed >= 1")

    with op.batch_alter_table("recurring_schedules") as batch:
        batch.create_foreign_key(
            "fk_recurring_schedules_template_id_shift_templates",
            "shift_templates",
            ["template_id"],
            ["template_id"],
            ondelete="CASCADE",
        )
        batch.create_check_constraint("ck_recurring_schedules_frequency", "frequency IN ('daily', 'weekly', 'monthly')")
        batch.create_check_constraint(
            "ck_recurring_schedules_day_of_week",
            "day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6)",
        )
        batch.create_check_constraint("ck_recurring_schedules_date_order", "end_date IS NULL OR end_date >= start_date")
        batch.create_index("ix_recurring_schedules_template_id", ["template_id"])

    with op.batch_alter_table("messages") as batch:
        batch.create_foreign_key(
            "fk_messages_shift_id_shifts",
            "shifts",
            ["shift_id"],
            ["shift_id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_messages_application_id_applications",
            "applications",
            ["application_id"],
            ["application_id"],
            ondelete="CASCADE",
        )
        batch.create_foreign_key(
            "fk_messages_booking_id_bookings",
            "bookings",
            ["booking_id"],
            ["booking_id"],
            ondelete="CASCADE",
        )
        batch.create_check_constraint(
            "ck_messages_context_present",
            "application_id IS NOT NULL OR booking_id IS NOT NULL",
        )

    with op.batch_alter_table("application_message_history") as batch:
        batch.create_foreign_key(
            "fk_application_message_history_application_id_applications",
            "applications",
            ["application_id"],
            ["application_id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("application_message_history") as batch:
        batch.drop_constraint("fk_application_message_history_application_id_applications", type_="foreignkey")

    with op.batch_alter_table("messages") as batch:
        batch.drop_constraint("ck_messages_context_present", type_="check")
        batch.drop_constraint("fk_messages_booking_id_bookings", type_="foreignkey")
        batch.drop_constraint("fk_messages_application_id_applications", type_="foreignkey")
        batch.drop_constraint("fk_messages_shift_id_shifts", type_="foreignkey")

    with op.batch_alter_table("recurring_schedules") as batch:
        batch.drop_index("ix_recurring_schedules_template_id")
        batch.drop_constraint("ck_recurring_schedules_date_order", type_="check")
        batch.drop_constraint("ck_recurring_schedules_day_of_week", type_="check")
        batch.drop_constraint("ck_recurring_schedules_frequency", type_="check")
        batch.drop_constraint("fk_recurring_schedules_template_id_shift_templates", type_="foreignkey")

    with op.batch_alter_table("shift_templates") as batch:
        batch.drop_constraint("ck_shift_templates_workers_needed_positive", type_="check")
        batch.drop_constraint("ck_shift_templates_pay_rate_nonnegative", type_="check")
        batch.drop_constraint("ck_shift_templates_duration_positive", type_="check")

    with op.batch_alter_table("worker_profiles") as batch:
        batch.drop_constraint("ck_worker_profiles_pay_rate_nonnegative", type_="check")
        batch.drop_constraint("ck_worker_profiles_reliability_range", type_="check")
        batch.drop_constraint("ck_worker_profiles_experience_nonnegative", type_="check")

    with op.batch_alter_table("applications") as batch:
        batch.drop_index("ix_applications_worker_id")
        batch.drop_index("ix_applications_shift_id")
        batch.drop_constraint("ck_applications_status", type_="check")
        batch.drop_constraint("ck_applications_time_order", type_="check")
        batch.drop_constraint("uq_applications_worker_shift", type_="unique")
        batch.drop_constraint("fk_applications_booking_id_bookings", type_="foreignkey")
        batch.drop_constraint("fk_applications_shift_id_shifts", type_="foreignkey")

    with op.batch_alter_table("bookings") as batch:
        batch.drop_index("ix_bookings_worker_id")
        batch.drop_index("ix_bookings_shift_id")
        batch.drop_constraint("ck_bookings_time_order", type_="check")
        batch.drop_constraint("uq_bookings_worker_shift", type_="unique")
        batch.drop_constraint("fk_bookings_shift_id_shifts", type_="foreignkey")

    with op.batch_alter_table("shifts") as batch:
        batch.drop_constraint("ck_shifts_capacity_bounds", type_="check")
        batch.drop_constraint("ck_shifts_workers_filled_nonnegative", type_="check")
        batch.drop_constraint("ck_shifts_workers_needed_positive", type_="check")
        batch.drop_constraint("ck_shifts_pay_rate_nonnegative", type_="check")
        batch.drop_constraint("ck_shifts_time_order", type_="check")

from enum import Enum

class BookingState(str, Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED_BY_WORKER = "cancelled_by_worker"
    CANCELLED_BY_OPERATOR = "cancelled_by_operator"
    NO_SHOW = "no_show"

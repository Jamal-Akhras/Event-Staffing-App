from dataclasses import dataclass
from enum import Enum


class ActorRole(str, Enum):
    WORKER = "worker"
    OPERATOR = "operator"
    SYSTEM = "system"


@dataclass(frozen=True)
class ActorContext:
    user_id: str
    role: ActorRole
    account_id: str | None = None
    worker_profile_id: str | None = None
    organisation_id: str | None = None
    email_verified: bool = False
    membership_role: str | None = None
    venue_scope: tuple[str, ...] | None = None

    @property
    def effective_worker_id(self) -> str:
        return self.worker_profile_id or self.user_id

from __future__ import annotations

from typing import Protocol

from apps.api.src.models.manager_invitation import ManagerInvitation


class ManagerInvitationRepository(Protocol):
    def save(self, invitation: ManagerInvitation) -> ManagerInvitation:
        ...

    def get_by_token(self, token: str) -> ManagerInvitation | None:
        ...

    def list_for_organisation(self, organisation_id: str) -> list[ManagerInvitation]:
        ...

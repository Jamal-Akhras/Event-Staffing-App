from __future__ import annotations

from apps.api.src.models.manager_invitation import ManagerInvitation


class InMemoryManagerInvitationRepository:
    def __init__(self) -> None:
        self._items: dict[str, ManagerInvitation] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, invitation: ManagerInvitation) -> ManagerInvitation:
        self._items[invitation.invitation_id] = invitation
        return invitation

    def get_by_token(self, token: str) -> ManagerInvitation | None:
        for invitation in self._items.values():
            if invitation.token == token:
                return invitation
        return None

    def list_for_organisation(self, organisation_id: str) -> list[ManagerInvitation]:
        rows = [
            item for item in self._items.values() if item.organisation_id == organisation_id
        ]
        return sorted(rows, key=lambda item: item.created_at)

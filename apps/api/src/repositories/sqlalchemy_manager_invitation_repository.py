from __future__ import annotations

from dataclasses import fields

from sqlalchemy.orm import Session

from apps.api.src.db.tenancy_models import ManagerInvitationModel
from apps.api.src.models.manager_invitation import ManagerInvitation

_FIELDS = tuple(field.name for field in fields(ManagerInvitation))


class SqlAlchemyManagerInvitationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, invitation: ManagerInvitation) -> ManagerInvitation:
        model = self._session.get(ManagerInvitationModel, invitation.invitation_id)
        if model is None:
            model = ManagerInvitationModel(invitation_id=invitation.invitation_id)
            self._session.add(model)
        for name in _FIELDS:
            value = getattr(invitation, name)
            if name == "venue_scope" and value is not None:
                value = list(value)
            setattr(model, name, value)
        self._session.flush()
        return invitation

    def get_by_token(self, token: str) -> ManagerInvitation | None:
        row = (
            self._session.query(ManagerInvitationModel)
            .filter(ManagerInvitationModel.token == token)
            .one_or_none()
        )
        return _to_domain(row) if row is not None else None

    def list_for_organisation(self, organisation_id: str) -> list[ManagerInvitation]:
        rows = (
            self._session.query(ManagerInvitationModel)
            .filter(ManagerInvitationModel.organisation_id == organisation_id)
            .order_by(ManagerInvitationModel.created_at)
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: ManagerInvitationModel) -> ManagerInvitation:
    values = {name: getattr(model, name) for name in _FIELDS}
    if values["venue_scope"] is not None:
        values["venue_scope"] = tuple(values["venue_scope"])
    return ManagerInvitation(**values)

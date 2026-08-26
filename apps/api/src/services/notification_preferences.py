from __future__ import annotations

from typing import Literal

NotificationPreferenceKey = Literal["new_applications", "shift_reminders", "no_show_alerts"]
NotificationPreferences = dict[NotificationPreferenceKey, bool]

DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
    "new_applications": True,
    "shift_reminders": True,
    "no_show_alerts": True,
}


def default_notification_preferences() -> NotificationPreferences:
    return dict(DEFAULT_NOTIFICATION_PREFERENCES)


def normalize_notification_preferences(raw: object | None) -> NotificationPreferences:
    preferences = default_notification_preferences()
    if not isinstance(raw, dict):
        return preferences
    for key in preferences:
        value = raw.get(key)
        if isinstance(value, bool):
            preferences[key] = value
    return preferences

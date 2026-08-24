import type { NotificationAction } from "./notificationsApi";

export function notificationActionPath(action: NotificationAction | null): string | null {
  if (!action) return null;
  switch (action.kind) {
    case "shift":
      return `/app/shifts?shift_id=${encodeURIComponent(action.entity_id)}`;
    case "application":
      return `/app/applications?application_id=${encodeURIComponent(action.entity_id)}`;
    case "booking":
      return `/app/schedule?booking_id=${encodeURIComponent(action.entity_id)}`;
    case "messages":
      return `/app/applications?application_id=${encodeURIComponent(action.entity_id)}&open=messages`;
    default:
      return null;
  }
}

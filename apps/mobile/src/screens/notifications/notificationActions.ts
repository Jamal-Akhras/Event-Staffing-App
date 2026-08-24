import type { NotificationAction } from "../../lib/notifications";
import type {
  BrowseNotificationParams,
  ShiftsNotificationParams,
} from "../../navigation/navigationTypes";

export type NotificationTarget =
  | { tab: "Browse"; params: BrowseNotificationParams }
  | { tab: "Shifts"; params: ShiftsNotificationParams };

export function notificationActionTarget(
  action: NotificationAction | null,
  notificationKey: string
): NotificationTarget | null {
  if (!action) return null;
  switch (action.kind) {
    case "shift":
      return {
        tab: "Browse",
        params: { shift_id: action.entity_id, notification_key: notificationKey },
      };
    case "application":
      return {
        tab: "Shifts",
        params: {
          focus: "applications",
          application_id: action.entity_id,
          notification_key: notificationKey,
        },
      };
    case "booking":
      return {
        tab: "Shifts",
        params: {
          focus: "upcoming",
          booking_id: action.entity_id,
          notification_key: notificationKey,
        },
      };
    case "messages":
      return {
        tab: "Shifts",
        params: {
          focus: "applications",
          open: "messages",
          application_id: action.entity_id,
          notification_key: notificationKey,
        },
      };
    default:
      return null;
  }
}

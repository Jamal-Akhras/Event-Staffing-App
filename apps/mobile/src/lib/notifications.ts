import { deleteWorker, fetchWorker, postWorker, putWorker } from "./api";

export type NotificationActionKind = "shift" | "application" | "booking" | "messages";

export type NotificationAction = {
  kind: NotificationActionKind;
  entity_id: string;
};

export type AppNotification = {
  notification_id: string;
  type: string;
  title: string;
  body: string;
  action: NotificationAction | null;
  read: boolean;
  created_at: string;
};

export type NotificationsPage = {
  items: AppNotification[];
  next_cursor: string | null;
  unread_count: number;
};

export type NotificationChannels = {
  in_app: boolean;
  email: boolean;
  push: boolean;
};

export type NotificationCategories = {
  applications: boolean;
  shift_changes: boolean;
  messages: boolean;
  reminders: boolean;
  attendance: boolean;
};

export type NotificationPreferences = {
  channels: NotificationChannels;
  categories: NotificationCategories;
};

export type PushTokenRegistration = {
  token: string;
  platform: "ios" | "android";
  device_id: string;
};

const PAGE_LIMIT = 50;

export function fetchNotificationsPage(cursor: string | null): Promise<NotificationsPage> {
  const params = [`limit=${PAGE_LIMIT}`];
  if (cursor) params.push(`cursor=${encodeURIComponent(cursor)}`);
  return fetchWorker<NotificationsPage>(`/notifications?${params.join("&")}`);
}

export function markNotificationRead(notificationId: string): Promise<void> {
  return postWorker(`/notifications/${notificationId}/read`);
}

export function markAllNotificationsRead(): Promise<void> {
  return postWorker("/notifications/read-all");
}

export function fetchNotificationPreferences(): Promise<NotificationPreferences> {
  return fetchWorker<NotificationPreferences>("/notification-preferences");
}

export function saveNotificationPreferences(
  preferences: NotificationPreferences
): Promise<NotificationPreferences> {
  return putWorker<NotificationPreferences>("/notification-preferences", preferences);
}

export function registerPushToken(registration: PushTokenRegistration): Promise<{ push_token_id: string }> {
  return postWorker<{ push_token_id: string }>("/devices/push-tokens", registration);
}

export function unregisterPushToken(pushTokenId: string): Promise<void> {
  return deleteWorker(`/devices/push-tokens/${encodeURIComponent(pushTokenId)}`);
}

import { createNavigationContainerRef } from "@react-navigation/native";

import type { NotificationTarget } from "../screens/notifications/notificationActions";
import type { RootTabParamList } from "./navigationTypes";

export const navigationRef = createNavigationContainerRef<RootTabParamList>();

let pendingTarget: NotificationTarget | null = null;

export function navigateToNotificationTarget(target: NotificationTarget): void {
  if (!navigationRef.isReady()) {
    pendingTarget = target;
    return;
  }
  if (target.tab === "Browse") {
    navigationRef.navigate("Browse", target.params);
  } else {
    navigationRef.navigate("Shifts", target.params);
  }
}

export function flushPendingNotificationTarget(): void {
  if (!pendingTarget) return;
  const target = pendingTarget;
  pendingTarget = null;
  navigateToNotificationTarget(target);
}

import * as Notifications from "expo-notifications";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import type { NotificationAction } from "../lib/notifications";
import {
  remotePushRuntimeSupported,
  syncPushRegistration,
  type PushRegistrationStatus,
} from "../lib/pushRegistration";
import { navigateToNotificationTarget } from "../navigation/navigationRef";
import { notificationActionTarget } from "../screens/notifications/notificationActions";
import { useNotifications } from "./NotificationContext";

type PushNotificationContextType = {
  status: PushRegistrationStatus;
  message: string;
  enable: () => Promise<void>;
  retry: () => Promise<void>;
};

const PushNotificationContext = createContext<PushNotificationContextType | null>(null);

export function PushNotificationProvider({ children }: { children: React.ReactNode }) {
  const inbox = useNotifications();
  const [status, setStatus] = useState<PushRegistrationStatus>("checking");
  const [message, setMessage] = useState("Checking device notification access…");
  const handledResponseIds = useRef(new Set<string>());

  const sync = useCallback(async (requestPermission: boolean) => {
    setStatus(requestPermission ? "registering" : "checking");
    try {
      const result = await syncPushRegistration(requestPermission);
      setStatus(result.status);
      setMessage(result.message);
    } catch (error) {
      setStatus("error");
      setMessage((error as Error).message);
    }
  }, []);

  useEffect(() => {
    void sync(false);
    const tokenSubscription = remotePushRuntimeSupported()
      ? Notifications.addPushTokenListener(() => void sync(false))
      : null;
    const receivedSubscription = Notifications.addNotificationReceivedListener(
      () => void inbox.refresh()
    );
    const responseSubscription = Notifications.addNotificationResponseReceivedListener(
      handleNotificationResponse
    );
    void Notifications.getLastNotificationResponseAsync().then((response) => {
      if (!response) return;
      handleNotificationResponse(response);
      void Notifications.clearLastNotificationResponseAsync();
    });
    return () => {
      tokenSubscription?.remove();
      receivedSubscription.remove();
      responseSubscription.remove();
    };
  }, [inbox.refresh, sync]);

  const enable = useCallback(() => sync(true), [sync]);
  const retry = useCallback(() => sync(false), [sync]);

  return (
    <PushNotificationContext.Provider value={{ status, message, enable, retry }}>
      {children}
    </PushNotificationContext.Provider>
  );

  function handleNotificationResponse(response: Notifications.NotificationResponse): void {
    const responseId = response.notification.request.identifier;
    if (handledResponseIds.current.has(responseId)) return;
    handledResponseIds.current.add(responseId);
    const action = parseNotificationAction(response.notification.request.content.data);
    const target = notificationActionTarget(action, responseId);
    if (target) navigateToNotificationTarget(target);
    void inbox.refresh();
  }
}

export function usePushNotifications(): PushNotificationContextType {
  const context = useContext(PushNotificationContext);
  if (!context) throw new Error("usePushNotifications must be used within PushNotificationProvider");
  return context;
}

function parseNotificationAction(data: Record<string, unknown>): NotificationAction | null {
  const kind = data.kind;
  const entityId = data.entity_id;
  if (
    (kind === "shift" || kind === "application" || kind === "booking" || kind === "messages") &&
    typeof entityId === "string" &&
    entityId.length > 0
  ) {
    return { kind, entity_id: entityId };
  }
  return null;
}

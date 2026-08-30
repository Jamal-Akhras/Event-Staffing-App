import * as Device from "expo-device";
import Constants, { ExecutionEnvironment } from "expo-constants";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import { registerPushToken, unregisterPushToken } from "./notifications";
import { deleteItem, getItem, setItem } from "./secureStorage";

const DEVICE_ID_KEY = "push_device_id";
const PUSH_TOKEN_ID_KEY = "push_token_id";
const DEFAULT_CHANNEL_ID = "shift-updates";

export type PushRegistrationStatus =
  | "checking"
  | "available"
  | "registering"
  | "registered"
  | "denied"
  | "not-configured"
  | "unsupported"
  | "error";

export type PushRegistrationResult = {
  status: Exclude<PushRegistrationStatus, "checking" | "registering">;
  message: string;
};

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function syncPushRegistration(
  requestPermission: boolean
): Promise<PushRegistrationResult> {
  if (Platform.OS !== "ios" && Platform.OS !== "android") {
    return { status: "unsupported", message: "Push notifications require iOS or Android." };
  }
  if (!remotePushRuntimeSupported()) {
    return {
      status: "unsupported",
      message: "Android push notifications require a development or release build.",
    };
  }

  const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
  if (!projectId) {
    return {
      status: "not-configured",
      message: "Push will activate after this app is linked to its Expo project.",
    };
  }

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync(DEFAULT_CHANNEL_ID, {
      name: "Shift updates",
      description: "Applications, messages, bookings and shift changes",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 180, 120, 180],
    });
  }

  let permission = await Notifications.getPermissionsAsync();
  if (!permissionGranted(permission) && requestPermission && permission.canAskAgain) {
    permission = await Notifications.requestPermissionsAsync();
  }
  if (!permissionGranted(permission)) {
    if (!permission.canAskAgain) await unregisterStoredPushDevice();
    return permission.canAskAgain
      ? { status: "available", message: "Turn on device alerts when you're ready." }
      : { status: "denied", message: "Device alerts are disabled in system settings." };
  }

  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
  const deviceId = await getInstallationId();
  const saved = await registerPushToken({ token, platform: Platform.OS, device_id: deviceId });
  await setItem(PUSH_TOKEN_ID_KEY, saved.push_token_id);
  const deviceLabel = Device.modelName?.trim() || "this device";
  return { status: "registered", message: `Alerts are active on ${deviceLabel}.` };
}

export function remotePushRuntimeSupported(): boolean {
  return !(
    Platform.OS === "android" &&
    Constants.executionEnvironment === ExecutionEnvironment.StoreClient
  );
}

export async function unregisterStoredPushDevice(): Promise<void> {
  const pushTokenId = await getItem(PUSH_TOKEN_ID_KEY);
  if (!pushTokenId) return;
  try {
    await unregisterPushToken(pushTokenId);
  } finally {
    await deleteItem(PUSH_TOKEN_ID_KEY);
  }
}

function permissionGranted(permission: Notifications.NotificationPermissionsStatus): boolean {
  return (
    permission.granted ||
    permission.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL ||
    permission.ios?.status === Notifications.IosAuthorizationStatus.EPHEMERAL
  );
}

async function getInstallationId(): Promise<string> {
  const stored = await getItem(DEVICE_ID_KEY);
  if (stored) return stored;
  const generated = `device-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`;
  await setItem(DEVICE_ID_KEY, generated);
  return generated;
}

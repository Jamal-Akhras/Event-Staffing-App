import { Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { usePushNotifications } from "../../contexts/PushNotificationContext";
import type { PushRegistrationStatus } from "../../lib/pushRegistration";
import { COLORS } from "../../theme/colors";

export function PushDeviceStatusCard() {
  const { status, message, enable, retry } = usePushNotifications();
  const busy = status === "checking" || status === "registering";
  const action = getAction(status, enable, retry);

  return (
    <View style={[styles.card, status === "registered" && styles.cardReady]}>
      <View style={[styles.indicator, status === "registered" && styles.indicatorReady]} />
      <View style={styles.copy}>
        <Text style={styles.title}>This device</Text>
        <Text style={styles.message}>{message}</Text>
      </View>
      {action && (
        <Pressable
          accessibilityRole="button"
          disabled={busy}
          style={[styles.button, busy && styles.buttonDisabled]}
          onPress={() => void action.run()}
        >
          <Text style={styles.buttonText}>{action.label}</Text>
        </Pressable>
      )}
    </View>
  );
}

function getAction(
  status: PushRegistrationStatus,
  onEnable: () => Promise<void>,
  onRetry: () => Promise<void>
): { label: string; run: () => Promise<void> } | null {
  if (status === "available") return { label: "Enable", run: onEnable };
  if (status === "denied") return { label: "Settings", run: Linking.openSettings };
  if (status === "error") return { label: "Retry", run: onRetry };
  return null;
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surfaceMuted,
  },
  cardReady: { borderColor: "rgba(14,90,58,0.22)", backgroundColor: "rgba(14,90,58,0.05)" },
  indicator: { width: 8, height: 8, borderRadius: 99, backgroundColor: COLORS.inkSubtle },
  indicatorReady: { backgroundColor: COLORS.primary },
  copy: { flex: 1 },
  title: { color: COLORS.ink, fontSize: 13, fontWeight: "800" },
  message: { color: COLORS.inkMuted, fontSize: 11, lineHeight: 16, marginTop: 2 },
  button: {
    minHeight: 36,
    justifyContent: "center",
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: COLORS.primary,
  },
  buttonDisabled: { opacity: 0.55 },
  buttonText: { color: COLORS.onPrimary, fontSize: 12, fontWeight: "800" },
});

import { Pressable, StyleSheet, Text, View } from "react-native";

import type { AppNotification } from "../../lib/notifications";
import { COLORS } from "../../theme/colors";

type NotificationBannerProps = {
  notifications: AppNotification[];
  onDismiss: () => void;
};

export function NotificationBanner({ notifications, onDismiss }: NotificationBannerProps) {
  return (
    <View style={styles.banner}>
      <View style={styles.header}>
        <Text style={styles.title}>
          {notifications.length} new update{notifications.length > 1 ? "s" : ""}
        </Text>
        <Pressable onPress={onDismiss} hitSlop={8} accessibilityRole="button">
          <Text style={styles.dismiss}>Mark all read</Text>
        </Pressable>
      </View>
      {notifications.slice(0, 3).map((notification) => (
        <View key={notification.notification_id} style={styles.row}>
          <Text style={styles.dot}>•</Text>
          <View style={styles.copy}>
            <Text style={styles.notificationTitle}>{notification.title}</Text>
            <Text style={styles.body}>{notification.body}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    marginBottom: 14,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(14,90,58,0.18)",
    backgroundColor: "rgba(14,90,58,0.05)",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  title: { color: COLORS.primary, fontWeight: "800", fontSize: 13 },
  dismiss: { color: COLORS.primary, fontWeight: "600", fontSize: 12 },
  row: { flexDirection: "row", gap: 10, marginBottom: 6, alignItems: "flex-start" },
  dot: { color: COLORS.primary, fontWeight: "800", fontSize: 16 },
  copy: { flex: 1 },
  notificationTitle: { color: COLORS.ink, fontWeight: "700", fontSize: 13 },
  body: { color: COLORS.inkMuted, fontSize: 12, marginTop: 1 },
});

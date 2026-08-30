import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useNotifications } from "../contexts/NotificationContext";
import { COLORS } from "../theme/colors";

export function NotificationBell() {
  const navigation = useNavigation<{ navigate: (screen: "Alerts") => void }>();
  const { unreadCount } = useNotifications();
  const label = unreadCount > 99 ? "99+" : String(unreadCount);

  return (
    <Pressable
      style={styles.button}
      onPress={() => navigation.navigate("Alerts")}
      accessibilityRole="button"
      accessibilityLabel={
        unreadCount > 0 ? `Notifications, ${unreadCount} unread` : "Notifications"
      }
    >
      <Ionicons
        name={unreadCount > 0 ? "notifications" : "notifications-outline"}
        size={22}
        color={COLORS.ink}
      />
      {unreadCount > 0 && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{label}</Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  badge: {
    position: "absolute",
    top: 2,
    right: 10,
    minWidth: 18,
    height: 18,
    paddingHorizontal: 4,
    borderRadius: 9,
    backgroundColor: COLORS.error,
    alignItems: "center",
    justifyContent: "center",
  },
  badgeText: {
    color: COLORS.onPrimary,
    fontSize: 10,
    fontWeight: "800",
  },
});

import { useNavigation } from "@react-navigation/native";
import type { BottomTabNavigationProp } from "@react-navigation/bottom-tabs";
import { useCallback } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { EmptyState } from "../components/EmptyState";
import { SkeletonCard } from "../components/Skeleton";
import { useNotifications } from "../contexts/NotificationContext";
import type { AppNotification } from "../lib/notifications";
import type { RootTabParamList } from "../navigation/navigationTypes";
import { COLORS } from "../theme/colors";
import { notificationActionTarget } from "./notifications/notificationActions";

export function NotificationCenterScreen() {
  const navigation = useNavigation<BottomTabNavigationProp<RootTabParamList>>();
  const inbox = useNotifications();

  const openNotification = useCallback(
    (notification: AppNotification) => {
      inbox.markRead(notification.notification_id);
      const target = notificationActionTarget(notification.action, notification.notification_id);
      if (target) {
        if (target.tab === "Browse") navigation.navigate("Browse", target.params);
        else navigation.navigate("Shifts", target.params);
      }
    },
    [inbox, navigation]
  );

  const header = (
    <View style={styles.header}>
      <View style={styles.headerCopy}>
        <Text style={styles.eyebrow}>Stay in the loop</Text>
        <Text style={styles.title}>
          {inbox.unreadCount > 0 ? `${inbox.unreadCount} unread` : "All caught up"}
        </Text>
      </View>
      <Pressable
        style={[styles.markAllBtn, inbox.unreadCount === 0 && styles.markAllBtnDisabled]}
        disabled={inbox.unreadCount === 0}
        onPress={() => void inbox.markAllRead()}
        accessibilityRole="button"
        accessibilityLabel="Mark all notifications read"
      >
        <Text
          style={[styles.markAllText, inbox.unreadCount === 0 && styles.markAllTextDisabled]}
        >
          Mark all read
        </Text>
      </Pressable>
    </View>
  );

  const emptyComponent =
    inbox.status === "loading" ? (
      <View>
        <SkeletonCard lines={2} />
        <SkeletonCard lines={2} />
        <SkeletonCard lines={2} />
      </View>
    ) : inbox.status === "error" ? (
      <EmptyState
        title="Couldn't load notifications"
        message={inbox.error ?? "Something went wrong. Please try again."}
        actionLabel="Retry"
        onAction={() => void inbox.refresh()}
      />
    ) : (
      <EmptyState
        title="No notifications yet"
        message="Application decisions, shift changes and messages will appear here."
      />
    );

  return (
    <View style={styles.container}>
      <FlatList
        contentContainerStyle={styles.content}
        data={inbox.notifications}
        keyExtractor={(item) => item.notification_id}
        ListHeaderComponent={header}
        ListEmptyComponent={emptyComponent}
        ListFooterComponent={
          inbox.isLoadingMore ? (
            <ActivityIndicator color={COLORS.primary} style={styles.footerSpinner} />
          ) : null
        }
        onEndReached={() => void inbox.loadMore()}
        onEndReachedThreshold={0.4}
        refreshControl={
          <RefreshControl
            colors={[COLORS.primary]}
            refreshing={inbox.isRefreshing}
            tintColor={COLORS.primary}
            onRefresh={() => void inbox.refresh()}
          />
        }
        renderItem={({ item }) => (
          <NotificationRow notification={item} onPress={() => openNotification(item)} />
        )}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

function NotificationRow({
  notification,
  onPress,
}: {
  notification: AppNotification;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.row, !notification.read && styles.rowUnread]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${notification.read ? "" : "Unread. "}${notification.title}`}
    >
      <View style={[styles.dot, !notification.read && styles.dotUnread]} />
      <View style={styles.rowCopy}>
        <Text style={[styles.rowTitle, !notification.read && styles.rowTitleUnread]}>
          {notification.title}
        </Text>
        <Text style={styles.rowBody}>{notification.body}</Text>
        <Text style={styles.rowTime}>{formatWhen(notification.created_at)}</Text>
      </View>
    </Pressable>
  );
}

function formatWhen(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const minutes = Math.round((Date.now() - then) / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: 16, paddingBottom: 44 },
  header: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 16,
  },
  headerCopy: { flex: 1 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  markAllBtn: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  markAllBtnDisabled: { borderColor: COLORS.border },
  markAllText: { color: COLORS.primary, fontWeight: "800", fontSize: 13 },
  markAllTextDisabled: { color: COLORS.inkSubtle },
  row: {
    flexDirection: "row",
    gap: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
  },
  rowUnread: { borderColor: COLORS.primary, backgroundColor: "rgba(14,90,58,0.04)" },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 999,
    marginTop: 6,
    backgroundColor: COLORS.border,
  },
  dotUnread: { backgroundColor: COLORS.primary },
  rowCopy: { flex: 1, gap: 2 },
  rowTitle: { color: COLORS.ink, fontSize: 15, fontWeight: "600" },
  rowTitleUnread: { fontWeight: "800" },
  rowBody: { color: COLORS.inkMuted, fontSize: 13, lineHeight: 18 },
  rowTime: { color: COLORS.inkSubtle, fontSize: 11, fontWeight: "600", marginTop: 2 },
  footerSpinner: { marginVertical: 16 },
});

import { StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";

type StatusType =
  | "open"
  | "applied"
  | "approved"
  | "confirmed"
  | "checked_in"
  | "checked_out"
  | "completed"
  | "paid"
  | "cancelled"
  | "cancelled_by_worker"
  | "cancelled_by_operator"
  | "rejected"
  | "no_show";

type StatusBadgeProps = {
  status: string;
  size?: "small" | "medium";
};

const STATUS_CONFIG: Record<StatusType, { color: string; label: string }> = {
  open: { color: COLORS.success, label: "OPEN" },
  applied: { color: COLORS.warning, label: "APPLIED" },
  approved: { color: COLORS.success, label: "APPROVED" },
  confirmed: { color: COLORS.info, label: "CONFIRMED" },
  checked_in: { color: COLORS.info, label: "CHECKED IN" },
  checked_out: { color: COLORS.info, label: "CHECKED OUT" },
  completed: { color: COLORS.success, label: "COMPLETED" },
  paid: { color: COLORS.success, label: "PAID" },
  cancelled: { color: COLORS.error, label: "CANCELLED" },
  cancelled_by_worker: { color: COLORS.error, label: "CANCELLED" },
  cancelled_by_operator: { color: COLORS.error, label: "CANCELLED" },
  rejected: { color: COLORS.error, label: "REJECTED" },
  no_show: { color: COLORS.error, label: "NO SHOW" },
};

export function StatusBadge({ status, size = "medium" }: StatusBadgeProps) {
  const config =
    STATUS_CONFIG[status as StatusType] ?? {
      color: COLORS.inkMuted,
      label: status.toUpperCase(),
    };
  const isSmall = size === "small";

  return (
    <View style={[styles.badge, isSmall && styles.badgeSmall]}>
      <View style={[styles.dot, { backgroundColor: config.color }]} />
      <Text style={[styles.label, isSmall && styles.labelSmall]}>{config.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    height: 22,
    paddingHorizontal: 10,
    backgroundColor: COLORS.surfaceMuted,
    borderColor: COLORS.border,
    borderRadius: 999,
    borderWidth: 1,
  },
  badgeSmall: {
    height: 20,
    paddingHorizontal: 8,
  },
  dot: {
    width: 6,
    height: 6,
    marginRight: 6,
    borderRadius: 999,
  },
  label: {
    color: COLORS.ink,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },
  labelSmall: {
    fontSize: 9,
  },
});

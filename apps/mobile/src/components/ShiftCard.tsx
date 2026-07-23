import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";
import { formatMoney } from "../screens/earnings/earningsTypes";
import type { Shift } from "../types";
import { StatusBadge } from "./StatusBadge";

type ShiftCardProps = {
  shift: Shift;
  onPress?: () => void;
  compact?: boolean;
};

export function ShiftCard({ shift, onPress, compact = false }: ShiftCardProps) {
  const startDate = new Date(shift.start_time);
  const endDate = new Date(shift.end_time);
  const duration = Math.max(
    Math.round((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60)),
    0
  );
  const totalPay = shift.pay_rate * duration;
  const filled = shift.workers_filled ?? 0;
  const needed = shift.workers_needed ?? 1;
  const remaining = Math.max(needed - filled, 0);

  return (
    <Pressable
      style={({ pressed }) => [
        styles.card,
        compact && styles.cardCompact,
        pressed && styles.cardPressed,
      ]}
      onPress={onPress}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.payRate}>{formatMoney(shift.pay_rate, shift.currency)}/hr</Text>
          <Text style={styles.totalPay}>{formatMoney(totalPay, shift.currency)} estimated</Text>
        </View>
        <StatusBadge status={shift.status} size="small" />
      </View>

      <Text style={styles.role}>{shift.role}</Text>
      <Text style={styles.meta}>{shift.location}</Text>
      <Text style={styles.meta}>{formatShiftWindow(startDate, endDate)}</Text>

      {!compact && (
        <View style={styles.footer}>
          <View style={styles.capacityTrack}>
            <View style={[styles.capacityFill, { width: `${Math.min((filled / needed) * 100, 100)}%` }]} />
          </View>
          <Text style={styles.capacityText}>
            {remaining} {remaining === 1 ? "spot" : "spots"} left
          </Text>
        </View>
      )}
    </Pressable>
  );
}

function formatShiftWindow(startDate: Date, endDate: Date) {
  const date = startDate.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const start = startDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  const end = endDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} / ${start} - ${end}`;
}

const styles = StyleSheet.create({
  card: {
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    shadowColor: COLORS.ink,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 2,
  },
  cardCompact: {
    padding: 14,
  },
  cardPressed: {
    opacity: 0.82,
  },
  header: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  payRate: {
    color: COLORS.primary,
    fontSize: 24,
    fontWeight: "900",
  },
  totalPay: {
    color: COLORS.inkMuted,
    fontSize: 13,
  },
  role: {
    marginBottom: 5,
    color: COLORS.ink,
    fontSize: 18,
    fontWeight: "800",
  },
  meta: {
    marginTop: 2,
    color: COLORS.inkMuted,
    fontSize: 14,
  },
  footer: {
    marginTop: 14,
    gap: 8,
  },
  capacityTrack: {
    height: 6,
    overflow: "hidden",
    borderRadius: 999,
    backgroundColor: COLORS.border,
  },
  capacityFill: {
    height: "100%",
    borderRadius: 999,
    backgroundColor: COLORS.primary,
  },
  capacityText: {
    color: COLORS.inkMuted,
    fontSize: 12,
    fontWeight: "700",
  },
});

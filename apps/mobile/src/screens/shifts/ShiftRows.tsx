import { Pressable, StyleSheet, Text, View } from "react-native";

import { StatusBadge } from "../../components/StatusBadge";
import { COLORS } from "../../theme/colors";
import type { Application, Booking } from "../../types";
import { formatDateTime } from "./shiftsUtils";

type BookingRowProps = {
  booking: Booking;
  highlighted?: boolean;
  onSelect: () => void;
  onMessage?: () => void;
};

export function BookingRow({ booking, highlighted, onSelect, onMessage }: BookingRowProps) {
  return (
    <View style={[styles.row, highlighted && styles.rowHighlighted]}>
      <Pressable style={styles.rowBody} onPress={onSelect}>
        <Text style={styles.title}>{booking.shift_id}</Text>
        <Text style={styles.meta}>{formatDateTime(booking.start_time)}</Text>
        <StatusBadge status={booking.state} size="small" />
      </Pressable>
      {onMessage && (
        <Pressable style={styles.messageButton} onPress={onMessage}>
          <Text style={styles.messageText}>MSG</Text>
        </Pressable>
      )}
    </View>
  );
}

type ApplicationRowProps = {
  application: Application;
  highlighted?: boolean;
  onMessage: () => void;
  onWithdraw?: () => void;
};

export function ApplicationRow({ application, highlighted, onMessage, onWithdraw }: ApplicationRowProps) {
  return (
    <View style={[styles.row, highlighted && styles.rowHighlighted]}>
      <View style={styles.rowBody}>
        <Text style={styles.title}>{application.shift_id}</Text>
        <Text style={styles.meta}>{formatDateTime(application.created_at)}</Text>
        {application.message && (
          <Text style={styles.meta} numberOfLines={2}>
            "{application.message}"
          </Text>
        )}
        <StatusBadge status={application.status} size="small" />
      </View>
      <View style={styles.rowActions}>
        <Pressable style={styles.messageButton} onPress={onMessage}>
          <Text style={styles.messageText}>MSG</Text>
        </Pressable>
        {application.status === "applied" && onWithdraw && (
          <Pressable style={styles.withdrawButton} onPress={onWithdraw}>
            <Text style={styles.withdrawText}>Withdraw</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  rowHighlighted: { borderColor: COLORS.primary, backgroundColor: "rgba(14,90,58,0.05)" },
  rowBody: {
    flex: 1,
    gap: 5,
  },
  title: {
    color: COLORS.ink,
    fontSize: 16,
    fontWeight: "800",
  },
  meta: {
    color: COLORS.inkMuted,
    fontSize: 13,
  },
  messageButton: {
    alignItems: "center",
    justifyContent: "center",
    width: 48,
    height: 40,
    borderRadius: 12,
    backgroundColor: COLORS.surfaceMuted,
  },
  messageText: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "900",
  },
  rowActions: { alignItems: "stretch", gap: 6 },
  withdrawButton: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 34,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: "rgba(180, 35, 24, 0.08)",
  },
  withdrawText: { color: COLORS.error, fontSize: 10, fontWeight: "900" },
});

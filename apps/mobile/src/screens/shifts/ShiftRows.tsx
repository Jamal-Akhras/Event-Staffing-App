import { Pressable, StyleSheet, Text, View } from "react-native";

import { StatusBadge } from "../../components/StatusBadge";
import { COLORS } from "../../theme/colors";
import type { Application, Booking } from "../../types";
import { formatDateTime } from "./shiftsUtils";

type BookingRowProps = {
  booking: Booking;
  onSelect: () => void;
  onMessage?: () => void;
  onRate?: () => void;
};

export function BookingRow({ booking, onSelect, onMessage, onRate }: BookingRowProps) {
  return (
    <View style={styles.row}>
      <Pressable style={styles.rowBody} onPress={onSelect}>
        <Text style={styles.title}>{booking.shift_id}</Text>
        <Text style={styles.meta}>{formatDateTime(booking.start_time)}</Text>
        <StatusBadge status={booking.state} size="small" />
      </Pressable>
      {onRate && (
        <Pressable style={styles.rateButton} onPress={onRate}>
          <Text style={styles.rateText}>★</Text>
        </Pressable>
      )}
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
  onMessage: () => void;
};

export function ApplicationRow({ application, onMessage }: ApplicationRowProps) {
  return (
    <View style={styles.row}>
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
      <Pressable style={styles.messageButton} onPress={onMessage}>
        <Text style={styles.messageText}>MSG</Text>
      </Pressable>
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
  rateButton: {
    alignItems: "center",
    justifyContent: "center",
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "rgba(245,158,11,0.12)",
  },
  rateText: {
    color: "#F59E0B",
    fontSize: 18,
    fontWeight: "900",
  },
});

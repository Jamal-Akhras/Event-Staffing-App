import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import type { Booking } from "../../types";
import { formatDateTime, getCheckInWindow } from "./shiftsUtils";

type SelectedBookingPanelProps = {
  booking: Booking | null;
  error: string | null;
  onCheckIn: () => void;
  onCheckOut: () => void;
};

export function SelectedBookingPanel({
  booking,
  error,
  onCheckIn,
  onCheckOut,
}: SelectedBookingPanelProps) {
  const canCheckIn = booking?.allowed_transitions?.includes("checked_in") ?? false;
  const canCheckOut = booking?.allowed_transitions?.includes("checked_out") ?? false;

  return (
    <View style={styles.card}>
      <Text style={styles.label}>Action window</Text>
      {!booking ? (
        <Text style={styles.value}>No selected shift</Text>
      ) : (
        <>
          <Text style={styles.value}>{booking.state.replaceAll("_", " ")}</Text>
          <Text style={styles.meta}>{booking.shift_id}</Text>
          <Text style={styles.meta}>{formatDateTime(booking.start_time)}</Text>
          <Text style={styles.meta}>Check-in: {getCheckInWindow(booking)}</Text>
        </>
      )}
      {error && <Text style={styles.error}>{error}</Text>}
      <View style={styles.actions}>
        <ActionButton label="Check in" disabled={!canCheckIn} onPress={onCheckIn} />
        <ActionButton label="Check out" disabled={!canCheckOut} onPress={onCheckOut} />
      </View>
    </View>
  );
}

function ActionButton({
  label,
  disabled,
  onPress,
}: {
  label: string;
  disabled: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={[styles.button, disabled && styles.buttonDisabled]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 18,
    marginTop: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
  },
  label: {
    color: COLORS.primary,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  value: {
    marginTop: 8,
    color: COLORS.ink,
    fontSize: 22,
    fontWeight: "900",
    textTransform: "capitalize",
  },
  meta: {
    marginTop: 5,
    color: COLORS.inkMuted,
    fontSize: 13,
  },
  error: {
    marginTop: 8,
    color: COLORS.error,
    fontWeight: "700",
  },
  actions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14,
  },
  button: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 12,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonText: {
    color: COLORS.onPrimary,
    fontWeight: "900",
  },
});

import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { COLORS } from "../../theme/colors";
import type { Booking } from "../../types";
import { formatDateTime, getCheckInWindow } from "./shiftsUtils";

type SelectedBookingPanelProps = {
  booking: Booking | null;
  error: string | null;
  checkInCode: string;
  onCheckInCodeChange: (code: string) => void;
  onCheckIn: () => void;
  onCheckOut: () => void;
  onCancel: () => void;
};

export function SelectedBookingPanel({
  booking,
  error,
  checkInCode,
  onCheckInCodeChange,
  onCheckIn,
  onCheckOut,
  onCancel,
}: SelectedBookingPanelProps) {
  const canCheckIn = booking?.allowed_transitions.includes("checked_in") ?? false;
  const canCheckOut = booking?.allowed_transitions.includes("checked_out") ?? false;
  const canCancel = booking?.allowed_transitions.includes("cancelled_by_worker") ?? false;
  const showCompletionCode = booking?.completion_code && (booking.state === "checked_in" || booking.state === "checked_out");

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
      {canCheckIn && (
        <View style={styles.codeBlock}>
          <Text style={styles.codeLabel}>Venue check-in code</Text>
          <TextInput
            style={styles.codeInput}
            value={checkInCode}
            onChangeText={(value) => onCheckInCodeChange(value.replace(/\D/g, "").slice(0, 4))}
            keyboardType="number-pad"
            maxLength={4}
            placeholder="0000"
            placeholderTextColor={COLORS.inkMuted}
          />
          <Text style={styles.codeHint}>Ask the manager for the 4-digit code on their board.</Text>
        </View>
      )}
      {showCompletionCode && (
        <View style={styles.completion}>
          <Text style={styles.codeLabel}>Your completion code</Text>
          <Text style={styles.completionCode}>{booking?.completion_code}</Text>
          <Text style={styles.codeHint}>Show this to the manager when you finish so they can approve your hours.</Text>
        </View>
      )}
      {error && <Text style={styles.error}>{error}</Text>}
      <View style={styles.actions}>
        <ActionButton label="Check in" disabled={!canCheckIn || checkInCode.length !== 4} onPress={onCheckIn} />
        <ActionButton label="Check out" disabled={!canCheckOut} onPress={onCheckOut} />
      </View>
      {canCancel && (
        <Pressable style={styles.cancelButton} onPress={onCancel}>
          <Text style={styles.cancelText}>Cancel this booking</Text>
        </Pressable>
      )}
    </View>
  );
}

function ActionButton({ label, disabled, onPress }: { label: string; disabled: boolean; onPress: () => void }) {
  return (
    <Pressable style={[styles.button, disabled && styles.buttonDisabled]} onPress={onPress} disabled={disabled}>
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
  codeBlock: {
    marginTop: 14,
    gap: 6,
  },
  codeLabel: {
    color: COLORS.inkMuted,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  codeInput: {
    height: 52,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    paddingHorizontal: 16,
    backgroundColor: COLORS.canvas,
    color: COLORS.ink,
    fontSize: 24,
    fontWeight: "900",
    letterSpacing: 8,
  },
  codeHint: {
    color: COLORS.inkMuted,
    fontSize: 12,
    lineHeight: 17,
  },
  completion: {
    marginTop: 14,
    padding: 14,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
    gap: 4,
  },
  completionCode: {
    color: COLORS.onPrimary,
    fontSize: 34,
    fontWeight: "900",
    letterSpacing: 10,
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
  cancelButton: {
    alignItems: "center",
    marginTop: 10,
    paddingVertical: 11,
    borderRadius: 14,
    backgroundColor: "rgba(180, 35, 24, 0.08)",
  },
  cancelText: { color: COLORS.error, fontWeight: "900" },
});

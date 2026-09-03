import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { Money } from "../../components/Money";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { NUMERIC, TYPE } from "../../theme/type";
import type { Booking } from "../../types";
import { countdown, dayLabel, hoursRange, roleLine, shiftValue, venueName } from "./shiftLabels";

type NextShiftCardProps = {
  booking: Booking;
  now: Date;
  error: string | null;
  onCheckIn: (code: string) => void;
  onCheckOut: () => void;
  onMessage: () => void;
};

export function NextShiftCard({ booking, now, error, onCheckIn, onCheckOut, onMessage }: NextShiftCardProps) {
  const [entering, setEntering] = useState(false);
  const [code, setCode] = useState("");
  const value = shiftValue(booking);
  const onShift = booking.state === "checked_in";
  const eyebrow = onShift
    ? "On shift now"
    : [dayLabel(booking.start_time, now), countdown(booking.start_time, now)].filter(Boolean).join(" · ");

  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text style={styles.venue}>{venueName(booking.shift)}</Text>
      <Text style={styles.role}>{roleLine(booking.shift)}</Text>

      <View style={styles.split}>
        <View>
          <Text style={styles.label}>Hours</Text>
          <Text style={styles.figure}>{hoursRange(booking.start_time, booking.end_time)}</Text>
        </View>
        {value !== null && (
          <View style={styles.right}>
            <Text style={styles.label}>{onShift ? "Earning" : "You'll earn"}</Text>
            <Money amount={value} currency={booking.shift?.currency} style={styles.figure} />
          </View>
        )}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {onShift ? (
        <>
          {booking.completion_code && booking.check_in_requires_code !== false ? (
            <View style={styles.stub}>
              <Text style={styles.label}>Show to finish</Text>
              <Text style={styles.code}>{booking.completion_code}</Text>
            </View>
          ) : null}
          <Pressable style={styles.action} onPress={onCheckOut} accessibilityRole="button">
            <Text style={styles.actionText}>Finish shift</Text>
          </Pressable>
        </>
      ) : booking.check_in_requires_code === false ? (
        <Pressable style={styles.action} onPress={() => onCheckIn("")} accessibilityRole="button">
          <Text style={styles.actionText}>I'm here</Text>
        </Pressable>
      ) : entering ? (
        <>
          <Text style={styles.prompt}>Ask the manager for tonight's code</Text>
          <TextInput
            style={styles.input}
            value={code}
            onChangeText={setCode}
            keyboardType="number-pad"
            maxLength={4}
            autoFocus
            placeholder="0000"
            placeholderTextColor={COLORS.borderStrong}
            accessibilityLabel="Check-in code"
          />
          <Pressable
            style={[styles.action, code.length < 4 && styles.actionDisabled]}
            disabled={code.length < 4}
            onPress={() => onCheckIn(code)}
            accessibilityRole="button"
          >
            <Text style={styles.actionText}>Check in</Text>
          </Pressable>
        </>
      ) : (
        <Pressable style={styles.action} onPress={() => setEntering(true)} accessibilityRole="button">
          <Text style={styles.actionText}>I'm here</Text>
        </Pressable>
      )}

      <Pressable style={styles.link} onPress={onMessage} accessibilityRole="button">
        <Text style={styles.linkText}>Message venue</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s5,
  },
  eyebrow: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  venue: { ...TYPE.venue, color: COLORS.ink, marginTop: SPACE.s3 },
  role: { ...TYPE.body, color: COLORS.inkMuted, marginTop: 2 },
  split: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    marginTop: SPACE.s4,
    paddingTop: SPACE.s4,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  right: { alignItems: "flex-end" },
  label: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  figure: { ...TYPE.number, ...NUMERIC, color: COLORS.ink, marginTop: 4 },
  action: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3 + 2,
    alignItems: "center",
    marginTop: SPACE.s4,
  },
  actionDisabled: { opacity: 0.4 },
  actionText: { ...TYPE.action, color: COLORS.onPrimary },
  link: { alignItems: "center", marginTop: SPACE.s3 },
  linkText: { ...TYPE.meta, color: COLORS.inkMuted, textDecorationLine: "underline" },
  prompt: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: SPACE.s4, textAlign: "center" },
  input: {
    ...NUMERIC,
    marginTop: SPACE.s2,
    borderWidth: 1,
    borderColor: COLORS.borderStrong,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surfaceMuted,
    paddingVertical: SPACE.s3,
    textAlign: "center",
    fontSize: 26,
    letterSpacing: 10,
    color: COLORS.ink,
  },
  stub: {
    marginTop: SPACE.s4,
    paddingTop: SPACE.s4,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    borderStyle: "dashed",
    alignItems: "center",
  },
  code: { ...NUMERIC, fontSize: 34, letterSpacing: 12, color: COLORS.ink, marginTop: SPACE.s2 },
  error: { ...TYPE.meta, color: COLORS.error, marginTop: SPACE.s3 },
});

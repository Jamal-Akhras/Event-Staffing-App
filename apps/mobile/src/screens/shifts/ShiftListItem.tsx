import { Pressable, StyleSheet, Text, View } from "react-native";

import { Money } from "../../components/Money";
import { COLORS } from "../../theme/colors";
import { SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { Booking } from "../../types";
import { roleLine, shiftValue, venueName, whenLine } from "./shiftLabels";

type ShiftListItemProps = {
  booking: Booking;
  now: Date;
  onPress: () => void;
  trailing?: string;
  highlighted?: boolean;
};

export function ShiftListItem({ booking, now, onPress, trailing, highlighted }: ShiftListItemProps) {
  const value = shiftValue(booking);
  return (
    <Pressable style={styles.row} onPress={onPress} accessibilityRole="button">
      <View style={[styles.dot, highlighted && styles.dotAttention]} />
      <View style={styles.grow}>
        <Text style={styles.venue} numberOfLines={1}>{venueName(booking.shift)}</Text>
        <Text style={styles.meta} numberOfLines={1}>
          {booking.shift?.role ?? "Shift"} · {whenLine(booking.start_time, now)}
        </Text>
      </View>
      <View style={styles.trailing}>
        {value !== null && <Money amount={value} currency={booking.shift?.currency} />}
        {trailing ? <Text style={styles.state}>{trailing}</Text> : null}
      </View>
    </Pressable>
  );
}

export function PastShiftItem({ booking, onPress }: { booking: Booking; onPress: () => void }) {
  const value = shiftValue(booking);
  const settled = booking.state === "paid";
  return (
    <Pressable style={styles.row} onPress={onPress} accessibilityRole="button">
      <View style={styles.grow}>
        <Text style={styles.venue} numberOfLines={1}>{venueName(booking.shift)}</Text>
        <Text style={styles.meta} numberOfLines={1}>{roleLine(booking.shift)}</Text>
      </View>
      <View style={styles.trailing}>
        {value !== null && <Money amount={value} currency={booking.shift?.currency} />}
        <Text style={styles.state}>{settled ? "Paid" : "Awaiting"}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACE.s3,
    paddingVertical: SPACE.s3,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.primary },
  dotAttention: { backgroundColor: COLORS.warning },
  grow: { flex: 1, minWidth: 0 },
  venue: { ...TYPE.venueSmall, color: COLORS.ink },
  meta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 1 },
  trailing: { alignItems: "flex-end" },
  state: { ...TYPE.caption, color: COLORS.inkSubtle, marginTop: 1 },
});

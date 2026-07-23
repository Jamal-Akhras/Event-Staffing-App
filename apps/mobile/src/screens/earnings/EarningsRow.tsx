import { StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { formatEntryDate, formatMoney, type EarningsEntry } from "./earningsTypes";

type EarningsRowProps = {
  entry: EarningsEntry;
};

export function EarningsRow({ entry }: EarningsRowProps) {
  const isPaid = entry.status === "paid";
  return (
    <View style={styles.row}>
      <View style={[styles.marker, { backgroundColor: isPaid ? COLORS.success : COLORS.warning }]} />
      <View style={styles.body}>
        <Text style={styles.role}>{entry.role}</Text>
        <Text style={styles.meta}>
          {entry.location} / {entry.hours}h / {formatEntryDate(entry.start_time)}
        </Text>
      </View>
      <Text style={[styles.total, { color: isPaid ? COLORS.success : COLORS.warning }]}>
        {formatMoney(entry.total, entry.currency)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  marker: {
    width: 10,
    height: 40,
    borderRadius: 999,
  },
  body: {
    flex: 1,
  },
  role: {
    color: COLORS.ink,
    fontSize: 15,
    fontWeight: "800",
  },
  meta: {
    marginTop: 3,
    color: COLORS.inkMuted,
    fontSize: 13,
  },
  total: {
    fontSize: 16,
    fontWeight: "900",
  },
});

import { StyleSheet, Text, View } from "react-native";

import { Money } from "../../components/Money";
import { COLORS } from "../../theme/colors";
import { SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { EarningsEntry } from "./earningsTypes";

function shiftDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { weekday: "short", day: "numeric" });
}

export function EarningsEntryRow({ entry }: { entry: EarningsEntry }) {
  return (
    <View style={styles.row}>
      <View style={styles.grow}>
        <Text style={styles.venue} numberOfLines={1}>{entry.venue_name ?? entry.location}</Text>
        <Text style={styles.meta} numberOfLines={1}>
          {entry.role} · {shiftDate(entry.start_time)} · {entry.hours}h
        </Text>
      </View>
      <View style={styles.right}>
        <Money amount={entry.total} currency={entry.currency} />
        <Text style={styles.state}>{entry.status === "paid" ? "Paid" : "Awaiting"}</Text>
      </View>
    </View>
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
  grow: { flex: 1, minWidth: 0 },
  venue: { ...TYPE.venueSmall, color: COLORS.ink },
  meta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 1 },
  right: { alignItems: "flex-end" },
  state: { ...TYPE.caption, color: COLORS.inkSubtle, marginTop: 1 },
});

import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { Application } from "../../types";
import { hoursRange, roleLine, venueName, whenLine } from "../shifts/shiftLabels";

function appliedAgo(created: string, now: Date) {
  const minutes = Math.max(1, Math.round((now.getTime() - new Date(created).getTime()) / 60_000));
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return hours === 1 ? "1 hour ago" : `${hours} hours ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}

const DECIDED: Record<string, string> = {
  rejected: "Not this time",
  withdrawn: "You withdrew",
  approved: "Confirmed",
};

export function WaitingRow({
  application,
  now,
  onMessage,
  onWithdraw,
  highlighted,
}: {
  application: Application;
  now: Date;
  onMessage: () => void;
  onWithdraw: () => void;
  highlighted?: boolean;
}) {
  return (
    <View style={[styles.row, highlighted && styles.rowHighlighted]}>
      <View style={styles.dot} />
      <View style={styles.grow}>
        <Text style={styles.venue} numberOfLines={1}>{venueName(application.shift)}</Text>
        <Text style={styles.meta} numberOfLines={1}>
          {application.shift?.role ?? "Shift"} · {whenLine(application.start_time, now)}
        </Text>
        <Text style={styles.meta}>{hoursRange(application.start_time, application.end_time)}</Text>
        <View style={styles.actions}>
          <Pressable onPress={onMessage} accessibilityRole="button">
            <Text style={styles.link}>Message</Text>
          </Pressable>
          <Pressable onPress={onWithdraw} accessibilityRole="button">
            <Text style={styles.link}>Withdraw</Text>
          </Pressable>
        </View>
      </View>
      <Text style={styles.state}>Applied{"\n"}{appliedAgo(application.created_at, now)}</Text>
    </View>
  );
}

export function DecidedRow({ application }: { application: Application }) {
  return (
    <View style={styles.row}>
      <View style={styles.grow}>
        <Text style={[styles.venue, styles.faded]} numberOfLines={1}>{venueName(application.shift)}</Text>
        <Text style={styles.meta} numberOfLines={1}>{roleLine(application.shift)}</Text>
      </View>
      <Text style={styles.state}>{DECIDED[application.status] ?? application.status}</Text>
    </View>
  );
}

export function DecisionCard({ application, onView }: { application: Application; onView: () => void }) {
  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>{venueName(application.shift)} said yes</Text>
      <Text style={styles.cardTitle}>{roleLine(application.shift)}</Text>
      <Text style={styles.meta}>Moved to your upcoming shifts</Text>
      <Pressable onPress={onView} accessibilityRole="button">
        <Text style={[styles.link, styles.cardLink]}>View the shift</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: SPACE.s3,
    paddingVertical: SPACE.s3,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  rowHighlighted: { backgroundColor: COLORS.surfaceMuted },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.borderStrong, marginTop: 7 },
  grow: { flex: 1, minWidth: 0 },
  venue: { ...TYPE.venueSmall, color: COLORS.ink },
  faded: { color: COLORS.inkMuted },
  meta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 1 },
  actions: { flexDirection: "row", gap: SPACE.s4, marginTop: SPACE.s2 },
  link: { ...TYPE.meta, color: COLORS.inkMuted, textDecorationLine: "underline" },
  state: { ...TYPE.caption, color: COLORS.inkSubtle, textAlign: "right" },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s4,
  },
  eyebrow: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  cardTitle: { ...TYPE.venueSmall, color: COLORS.ink, marginTop: SPACE.s2 },
  cardLink: { marginTop: SPACE.s3 },
});

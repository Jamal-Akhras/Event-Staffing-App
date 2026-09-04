import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { StatusBadge } from "../../components/StatusBadge";
import { formatMoney } from "../earnings/earningsTypes";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { FeedShift } from "../../types";
import { formatShiftWindow, getShiftStats, getShiftTags } from "./browseUtils";

type BrowseFeedCardProps = {
  highPayThreshold?: number | null;
  isApplying: boolean;
  shift: FeedShift;
  onDetails: () => void;
  onPass: () => void;
  onQuickApply: () => void;
};

export function BrowseFeedCard({
  highPayThreshold,
  isApplying,
  shift,
  onDetails,
  onPass,
  onQuickApply,
}: BrowseFeedCardProps) {
  const stats = getShiftStats(shift);
  const tags = getShiftTags(shift, highPayThreshold);
  const venueName = shift.venue?.name?.trim();
  const placeLine = venueName && venueName !== shift.location
    ? `${venueName} · ${shift.location}`
    : venueName || shift.location;

  return (
    <View style={styles.card}>
      <Pressable
        onPress={onDetails}
        accessibilityRole="button"
        accessibilityLabel={`View details for ${shift.role} at ${shift.location}`}
      >
        <View style={styles.headerRow}>
          <View style={styles.headerCopy}>
            <Text style={styles.role} numberOfLines={1}>{shift.role}</Text>
            <Text style={styles.location} numberOfLines={1}>{placeLine}</Text>
            {shift.required_certification ? (
              <Text style={styles.requires}>Requires {shift.required_certification}</Text>
            ) : null}
            {shift.risk_information ? (
              <Text style={styles.requires} numberOfLines={2}>Safety: {shift.risk_information}</Text>
            ) : null}
          </View>
          <StatusBadge status={shift.status} size="small" />
        </View>

        <View style={styles.payRow}>
          <View>
            <Text style={styles.payRate}>{formatMoney(shift.pay_rate, shift.currency)}/hr</Text>
            <Text style={styles.totalPay}>{formatMoney(stats.totalPay, shift.currency)} est · {stats.durationHours}h</Text>
          </View>
          <Text style={styles.window}>{formatShiftWindow(shift)}</Text>
        </View>

        {tags.length > 0 && (
          <View style={styles.tags}>
            {tags.map((tag) => (
              <Text key={tag} style={styles.tag}>
                {tag}
              </Text>
            ))}
          </View>
        )}

        <View style={styles.capacityRow}>
          <View style={styles.capacityTrack}>
            <View style={[styles.capacityFill, { width: `${stats.capacityPct}%` }]} />
          </View>
          <Text style={styles.capacityText}>
            {stats.remaining} {stats.remaining === 1 ? "spot" : "spots"} left
          </Text>
        </View>
      </Pressable>

      <Pressable
        style={[styles.applyButton, isApplying && styles.disabledButton]}
        disabled={isApplying}
        onPress={onQuickApply}
        accessibilityRole="button"
        accessibilityLabel="Quick apply to this shift"
      >
        <Text style={styles.applyText}>{isApplying ? "Applying…" : "Quick apply"}</Text>
      </Pressable>

      <View style={styles.secondaryRow}>
        <Pressable
          style={styles.passButton}
          onPress={onPass}
          accessibilityRole="button"
          accessibilityLabel="Pass on this shift"
        >
          <Ionicons name="close" size={16} color={COLORS.inkSubtle} />
          <Text style={styles.passText}>Pass</Text>
        </Pressable>
        <Pressable
          style={styles.detailButton}
          onPress={onDetails}
          accessibilityRole="button"
          accessibilityLabel="View shift details"
        >
          <Text style={styles.detailText}>Details</Text>
          <Ionicons name="chevron-forward" size={16} color={COLORS.primary} />
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: SPACE.s4,
    marginBottom: SPACE.s3,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md + 2,
    backgroundColor: COLORS.surface,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: SPACE.s3,
    marginBottom: SPACE.s3,
  },
  headerCopy: { flex: 1, gap: 2 },
  role: { ...TYPE.section, color: COLORS.ink, fontSize: 18 },
  location: { ...TYPE.body, color: COLORS.inkMuted },
  requires: { ...TYPE.caption, color: COLORS.inkSubtle, marginTop: 2 },
  payRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    marginBottom: SPACE.s3,
  },
  payRate: { color: COLORS.primary, fontSize: 26, fontWeight: "800", letterSpacing: -0.3 },
  totalPay: { ...TYPE.caption, color: COLORS.inkMuted, marginTop: 2 },
  window: { ...TYPE.caption, color: COLORS.inkMuted, textAlign: "right" },
  tags: { flexDirection: "row", flexWrap: "wrap", gap: SPACE.s2, marginBottom: SPACE.s3 },
  tag: {
    paddingHorizontal: SPACE.s2,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.surfaceMuted,
    color: COLORS.inkMuted,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.4,
    textTransform: "uppercase",
  },
  capacityRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACE.s3,
    marginBottom: SPACE.s4,
  },
  capacityTrack: {
    flex: 1,
    height: 4,
    overflow: "hidden",
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.border,
  },
  capacityFill: {
    height: "100%",
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.primary,
  },
  capacityText: { ...TYPE.caption, color: COLORS.inkMuted, fontSize: 11 },
  applyButton: {
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: RADIUS.sm,
    backgroundColor: COLORS.primary,
  },
  disabledButton: { opacity: 0.6 },
  applyText: { color: COLORS.onPrimary, fontWeight: "800", fontSize: 15 },
  secondaryRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: SPACE.s2,
  },
  passButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    minHeight: 44,
    paddingHorizontal: SPACE.s2,
    justifyContent: "center",
  },
  detailButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    minHeight: 44,
    paddingHorizontal: SPACE.s2,
    justifyContent: "center",
  },
  passText: { color: COLORS.inkSubtle, fontWeight: "600", fontSize: 13 },
  detailText: { color: COLORS.primary, fontWeight: "700", fontSize: 13 },
});

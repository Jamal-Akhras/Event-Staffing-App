import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";

export function FeedStat({ label, value }: { label: string; value: number }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export function StatusCard({
  actionLabel,
  message,
  tone,
  onAction,
}: {
  actionLabel?: string;
  message: string;
  tone: "error" | "success";
  onAction?: () => void;
}) {
  return (
    <View style={[styles.statusCard, tone === "error" && styles.errorCard]}>
      <Text style={styles.statusText}>{message}</Text>
      {actionLabel && onAction && (
        <Pressable style={styles.statusAction} onPress={onAction}>
          <Text style={styles.statusActionText}>{actionLabel}</Text>
        </Pressable>
      )}
    </View>
  );
}

export function addShiftId(
  setter: (value: React.SetStateAction<Set<string>>) => void,
  shiftId: string
) {
  setter((current) => new Set(current).add(shiftId));
}

export function removeShiftId(
  setter: (value: React.SetStateAction<Set<string>>) => void,
  shiftId: string
) {
  setter((current) => {
    const next = new Set(current);
    next.delete(shiftId);
    return next;
  });
}

const styles = StyleSheet.create({
  statCard: {
    flex: 1,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  statValue: { color: COLORS.primary, fontSize: 22, fontWeight: "900" },
  statLabel: { color: COLORS.inkMuted, fontSize: 12, fontWeight: "800" },
  statusCard: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    marginBottom: 12,
  },
  errorCard: { backgroundColor: COLORS.error },
  statusText: { flex: 1, color: COLORS.onPrimary, fontWeight: "800" },
  statusAction: {
    minHeight: 34,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: COLORS.surface,
  },
  statusActionText: { color: COLORS.primary, fontWeight: "900" },
});

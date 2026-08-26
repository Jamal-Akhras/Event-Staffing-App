import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";

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

const styles = StyleSheet.create({
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

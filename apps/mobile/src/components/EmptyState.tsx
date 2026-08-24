import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";
import { RADIUS, SPACE } from "../theme/space";

type EmptyStateProps = {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ title, message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <View style={styles.card}>
      <View style={styles.mark}>
        <View style={styles.markInner} />
      </View>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
      {actionLabel && onAction && (
        <Pressable style={styles.actionBtn} onPress={onAction} accessibilityRole="button">
          <Text style={styles.actionText}>{actionLabel}</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    alignItems: "center",
    paddingVertical: SPACE.s7,
    paddingHorizontal: SPACE.s5,
    marginBottom: SPACE.s4,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md + 2,
    backgroundColor: COLORS.surface,
  },
  mark: {
    width: 48,
    height: 48,
    borderRadius: RADIUS.md,
    backgroundColor: "rgba(14,90,58,0.08)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: SPACE.s3,
  },
  markInner: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: COLORS.primary,
    opacity: 0.6,
  },
  title: {
    marginBottom: 6,
    color: COLORS.ink,
    fontSize: 16,
    fontWeight: "700",
    textAlign: "center",
  },
  message: {
    maxWidth: 280,
    color: COLORS.inkMuted,
    fontSize: 13,
    lineHeight: 19,
    textAlign: "center",
  },
  actionBtn: {
    marginTop: SPACE.s3,
    paddingHorizontal: SPACE.s4,
    paddingVertical: 10,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.primary,
  },
  actionText: { color: COLORS.onPrimary, fontWeight: "800", fontSize: 13 },
});

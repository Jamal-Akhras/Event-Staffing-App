import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";

type SettingsRowProps = {
  label: string;
  value?: string | null;
  onPress?: () => void;
  tone?: "default" | "danger";
};

export function SettingsRow({ label, value, onPress, tone = "default" }: SettingsRowProps) {
  return (
    <Pressable
      style={styles.row}
      onPress={onPress}
      disabled={!onPress}
      accessibilityRole={onPress ? "button" : "text"}
    >
      <Text style={[styles.label, tone === "danger" && styles.danger]}>{label}</Text>
      {value ? (
        <Text style={styles.value} numberOfLines={1}>
          {value}
        </Text>
      ) : null}
      {onPress ? <Text style={styles.chevron}>›</Text> : null}
    </Pressable>
  );
}

export function SettingsGroup({ children }: { children: React.ReactNode }) {
  return <View style={styles.group}>{children}</View>;
}

const styles = StyleSheet.create({
  group: { marginTop: SPACE.s2 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACE.s3,
    paddingVertical: SPACE.s4,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  label: { ...TYPE.body, fontSize: 15, color: COLORS.ink, flex: 1 },
  danger: { color: COLORS.error },
  value: { ...TYPE.meta, color: COLORS.inkSubtle, maxWidth: "50%" },
  chevron: { ...TYPE.body, color: COLORS.inkSubtle, fontSize: 20, lineHeight: 20 },
});

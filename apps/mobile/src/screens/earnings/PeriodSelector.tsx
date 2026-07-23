import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { PERIOD_LABELS, type Period } from "./earningsTypes";

type PeriodSelectorProps = {
  period: Period;
  onChange: (period: Period) => void;
};

export function PeriodSelector({ period, onChange }: PeriodSelectorProps) {
  return (
    <View style={styles.row}>
      {(["week", "month", "year"] as Period[]).map((item) => (
        <Pressable
          key={item}
          style={[styles.button, period === item && styles.buttonActive]}
          onPress={() => onChange(item)}
        >
          <Text style={[styles.text, period === item && styles.textActive]}>
            {PERIOD_LABELS[item]}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    gap: 6,
    padding: 4,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  button: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 10,
    borderRadius: 12,
  },
  buttonActive: {
    backgroundColor: COLORS.primary,
  },
  text: {
    color: COLORS.inkMuted,
    fontWeight: "800",
  },
  textActive: {
    color: COLORS.onPrimary,
  },
});

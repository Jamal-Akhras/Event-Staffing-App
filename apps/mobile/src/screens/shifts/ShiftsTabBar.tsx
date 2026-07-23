import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { SHIFT_TABS, type ShiftTab } from "./shiftsUtils";

type ShiftsTabBarProps = {
  activeTab: ShiftTab;
  onChange: (tab: ShiftTab) => void;
};

export function ShiftsTabBar({ activeTab, onChange }: ShiftsTabBarProps) {
  return (
    <View style={styles.tabs}>
      {SHIFT_TABS.map((tab) => (
        <Pressable
          key={tab.key}
          style={[styles.tab, activeTab === tab.key && styles.tabActive]}
          onPress={() => onChange(tab.key)}
        >
          <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
            {tab.label}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 16,
    padding: 4,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  tab: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 10,
    borderRadius: 12,
  },
  tabActive: {
    backgroundColor: COLORS.primary,
  },
  tabText: {
    color: COLORS.inkMuted,
    fontWeight: "800",
    fontSize: 12,
  },
  tabTextActive: {
    color: COLORS.onPrimary,
  },
});

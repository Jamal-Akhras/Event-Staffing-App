import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";
import { SPACE } from "../theme/space";
import { TYPE } from "../theme/type";

type SegmentedTabsProps<T extends string> = {
  tabs: { key: T; label: string }[];
  active: T;
  onChange: (key: T) => void;
};

const FIT_LIMIT = 3;

export function SegmentedTabs<T extends string>({ tabs, active, onChange }: SegmentedTabsProps<T>) {
  const buttons = tabs.map((tab) => {
    const on = tab.key === active;
    return (
      <Pressable
        key={tab.key}
        style={[styles.tab, tabs.length > FIT_LIMIT ? styles.tabScroll : styles.tabFit, on && styles.tabOn]}
        onPress={() => onChange(tab.key)}
        accessibilityRole="tab"
        accessibilityState={{ selected: on }}
      >
        <Text style={[styles.label, on && styles.labelOn]}>{tab.label}</Text>
      </Pressable>
    );
  });

  if (tabs.length > FIT_LIMIT) {
    return (
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.strip}
        contentContainerStyle={styles.stripContent}
      >
        {buttons}
      </ScrollView>
    );
  }

  return <View style={styles.row}>{buttons}</View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", borderBottomWidth: 1, borderBottomColor: COLORS.border },
  strip: { flexGrow: 0, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  stripContent: { paddingHorizontal: SPACE.s4 - 2, gap: SPACE.s5 },
  tab: {
    alignItems: "center",
    paddingBottom: SPACE.s3,
    borderBottomWidth: 2,
    borderBottomColor: "transparent",
    marginBottom: -1,
  },
  tabFit: { flex: 1 },
  tabScroll: { flexGrow: 0 },
  tabOn: { borderBottomColor: COLORS.primary },
  label: { ...TYPE.action, color: COLORS.inkSubtle },
  labelOn: { color: COLORS.ink },
});

import { StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";
import { SPACE } from "../theme/space";
import { TYPE } from "../theme/type";

export function SectionHeader({ title, count }: { title: string; count?: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.title}>{title}</Text>
      {count ? <Text style={styles.count}>{count}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    marginBottom: SPACE.s2,
  },
  title: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  count: { ...TYPE.eyebrow, color: COLORS.inkSubtle, letterSpacing: 1.1 },
});

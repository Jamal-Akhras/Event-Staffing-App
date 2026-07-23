import { useEffect, useRef } from "react";
import { Animated, StyleSheet, View, type ViewStyle } from "react-native";

import { COLORS } from "../theme/colors";
import { RADIUS, SPACE } from "../theme/space";

type SkeletonCardProps = {
  lines?: number;
  style?: ViewStyle;
};

export function SkeletonCard({ lines = 3, style }: SkeletonCardProps) {
  const opacity = useRef(new Animated.Value(0.5)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.5, duration: 700, useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [opacity]);

  return (
    <View style={[styles.card, style]}>
      <Animated.View style={[styles.block, styles.title, { opacity }]} />
      {Array.from({ length: lines }, (_, index) => (
        <Animated.View
          key={index}
          style={[
            styles.block,
            styles.line,
            index === lines - 1 ? styles.lineShort : null,
            { opacity },
          ]}
        />
      ))}
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
    gap: SPACE.s2,
  },
  block: {
    backgroundColor: COLORS.surfaceMuted,
    borderRadius: 6,
  },
  title: {
    height: 18,
    width: "55%",
    marginBottom: SPACE.s2,
  },
  line: {
    height: 10,
    width: "100%",
  },
  lineShort: {
    width: "70%",
  },
});

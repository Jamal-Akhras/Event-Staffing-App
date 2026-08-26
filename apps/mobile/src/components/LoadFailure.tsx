import { Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";

type LoadFailureProps = {
  message: string;
  onRetry: () => void;
};

export function LoadFailure({ message, onRetry }: LoadFailureProps) {
  return (
    <View style={loadStateStyles.stateBlock}>
      <Text style={loadStateStyles.errorText}>{message}</Text>
      <Pressable style={loadStateStyles.retryBtn} onPress={onRetry} accessibilityRole="button">
        <Text style={loadStateStyles.retryText}>Try again</Text>
      </Pressable>
    </View>
  );
}

export const loadStateStyles = StyleSheet.create({
  stateText: { color: COLORS.inkMuted, fontWeight: "600", fontSize: 13 },
  stateBlock: { gap: 8 },
  errorText: { color: COLORS.error, fontWeight: "700", fontSize: 13 },
  retryBtn: {
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  retryText: { color: COLORS.primary, fontWeight: "800", fontSize: 13 },
});

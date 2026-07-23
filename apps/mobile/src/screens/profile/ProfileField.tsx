import { StyleSheet, TextInput } from "react-native";

import { COLORS } from "../../theme/colors";

type ProfileFieldProps = {
  placeholder: string;
  value: string;
  onChangeText: (value: string) => void;
  keyboardType?: "default" | "email-address" | "numeric" | "phone-pad";
  multiline?: boolean;
};

export function ProfileField({
  placeholder,
  value,
  onChangeText,
  keyboardType = "default",
  multiline = false,
}: ProfileFieldProps) {
  return (
    <TextInput
      placeholder={placeholder}
      placeholderTextColor={COLORS.inkSubtle}
      value={value}
      onChangeText={onChangeText}
      style={[styles.input, multiline && styles.multiline]}
      keyboardType={keyboardType}
      multiline={multiline}
    />
  );
}

const styles = StyleSheet.create({
  input: {
    padding: 12,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surfaceMuted,
    color: COLORS.ink,
    fontSize: 14,
  },
  multiline: {
    minHeight: 78,
    textAlignVertical: "top",
  },
});

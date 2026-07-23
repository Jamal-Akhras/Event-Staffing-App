import { BottomSheetBackdrop, BottomSheetModal, BottomSheetView } from "@gorhom/bottom-sheet";
import type { BottomSheetBackdropProps } from "@gorhom/bottom-sheet";
import { forwardRef, useCallback, useMemo } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { NavigationLinks } from "../../components/NavigationLinks";
import { formatMoney } from "../earnings/earningsTypes";
import { COLORS } from "../../theme/colors";
import type { Shift } from "../../types";
import { formatShiftWindow } from "./browseUtils";

type ApplyPanelProps = {
  message: string;
  shift: Shift | null;
  onApply: () => void;
  onChangeMessage: (value: string) => void;
  onDismiss: () => void;
};

export const ApplyPanel = forwardRef<BottomSheetModal, ApplyPanelProps>(function ApplyPanel(
  { message, shift, onApply, onChangeMessage, onDismiss },
  ref,
) {
  const snapPoints = useMemo(() => ["55%", "90%"], []);

  const renderBackdrop = useCallback(
    (props: BottomSheetBackdropProps) => (
      <BottomSheetBackdrop {...props} appearsOnIndex={0} disappearsOnIndex={-1} pressBehavior="close" />
    ),
    [],
  );

  return (
    <BottomSheetModal
      ref={ref}
      snapPoints={snapPoints}
      backdropComponent={renderBackdrop}
      backgroundStyle={styles.sheetBackground}
      handleIndicatorStyle={styles.handleIndicator}
      onDismiss={onDismiss}
      keyboardBehavior="interactive"
      keyboardBlurBehavior="restore"
    >
      <BottomSheetView style={styles.content}>
        {shift && (
          <>
            <View style={styles.header}>
              <Text style={styles.title}>{shift.role}</Text>
              <Text style={styles.meta}>{shift.location}</Text>
              <Text style={styles.meta}>
                {formatShiftWindow(shift)} · {formatMoney(shift.pay_rate, shift.currency)}/hr
              </Text>
            </View>

            {shift.notes ? <Text style={styles.notes}>{shift.notes}</Text> : null}

            {shift.latitude != null && shift.longitude != null && (
              <NavigationLinks latitude={shift.latitude} longitude={shift.longitude} />
            )}

            <TextInput
              style={styles.messageInput}
              placeholder="Message to venue"
              placeholderTextColor={COLORS.inkSubtle}
              value={message}
              onChangeText={onChangeMessage}
              multiline
            />

            <Pressable style={styles.applyButton} onPress={onApply}>
              <Text style={styles.applyButtonText}>Send application</Text>
            </Pressable>
          </>
        )}
      </BottomSheetView>
    </BottomSheetModal>
  );
});

const styles = StyleSheet.create({
  sheetBackground: { backgroundColor: COLORS.surface },
  handleIndicator: { backgroundColor: COLORS.borderStrong, width: 44 },
  content: { paddingHorizontal: 20, paddingBottom: 24, gap: 14 },
  header: { gap: 4 },
  title: { color: COLORS.ink, fontSize: 24, fontWeight: "900" },
  meta: { color: COLORS.inkMuted },
  notes: { color: COLORS.inkMuted, lineHeight: 20 },
  messageInput: {
    minHeight: 96,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    color: COLORS.ink,
    textAlignVertical: "top",
  },
  applyButton: {
    alignItems: "center",
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
  },
  applyButtonText: { color: COLORS.onPrimary, fontSize: 16, fontWeight: "900" },
});

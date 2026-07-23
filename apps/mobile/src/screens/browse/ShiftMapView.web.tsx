import { useMemo } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { NavigationLinks } from "../../components/NavigationLinks";
import { COLORS } from "../../theme/colors";
import type { Shift } from "../../types";
import { formatMoney } from "../earnings/earningsTypes";
import { formatShiftWindow } from "./browseUtils";

type Props = {
  shifts: Shift[];
  onApply: (shift: Shift) => void;
};

export function ShiftMapView({ shifts, onApply }: Props) {
  const mappableShifts = useMemo(
    () => shifts.filter((shift) => shift.latitude != null && shift.longitude != null),
    [shifts],
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.notice}>
        <Text style={styles.noticeTitle}>Map preview is available on device</Text>
        <Text style={styles.noticeText}>
          Open this project in Expo Go to use the native map. Web preview shows shifts with saved coordinates.
        </Text>
      </View>

      {mappableShifts.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyTitle}>No shifts with location data yet.</Text>
          <Text style={styles.emptyText}>Newly posted shifts will appear here automatically.</Text>
        </View>
      ) : (
        mappableShifts.map((shift) => (
          <View key={shift.shift_id} style={styles.shiftCard}>
            <Text style={styles.role}>{shift.role}</Text>
            <Text style={styles.meta}>{shift.location}</Text>
            <Text style={styles.meta}>
              {formatShiftWindow(shift)} · {formatMoney(shift.pay_rate, shift.currency)}/hr
            </Text>
            <NavigationLinks latitude={shift.latitude as number} longitude={shift.longitude as number} />
            <Pressable style={styles.applyBtn} onPress={() => onApply(shift)}>
              <Text style={styles.applyBtnText}>Apply for this shift</Text>
            </Pressable>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: 16, paddingBottom: 32, gap: 12 },
  notice: {
    padding: 16,
    borderWidth: 1,
    borderColor: "rgba(14,90,58,0.18)",
    borderRadius: 16,
    backgroundColor: "rgba(14,90,58,0.06)",
  },
  noticeTitle: { color: COLORS.primary, fontSize: 16, fontWeight: "900" },
  noticeText: { color: COLORS.inkMuted, fontSize: 13, lineHeight: 19, marginTop: 4 },
  emptyCard: {
    alignItems: "center",
    padding: 18,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  emptyTitle: { color: COLORS.ink, fontSize: 15, fontWeight: "900" },
  emptyText: { color: COLORS.inkMuted, fontSize: 13, lineHeight: 19, marginTop: 4, textAlign: "center" },
  shiftCard: {
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
  },
  role: { color: COLORS.ink, fontSize: 20, fontWeight: "900" },
  meta: { color: COLORS.inkMuted, marginTop: 4, fontSize: 14 },
  applyBtn: {
    marginTop: 14,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
    alignItems: "center",
  },
  applyBtnText: { color: COLORS.onPrimary, fontWeight: "900", fontSize: 16 },
});

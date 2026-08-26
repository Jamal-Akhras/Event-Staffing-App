import { useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import MapView, { Marker, PROVIDER_DEFAULT } from "react-native-maps";

import { NavigationLinks } from "../../components/NavigationLinks";
import { COLORS } from "../../theme/colors";
import type { FeedShift } from "../../types";
import { formatMoney } from "../earnings/earningsTypes";
import { formatShiftWindow } from "./browseUtils";

type Props = {
  shifts: FeedShift[];
  onApply: (shift: FeedShift) => void;
};

type Region = {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
};

const LONDON: Region = {
  latitude: 51.5074,
  longitude: -0.1278,
  latitudeDelta: 0.12,
  longitudeDelta: 0.12,
};

export function ShiftMapView({ shifts, onApply }: Props) {
  const [selected, setSelected] = useState<FeedShift | null>(null);

  const mappableShifts = useMemo(
    () => shifts.filter((s) => s.latitude != null && s.longitude != null),
    [shifts]
  );

  const initialRegion = useMemo((): Region => {
    if (mappableShifts.length === 0) return LONDON;
    const lats = mappableShifts.map((s) => s.latitude as number);
    const lngs = mappableShifts.map((s) => s.longitude as number);
    const midLat = (Math.max(...lats) + Math.min(...lats)) / 2;
    const midLng = (Math.max(...lngs) + Math.min(...lngs)) / 2;
    const deltaLat = Math.max(Math.max(...lats) - Math.min(...lats), 0.05) * 1.4;
    const deltaLng = Math.max(Math.max(...lngs) - Math.min(...lngs), 0.05) * 1.4;
    return { latitude: midLat, longitude: midLng, latitudeDelta: deltaLat, longitudeDelta: deltaLng };
  }, [mappableShifts]);

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        provider={PROVIDER_DEFAULT}
        initialRegion={initialRegion}
      >
        {mappableShifts.map((shift) => (
          <Marker
            key={shift.shift_id}
            coordinate={{ latitude: shift.latitude as number, longitude: shift.longitude as number }}
            pinColor={selected?.shift_id === shift.shift_id ? COLORS.primary : "#e05c2a"}
            onPress={() => setSelected(shift)}
          />
        ))}
      </MapView>

      {mappableShifts.length === 0 && (
        <View style={styles.emptyOverlay}>
          <Text style={styles.emptyText}>No shifts with location data yet.</Text>
          <Text style={styles.emptySubtext}>Newly posted shifts will appear here automatically.</Text>
        </View>
      )}

      {selected && (
        <View style={styles.panel}>
          <View style={styles.panelHeader}>
            <View style={{ flex: 1 }}>
              <Text style={styles.panelRole}>{selected.role}</Text>
              <Text style={styles.panelMeta}>{selected.location}</Text>
              <Text style={styles.panelMeta}>
                {formatShiftWindow(selected)} · {formatMoney(selected.pay_rate, selected.currency)}/hr
              </Text>
            </View>
            <Pressable style={styles.closeBtn} onPress={() => setSelected(null)}>
              <Text style={styles.closeBtnText}>✕</Text>
            </Pressable>
          </View>

          <NavigationLinks latitude={selected.latitude as number} longitude={selected.longitude as number} />

          <Pressable style={styles.applyBtn} onPress={() => { onApply(selected); setSelected(null); }}>
            <Text style={styles.applyBtnText}>Apply for this shift</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  emptyOverlay: {
    position: "absolute",
    bottom: 120,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 16,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: "center",
  },
  emptyText: { color: COLORS.ink, fontWeight: "800", fontSize: 15 },
  emptySubtext: { color: COLORS.inkMuted, fontSize: 13, marginTop: 4, textAlign: "center" },
  panel: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    paddingBottom: 32,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderColor: COLORS.border,
  },
  panelHeader: { flexDirection: "row", alignItems: "flex-start", gap: 12 },
  panelRole: { color: COLORS.ink, fontSize: 20, fontWeight: "900" },
  panelMeta: { color: COLORS.inkMuted, marginTop: 3, fontSize: 14 },
  closeBtn: { padding: 6 },
  closeBtnText: { color: COLORS.inkMuted, fontSize: 18 },
  applyBtn: {
    marginTop: 14,
    paddingVertical: 14,
    borderRadius: 14,
    backgroundColor: COLORS.primary,
    alignItems: "center",
  },
  applyBtnText: { color: COLORS.onPrimary, fontWeight: "900", fontSize: 16 },
});

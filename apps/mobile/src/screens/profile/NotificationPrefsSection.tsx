import { useCallback, useEffect, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";

import { LoadFailure, loadStateStyles } from "../../components/LoadFailure";
import {
  fetchNotificationPreferences,
  saveNotificationPreferences,
  type NotificationPreferences,
} from "../../lib/notifications";
import { usePushNotifications } from "../../contexts/PushNotificationContext";
import { COLORS } from "../../theme/colors";
import { PushDeviceStatusCard } from "./PushDeviceStatusCard";

const CHANNEL_ROWS = [
  ["in_app", "In-app", "Alerts inside the app"],
  ["email", "Email", "A copy of important updates by email"],
  ["push", "Push", "Device alerts, active once push is enabled"],
] as const;

const CATEGORY_ROWS = [
  ["applications", "Applications", "Decisions on your applications"],
  ["shift_changes", "Shift changes", "Edits, closures and cancellations"],
  ["messages", "Messages", "New messages from venues"],
  ["reminders", "Reminders", "Upcoming shift reminders"],
  ["attendance", "Attendance", "Check-in and check-out updates"],
] as const;

export function NotificationPrefsSection() {
  const push = usePushNotifications();
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchNotificationPreferences()
      .then(setPrefs)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  const applyChange = (next: NotificationPreferences, previous: NotificationPreferences) => {
    if (saving) return;
    setSaving(true);
    setError(null);
    setPrefs(next);
    saveNotificationPreferences(next)
      .then(setPrefs)
      .catch((err: Error) => {
        setPrefs(previous);
        setError(err.message);
      })
      .finally(() => setSaving(false));
  };

  if (loading) {
    return <Text style={loadStateStyles.stateText}>Loading notification preferences…</Text>;
  }

  if (!prefs) {
    return (
      <LoadFailure message={error ?? "Couldn't load notification preferences."} onRetry={load} />
    );
  }

  return (
    <View style={styles.block}>
      {error && <Text style={loadStateStyles.errorText}>{error}</Text>}
      <Text style={styles.groupLabel}>Delivery</Text>
      {CHANNEL_ROWS.map(([key, label, desc]) => (
        <PrefRow
          key={key}
          desc={desc}
          label={label}
          disabled={saving}
          value={prefs.channels[key]}
          onChange={() => {
            if (key === "push" && !prefs.channels.push) void push.enable();
            applyChange(
              { ...prefs, channels: { ...prefs.channels, [key]: !prefs.channels[key] } },
              prefs
            );
          }}
        />
      ))}
      <PushDeviceStatusCard />
      <Text style={[styles.groupLabel, styles.groupLabelSpaced]}>Categories</Text>
      {CATEGORY_ROWS.map(([key, label, desc]) => (
        <PrefRow
          key={key}
          desc={desc}
          label={label}
          disabled={saving}
          value={prefs.categories[key]}
          onChange={() =>
            applyChange(
              { ...prefs, categories: { ...prefs.categories, [key]: !prefs.categories[key] } },
              prefs
            )
          }
        />
      ))}
    </View>
  );
}

function PrefRow({
  desc,
  label,
  disabled,
  value,
  onChange,
}: {
  desc: string;
  label: string;
  disabled: boolean;
  value: boolean;
  onChange: () => void;
}) {
  return (
    <View style={styles.row}>
      <View style={styles.rowCopy}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowDesc}>{desc}</Text>
      </View>
      <Switch
        disabled={disabled}
        value={value}
        onValueChange={onChange}
        trackColor={{ false: COLORS.border, true: COLORS.primary }}
        thumbColor="#fff"
        accessibilityLabel={`${label} notifications`}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: 10 },
  groupLabel: {
    color: COLORS.inkMuted,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.6,
    textTransform: "uppercase",
  },
  groupLabelSpaced: { marginTop: 10 },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  rowCopy: { flex: 1 },
  rowLabel: { color: COLORS.ink, fontSize: 15, fontWeight: "700" },
  rowDesc: { color: COLORS.inkMuted, fontSize: 12, marginTop: 1 },
});

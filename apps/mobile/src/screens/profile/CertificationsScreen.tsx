import { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { SectionHeader } from "../../components/SectionHeader";
import { deleteWorker, fetchWorker, putWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";

type Certification = {
  certification_id: string;
  name: string;
  display_name: string;
  expires_at: string;
  reference: string | null;
};

const MONTH_AHEAD = 30 * 24 * 60 * 60 * 1000;

export function CertificationsScreen() {
  const [items, setItems] = useState<Certification[]>([]);
  const [name, setName] = useState("");
  const [expiry, setExpiry] = useState("");
  const [reference, setReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setItems(await fetchWorker<Certification[]>("/me/certifications"));
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    const trimmed = name.trim();
    if (trimmed.length < 2) {
      setError("Name the certification first.");
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(expiry.trim())) {
      setError("Give the expiry as YYYY-MM-DD.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await putWorker(`/me/certifications/${encodeURIComponent(trimmed)}`, {
        display_name: trimmed,
        expires_at: `${expiry.trim()}T00:00:00Z`,
        reference: reference.trim() || null,
      });
      setName("");
      setExpiry("");
      setReference("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (item: Certification) => {
    setBusy(true);
    setError(null);
    try {
      await deleteWorker(`/me/certifications/${encodeURIComponent(item.name)}`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const now = Date.now();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.hint}>
        Some shifts need a current certification. Venues only see this when it blocks a booking.
      </Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}

      {items.length > 0 && (
        <View>
          <SectionHeader title="Yours" />
          {items.map((item) => {
            const expires = new Date(item.expires_at).getTime();
            const state =
              expires <= now ? "Expired" : expires - now < MONTH_AHEAD ? "Expiring soon" : null;
            return (
              <View key={item.certification_id} style={styles.row}>
                <View style={styles.grow}>
                  <Text style={styles.rowTitle}>{item.display_name}</Text>
                  <Text style={[styles.rowMeta, state ? styles.rowWarn : null]}>
                    {state ? `${state} · ` : ""}Until {item.expires_at.slice(0, 10)}
                    {item.reference ? ` · ${item.reference}` : ""}
                  </Text>
                </View>
                <Pressable
                  onPress={() => void remove(item)}
                  disabled={busy}
                  accessibilityRole="button"
                >
                  <Text style={styles.removeText}>Remove</Text>
                </Pressable>
              </View>
            );
          })}
        </View>
      )}

      <View>
        <SectionHeader title="Add one" />
        <Text style={styles.fieldLabel}>Certification</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder="Personal Licence"
          placeholderTextColor={COLORS.borderStrong}
        />
        <Text style={styles.fieldLabel}>Valid until</Text>
        <TextInput
          style={styles.input}
          value={expiry}
          onChangeText={setExpiry}
          placeholder="2027-01-31"
          placeholderTextColor={COLORS.borderStrong}
        />
        <Text style={styles.fieldLabel}>Reference (optional)</Text>
        <TextInput
          style={styles.input}
          value={reference}
          onChangeText={setReference}
          placeholder="Licence number"
          placeholderTextColor={COLORS.borderStrong}
        />
        <Pressable
          style={[styles.action, busy && styles.disabled]}
          onPress={() => void save()}
          disabled={busy}
          accessibilityRole="button"
        >
          <Text style={styles.actionText}>Save certification</Text>
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  grow: { flex: 1 },
  hint: { ...TYPE.meta, color: COLORS.inkSubtle },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACE.s3,
    paddingVertical: SPACE.s3,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  rowTitle: { ...TYPE.body, color: COLORS.ink },
  rowMeta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 2 },
  rowWarn: { color: COLORS.error },
  removeText: { ...TYPE.meta, color: COLORS.inkMuted, textDecorationLine: "underline" },
  fieldLabel: { ...TYPE.eyebrow, color: COLORS.inkSubtle, marginTop: SPACE.s3, marginBottom: SPACE.s2 },
  input: {
    borderWidth: 1,
    borderColor: COLORS.borderStrong,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surface,
    paddingHorizontal: SPACE.s3,
    paddingVertical: SPACE.s3,
    color: COLORS.ink,
  },
  action: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3 + 2,
    alignItems: "center",
    marginTop: SPACE.s4,
  },
  actionText: { ...TYPE.action, color: COLORS.onPrimary },
  disabled: { opacity: 0.5 },
  error: { ...TYPE.meta, color: COLORS.error },
});

import { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from "react-native";

import { SectionHeader } from "../../components/SectionHeader";
import { deleteWorker, fetchWorker, putWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";

type Relationship = {
  relationship_id: string;
  venue_id: string;
  venue_name: string | null;
  relationship_type: string;
  status: string;
};

type Rule = {
  rule_id: string;
  venue_id: string;
  enabled: boolean;
  roles: string[];
  minimum_rate: string | null;
  minimum_notice_hours: number | null;
  version: number;
};

type Attempt = {
  attempt_id: string;
  offer_id: string;
  outcome: string;
  reason: string | null;
  evaluated_at: string;
};

type Draft = {
  enabled: boolean;
  roles: string;
  minimum_rate: string;
  minimum_notice_hours: string;
};

export function AutoAcceptScreen() {
  const [venues, setVenues] = useState<Relationship[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [ruled, setRuled] = useState<Record<string, boolean>>({});
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const relationships = await fetchWorker<Relationship[]>("/me/relationships");
      const pools = relationships.filter(
        (item) => item.relationship_type === "pool" && item.status === "active",
      );
      setVenues(pools);
      const rules = await fetchWorker<Rule[]>("/me/auto-accept-rules");
      const byVenue = Object.fromEntries(rules.map((rule) => [rule.venue_id, rule]));
      setRuled(Object.fromEntries(rules.map((rule) => [rule.venue_id, true])));
      setDrafts((current) => {
        const next: Record<string, Draft> = { ...current };
        for (const pool of pools) {
          const rule = byVenue[pool.venue_id];
          next[pool.venue_id] = {
            enabled: rule?.enabled ?? false,
            roles: rule ? rule.roles.join(", ") : "",
            minimum_rate: rule?.minimum_rate ? String(rule.minimum_rate) : "",
            minimum_notice_hours:
              rule?.minimum_notice_hours != null ? String(rule.minimum_notice_hours) : "",
          };
        }
        return next;
      });
      setAttempts(await fetchWorker<Attempt[]>("/me/auto-accept-attempts?limit=10"));
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async (venue: Relationship) => {
    const draft = drafts[venue.venue_id];
    if (!draft) return;
    setBusyId(venue.venue_id);
    setError(null);
    setStatus(null);
    try {
      await putWorker(`/me/auto-accept-rules/${venue.venue_id}`, {
        enabled: draft.enabled,
        roles: draft.roles
          .split(",")
          .map((role) => role.trim())
          .filter(Boolean),
        minimum_rate: draft.minimum_rate.trim() ? Number(draft.minimum_rate) : null,
        minimum_notice_hours: draft.minimum_notice_hours.trim()
          ? Number(draft.minimum_notice_hours)
          : null,
      });
      setStatus(`Saved for ${venue.venue_name ?? "venue"}.`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  const clear = async (venue: Relationship) => {
    setBusyId(venue.venue_id);
    setError(null);
    setStatus(null);
    try {
      await deleteWorker(`/me/auto-accept-rules/${venue.venue_id}`);
      setStatus(`Removed for ${venue.venue_name ?? "venue"}.`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  const update = (venueId: string, patch: Partial<Draft>) =>
    setDrafts((current) => ({
      ...current,
      [venueId]: { ...current[venueId], ...patch },
    }));

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.hint}>
        Auto-accept answers offers a venue sends you by name. It never applies to open shifts, and
        it only works for venues whose pool you are in.
      </Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {status ? <Text style={styles.status}>{status}</Text> : null}

      {venues.length === 0 ? (
        <Text style={styles.hint}>
          You are not in any venue pools yet. Pools appear here once a venue keeps you.
        </Text>
      ) : (
        venues.map((venue) => {
          const draft = drafts[venue.venue_id] ?? {
            enabled: false,
            roles: "",
            minimum_rate: "",
            minimum_notice_hours: "",
          };
          const busy = busyId === venue.venue_id;
          return (
            <View key={venue.venue_id} style={styles.card}>
              <View style={styles.toggleRow}>
                <View style={styles.grow}>
                  <Text style={styles.venueName}>{venue.venue_name ?? "Venue"}</Text>
                  <Text style={styles.toggleHint}>
                    {draft.enabled ? "Accepting offers automatically" : "Asking you every time"}
                  </Text>
                </View>
                <Switch
                  value={draft.enabled}
                  onValueChange={(enabled) => update(venue.venue_id, { enabled })}
                  trackColor={{ false: COLORS.border, true: COLORS.primary }}
                  thumbColor="#fff"
                />
              </View>

              <Text style={styles.fieldLabel}>Only these roles (blank = any)</Text>
              <TextInput
                style={styles.input}
                value={draft.roles}
                onChangeText={(roles) => update(venue.venue_id, { roles })}
                placeholder="Bartender, Server"
                placeholderTextColor={COLORS.borderStrong}
              />
              <Text style={styles.fieldLabel}>Minimum hourly rate</Text>
              <TextInput
                style={styles.input}
                value={draft.minimum_rate}
                onChangeText={(minimum_rate) => update(venue.venue_id, { minimum_rate })}
                keyboardType="decimal-pad"
                placeholder="Any rate"
                placeholderTextColor={COLORS.borderStrong}
              />
              <Text style={styles.fieldLabel}>Minimum notice (hours)</Text>
              <TextInput
                style={styles.input}
                value={draft.minimum_notice_hours}
                onChangeText={(minimum_notice_hours) =>
                  update(venue.venue_id, { minimum_notice_hours })
                }
                keyboardType="number-pad"
                placeholder="Any notice"
                placeholderTextColor={COLORS.borderStrong}
              />

              <View style={styles.actions}>
                <Pressable
                  style={[styles.action, busy && styles.disabled]}
                  disabled={busy}
                  onPress={() => void save(venue)}
                  accessibilityRole="button"
                >
                  <Text style={styles.actionText}>Save</Text>
                </Pressable>
                {ruled[venue.venue_id] ? (
                  <Pressable
                    style={[styles.secondary, busy && styles.disabled]}
                    disabled={busy}
                    onPress={() => void clear(venue)}
                    accessibilityRole="button"
                  >
                    <Text style={styles.secondaryText}>Remove rule</Text>
                  </Pressable>
                ) : null}
              </View>
            </View>
          );
        })
      )}

      {attempts.length > 0 && (
        <View>
          <SectionHeader title="Recent decisions" />
          {attempts.map((attempt) => (
            <View key={attempt.attempt_id} style={styles.attemptRow}>
              <Text style={styles.attemptOutcome}>
                {attempt.outcome === "accepted" ? "Accepted for you" : `Skipped`}
              </Text>
              <Text style={styles.attemptMeta}>
                {attempt.evaluated_at.slice(0, 16).replace("T", " ")}
                {attempt.reason ? ` · ${attempt.reason.replaceAll("_", " ")}` : ""}
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  grow: { flex: 1 },
  hint: { ...TYPE.meta, color: COLORS.inkSubtle },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s4,
  },
  toggleRow: { flexDirection: "row", alignItems: "center", gap: SPACE.s4 },
  venueName: { ...TYPE.body, fontSize: 15, color: COLORS.ink },
  toggleHint: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 2 },
  fieldLabel: { ...TYPE.eyebrow, color: COLORS.inkSubtle, marginTop: SPACE.s4, marginBottom: SPACE.s2 },
  input: {
    borderWidth: 1,
    borderColor: COLORS.borderStrong,
    borderRadius: RADIUS.md,
    backgroundColor: COLORS.surfaceMuted,
    paddingHorizontal: SPACE.s3,
    paddingVertical: SPACE.s3,
    color: COLORS.ink,
  },
  actions: { flexDirection: "row", gap: SPACE.s3, marginTop: SPACE.s4 },
  action: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3,
    alignItems: "center",
  },
  actionText: { ...TYPE.action, color: COLORS.onPrimary },
  secondary: {
    flex: 1,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3,
    alignItems: "center",
  },
  secondaryText: { ...TYPE.action, color: COLORS.inkMuted },
  attemptRow: {
    paddingVertical: SPACE.s3,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  attemptOutcome: { ...TYPE.body, color: COLORS.ink },
  attemptMeta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 2 },
  disabled: { opacity: 0.5 },
  status: { ...TYPE.meta, color: COLORS.inkMuted },
  error: { ...TYPE.meta, color: COLORS.error },
});

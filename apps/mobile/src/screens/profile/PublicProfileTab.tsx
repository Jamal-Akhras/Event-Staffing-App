import { useEffect, useState } from "react";
import { Image, StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "../../components/SectionHeader";
import { fetchWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { NUMERIC, TYPE } from "../../theme/type";
import type { WorkerProfile } from "../../types";

type RatingSummary = { avg_stars: number | null; total_ratings: number };

const VISIBILITY: { label: string; value: string }[] = [
  { label: "Name, photo and bio", value: "Visible" },
  { label: "Role and experience", value: "Visible" },
  { label: "Shifts worked with them", value: "Visible" },
  { label: "Ratings venues gave you", value: "Visible" },
  { label: "Phone and address", value: "Only once booked" },
  { label: "Ratings you gave them", value: "Never shown" },
];

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function PublicProfileTab({ profile }: { profile: WorkerProfile | null }) {
  const [rating, setRating] = useState<RatingSummary | null>(null);

  useEffect(() => {
    if (!profile) return;
    fetchWorker<RatingSummary>(`/workers/${profile.worker_id}/rating-summary`)
      .then(setRating)
      .catch(() => setRating(null));
  }, [profile?.worker_id]);

  if (!profile) return null;

  const turnUp = Math.round(profile.reliability_score * 100);

  return (
    <View style={styles.wrap}>
      <View style={styles.panel}>
        <Text style={styles.label}>Your card in a venue's list</Text>
        <View style={styles.identity}>
          {profile.avatar_url ? (
            <Image source={{ uri: profile.avatar_url }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatar, styles.avatarFallback]}>
              <Text style={styles.avatarText}>{initials(profile.display_name)}</Text>
            </View>
          )}
          <View style={styles.grow}>
            <Text style={styles.name}>{profile.display_name}</Text>
            <Text style={styles.meta}>
              {profile.role} · {profile.experience_years}{" "}
              {profile.experience_years === 1 ? "year" : "years"}
            </Text>
          </View>
        </View>

        <View style={styles.trio}>
          <Stat figure={`${turnUp}%`} label="Turn up" />
          <Stat figure={rating?.avg_stars ? rating.avg_stars.toFixed(1) : "—"} label="Rating" />
          <Stat figure={String(rating?.total_ratings ?? 0)} label="Reviews" />
        </View>
      </View>

      <View>
        <SectionHeader title="What they can read" />
        {VISIBILITY.map((row) => (
          <View key={row.label} style={styles.row}>
            <Text style={styles.rowLabel}>{row.label}</Text>
            <Text style={styles.rowValue}>{row.value}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function Stat({ figure, label }: { figure: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.figure}>{figure}</Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: SPACE.s5 },
  panel: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s5,
  },
  label: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  identity: { flexDirection: "row", alignItems: "center", gap: SPACE.s4, marginTop: SPACE.s4 },
  avatar: { width: 58, height: 58, borderRadius: 29 },
  avatarFallback: { backgroundColor: COLORS.primary, alignItems: "center", justifyContent: "center" },
  avatarText: { color: COLORS.onPrimary, fontSize: 20, fontWeight: "500" },
  grow: { flex: 1, minWidth: 0 },
  name: { ...TYPE.venue, color: COLORS.ink },
  meta: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 2 },
  trio: {
    flexDirection: "row",
    marginTop: SPACE.s4,
    paddingTop: SPACE.s4,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  stat: { flex: 1, alignItems: "center", gap: 2 },
  figure: { ...NUMERIC, fontSize: 22, fontWeight: "400", letterSpacing: -0.6, color: COLORS.ink },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: SPACE.s3,
    paddingVertical: SPACE.s3,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  rowLabel: { ...TYPE.body, color: COLORS.ink, flex: 1 },
  rowValue: { ...TYPE.meta, color: COLORS.inkSubtle },
});

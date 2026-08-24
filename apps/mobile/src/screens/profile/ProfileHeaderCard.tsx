import { Image, Pressable, StyleSheet, Text, View } from "react-native";

import { API_BASE } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import type { WorkerProfile } from "../../types";

type ProfileHeaderCardProps = {
  profile: WorkerProfile | null;
  uploading: boolean;
  onChangePhoto: () => void;
};

export function ProfileHeaderCard({
  profile,
  uploading,
  onChangePhoto,
}: ProfileHeaderCardProps) {
  const initials = profile?.display_name
    ? profile.display_name.slice(0, 2).toUpperCase()
    : "WK";
  const avatarSrc = profile?.avatar_url
    ? { uri: profile.avatar_url.startsWith("/uploads") ? `${API_BASE}${profile.avatar_url}` : profile.avatar_url }
    : null;
  const stars = profile ? formatStars(profile.reliability_score) : "—";
  const exp = profile ? `${profile.experience_years} yr` : "—";
  const badges = profile ? profile.badges.length : 0;

  return (
    <View style={styles.headerCard}>
      <View style={styles.headerCardTop}>
        {avatarSrc ? (
          <Image source={avatarSrc} style={styles.avatarImage} />
        ) : (
          <View style={styles.avatarPlaceholder}>
            <Text style={styles.avatarInitials}>{initials}</Text>
          </View>
        )}
        <View style={styles.headerCardCopy}>
          <Text style={styles.avatarName} numberOfLines={1}>{profile?.display_name || "Worker"}</Text>
          <Text style={styles.reliabilityLine}>
            <Text style={styles.starGlyph}>★</Text>
            <Text style={styles.reliabilityValue}> {stars}</Text>
            <Text style={styles.reliabilityCaption}>  / 5 reliability</Text>
          </Text>
          <Pressable style={styles.avatarBtn} onPress={onChangePhoto} disabled={uploading}>
            <Text style={styles.avatarBtnText}>{uploading ? "Uploading…" : "Change photo"}</Text>
          </Pressable>
        </View>
      </View>
      <View style={styles.headerStats}>
        <View style={styles.headerStatCol}>
          <Text style={styles.headerStatLabel}>Experience</Text>
          <Text style={styles.headerStatValue}>{exp}</Text>
        </View>
        <View style={styles.headerStatDivider} />
        <View style={styles.headerStatCol}>
          <Text style={styles.headerStatLabel}>Badges</Text>
          <Text style={styles.headerStatValue}>{badges}</Text>
        </View>
      </View>
    </View>
  );
}

function formatStars(score: number): string {
  return (score * 5).toFixed(1);
}

const styles = StyleSheet.create({
  headerCard: {
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    overflow: "hidden",
  },
  headerCardTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    padding: 16,
  },
  headerCardCopy: { flex: 1 },
  reliabilityLine: { marginTop: 2 },
  starGlyph: { color: "#f59e0b", fontSize: 14, fontWeight: "700" },
  reliabilityValue: { color: COLORS.ink, fontSize: 14, fontWeight: "800" },
  reliabilityCaption: { color: COLORS.inkMuted, fontSize: 12, fontWeight: "500" },
  headerStats: {
    flexDirection: "row",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.surfaceMuted,
  },
  headerStatCol: { flex: 1, paddingVertical: 12, paddingHorizontal: 16 },
  headerStatDivider: { width: 1, alignSelf: "stretch", backgroundColor: COLORS.border },
  headerStatLabel: { color: COLORS.inkMuted, fontSize: 11, fontWeight: "700", letterSpacing: 0.4, textTransform: "uppercase" },
  headerStatValue: { color: COLORS.ink, fontSize: 16, fontWeight: "800", marginTop: 2 },
  avatarImage: { width: 64, height: 64, borderRadius: 32, borderWidth: 1, borderColor: COLORS.border },
  avatarPlaceholder: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "rgba(14,90,58,0.1)",
    alignItems: "center",
    justifyContent: "center",
  },
  avatarInitials: { color: COLORS.primary, fontSize: 20, fontWeight: "800" },
  avatarName: { color: COLORS.ink, fontSize: 17, fontWeight: "800", letterSpacing: -0.2 },
  avatarBtn: {
    alignSelf: "flex-start",
    marginTop: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  avatarBtnText: { color: COLORS.primary, fontSize: 13, fontWeight: "800" },
});

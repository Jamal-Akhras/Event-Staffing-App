import * as ImagePicker from "expo-image-picker";
import { useEffect, useState } from "react";
import { Image, Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";

import { useAuth } from "../contexts/AuthContext";
import { API_BASE, fetchWorker, putWorker, uploadWorkerAvatar } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { WorkerProfile } from "../types";
import { ProfileFormFields } from "./profile/ProfileFormFields";
import { ProfileSection } from "./profile/ProfileSection";
import {
  emptyProfileForm,
  formToPayload,
  profileToForm,
  type ProfileForm,
} from "./profile/profileForm";

export function ProfileScreen() {
  const { user, logout } = useAuth();
  const workerId = user?.worker_profile_id ?? "";
  const [health, setHealth] = useState<string>("Unknown");
  const [error, setError] = useState<string | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileForm>({
    ...emptyProfileForm,
    worker_id: workerId,
  });
  const [profileMeta, setProfileMeta] = useState<WorkerProfile | null>(null);
  const [profileStatus, setProfileStatus] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [allowRecontact, setAllowRecontact] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        return response.json();
      })
      .then(() => {
        setHealth("Healthy");
        setError(null);
      })
      .catch((err) => {
        if ((err as Error).name !== "AbortError") {
          setHealth("Unavailable");
          setError((err as Error).message);
        }
      });
    return () => controller.abort();
  }, []);

  const loadProfile = async () => {
    if (!workerId) return;
    try {
      const data = await fetchWorker<WorkerProfile>(`/workers/${workerId}`);
      setProfileMeta(data);
      setProfileForm(profileToForm(data));
      setAllowRecontact(data.allow_venue_recontact ?? false);
      setProfileStatus(null);
    } catch (err) {
      setProfileMeta(null);
      setProfileStatus((err as Error).message);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [workerId]);

  const pickAvatar = async () => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      setProfileStatus("Photo library access is required to change your avatar.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (result.canceled || !result.assets[0]) return;
    setAvatarUploading(true);
    try {
      const asset = result.assets[0];
      const data = await uploadWorkerAvatar(asset.uri, asset.mimeType ?? "image/jpeg");
      setProfileMeta((prev) => (prev ? { ...prev, avatar_url: data.url } : prev));
      setProfileStatus("Photo updated.");
    } catch (err) {
      setProfileStatus((err as Error).message);
    } finally {
      setAvatarUploading(false);
    }
  };

  const saveProfile = async () => {
    if (!workerId) return;
    setProfileStatus(null);
    try {
      const data = await putWorker<WorkerProfile>(
        `/workers/${workerId}`,
        { ...formToPayload(profileForm), allow_venue_recontact: allowRecontact }
      );
      setProfileMeta(data);
      setProfileStatus("Profile saved.");
    } catch (err) {
      setProfileStatus((err as Error).message);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Text style={styles.eyebrow}>Worker readiness</Text>
        <Text style={styles.title}>Profile</Text>
        <Text style={styles.subtitle}>Keep venue-facing details accurate.</Text>
      </View>

      <ProfileHeaderCard
        profile={profileMeta}
        uploading={avatarUploading}
        onChangePhoto={pickAvatar}
      />

      <ProfileSection title="Public profile">
        <ProfileFormFields form={profileForm} onChange={setProfileForm} />
      </ProfileSection>

      <ProfileSection title="Private info">
        <ProfileFormFields form={profileForm} onChange={setProfileForm} privateFields />
        <Pressable style={styles.button} onPress={saveProfile}>
          <Text style={styles.buttonText}>Save profile</Text>
        </Pressable>
        {profileStatus && <Text style={styles.statusText}>{profileStatus}</Text>}
      </ProfileSection>

      <ProfileSection title="Privacy">
        <View style={styles.toggleRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.toggleLabel}>Visible to past venues</Text>
            <Text style={styles.toggleDescription}>
              Allow venues you've worked at to see your profile and availability.
            </Text>
          </View>
          <Switch
            value={allowRecontact}
            onValueChange={(value) => {
              setAllowRecontact(value);
              if (workerId) {
                putWorker(`/workers/${workerId}`, {
                  ...formToPayload(profileForm),
                  allow_venue_recontact: value,
                }).catch(() => {});
              }
            }}
            trackColor={{ false: COLORS.border, true: COLORS.primary }}
            thumbColor="#fff"
          />
        </View>
      </ProfileSection>

      <ProfileSection title="Connection">
        <Text style={styles.connectionValue}>{health}</Text>
        <Text style={styles.connectionMeta}>{API_BASE}</Text>
        {error && <Text style={styles.errorText}>{error}</Text>}
      </ProfileSection>

      <ProfileSection title="Account">
        <Text style={styles.connectionMeta}>{user?.email}</Text>
        <Pressable style={[styles.button, styles.signOutButton]} onPress={logout}>
          <Text style={styles.signOutText}>Sign out</Text>
        </Pressable>
      </ProfileSection>
    </ScrollView>
  );
}

function formatStars(score: number): string {
  return (score * 5).toFixed(1);
}

function ProfileHeaderCard({
  profile,
  uploading,
  onChangePhoto,
}: {
  profile: WorkerProfile | null;
  uploading: boolean;
  onChangePhoto: () => void;
}) {
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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: 20, paddingBottom: 40 },
  header: { marginBottom: 16 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  subtitle: { color: COLORS.inkMuted, fontSize: 14, lineHeight: 20, marginTop: 6 },
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
  button: {
    alignItems: "center",
    paddingVertical: 12,
    marginTop: 2,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
  },
  buttonText: { color: COLORS.onPrimary, fontWeight: "800" },
  statusText: { marginTop: 10, color: COLORS.inkMuted, fontWeight: "600" },
  connectionValue: { color: COLORS.ink, fontSize: 16, fontWeight: "700" },
  connectionMeta: { marginTop: 4, color: COLORS.inkMuted, fontSize: 13 },
  errorText: { marginTop: 6, color: COLORS.error, fontWeight: "700" },
  signOutButton: { backgroundColor: COLORS.surfaceMuted, borderWidth: 1, borderColor: COLORS.border, marginTop: 12 },
  signOutText: { color: COLORS.error, fontWeight: "800" },
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
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  toggleLabel: { color: COLORS.ink, fontSize: 15, fontWeight: "800" },
  toggleDescription: { color: COLORS.inkMuted, fontSize: 13, marginTop: 2 },
});

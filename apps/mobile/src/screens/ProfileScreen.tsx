import * as ImagePicker from "expo-image-picker";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";

import { MarketPicker } from "../components/MarketPicker";
import { useAuth } from "../contexts/AuthContext";
import {
  API_BASE,
  fetchPublicJson,
  fetchWorker,
  getWorkerId,
  putWorker,
  uploadWorkerAvatar,
} from "../lib/api";
import { COLORS } from "../theme/colors";
import type { WorkerProfile } from "../types";
import { NotificationPrefsSection } from "./profile/NotificationPrefsSection";
import { PrivateProfileFields, PublicProfileFields } from "./profile/ProfileFormFields";
import { ProfileHeaderCard } from "./profile/ProfileHeaderCard";
import { ProfileSection } from "./profile/ProfileSection";
import {
  emptyProfileForm,
  formToPayload,
  profileToForm,
  type ProfileForm,
} from "./profile/profileForm";

export function ProfileScreen() {
  const { user, logout } = useAuth();
  const workerId = getWorkerId();
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
    fetchPublicJson("/health")
      .then(() => {
        setHealth("Healthy");
        setError(null);
      })
      .catch((err: Error) => {
        setHealth("Unavailable");
        setError(err.message);
      });
  }, []);

  const loadProfile = async () => {
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

  const persistProfile = async (allowVenueRecontact: boolean) => {
    setProfileStatus(null);
    try {
      const data = await putWorker<WorkerProfile>(
        `/workers/${workerId}`,
        { ...formToPayload(profileForm), allow_venue_recontact: allowVenueRecontact }
      );
      setProfileMeta(data);
      setProfileStatus("Profile saved.");
    } catch (err) {
      setProfileStatus((err as Error).message);
    }
  };

  const saveProfile = () => persistProfile(allowRecontact);

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
        <View style={styles.marketBlock}>
          <Text style={styles.marketLabel}>Your city</Text>
          <MarketPicker
            selectedMarketId={profileForm.market_id || null}
            onSelect={(market) =>
              setProfileForm({ ...profileForm, market_id: market.market_id, city: market.name })
            }
          />
        </View>
        <PublicProfileFields form={profileForm} onChange={setProfileForm} />
      </ProfileSection>

      <ProfileSection title="Private info">
        <PrivateProfileFields form={profileForm} onChange={setProfileForm} />
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
              void persistProfile(value);
            }}
            trackColor={{ false: COLORS.border, true: COLORS.primary }}
            thumbColor="#fff"
          />
        </View>
      </ProfileSection>

      <ProfileSection title="Notifications">
        <NotificationPrefsSection />
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
  marketBlock: { gap: 8, marginBottom: 12 },
  marketLabel: { color: COLORS.ink, fontSize: 14, fontWeight: "800" },
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
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  toggleLabel: { color: COLORS.ink, fontSize: 15, fontWeight: "800" },
  toggleDescription: { color: COLORS.inkMuted, fontSize: 13, marginTop: 2 },
});

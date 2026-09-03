import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from "react-native";

import { MarketPicker } from "../../components/MarketPicker";
import { SectionHeader } from "../../components/SectionHeader";
import { useAuth } from "../../contexts/AuthContext";
import { API_BASE } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import { NotificationPrefsSection } from "./NotificationPrefsSection";
import { ProfileHeaderCard } from "./ProfileHeaderCard";
import { PrivateProfileFields, PublicProfileFields } from "./ProfileFormFields";
import { SettingsRow } from "./SettingsRow";
import { useWorkerProfile } from "./useWorkerProfile";
import { useWorkPreferences } from "./useWorkPreferences";

export function ProfileDetailsScreen() {
  const { form, setForm, profile, status, uploading, save, pickAvatar } = useWorkerProfile();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <ProfileHeaderCard profile={profile} uploading={uploading} onChangePhoto={pickAvatar} />

      <View>
        <SectionHeader title="Public profile" />
        <Text style={styles.fieldLabel}>Your city</Text>
        <MarketPicker
          selectedMarketId={form.market_id || null}
          onSelect={(market) => setForm({ ...form, market_id: market.market_id, city: market.name })}
        />
        <PublicProfileFields form={form} onChange={setForm} />
      </View>

      <View>
        <SectionHeader title="Private info" />
        <Text style={styles.hint}>Venues only see this once you are booked.</Text>
        <PrivateProfileFields form={form} onChange={setForm} />
      </View>

      <Pressable style={styles.action} onPress={save} accessibilityRole="button">
        <Text style={styles.actionText}>Save profile</Text>
      </Pressable>
      {status ? <Text style={styles.status}>{status}</Text> : null}
    </ScrollView>
  );
}

export function NotificationSettingsScreen() {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <NotificationPrefsSection />
    </ScrollView>
  );
}

export function PrivacySettingsScreen() {
  const { allowRecontact, setAllowRecontact, persist } = useWorkerProfile();
  const workPreferences = useWorkPreferences();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.toggleRow}>
        <View style={styles.grow}>
          <Text style={styles.toggleLabel}>Visible to past venues</Text>
          <Text style={styles.toggleHint}>
            Venues you have worked at can see your profile and availability.
          </Text>
        </View>
        <Switch
          value={allowRecontact}
          onValueChange={(value) => {
            setAllowRecontact(value);
            void persist(value);
          }}
          trackColor={{ false: COLORS.border, true: COLORS.primary }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.toggleRow}>
        <View style={styles.grow}>
          <Text style={styles.toggleLabel}>Open marketplace shifts</Text>
          <Text style={styles.toggleHint}>
            Show open-market shifts in Browse. Work from your venues' teams and pools always shows.
          </Text>
        </View>
        <Switch
          value={workPreferences.marketplaceEnabled ?? true}
          disabled={workPreferences.marketplaceEnabled === null}
          onValueChange={(value) => void workPreferences.setMarketplace(value)}
          trackColor={{ false: COLORS.border, true: COLORS.primary }}
          thumbColor="#fff"
        />
      </View>
      {workPreferences.error ? <Text style={styles.error}>{workPreferences.error}</Text> : null}

      <Text style={styles.hint}>
        Ratings you give a venue are never shown to that venue.
      </Text>
    </ScrollView>
  );
}

export function AccountSettingsScreen() {
  const { user, logout } = useAuth();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View>
        <SectionHeader title="Signed in as" />
        <SettingsRow label={user?.email ?? "Unknown"} />
      </View>

      <View>
        <SectionHeader title="Connection" />
        <SettingsRow label="Server" value={API_BASE} />
      </View>

      <Pressable style={styles.signOut} onPress={logout} accessibilityRole="button">
        <Text style={styles.signOutText}>Sign out</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  grow: { flex: 1 },
  fieldLabel: { ...TYPE.eyebrow, color: COLORS.inkSubtle, marginBottom: SPACE.s2 },
  hint: { ...TYPE.meta, color: COLORS.inkSubtle, marginBottom: SPACE.s2 },
  action: {
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3 + 2,
    alignItems: "center",
  },
  actionText: { ...TYPE.action, color: COLORS.onPrimary },
  status: { ...TYPE.meta, color: COLORS.inkMuted, textAlign: "center" },
  error: { ...TYPE.meta, color: COLORS.error },
  toggleRow: { flexDirection: "row", alignItems: "center", gap: SPACE.s4 },
  toggleLabel: { ...TYPE.body, fontSize: 15, color: COLORS.ink },
  toggleHint: { ...TYPE.meta, color: COLORS.inkMuted, marginTop: 2 },
  signOut: {
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surfaceMuted,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3 + 2,
    alignItems: "center",
  },
  signOutText: { ...TYPE.action, color: COLORS.error },
});

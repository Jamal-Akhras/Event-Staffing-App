import { useState } from "react";
import { useNavigation } from "@react-navigation/native";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { SectionHeader } from "../components/SectionHeader";
import { SegmentedTabs } from "../components/SegmentedTabs";
import { useAuth } from "../contexts/AuthContext";
import { COLORS } from "../theme/colors";
import { SPACE } from "../theme/space";
import { TYPE } from "../theme/type";
import { PublicProfileTab } from "./profile/PublicProfileTab";
import { SettingsRow } from "./profile/SettingsRow";
import { useWorkerProfile } from "./profile/useWorkerProfile";

type ProfileTab = "public" | "settings";

const TABS: { key: ProfileTab; label: string }[] = [
  { key: "public", label: "How venues see you" },
  { key: "settings", label: "Settings" },
];

type SettingsNav = {
  navigate: (
    screen: "ProfileDetails" | "NotificationSettings" | "PrivacySettings" | "AccountSettings" | "Certifications"
  ) => void;
};

export function ProfileScreen() {
  const { user } = useAuth();
  const { profile, allowRecontact, status } = useWorkerProfile();
  const navigation = useNavigation<SettingsNav>();
  const [tab, setTab] = useState<ProfileTab>("public");

  const experience = profile
    ? `${profile.role} · ${profile.experience_years} ${profile.experience_years === 1 ? "year" : "years"}`
    : undefined;

  return (
    <View style={styles.screen}>
      <SegmentedTabs tabs={TABS} active={tab} onChange={setTab} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {tab === "public" ? (
          <PublicProfileTab profile={profile} />
        ) : (
          <>
            {status ? <Text style={styles.status}>{status}</Text> : null}

            <View>
              <SectionHeader title="You" />
              <SettingsRow
                label="Name, photo and bio"
                value={profile?.display_name}
                onPress={() => navigation.navigate("ProfileDetails")}
              />
              <SettingsRow
                label="Role and experience"
                value={experience}
                onPress={() => navigation.navigate("ProfileDetails")}
              />
              <SettingsRow label="Your city" value={profile?.city} onPress={() => navigation.navigate("ProfileDetails")} />
            </View>

            <View>
              <SectionHeader title="App" />
              <SettingsRow
                label="Notifications"
                onPress={() => navigation.navigate("NotificationSettings")}
              />
              <SettingsRow
                label="Privacy"
                value={allowRecontact ? "Visible to past venues" : "Hidden from past venues"}
                onPress={() => navigation.navigate("PrivacySettings")}
              />
              <SettingsRow
                label="Certifications"
                onPress={() => navigation.navigate("Certifications")}
              />
            </View>

            <View>
              <SectionHeader title="Account" />
              <SettingsRow
                label="Account and sign out"
                value={user?.email}
                onPress={() => navigation.navigate("AccountSettings")}
              />
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  status: { ...TYPE.meta, color: COLORS.error },
});

import { createNativeStackNavigator } from "@react-navigation/native-stack";

import { ProfileScreen } from "../screens/ProfileScreen";
import {
  AccountSettingsScreen,
  NotificationSettingsScreen,
  PrivacySettingsScreen,
  ProfileDetailsScreen,
} from "../screens/profile/SettingsDetailScreens";
import { AutoAcceptScreen } from "../screens/profile/AutoAcceptScreen";
import { CertificationsScreen } from "../screens/profile/CertificationsScreen";
import { COLORS } from "../theme/colors";
import { NotificationBell } from "./NotificationBell";
import type { ProfileStackParamList } from "./navigationTypes";

const Stack = createNativeStackNavigator<ProfileStackParamList>();

export function ProfileStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.surface },
        headerShadowVisible: false,
        headerTintColor: COLORS.ink,
        headerTitleStyle: { color: COLORS.ink, fontSize: 17, fontWeight: "500" },
        headerBackTitleVisible: false,
        contentStyle: { backgroundColor: COLORS.canvas },
      }}
    >
      <Stack.Screen
        name="ProfileHome"
        component={ProfileScreen}
        options={{ title: "Profile", headerRight: () => <NotificationBell /> }}
      />
      <Stack.Screen
        name="ProfileDetails"
        component={ProfileDetailsScreen}
        options={{ title: "Your details" }}
      />
      <Stack.Screen
        name="NotificationSettings"
        component={NotificationSettingsScreen}
        options={{ title: "Notifications" }}
      />
      <Stack.Screen
        name="PrivacySettings"
        component={PrivacySettingsScreen}
        options={{ title: "Privacy" }}
      />
      <Stack.Screen
        name="Certifications"
        component={CertificationsScreen}
        options={{ title: "Certifications" }}
      />
      <Stack.Screen
        name="AutoAccept"
        component={AutoAcceptScreen}
        options={{ title: "Auto-accept" }}
      />
      <Stack.Screen
        name="AccountSettings"
        component={AccountSettingsScreen}
        options={{ title: "Account" }}
      />
    </Stack.Navigator>
  );
}

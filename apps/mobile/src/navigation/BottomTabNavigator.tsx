import { Ionicons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { BrowseScreen } from "../screens/BrowseScreen";
import EarningsScreen from "../screens/EarningsScreen";
import { NotificationCenterScreen } from "../screens/NotificationCenterScreen";
import { ApplicationsScreen } from "../screens/ApplicationsScreen";
import { ShiftsScreen } from "../screens/ShiftsScreen";
import { COLORS } from "../theme/colors";
import { NotificationBell } from "./NotificationBell";
import { ProfileStack } from "./ProfileStack";
import type { RootTabParamList } from "./navigationTypes";

const Tab = createBottomTabNavigator<RootTabParamList>();

type IoniconName = keyof typeof Ionicons.glyphMap;

const TAB_ICONS: Record<string, { active: IoniconName; inactive: IoniconName }> = {
  Browse: { active: "compass", inactive: "compass-outline" },
  Shifts: { active: "briefcase", inactive: "briefcase-outline" },
  Applications: { active: "document-text", inactive: "document-text-outline" },
  Earnings: { active: "receipt", inactive: "receipt-outline" },
  Profile: { active: "person", inactive: "person-outline" },
};

export function BottomTabNavigator() {
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: true,
        headerRight: () => <NotificationBell />,
        headerStyle: {
          backgroundColor: COLORS.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: COLORS.border,
        },
        headerTitleStyle: {
          color: COLORS.ink,
          fontSize: 18,
          fontWeight: "700",
        },
        tabBarStyle: {
          height: 58 + insets.bottom,
          paddingBottom: Math.max(insets.bottom, 6),
          paddingTop: 6,
          borderTopWidth: 1,
          borderTopColor: COLORS.border,
          backgroundColor: COLORS.surface,
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.inkMuted,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "700",
          marginTop: 2,
        },
        tabBarIcon: ({ focused, color }) => (
          <Ionicons
            name={focused ? TAB_ICONS[route.name].active : TAB_ICONS[route.name].inactive}
            size={22}
            color={color}
          />
        ),
      })}
    >
      <Tab.Screen
        name="Browse"
        component={BrowseScreen}
        options={{ title: "Find Shifts", tabBarLabel: "Browse" }}
      />
      <Tab.Screen
        name="Shifts"
        component={ShiftsScreen}
        options={{ title: "My Shifts", tabBarLabel: "Shifts" }}
      />
      <Tab.Screen
        name="Applications"
        component={ApplicationsScreen}
        options={{ title: "Applications", tabBarLabel: "Applications" }}
      />
      <Tab.Screen
        name="Earnings"
        component={EarningsScreen}
        options={{ title: "Earnings", tabBarLabel: "Earnings" }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileStack}
        options={{ title: "Profile", tabBarLabel: "Profile", headerShown: false }}
      />
      <Tab.Screen
        name="Alerts"
        component={NotificationCenterScreen}
        options={{ title: "Notifications", tabBarButton: () => null }}
      />
    </Tab.Navigator>
  );
}

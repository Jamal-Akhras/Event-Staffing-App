import "react-native-gesture-handler";
import { BottomSheetModalProvider } from "@gorhom/bottom-sheet";
import { NavigationContainer } from "@react-navigation/native";
import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider, useAuth } from "./src/contexts/AuthContext";
import { NotificationProvider } from "./src/contexts/NotificationContext";
import { PushNotificationProvider } from "./src/contexts/PushNotificationContext";
import { RatingPromptProvider } from "./src/contexts/RatingPromptContext";
import { BottomTabNavigator } from "./src/navigation/BottomTabNavigator";
import { ForgotPasswordScreen } from "./src/screens/auth/ForgotPasswordScreen";
import { LoginScreen } from "./src/screens/auth/LoginScreen";
import { OnboardingScreen } from "./src/screens/OnboardingScreen";
import { RegisterScreen } from "./src/screens/auth/RegisterScreen";
import { COLORS } from "./src/theme/colors";
import { fetchWorker } from "./src/lib/api";
import type { WorkerProfile } from "./src/types";
import { flushPendingNotificationTarget, navigationRef } from "./src/navigation/navigationRef";

type AuthScreen = "login" | "register" | "forgotPassword";

function AppContent() {
  const { user, isLoading } = useAuth();
  const [authScreen, setAuthScreen] = useState<AuthScreen>("login");
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [checkingProfile, setCheckingProfile] = useState(false);

  useEffect(() => {
    if (!user || user.role !== "worker" || !user.worker_profile_id) {
      setNeedsOnboarding(false);
      return;
    }
    setCheckingProfile(true);
    fetchWorker<WorkerProfile>(`/workers/${user.worker_profile_id}`)
      .then((p) => setNeedsOnboarding(!p.display_name || p.display_name.trim() === ""))
      .catch(() => setNeedsOnboarding(false))
      .finally(() => setCheckingProfile(false));
  }, [user]);

  if (isLoading || checkingProfile) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: COLORS.canvas }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!user) {
    if (authScreen === "register") {
      return <RegisterScreen onBack={() => setAuthScreen("login")} />;
    }
    if (authScreen === "forgotPassword") {
      return <ForgotPasswordScreen onBack={() => setAuthScreen("login")} />;
    }
    return (
      <LoginScreen
        onRegister={() => setAuthScreen("register")}
        onForgotPassword={() => setAuthScreen("forgotPassword")}
      />
    );
  }

  if (needsOnboarding) {
    return <OnboardingScreen onComplete={() => setNeedsOnboarding(false)} />;
  }

  return (
    <NotificationProvider>
      <PushNotificationProvider>
        <RatingPromptProvider>
          <NavigationContainer ref={navigationRef} onReady={flushPendingNotificationTarget}>
            <BottomSheetModalProvider>
              <BottomTabNavigator />
            </BottomSheetModalProvider>
          </NavigationContainer>
        </RatingPromptProvider>
      </PushNotificationProvider>
    </NotificationProvider>
  );
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: COLORS.canvas }}>
      <SafeAreaProvider>
        <StatusBar style="dark" />
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

import "react-native-gesture-handler";
import { ClerkProvider } from "@clerk/expo";
import { tokenCache } from "@clerk/expo/token-cache";
import { BottomSheetModalProvider } from "@gorhom/bottom-sheet";
import { NavigationContainer } from "@react-navigation/native";
import { StatusBar } from "expo-status-bar";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useState, type ReactNode } from "react";

import { startAnalytics } from "./src/lib/analytics";
import { ActivityIndicator, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider, useAuth } from "./src/contexts/AuthContext";
import { NotificationProvider } from "./src/contexts/NotificationContext";
import { PushNotificationProvider } from "./src/contexts/PushNotificationContext";
import { RatingPromptProvider } from "./src/contexts/RatingPromptContext";
import { BottomTabNavigator, type HomeTab } from "./src/navigation/BottomTabNavigator";
import { ForgotPasswordScreen } from "./src/screens/auth/ForgotPasswordScreen";
import { LoginScreen } from "./src/screens/auth/LoginScreen";
import { OnboardingScreen } from "./src/screens/OnboardingScreen";
import { JoinChoiceScreen } from "./src/screens/auth/JoinChoiceScreen";
import { RegisterScreen } from "./src/screens/auth/RegisterScreen";
import { COLORS } from "./src/theme/colors";
import { fetchWorker } from "./src/lib/api";
import { CLERK_PUBLISHABLE_KEY, SSO_ENABLED } from "./src/lib/clerk";
import type { WorkerContext, WorkerProfile } from "./src/types";
import { flushPendingNotificationTarget, navigationRef } from "./src/navigation/navigationRef";

WebBrowser.maybeCompleteAuthSession();
startAnalytics();

type AuthScreen = "login" | "joinChoice" | "register" | "registerWithCode" | "forgotPassword";

function IdentityProvider({ children }: { children: ReactNode }) {
  if (!SSO_ENABLED) return <>{children}</>;
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={tokenCache}>
      {children}
    </ClerkProvider>
  );
}

function AppContent() {
  const { user, isLoading } = useAuth();
  const [authScreen, setAuthScreen] = useState<AuthScreen>("login");
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [checkingProfile, setCheckingProfile] = useState(false);
  const [homeTab, setHomeTab] = useState<HomeTab>("Browse");

  useEffect(() => {
    if (!user || user.role !== "worker" || !user.worker_profile_id) {
      setNeedsOnboarding(false);
      setHomeTab("Browse");
      return;
    }
    setCheckingProfile(true);
    Promise.all([
      fetchWorker<WorkerProfile>(`/workers/${user.worker_profile_id}`)
        .then((p) => setNeedsOnboarding(!p.display_name || p.display_name.trim() === ""))
        .catch(() => setNeedsOnboarding(false)),
      fetchWorker<WorkerContext>("/me/work-context")
        .then((context) => setHomeTab(context.home_mode === "shifts" ? "Shifts" : "Browse"))
        .catch(() => setHomeTab("Browse")),
    ]).finally(() => setCheckingProfile(false));
  }, [user]);

  if (isLoading || checkingProfile) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: COLORS.canvas }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  if (!user) {
    if (authScreen === "joinChoice") {
      return (
        <JoinChoiceScreen
          onJoinVenue={() => setAuthScreen("registerWithCode")}
          onFindShifts={() => setAuthScreen("register")}
          onBack={() => setAuthScreen("login")}
        />
      );
    }
    if (authScreen === "register" || authScreen === "registerWithCode") {
      return (
        <RegisterScreen
          withJoinCode={authScreen === "registerWithCode"}
          onBack={() => setAuthScreen("login")}
        />
      );
    }
    if (authScreen === "forgotPassword") {
      return <ForgotPasswordScreen onBack={() => setAuthScreen("login")} />;
    }
    return (
      <LoginScreen
        onRegister={() => setAuthScreen("joinChoice")}
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
              <BottomTabNavigator initialTab={homeTab} />
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
        <IdentityProvider>
          <AuthProvider>
            <AppContent />
          </AuthProvider>
        </IdentityProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

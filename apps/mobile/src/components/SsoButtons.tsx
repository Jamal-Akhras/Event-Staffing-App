import { useAuth as useClerkAuth, useSSO } from "@clerk/expo";
import * as AuthSession from "expo-auth-session";
import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { useAuth } from "../contexts/AuthContext";
import { APP_SCHEME, SSO_PROVIDERS, type SsoStrategy } from "../lib/clerk";
import { authStyles } from "../screens/auth/authStyles";
import { COLORS } from "../theme/colors";

export function SsoButtons() {
  const { startSSOFlow } = useSSO();
  const { getToken } = useClerkAuth();
  const { loginWithSso } = useAuth();
  const [pending, setPending] = useState<SsoStrategy | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function start(strategy: SsoStrategy) {
    setError(null);
    setPending(strategy);
    try {
      const { createdSessionId, setActive } = await startSSOFlow({
        strategy,
        redirectUrl: AuthSession.makeRedirectUri({ scheme: APP_SCHEME, path: "sso-callback" }),
      });
      if (!createdSessionId || !setActive) {
        setError("That sign-in didn't complete. Try again or use your email and password.");
        return;
      }
      await setActive({ session: createdSessionId });
      const token = await getToken();
      if (!token) throw new Error("We couldn't confirm your sign-in. Please try again.");
      await loginWithSso(token);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPending(null);
    }
  }

  return (
    <View style={styles.container}>
      {SSO_PROVIDERS.map((provider) => (
        <Pressable
          key={provider.strategy}
          style={[styles.button, pending !== null && styles.buttonDisabled]}
          disabled={pending !== null}
          onPress={() => start(provider.strategy)}
        >
          {pending === provider.strategy ? (
            <ActivityIndicator size="small" color={COLORS.ink} />
          ) : (
            <Text style={styles.buttonText}>{provider.label}</Text>
          )}
        </Pressable>
      ))}
      {error && <Text style={authStyles.error}>{error}</Text>}
      <View style={styles.divider}>
        <View style={styles.dividerLine} />
        <Text style={styles.dividerText}>or with email</Text>
        <View style={styles.dividerLine} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10, marginBottom: 20 },
  button: {
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  buttonDisabled: { opacity: 0.55 },
  buttonText: { color: COLORS.ink, fontSize: 15, fontWeight: "700" },
  divider: { flexDirection: "row", alignItems: "center", gap: 12, marginTop: 8 },
  dividerLine: { flex: 1, height: 1, backgroundColor: COLORS.border },
  dividerText: { color: COLORS.inkMuted, fontSize: 12, fontWeight: "600" },
});

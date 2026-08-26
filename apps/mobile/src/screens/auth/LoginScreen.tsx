import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { SsoButtons } from "../../components/SsoButtons";
import { useAuth } from "../../contexts/AuthContext";
import { SSO_ENABLED } from "../../lib/clerk";
import { authStyles } from "./authStyles";
import { COLORS } from "../../theme/colors";

type Props = { onRegister: () => void; onForgotPassword: () => void };

export function LoginScreen({ onRegister, onForgotPassword }: Props) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={authStyles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={authStyles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={authStyles.brand}>
            <View style={authStyles.brandMark}>
              <Text style={authStyles.brandMarkText}>V</Text>
            </View>
            <Text style={authStyles.brandName}>Venue OS</Text>
            <Text style={authStyles.brandTagline}>Find shifts near you</Text>
          </View>

          <View style={authStyles.card}>
            <Text style={authStyles.heading}>Welcome back</Text>
            <Text style={authStyles.subheading}>Sign in to see available shifts.</Text>

            {SSO_ENABLED && <SsoButtons />}

            <View style={authStyles.fieldGroup}>
              <Text style={authStyles.label}>Email address</Text>
              <TextInput
                style={authStyles.input}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                placeholder="you@email.com"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="next"
              />
            </View>

            <View style={authStyles.fieldGroup}>
              <Text style={authStyles.label}>Password</Text>
              <TextInput
                style={authStyles.input}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoComplete="current-password"
                placeholder="••••••••"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
              />
            </View>

            {error && <Text style={authStyles.error}>{error}</Text>}

            <Pressable
              style={[authStyles.button, loading && authStyles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading}
            >
              <Text style={authStyles.buttonText}>{loading ? "Signing in…" : "Sign in"}</Text>
            </Pressable>
          </View>

          <View style={authStyles.footer}>
            <Text style={authStyles.footerText}>No account? </Text>
            <Pressable onPress={onRegister}>
              <Text style={authStyles.footerLink}>Create account</Text>
            </Pressable>
          </View>

          <View style={[authStyles.footer, { marginTop: 12 }]}>
            <Pressable onPress={onForgotPassword}>
              <Text style={authStyles.footerLink}>Forgot password?</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

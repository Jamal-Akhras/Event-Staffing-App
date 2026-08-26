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

type Props = { onBack: () => void };

export function RegisterScreen({ onBack }: Props) {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!email || !password) {
      setError("Email and password are required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords don't match.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await register(email.trim().toLowerCase(), password);
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
            <Text style={authStyles.brandTagline}>Join the worker network</Text>
          </View>

          <View style={authStyles.card}>
            <Text style={authStyles.heading}>Create account</Text>
            <Text style={authStyles.subheading}>Start applying for shifts today.</Text>

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
                autoComplete="new-password"
                placeholder="At least 8 characters"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="next"
              />
            </View>

            <View style={authStyles.fieldGroup}>
              <Text style={authStyles.label}>Confirm password</Text>
              <TextInput
                style={authStyles.input}
                value={confirm}
                onChangeText={setConfirm}
                secureTextEntry
                placeholder="Repeat your password"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="done"
                onSubmitEditing={handleRegister}
              />
            </View>

            {error && <Text style={authStyles.error}>{error}</Text>}

            <Pressable
              style={[authStyles.button, loading && authStyles.buttonDisabled]}
              onPress={handleRegister}
              disabled={loading}
            >
              <Text style={authStyles.buttonText}>{loading ? "Creating account…" : "Create account"}</Text>
            </Pressable>
          </View>

          <View style={authStyles.footer}>
            <Text style={authStyles.footerText}>Already have an account? </Text>
            <Pressable onPress={onBack}>
              <Text style={authStyles.footerLink}>Sign in</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

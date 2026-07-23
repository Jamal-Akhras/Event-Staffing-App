import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../../contexts/AuthContext";
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
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.brand}>
            <View style={styles.brandMark}>
              <Text style={styles.brandMarkText}>V</Text>
            </View>
            <Text style={styles.brandName}>Venue OS</Text>
            <Text style={styles.brandTagline}>Join the worker network</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.heading}>Create account</Text>
            <Text style={styles.subheading}>Start applying for shifts today.</Text>

            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Email address</Text>
              <TextInput
                style={styles.input}
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

            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Password</Text>
              <TextInput
                style={styles.input}
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoComplete="new-password"
                placeholder="At least 8 characters"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="next"
              />
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.label}>Confirm password</Text>
              <TextInput
                style={styles.input}
                value={confirm}
                onChangeText={setConfirm}
                secureTextEntry
                placeholder="Repeat your password"
                placeholderTextColor={COLORS.inkSubtle}
                returnKeyType="done"
                onSubmitEditing={handleRegister}
              />
            </View>

            {error && <Text style={styles.error}>{error}</Text>}

            <Pressable
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleRegister}
              disabled={loading}
            >
              <Text style={styles.buttonText}>{loading ? "Creating account…" : "Create account"}</Text>
            </Pressable>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account? </Text>
            <Pressable onPress={onBack}>
              <Text style={styles.footerLink}>Sign in</Text>
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  scroll: { flexGrow: 1, justifyContent: "center", padding: 28 },
  brand: { alignItems: "center", marginBottom: 36 },
  brandMark: {
    width: 60,
    height: 60,
    borderRadius: 18,
    backgroundColor: COLORS.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 14,
    shadowColor: COLORS.primaryDeep,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
  },
  brandMarkText: { color: COLORS.onPrimary, fontSize: 28, fontWeight: "900" },
  brandName: { color: COLORS.ink, fontSize: 22, fontWeight: "800", letterSpacing: -0.5 },
  brandTagline: { color: COLORS.inkMuted, fontSize: 13, marginTop: 4 },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 22,
    padding: 26,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 24,
    shadowColor: COLORS.ink,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 2,
  },
  heading: {
    color: COLORS.ink,
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 4,
    letterSpacing: -0.4,
  },
  subheading: { color: COLORS.inkMuted, fontSize: 14, marginBottom: 26 },
  fieldGroup: { marginBottom: 18 },
  label: {
    color: COLORS.inkMuted,
    fontSize: 11,
    fontWeight: "700",
    marginBottom: 7,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  input: {
    borderWidth: 1.5,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: COLORS.ink,
    fontSize: 15,
    backgroundColor: COLORS.surfaceMuted,
  },
  error: {
    color: COLORS.error,
    fontSize: 13,
    marginBottom: 14,
    padding: 12,
    backgroundColor: "rgba(184,59,50,0.06)",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "rgba(184,59,50,0.15)",
  },
  button: {
    backgroundColor: COLORS.primary,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: "center",
    marginTop: 6,
  },
  buttonDisabled: { opacity: 0.55 },
  buttonText: { color: COLORS.onPrimary, fontSize: 15, fontWeight: "800", letterSpacing: 0.1 },
  footer: { flexDirection: "row", justifyContent: "center", alignItems: "center" },
  footerText: { color: COLORS.inkMuted, fontSize: 14 },
  footerLink: { color: COLORS.primary, fontSize: 14, fontWeight: "700" },
});

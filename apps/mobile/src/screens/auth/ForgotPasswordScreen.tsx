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

import { postPublicJson } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { authStyles } from "./authStyles";

type Props = { onBack: () => void };
type Step = "email" | "reset" | "done";

export function ForgotPasswordScreen({ onBack }: Props) {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRequestReset() {
    if (!email) { setError("Email is required."); return; }
    setError(null);
    setLoading(true);
    try {
      const data = await postPublicJson<{ reset_token?: string } | undefined>("/auth/forgot-password", { email });
      if (data?.reset_token) setToken(data.reset_token);
      setStep("reset");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword() {
    if (!token) { setError("Reset token is required."); return; }
    if (!newPassword) { setError("New password is required."); return; }
    if (newPassword !== confirmPassword) { setError("Passwords do not match."); return; }
    setError(null);
    setLoading(true);
    try {
      await postPublicJson("/auth/reset-password", { token, new_password: newPassword });
      setStep("done");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  if (step === "done") {
    return (
      <SafeAreaView style={authStyles.container}>
        <View style={styles.centered}>
          <View style={styles.doneIcon}><Text style={styles.doneIconText}>✓</Text></View>
          <Text style={styles.doneTitle}>Password reset!</Text>
          <Text style={styles.doneSub}>You can now sign in with your new password.</Text>
          <Pressable style={authStyles.button} onPress={onBack}>
            <Text style={authStyles.buttonText}>Back to Sign In</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={authStyles.container}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <Pressable style={styles.backRow} onPress={onBack}>
            <Text style={styles.backText}>← Back to Sign In</Text>
          </Pressable>

          <View style={[authStyles.card, styles.card]}>
            {step === "email" ? (
              <>
                <Text style={authStyles.heading}>Forgot password?</Text>
                <Text style={authStyles.subheading}>Enter your email and we'll send you a reset link.</Text>
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
                  />
                </View>
                {error && <Text style={authStyles.error}>{error}</Text>}
                <Pressable
                  style={[authStyles.button, loading && authStyles.buttonDisabled]}
                  onPress={handleRequestReset}
                  disabled={loading}
                >
                  <Text style={authStyles.buttonText}>{loading ? "Sending…" : "Send Reset Link"}</Text>
                </Pressable>
              </>
            ) : (
              <>
                <Text style={authStyles.heading}>Reset password</Text>
                <Text style={authStyles.subheading}>Enter the reset token and your new password.</Text>
                <View style={authStyles.fieldGroup}>
                  <Text style={authStyles.label}>Reset token</Text>
                  <TextInput
                    style={[authStyles.input, styles.tokenInput]}
                    value={token}
                    onChangeText={setToken}
                    autoCapitalize="none"
                    placeholder="Paste your reset token"
                    placeholderTextColor={COLORS.inkSubtle}
                    multiline
                  />
                </View>
                <View style={authStyles.fieldGroup}>
                  <Text style={authStyles.label}>New password</Text>
                  <TextInput
                    style={authStyles.input}
                    value={newPassword}
                    onChangeText={setNewPassword}
                    secureTextEntry
                    placeholder="••••••••"
                    placeholderTextColor={COLORS.inkSubtle}
                  />
                </View>
                <View style={authStyles.fieldGroup}>
                  <Text style={authStyles.label}>Confirm password</Text>
                  <TextInput
                    style={authStyles.input}
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                    secureTextEntry
                    placeholder="••••••••"
                    placeholderTextColor={COLORS.inkSubtle}
                  />
                </View>
                {error && <Text style={authStyles.error}>{error}</Text>}
                <Pressable
                  style={[authStyles.button, loading && authStyles.buttonDisabled]}
                  onPress={handleResetPassword}
                  disabled={loading}
                >
                  <Text style={authStyles.buttonText}>{loading ? "Resetting…" : "Reset Password"}</Text>
                </Pressable>
              </>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1, padding: 28, paddingTop: 16 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center", padding: 28 },
  backRow: { marginBottom: 24 },
  backText: { color: COLORS.primary, fontSize: 14, fontWeight: "700" },
  card: { marginBottom: 0 },
  tokenInput: { minHeight: 70, textAlignVertical: "top" },
  doneIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  doneIconText: { color: COLORS.onPrimary, fontSize: 32, fontWeight: "900" },
  doneTitle: { color: COLORS.ink, fontSize: 24, fontWeight: "800", marginBottom: 8 },
  doneSub: { color: COLORS.inkMuted, fontSize: 15, marginBottom: 32, textAlign: "center" },
});

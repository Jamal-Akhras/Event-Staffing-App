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
import { useJoinCodePreview } from "./useJoinCodePreview";
import { COLORS } from "../../theme/colors";

type Props = { onBack: () => void; withJoinCode?: boolean };

export function RegisterScreen({ onBack, withJoinCode = false }: Props) {
  const { register } = useAuth();
  const [joinCode, setJoinCode] = useState("");
  const { preview, error: codeError, checking } = useJoinCodePreview(withJoinCode ? joinCode : "");
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
    if (withJoinCode && !preview) {
      setError(codeError ?? "Enter the code your venue gave you.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await register(email.trim().toLowerCase(), password, preview?.code);
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
            <Text style={authStyles.subheading}>
              {withJoinCode ? "Join the venue you work for." : "Start applying for shifts today."}
            </Text>

            {withJoinCode && (
              <View style={authStyles.fieldGroup}>
                <Text style={authStyles.label}>Venue code</Text>
                <TextInput
                  style={authStyles.input}
                  value={joinCode}
                  onChangeText={(value) => setJoinCode(value.toUpperCase())}
                  autoCapitalize="characters"
                  autoCorrect={false}
                  placeholder="TEAM-XXXX-XXXX"
                  placeholderTextColor={COLORS.inkSubtle}
                />
                {checking && <Text style={authStyles.subheading}>Checking…</Text>}
                {preview && (
                  <Text style={authStyles.subheading}>
                    Joining {preview.venue_name}
                    {preview.default_role ? ` as ${preview.default_role}` : ""}
                  </Text>
                )}
                {!checking && !preview && codeError && (
                  <Text style={authStyles.error}>{codeError}</Text>
                )}
              </View>
            )}

            {SSO_ENABLED && !withJoinCode && <SsoButtons />}

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

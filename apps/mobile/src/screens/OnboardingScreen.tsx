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

import { MarketPicker } from "../components/MarketPicker";
import { getWorkerId, putWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Market } from "../types";

type Props = { onComplete: () => void };

const ROLES = ["Bar Staff", "Waiter / Waitress", "Host / Hostess", "Security", "Kitchen", "Event Staff", "Other"];

export function OnboardingScreen({ onComplete }: Props) {
  const workerId = getWorkerId();
  const [step, setStep] = useState(0);
  const [displayName, setDisplayName] = useState("");
  const [role, setRole] = useState("");
  const [market, setMarket] = useState<Market | null>(null);
  const [experienceYears, setExperienceYears] = useState("0");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canContinue = step === 0
    ? displayName.trim().length > 0 && role.trim().length > 0 && market !== null
    : true;

  const save = async () => {
    if (!market) {
      setStep(0);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await putWorker(`/workers/${workerId}`, {
        display_name: displayName.trim(),
        role: role.trim(),
        city: market.name,
        market_id: market.market_id,
        experience_years: Math.max(0, parseInt(experienceYears) || 0),
        bio: bio.trim() || null,
        languages: [],
        now: new Date().toISOString(),
      });
      onComplete();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.eyebrow}>Step {step + 1} of 2</Text>
          <Text style={styles.title}>{step === 0 ? "About you" : "Your experience"}</Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: step === 0 ? "50%" : "100%" }]} />
          </View>
        </View>

        {step === 0 ? (
          <View style={styles.fields}>
            <Field label="Display name">
              <TextInput
                style={styles.input}
                value={displayName}
                onChangeText={setDisplayName}
                placeholder="e.g. Alex Johnson"
                placeholderTextColor={COLORS.inkMuted}
                autoFocus
              />
            </Field>

            <Field label="Primary role">
              <View style={styles.chips}>
                {ROLES.map((r) => (
                  <Pressable
                    key={r}
                    style={[styles.chip, role === r && styles.chipActive]}
                    onPress={() => setRole(r)}
                  >
                    <Text style={[styles.chipText, role === r && styles.chipTextActive]}>{r}</Text>
                  </Pressable>
                ))}
              </View>
            </Field>

            <Field label="Your city">
              <MarketPicker
                selectedMarketId={market?.market_id ?? null}
                onSelect={setMarket}
              />
            </Field>
          </View>
        ) : (
          <View style={styles.fields}>
            <Field label="Years of experience">
              <View style={styles.stepper}>
                <Pressable style={styles.stepBtn} onPress={() => setExperienceYears(String(Math.max(0, parseInt(experienceYears) - 1)))}>
                  <Text style={styles.stepBtnText}>−</Text>
                </Pressable>
                <Text style={styles.stepValue}>{experienceYears}</Text>
                <Pressable style={styles.stepBtn} onPress={() => setExperienceYears(String(parseInt(experienceYears) + 1))}>
                  <Text style={styles.stepBtnText}>+</Text>
                </Pressable>
              </View>
            </Field>

            <Field label="Short bio (optional)">
              <TextInput
                style={[styles.input, styles.inputMulti]}
                value={bio}
                onChangeText={setBio}
                placeholder="A sentence about yourself and your experience…"
                placeholderTextColor={COLORS.inkMuted}
                multiline
                numberOfLines={3}
              />
            </Field>

            {error && <Text style={styles.errorText}>{error}</Text>}
          </View>
        )}

        <View style={styles.actions}>
          {step === 1 && (
            <Pressable style={styles.backBtn} onPress={() => setStep(0)}>
              <Text style={styles.backText}>Back</Text>
            </Pressable>
          )}
          <Pressable
            style={[styles.primaryBtn, (!canContinue || saving) && styles.primaryBtnDisabled]}
            disabled={!canContinue || saving}
            onPress={step === 0 ? () => setStep(1) : save}
          >
            <Text style={styles.primaryText}>{step === 0 ? "Continue" : saving ? "Setting up…" : "Finish setup"}</Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: 24, paddingBottom: 48, flexGrow: 1 },
  header: { marginBottom: 32, marginTop: 40 },
  eyebrow: { color: COLORS.primary, fontSize: 12, fontWeight: "900", letterSpacing: 1, textTransform: "uppercase" },
  title: { color: COLORS.ink, fontSize: 32, fontWeight: "900", marginTop: 6, marginBottom: 16 },
  progressBar: { height: 4, backgroundColor: COLORS.border, borderRadius: 2 },
  progressFill: { height: 4, backgroundColor: COLORS.primary, borderRadius: 2 },
  fields: { gap: 20, flex: 1 },
  field: { gap: 8 },
  fieldLabel: { color: COLORS.ink, fontSize: 14, fontWeight: "800" },
  input: {
    borderWidth: 1.5, borderColor: COLORS.border, borderRadius: 12,
    padding: 13, fontSize: 15, color: COLORS.ink, backgroundColor: COLORS.surface,
  },
  inputMulti: { height: 90, textAlignVertical: "top" },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999,
    borderWidth: 1.5, borderColor: COLORS.border, backgroundColor: COLORS.surface,
  },
  chipActive: { borderColor: COLORS.primary, backgroundColor: "rgba(14,90,58,0.08)" },
  chipText: { color: COLORS.inkMuted, fontWeight: "700", fontSize: 13 },
  chipTextActive: { color: COLORS.primary },
  stepper: { flexDirection: "row", alignItems: "center", gap: 20 },
  stepBtn: {
    width: 44, height: 44, borderRadius: 22, borderWidth: 1.5,
    borderColor: COLORS.border, alignItems: "center", justifyContent: "center",
  },
  stepBtnText: { color: COLORS.ink, fontSize: 22, fontWeight: "700", lineHeight: 26 },
  stepValue: { color: COLORS.ink, fontSize: 28, fontWeight: "900", minWidth: 40, textAlign: "center" },
  actions: { flexDirection: "row", gap: 12, marginTop: 32 },
  backBtn: {
    flex: 1, alignItems: "center", paddingVertical: 14, borderRadius: 14,
    borderWidth: 1.5, borderColor: COLORS.border,
  },
  backText: { color: COLORS.ink, fontWeight: "800" },
  primaryBtn: { flex: 2, alignItems: "center", paddingVertical: 14, borderRadius: 14, backgroundColor: COLORS.primary },
  primaryBtnDisabled: { opacity: 0.5 },
  primaryText: { color: COLORS.onPrimary, fontWeight: "900", fontSize: 15 },
  errorText: { color: COLORS.error, fontWeight: "700", textAlign: "center" },
});

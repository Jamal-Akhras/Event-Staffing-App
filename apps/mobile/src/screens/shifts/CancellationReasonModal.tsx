import { useEffect, useState } from "react";
import { ActivityIndicator, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { COLORS } from "../../theme/colors";

type CancellationReasonModalProps = {
  visible: boolean;
  title: string;
  consequence: string;
  confirmLabel: string;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
};

export function CancellationReasonModal({
  visible,
  title,
  consequence,
  confirmLabel,
  onClose,
  onConfirm,
}: CancellationReasonModalProps) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) {
      setReason("");
      setError(null);
    }
  }, [visible]);

  async function confirm() {
    if (reason.trim().length < 3) {
      setError("Add a short reason before continuing.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onConfirm(reason.trim());
      setReason("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.eyebrow}>Confirmation required</Text>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.consequence}>{consequence}</Text>
          <Text style={styles.label}>Reason</Text>
          <TextInput
            style={styles.input}
            value={reason}
            onChangeText={setReason}
            placeholder="Give the venue useful context"
            placeholderTextColor={COLORS.inkMuted}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
          {error && <Text style={styles.error}>{error}</Text>}
          <View style={styles.actions}>
            <Pressable style={styles.backButton} disabled={busy} onPress={onClose}>
              <Text style={styles.backText}>Keep it</Text>
            </Pressable>
            <Pressable style={styles.cancelButton} disabled={busy} onPress={confirm}>
              {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.cancelText}>{confirmLabel}</Text>}
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    justifyContent: "center",
    padding: 20,
    backgroundColor: "rgba(9, 18, 28, 0.56)",
  },
  card: {
    padding: 22,
    borderRadius: 22,
    backgroundColor: COLORS.surface,
  },
  eyebrow: {
    color: COLORS.error,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { marginTop: 6, color: COLORS.ink, fontSize: 23, fontWeight: "900" },
  consequence: { marginTop: 10, color: COLORS.inkMuted, fontSize: 14, lineHeight: 21 },
  label: { marginTop: 18, marginBottom: 7, color: COLORS.ink, fontSize: 13, fontWeight: "800" },
  input: {
    minHeight: 100,
    padding: 13,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surfaceMuted,
    color: COLORS.ink,
    fontSize: 14,
  },
  error: { marginTop: 8, color: COLORS.error, fontWeight: "700" },
  actions: { flexDirection: "row", gap: 10, marginTop: 18 },
  backButton: { flex: 1, alignItems: "center", paddingVertical: 13, borderRadius: 14, backgroundColor: COLORS.surfaceMuted },
  backText: { color: COLORS.ink, fontWeight: "800" },
  cancelButton: { flex: 1, alignItems: "center", paddingVertical: 13, borderRadius: 14, backgroundColor: COLORS.error },
  cancelText: { color: "#fff", fontWeight: "900" },
});

import { useState } from "react";
import { Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { postWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";

type Props = {
  bookingId: string;
  shiftRole: string;
  shiftLocation: string;
  onDone: () => void;
  onSkip: () => void;
};

export function RatingModal({ bookingId, shiftRole, shiftLocation, onDone, onSkip }: Props) {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (stars === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await postWorker(`/bookings/${bookingId}/rate`, { stars, comment: comment || undefined });
      onDone();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  };

  return (
    <Modal transparent animationType="fade" visible>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.eyebrow}>Rate your shift</Text>
          <Text style={styles.title}>{shiftRole}</Text>
          <Text style={styles.subtitle}>{shiftLocation}</Text>

          <View style={styles.stars}>
            {[1, 2, 3, 4, 5].map((n) => (
              <Pressable key={n} onPress={() => setStars(n)} hitSlop={8}>
                <Text style={[styles.star, stars >= n && styles.starActive]}>★</Text>
              </Pressable>
            ))}
          </View>

          <TextInput
            style={styles.input}
            placeholder="Leave a comment (optional)"
            placeholderTextColor={COLORS.inkMuted}
            value={comment}
            onChangeText={setComment}
            multiline
            numberOfLines={3}
          />

          {error && <Text style={styles.error}>{error}</Text>}

          <View style={styles.actions}>
            <Pressable style={styles.skipBtn} onPress={onSkip}>
              <Text style={styles.skipText}>Skip</Text>
            </Pressable>
            <Pressable
              style={[styles.submitBtn, (stars === 0 || submitting) && styles.submitDisabled]}
              onPress={submit}
              disabled={stars === 0 || submitting}
            >
              <Text style={styles.submitText}>{submitting ? "Submitting…" : "Submit rating"}</Text>
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
    alignItems: "center",
    backgroundColor: "rgba(15,23,32,0.55)",
    padding: 24,
  },
  card: {
    width: "100%",
    maxWidth: 380,
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 24,
    gap: 12,
  },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 22, fontWeight: "900" },
  subtitle: { color: COLORS.inkMuted, fontSize: 14, marginTop: -6 },
  stars: { flexDirection: "row", gap: 8, marginVertical: 4 },
  star: { fontSize: 36, color: COLORS.border },
  starActive: { color: "#F59E0B" },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 12,
    color: COLORS.ink,
    fontSize: 14,
    minHeight: 72,
    textAlignVertical: "top",
  },
  error: { color: COLORS.error, fontSize: 13, fontWeight: "700" },
  actions: { flexDirection: "row", gap: 10, marginTop: 4 },
  skipBtn: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: "center",
  },
  skipText: { color: COLORS.inkMuted, fontWeight: "700" },
  submitBtn: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    alignItems: "center",
  },
  submitDisabled: { opacity: 0.4 },
  submitText: { color: "#fff", fontWeight: "900", fontSize: 15 },
});

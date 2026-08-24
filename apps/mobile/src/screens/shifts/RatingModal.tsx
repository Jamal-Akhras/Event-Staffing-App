import { Ionicons } from "@expo/vector-icons";
import { useState } from "react";
import { Image, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { postWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import type { PendingRating } from "../../types";

type Props = {
  rating: PendingRating;
  onDone: () => void;
  onSkip: () => void;
};

const STAR_LABELS = ["", "Poor", "Fair", "Good", "Great", "Excellent"];

export function RatingModal({ rating, onDone, onSkip }: Props) {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initials = rating.target_name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  async function submit() {
    if (stars === 0) return;
    setSubmitting(true);
    setError(null);
    try {
      await postWorker(`/bookings/${rating.booking_id}/rate`, {
        stars,
        comment: comment.trim() || undefined,
      });
      onDone();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <Modal transparent animationType="slide" visible statusBarTranslucent onRequestClose={onSkip}>
      <View style={styles.backdrop}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onSkip} accessibilityLabel="Rate later" />
        <View style={styles.sheet} accessibilityViewIsModal>
          <View style={styles.handle} />
          <Text style={styles.eyebrow}>Shift complete</Text>
          {rating.target_avatar_url ? (
            <Image source={{ uri: rating.target_avatar_url }} style={styles.avatar} />
          ) : (
            <View style={[styles.avatar, styles.avatarFallback]}>
              <Text style={styles.initials}>{initials}</Text>
            </View>
          )}
          <Text style={styles.title}>How was {rating.target_name}?</Text>
          <Text style={styles.subtitle}>
            {rating.shift_role} · {formatDate(rating.start_time)}
          </Text>

          <View style={styles.stars} accessibilityRole="radiogroup">
            {[1, 2, 3, 4, 5].map((value) => (
              <Pressable
                key={value}
                style={styles.starButton}
                onPress={() => setStars(value)}
                accessibilityRole="radio"
                accessibilityState={{ selected: stars === value }}
                accessibilityLabel={`${value} star${value === 1 ? "" : "s"}`}
              >
                <Ionicons
                  name={stars >= value ? "star" : "star-outline"}
                  size={38}
                  color={stars >= value ? "#F5B82E" : COLORS.borderStrong}
                />
              </Pressable>
            ))}
          </View>
          <Text style={styles.starLabel}>{stars ? STAR_LABELS[stars] : "Tap to rate"}</Text>

          {stars > 0 && (
            <TextInput
              style={styles.input}
              placeholder="Share a little more (optional)"
              placeholderTextColor={COLORS.inkSubtle}
              value={comment}
              onChangeText={setComment}
              maxLength={1000}
              multiline
              numberOfLines={3}
              textAlignVertical="top"
            />
          )}

          {error && <Text style={styles.error}>{error}</Text>}

          <Pressable
            style={[styles.submit, (stars === 0 || submitting) && styles.disabled]}
            onPress={submit}
            disabled={stars === 0 || submitting}
            accessibilityRole="button"
          >
            <Text style={styles.submitText}>{submitting ? "Sending…" : "Submit rating"}</Text>
          </Pressable>
          <Pressable style={styles.later} onPress={onSkip} accessibilityRole="button">
            <Text style={styles.laterText}>Not now</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(9,18,27,0.54)" },
  sheet: {
    alignItems: "center",
    paddingHorizontal: 24,
    paddingTop: 10,
    paddingBottom: 34,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    backgroundColor: COLORS.surface,
  },
  handle: { width: 42, height: 5, marginBottom: 22, borderRadius: 4, backgroundColor: COLORS.border },
  eyebrow: { color: COLORS.primary, fontSize: 11, fontWeight: "900", letterSpacing: 1.2, textTransform: "uppercase" },
  avatar: { width: 68, height: 68, marginTop: 18, borderRadius: 23 },
  avatarFallback: { alignItems: "center", justifyContent: "center", backgroundColor: COLORS.primary },
  initials: { color: COLORS.onPrimary, fontSize: 22, fontWeight: "900" },
  title: { marginTop: 16, color: COLORS.ink, fontSize: 24, fontWeight: "900", textAlign: "center", letterSpacing: -0.5 },
  subtitle: { marginTop: 6, color: COLORS.inkMuted, fontSize: 14 },
  stars: { flexDirection: "row", marginTop: 24, gap: 5 },
  starButton: { padding: 3 },
  starLabel: { minHeight: 20, marginTop: 8, color: COLORS.inkMuted, fontSize: 13, fontWeight: "700" },
  input: { width: "100%", minHeight: 86, marginTop: 18, padding: 13, borderWidth: 1, borderColor: COLORS.border, borderRadius: 15, color: COLORS.ink, backgroundColor: COLORS.surfaceMuted },
  error: { width: "100%", marginTop: 12, color: COLORS.error, fontSize: 13, fontWeight: "700" },
  submit: { width: "100%", minHeight: 52, alignItems: "center", justifyContent: "center", marginTop: 20, borderRadius: 16, backgroundColor: COLORS.primary },
  disabled: { opacity: 0.38 },
  submitText: { color: COLORS.onPrimary, fontSize: 16, fontWeight: "900" },
  later: { minHeight: 44, justifyContent: "center", paddingHorizontal: 20, marginTop: 5 },
  laterText: { color: COLORS.inkMuted, fontSize: 14, fontWeight: "700" },
});

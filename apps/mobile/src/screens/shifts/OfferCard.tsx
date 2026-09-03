import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { fetchWorker, postWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { ShiftOffer } from "../../types";
import { formatClock, formatDayDate } from "../../lib/format";

type OfferCardProps = {
  onChanged: () => void;
};

export function OfferCard({ onChanged }: OfferCardProps) {
  const [offers, setOffers] = useState<ShiftOffer[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const all = await fetchWorker<ShiftOffer[]>("/me/shift-offers");
      setOffers(all.filter((offer) => offer.status === "pending"));
    } catch {
      setOffers([]);
    }
  }, []);

  useEffect(() => {
    void load();
    const interval = setInterval(() => void load(), 20000);
    return () => clearInterval(interval);
  }, [load]);

  const answer = async (offer: ShiftOffer, action: "accept" | "decline") => {
    setBusyId(offer.offer_id);
    setError(null);
    try {
      await postWorker(`/me/shift-offers/${offer.offer_id}/${action}`, {
        now: new Date().toISOString(),
      });
      await load();
      onChanged();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusyId(null);
    }
  };

  if (offers.length === 0 && !error) return null;

  return (
    <View style={styles.wrap}>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {offers.map((offer) => {
        const start = new Date(offer.shift?.start_time ?? offer.offered_at);
        const end = offer.shift ? new Date(offer.shift.end_time) : null;
        return (
          <View key={offer.offer_id} style={styles.card}>
            <Text style={styles.eyebrow}>Shift offered to you</Text>
            <Text style={styles.venue}>{offer.shift?.venue_name ?? "A venue"}</Text>
            <Text style={styles.role}>
              {offer.shift?.role ?? "Shift"} · {formatDayDate(start)} · {formatClock(start)}
              {end ? ` – ${formatClock(end)}` : ""}
            </Text>
            {offer.expires_at ? (
              <Text style={styles.expiry}>
                Answer by {formatDayDate(new Date(offer.expires_at))} {formatClock(new Date(offer.expires_at))} or it moves on
              </Text>
            ) : null}
            <View style={styles.actions}>
              <Pressable
                style={[styles.accept, busyId === offer.offer_id && styles.disabled]}
                disabled={busyId !== null}
                onPress={() => void answer(offer, "accept")}
                accessibilityRole="button"
              >
                <Text style={styles.acceptText}>Accept shift</Text>
              </Pressable>
              <Pressable
                style={[styles.decline, busyId === offer.offer_id && styles.disabled]}
                disabled={busyId !== null}
                onPress={() => void answer(offer, "decline")}
                accessibilityRole="button"
              >
                <Text style={styles.declineText}>Decline</Text>
              </Pressable>
            </View>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: SPACE.s3 },
  card: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
    borderRadius: RADIUS.lg,
    padding: SPACE.s4,
  },
  eyebrow: { ...TYPE.eyebrow, color: COLORS.primary },
  venue: { ...TYPE.venue, color: COLORS.ink, marginTop: SPACE.s2 },
  role: { ...TYPE.body, color: COLORS.inkMuted, marginTop: 2 },
  expiry: { ...TYPE.meta, color: COLORS.inkSubtle, marginTop: SPACE.s2 },
  actions: { flexDirection: "row", gap: SPACE.s3, marginTop: SPACE.s4 },
  accept: {
    flex: 1,
    backgroundColor: COLORS.primary,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3,
    alignItems: "center",
  },
  acceptText: { ...TYPE.action, color: COLORS.onPrimary },
  decline: {
    flex: 1,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s3,
    alignItems: "center",
  },
  declineText: { ...TYPE.action, color: COLORS.inkMuted },
  disabled: { opacity: 0.5 },
  error: { ...TYPE.meta, color: COLORS.error },
});

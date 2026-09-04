import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { fetchWorker, getWorkerId, postWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { RADIUS, SPACE } from "../../theme/space";
import { TYPE } from "../../theme/type";
import type { ShiftChangeRequest } from "../../types";
import { formatClock, formatDayDate } from "../../lib/format";

const PENDING = ["pending_replacement", "pending_manager"];

type CoverAskCardProps = {
  onChanged: () => void;
};

export function CoverAskCard({ onChanged }: CoverAskCardProps) {
  const workerId = getWorkerId();
  const [requests, setRequests] = useState<ShiftChangeRequest[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const all = await fetchWorker<ShiftChangeRequest[]>("/me/shift-change-requests");
      setRequests(all.filter((request) => PENDING.includes(request.status)));
    } catch {
      setRequests([]);
    }
  }, []);

  useEffect(() => {
    void load();
    const interval = setInterval(() => void load(), 20000);
    return () => clearInterval(interval);
  }, [load]);

  const act = async (request: ShiftChangeRequest, action: string) => {
    setBusyId(request.request_id);
    setError(null);
    try {
      await postWorker(`/me/shift-change-requests/${request.request_id}/${action}`, {
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

  const asks = requests.filter(
    (request) =>
      request.status === "pending_replacement" && request.replacement_worker_id === workerId,
  );
  const mine = requests.filter((request) => request.worker_id === workerId);

  if (asks.length === 0 && mine.length === 0 && !error) return null;

  return (
    <View style={styles.wrap}>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {asks.map((request) => {
        const busy = busyId === request.request_id;
        return (
          <View key={request.request_id} style={styles.askCard}>
            <Text style={styles.eyebrow}>Cover request</Text>
            <Text style={styles.venue}>{request.shift?.venue_name ?? "A venue"}</Text>
            <Text style={styles.role}>
              {request.shift?.role ?? "Shift"}
              {request.shift ? ` · ${whenLine(request.shift.start_time, request.shift.end_time)}` : ""}
            </Text>
            <Text style={styles.note}>
              A colleague asked you to take this shift. Accepting sends it to the manager.
            </Text>
            <View style={styles.actions}>
              <Pressable
                style={[styles.accept, busy && styles.disabled]}
                disabled={busyId !== null}
                onPress={() => void act(request, "accept-replacement")}
                accessibilityRole="button"
              >
                <Text style={styles.acceptText}>I can cover it</Text>
              </Pressable>
              <Pressable
                style={[styles.decline, busy && styles.disabled]}
                disabled={busyId !== null}
                onPress={() => void act(request, "decline-replacement")}
                accessibilityRole="button"
              >
                <Text style={styles.declineText}>Not this time</Text>
              </Pressable>
            </View>
          </View>
        );
      })}
      {mine.map((request) => {
        const busy = busyId === request.request_id;
        return (
          <View key={request.request_id} style={styles.mineRow}>
            <View style={styles.grow}>
              <Text style={styles.mineTitle}>
                {request.change_type === "release" ? "Release requested" : "Cover requested"}
                {request.shift ? ` · ${request.shift.role}` : ""}
              </Text>
              <Text style={styles.mineMeta}>
                {request.status === "pending_replacement"
                  ? "Waiting on your colleague"
                  : "Waiting on the manager"}
                {request.shift ? ` · ${formatDayDate(new Date(request.shift.start_time))}` : ""}
              </Text>
            </View>
            <Pressable
              style={[styles.withdraw, busy && styles.disabled]}
              disabled={busyId !== null}
              onPress={() => void act(request, "withdraw")}
              accessibilityRole="button"
            >
              <Text style={styles.withdrawText}>Withdraw</Text>
            </Pressable>
          </View>
        );
      })}
    </View>
  );
}

function whenLine(start: string, end: string): string {
  const from = new Date(start);
  return `${formatDayDate(from)} · ${formatClock(from)} – ${formatClock(new Date(end))}`;
}

const styles = StyleSheet.create({
  wrap: { gap: SPACE.s3 },
  askCard: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.primary,
    borderRadius: RADIUS.lg,
    padding: SPACE.s4,
  },
  eyebrow: { ...TYPE.eyebrow, color: COLORS.primary },
  venue: { ...TYPE.venue, color: COLORS.ink, marginTop: SPACE.s2 },
  role: { ...TYPE.body, color: COLORS.inkMuted, marginTop: 2 },
  note: { ...TYPE.meta, color: COLORS.inkSubtle, marginTop: SPACE.s2 },
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
  mineRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACE.s3,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s4,
  },
  grow: { flex: 1 },
  mineTitle: { ...TYPE.body, color: COLORS.ink },
  mineMeta: { ...TYPE.meta, color: COLORS.inkSubtle, marginTop: 2 },
  withdraw: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.md,
    paddingVertical: SPACE.s2,
    paddingHorizontal: SPACE.s3,
  },
  withdrawText: { ...TYPE.meta, color: COLORS.inkMuted },
  disabled: { opacity: 0.5 },
  error: { ...TYPE.meta, color: COLORS.error },
});

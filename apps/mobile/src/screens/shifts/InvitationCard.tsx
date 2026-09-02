import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { fetchWorker, postWorker } from "../../lib/api";
import { COLORS } from "../../theme/colors";
import { TYPE } from "../../theme/type";

type Invitation = {
  relationship_id: string;
  venue_id: string;
  venue_name: string | null;
  relationship_type: string;
  default_role: string | null;
  invited_at: string;
};

const TYPE_LABELS: Record<string, string> = {
  permanent: "permanent",
  part_time: "part time",
  bank: "bank",
};

export function InvitationCard() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const found = await fetchWorker<Invitation[]>("/me/invitations");
    setInvitations(found);
  }, []);

  useEffect(() => {
    load().catch(() => setInvitations([]));
  }, [load]);

  async function respond(invitation: Invitation, accepted: boolean) {
    setBusy(invitation.relationship_id);
    setError(null);
    try {
      const action = accepted ? "accept" : "decline";
      await postWorker(`/me/invitations/${invitation.relationship_id}/${action}`);
      await load();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  if (invitations.length === 0) return null;

  return (
    <View style={styles.wrap}>
      {invitations.map((invitation) => (
        <View key={invitation.relationship_id} style={styles.card}>
          <Text style={styles.eyebrow}>Invitation</Text>
          <Text style={styles.title}>
            {invitation.venue_name ?? "A venue"} would like you to join their team
          </Text>
          <Text style={styles.body}>
            As {TYPE_LABELS[invitation.relationship_type] ?? invitation.relationship_type} staff
            {invitation.default_role ? `, working as ${invitation.default_role}` : ""}. You choose
            whether to accept.
          </Text>
          {error && <Text style={styles.error}>{error}</Text>}
          <View style={styles.actions}>
            <Pressable
              style={[styles.button, styles.accept]}
              disabled={busy === invitation.relationship_id}
              onPress={() => respond(invitation, true)}
            >
              {busy === invitation.relationship_id ? (
                <ActivityIndicator size="small" color={COLORS.onPrimary} />
              ) : (
                <Text style={styles.acceptText}>Accept</Text>
              )}
            </Pressable>
            <Pressable
              style={styles.button}
              disabled={busy === invitation.relationship_id}
              onPress={() => respond(invitation, false)}
            >
              <Text style={styles.declineText}>Not now</Text>
            </Pressable>
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 12 },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.primary,
    padding: 18,
  },
  eyebrow: { ...TYPE.eyebrow, color: COLORS.primary },
  title: { ...TYPE.venueSmall, color: COLORS.ink, marginTop: 8 },
  body: { ...TYPE.body, color: COLORS.inkMuted, marginTop: 6 },
  error: { ...TYPE.meta, color: COLORS.error, marginTop: 8 },
  actions: { flexDirection: "row", gap: 10, marginTop: 16 },
  button: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 11,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  accept: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  acceptText: { ...TYPE.action, color: COLORS.onPrimary },
  declineText: { ...TYPE.action, color: COLORS.inkMuted },
});

import { useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useNavigation } from "@react-navigation/native";

import { EmptyState } from "../components/EmptyState";
import { SectionHeader } from "../components/SectionHeader";
import { SegmentedTabs } from "../components/SegmentedTabs";
import { ApiError, fetchWorker, getWorkerId, postWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import { SPACE } from "../theme/space";
import { TYPE } from "../theme/type";
import type { Application } from "../types";
import { DecidedRow, DecisionCard, WaitingRow } from "./applications/ApplicationRows";
import { CancellationReasonModal } from "./shifts/CancellationReasonModal";
import { MessagingModal } from "./shifts/MessagingModal";

type ApplicationTab = "waiting" | "decided";

const TABS: { key: ApplicationTab; label: string }[] = [
  { key: "waiting", label: "Waiting" },
  { key: "decided", label: "Decided" },
];

export function ApplicationsScreen() {
  const workerId = getWorkerId();
  const navigation = useNavigation<{ navigate: (screen: "Shifts") => void }>();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<ApplicationTab>("waiting");
  const [messaging, setMessaging] = useState<Application | null>(null);
  const [withdrawing, setWithdrawing] = useState<Application | null>(null);
  const [acknowledged, setAcknowledged] = useState<string[]>([]);

  const load = async () => {
    try {
      const data = await fetchWorker<Application[]>(
        `/applications?worker_id=${encodeURIComponent(workerId)}`
      );
      setApplications(data);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 20000);
    return () => clearInterval(interval);
  }, []);

  const now = new Date();
  const waiting = useMemo(
    () =>
      applications
        .filter((item) => item.status === "applied")
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()),
    [applications]
  );
  const decided = useMemo(
    () => applications.filter((item) => item.status !== "applied"),
    [applications]
  );
  const freshlyApproved = useMemo(
    () => decided.filter((item) => item.status === "approved" && !acknowledged.includes(item.application_id)),
    [decided, acknowledged]
  );

  return (
    <View style={styles.screen}>
      <SegmentedTabs tabs={TABS} active={tab} onChange={setTab} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {error ? <Text style={styles.error}>{error}</Text> : null}

        {tab === "waiting" && (
          <>
            {freshlyApproved.map((application) => (
              <DecisionCard
                key={application.application_id}
                application={application}
                onView={() => {
                  setAcknowledged((current) => [...current, application.application_id]);
                  navigation.navigate("Shifts");
                }}
              />
            ))}

            {waiting.length === 0 && loaded ? (
              <EmptyState
                title="Nothing waiting"
                message="Shifts you apply for from Browse show up here until the venue decides."
              />
            ) : (
              <View>
                <SectionHeader title="Waiting on a decision" count={String(waiting.length)} />
                {waiting.map((application) => (
                  <WaitingRow
                    key={application.application_id}
                    application={application}
                    now={now}
                    onMessage={() => setMessaging(application)}
                    onWithdraw={() => setWithdrawing(application)}
                  />
                ))}
              </View>
            )}
          </>
        )}

        {tab === "decided" && (
          decided.length === 0 && loaded ? (
            <EmptyState title="Nothing decided yet" message="Answers from venues will collect here." />
          ) : (
            <View>
              <SectionHeader title="Recently decided" count={String(decided.length)} />
              {decided.map((application) => (
                <DecidedRow key={application.application_id} application={application} />
              ))}
            </View>
          )
        )}
      </ScrollView>

      <MessagingModal
        application={messaging}
        booking={null}
        onClose={() => setMessaging(null)}
      />

      <CancellationReasonModal
        visible={withdrawing !== null}
        title="Withdraw this application?"
        consequence="The venue will no longer be able to approve it. You can message them first if you'd rather talk."
        confirmLabel="Withdraw"
        onClose={() => setWithdrawing(null)}
        onConfirm={withdraw}
      />
    </View>
  );

  async function withdraw(reason: string) {
    if (!withdrawing) return;
    try {
      await postWorker(`/applications/${withdrawing.application_id}/withdraw`, {
        reason,
        now: new Date().toISOString(),
      });
      await load();
      setWithdrawing(null);
    } catch (err) {
      if (err instanceof ApiError && err.serverDetail) {
        throw new Error(err.serverDetail);
      }
      throw err;
    }
  }
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  error: { ...TYPE.meta, color: COLORS.error },
});

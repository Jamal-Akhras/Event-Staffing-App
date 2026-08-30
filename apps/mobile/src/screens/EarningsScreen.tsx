import { useCallback, useEffect, useMemo, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { EmptyState } from "../components/EmptyState";
import { Money } from "../components/Money";
import { SectionHeader } from "../components/SectionHeader";
import { SegmentedTabs } from "../components/SegmentedTabs";
import { fetchWorker, getWorkerId } from "../lib/api";
import { COLORS } from "../theme/colors";
import { RADIUS, SPACE } from "../theme/space";
import { NUMERIC, TYPE } from "../theme/type";
import { EarningsEntryRow } from "./earnings/EarningsEntryRow";
import { PERIOD_LABELS, type EarningsSummary, type Period } from "./earnings/earningsTypes";

const PERIODS: { key: Period; label: string }[] = (
  ["week", "month", "year"] as Period[]
).map((key) => ({ key, label: PERIOD_LABELS[key] }));

const HEADINGS: Record<Period, string> = {
  week: "Earned this week",
  month: "Earned this month",
  year: "Earned this year",
};

export default function EarningsScreen() {
  const workerId = getWorkerId();
  const [period, setPeriod] = useState<Period>("month");
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (selected: Period) => {
      setLoading(true);
      setError(null);
      try {
        setSummary(await fetchWorker<EarningsSummary>(`/workers/${workerId}/earnings?period=${selected}`));
      } catch (err) {
        setSummary(null);
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [workerId]
  );

  useEffect(() => {
    load(period);
  }, [period, load]);

  const total = useMemo(() => {
    if (!summary) return 0;
    return Number(summary.total_paid) + Number(summary.total_pending);
  }, [summary]);

  const entries = summary?.entries ?? [];

  return (
    <View style={styles.screen}>
      <SegmentedTabs tabs={PERIODS} active={period} onChange={setPeriod} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {error ? <Text style={styles.error}>{error}</Text> : null}

        <View style={styles.panel}>
          <Text style={styles.label}>{HEADINGS[period]}</Text>
          <Money amount={total} currency={summary?.currency} style={styles.hero} />
          <View style={styles.split}>
            <View>
              <Text style={styles.label}>Paid</Text>
              <Money amount={summary?.total_paid ?? 0} currency={summary?.currency} style={styles.figure} />
            </View>
            <View style={styles.right}>
              <Text style={styles.label}>Awaiting</Text>
              <Money amount={summary?.total_pending ?? 0} currency={summary?.currency} style={styles.figure} />
            </View>
          </View>
          <Text style={styles.note}>Each venue pays you directly</Text>
        </View>

        {entries.length === 0 && !loading ? (
          <EmptyState
            title="Nothing yet"
            message="Finished shifts show up here with what they paid and whether the venue has settled."
          />
        ) : (
          <View>
            <SectionHeader
              title={PERIOD_LABELS[period]}
              count={`${entries.length} ${entries.length === 1 ? "shift" : "shifts"}`}
            />
            {entries.map((entry) => (
              <EarningsEntryRow key={entry.booking_id} entry={entry} />
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  panel: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: RADIUS.lg,
    padding: SPACE.s5,
  },
  label: { ...TYPE.eyebrow, color: COLORS.inkSubtle },
  hero: { ...NUMERIC, fontSize: 40, fontWeight: "400", letterSpacing: -1.4, color: COLORS.ink, marginTop: SPACE.s2 },
  split: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: SPACE.s4,
    paddingTop: SPACE.s4,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  right: { alignItems: "flex-end" },
  figure: { ...TYPE.number, ...NUMERIC, color: COLORS.ink, marginTop: 4 },
  note: { ...TYPE.meta, color: COLORS.inkSubtle, marginTop: SPACE.s3 },
  error: { ...TYPE.meta, color: COLORS.error },
});

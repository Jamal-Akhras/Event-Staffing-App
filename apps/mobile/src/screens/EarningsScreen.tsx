import { useCallback, useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { EmptyState } from "../components/EmptyState";
import { fetchWorker, getWorkerId } from "../lib/api";
import { COLORS } from "../theme/colors";
import { EarningsRow } from "./earnings/EarningsRow";
import { EarningsSummaryCard } from "./earnings/EarningsSummaryCard";
import { PeriodSelector } from "./earnings/PeriodSelector";
import type { EarningsSummary, Period } from "./earnings/earningsTypes";

export default function EarningsScreen() {
  const workerId = getWorkerId();
  const [period, setPeriod] = useState<Period>("week");
  const [summary, setSummary] = useState<EarningsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEarnings = useCallback(async (selectedPeriod: Period) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWorker<EarningsSummary>(
        `/workers/${workerId}/earnings?period=${selectedPeriod}`
      );
      setSummary(data);
    } catch (err) {
      setSummary(null);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [workerId]);

  useEffect(() => {
    fetchEarnings(period);
  }, [period, fetchEarnings]);

  const paidEntries = useMemo(
    () => summary?.entries.filter((entry) => entry.status === "paid") ?? [],
    [summary]
  );
  const pendingEntries = useMemo(
    () => summary?.entries.filter((entry) => entry.status === "pending") ?? [],
    [summary]
  );

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.scroll}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Text style={styles.eyebrow}>Pay tracking</Text>
        <Text style={styles.title}>Earnings</Text>
        <Text style={styles.subtitle}>See paid and pending shift earnings by period.</Text>
      </View>

      <EarningsSummaryCard period={period} summary={summary} loading={loading} />
      <PeriodSelector period={period} onChange={setPeriod} />

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={() => fetchEarnings(period)} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      )}

      {!loading && !error && summary?.entries.length === 0 && (
        <EmptyState
          title="No earnings yet"
          message="Completed and paid shifts will build your earnings history."
        />
      )}

      <EarningsSection title="Paid" entries={paidEntries} />
      <EarningsSection title="Pending" entries={pendingEntries} />
    </ScrollView>
  );
}

function EarningsSection({
  title,
  entries,
}: {
  title: string;
  entries: NonNullable<EarningsSummary["entries"]>;
}) {
  if (entries.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionHeader}>{title}</Text>
      {entries.map((entry) => (
        <EarningsRow key={entry.booking_id} entry={entry} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.canvas },
  scroll: { padding: 20, paddingBottom: 40 },
  header: { marginBottom: 16 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  subtitle: { color: COLORS.inkMuted, fontSize: 14, lineHeight: 20, marginTop: 6 },
  errorBox: {
    alignItems: "center",
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.error,
    borderRadius: 12,
    backgroundColor: COLORS.surface,
  },
  errorText: { color: COLORS.error, fontWeight: "600", marginBottom: 10 },
  retryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: COLORS.primary,
  },
  retryText: { color: COLORS.onPrimary, fontWeight: "800" },
  section: { marginBottom: 24 },
  sectionHeader: {
    marginBottom: 8,
    color: COLORS.inkMuted,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
});

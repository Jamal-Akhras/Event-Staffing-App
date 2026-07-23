import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { formatMoney, PERIOD_LABELS, type EarningsSummary, type Period } from "./earningsTypes";

type EarningsSummaryCardProps = {
  period: Period;
  summary: EarningsSummary | null;
  loading: boolean;
};

export function EarningsSummaryCard({
  period,
  summary,
  loading,
}: EarningsSummaryCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{PERIOD_LABELS[period]} earnings</Text>
      {loading ? (
        <ActivityIndicator color={COLORS.primary} size="large" style={styles.loading} />
      ) : (
        <>
          <Text style={styles.amount}>{formatMoney(summary?.total_paid ?? 0, summary?.currency)}</Text>
          {(summary?.total_pending ?? 0) > 0 && (
            <Text style={styles.pending}>
              +{formatMoney(summary?.total_pending ?? 0, summary?.currency)} pending
            </Text>
          )}
        </>
      )}
      <Text style={styles.disclaimer}>Before taxes and deductions</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
  },
  label: {
    color: COLORS.inkMuted,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  loading: {
    marginVertical: 14,
  },
  amount: {
    marginTop: 6,
    color: COLORS.primary,
    fontSize: 36,
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  pending: {
    marginTop: 4,
    color: COLORS.warning,
    fontWeight: "700",
    fontSize: 13,
  },
  disclaimer: {
    marginTop: 8,
    color: COLORS.inkMuted,
    fontSize: 12,
  },
});

import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { fetchPublicJson } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Market } from "../types";

type MarketPickerProps = {
  selectedMarketId: string | null;
  onSelect: (market: Market) => void;
};

export function MarketPicker({ selectedMarketId, onSelect }: MarketPickerProps) {
  const [markets, setMarkets] = useState<Market[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchPublicJson<Market[]>("/markets")
      .then((data) => setMarkets(data))
      .catch((err: Error) => {
        setMarkets(null);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <Text style={styles.stateText}>Loading cities…</Text>;
  }

  if (error || markets === null) {
    return (
      <View style={styles.stateBlock}>
        <Text style={styles.errorText}>{error ?? "Couldn't load cities."}</Text>
        <Pressable style={styles.retryBtn} onPress={load}>
          <Text style={styles.retryText}>Try again</Text>
        </Pressable>
      </View>
    );
  }

  if (markets.length === 0) {
    return <Text style={styles.stateText}>No launch cities are available yet.</Text>;
  }

  return (
    <View style={styles.chips}>
      {markets.map((market) => {
        const isActive = market.market_id === selectedMarketId;
        return (
          <Pressable
            key={market.market_id}
            style={[styles.chip, isActive && styles.chipActive]}
            onPress={() => onSelect(market)}
            accessibilityRole="button"
            accessibilityLabel={`Select ${market.name}`}
          >
            <Text style={[styles.chipText, isActive && styles.chipTextActive]}>
              {market.name}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  chipActive: { borderColor: COLORS.primary, backgroundColor: "rgba(14,90,58,0.08)" },
  chipText: { color: COLORS.inkMuted, fontWeight: "700", fontSize: 13 },
  chipTextActive: { color: COLORS.primary },
  stateText: { color: COLORS.inkMuted, fontWeight: "600", fontSize: 13 },
  stateBlock: { gap: 8 },
  errorText: { color: COLORS.error, fontWeight: "700", fontSize: 13 },
  retryBtn: {
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  retryText: { color: COLORS.primary, fontWeight: "800", fontSize: 13 },
});

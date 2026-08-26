import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { fetchPublicJson } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Market } from "../types";
import { LoadFailure, loadStateStyles } from "./LoadFailure";

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
    return <Text style={loadStateStyles.stateText}>Loading cities…</Text>;
  }

  if (error || markets === null) {
    return <LoadFailure message={error ?? "Couldn't load cities."} onRetry={load} />;
  }

  if (markets.length === 0) {
    return <Text style={loadStateStyles.stateText}>No launch cities are available yet.</Text>;
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
});

import { StyleSheet, Text, type TextStyle } from "react-native";

import { COLORS } from "../theme/colors";
import { NUMERIC, TYPE } from "../theme/type";

const SYMBOLS: Record<string, string> = { GBP: "£", EUR: "€", USD: "$" };

type MoneyProps = {
  amount: string | number;
  currency?: string;
  suffix?: string;
  style?: TextStyle;
};

export function Money({ amount, currency = "GBP", suffix, style }: MoneyProps) {
  const value = Number(amount).toFixed(2);
  return (
    <Text style={[styles.value, style]}>
      <Text style={styles.symbol}>{SYMBOLS[currency] ?? currency}</Text>
      {value}
      {suffix ? <Text style={styles.suffix}>{suffix}</Text> : null}
    </Text>
  );
}

const styles = StyleSheet.create({
  value: { ...TYPE.number, ...NUMERIC, color: COLORS.ink },
  symbol: { color: COLORS.inkSubtle, fontWeight: "400" },
  suffix: { ...TYPE.meta, color: COLORS.inkMuted },
});

import type { TextStyle } from "react-native";

export const NUMERIC: TextStyle = { fontVariant: ["tabular-nums"] };

export const TYPE = {
  screen: { fontSize: 26, fontWeight: "500" as const, letterSpacing: -0.7, lineHeight: 30 },
  venue: { fontSize: 19, fontWeight: "500" as const, letterSpacing: -0.4, lineHeight: 24 },
  venueSmall: { fontSize: 16, fontWeight: "500" as const, letterSpacing: -0.3, lineHeight: 21 },
  section: { fontSize: 18, fontWeight: "600" as const, lineHeight: 22 },
  body: { fontSize: 14, fontWeight: "400" as const, lineHeight: 20 },
  meta: { fontSize: 13, fontWeight: "400" as const, lineHeight: 18 },
  caption: { fontSize: 12, fontWeight: "400" as const, lineHeight: 16 },
  number: { fontSize: 15, fontWeight: "500" as const },
  action: { fontSize: 15, fontWeight: "500" as const },
  eyebrow: {
    fontSize: 11,
    fontWeight: "500" as const,
    letterSpacing: 1.6,
    textTransform: "uppercase" as const,
  },
} as const;

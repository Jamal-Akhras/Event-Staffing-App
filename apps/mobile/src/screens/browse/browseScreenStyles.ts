import { StyleSheet } from "react-native";

import { COLORS } from "../../theme/colors";

export const browseScreenStyles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  toggleRow: {
    flexDirection: "row",
    margin: 16,
    marginBottom: 0,
    padding: 3,
    borderRadius: 10,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: 8,
    alignItems: "center",
  },
  toggleBtnActive: { backgroundColor: COLORS.primary },
  toggleText: { color: COLORS.inkMuted, fontWeight: "700", fontSize: 13 },
  toggleTextActive: { color: COLORS.onPrimary },
  content: { padding: 16, paddingBottom: 44 },
  summary: { marginBottom: 16 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  statsLine: { marginTop: 6, color: COLORS.inkMuted, fontSize: 13, fontWeight: "500" },
  footerSpinner: { marginVertical: 16 },
});

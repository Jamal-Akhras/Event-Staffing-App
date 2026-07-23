export const COLORS = {
  ink: "#0f1720",
  inkMuted: "#4b5563",
  inkSubtle: "#6b7280",
  surface: "#fefcf9",
  surfaceMuted: "#fbf7f1",
  canvas: "#f4efe6",
  border: "#e7dfd2",
  borderStrong: "#d6cbb8",
  primary: "#0e5a3a",
  primaryDeep: "#123a2a",
  primarySoft: "#2f8f5f",
  onPrimary: "#f7efe8",
  success: "#10b981",
  info: "#3b82f6",
  warning: "#d97706",
  error: "#b83b32",
  mapPinHigh: "#10b981",
  mapPinStandard: "#3b82f6",
  mapPinUrgent: "#f59e0b",
  mapPinFilled: "#9ca3af",
} as const;

export type ColorKey = keyof typeof COLORS;

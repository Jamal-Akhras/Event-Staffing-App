import { Linking, Pressable, StyleSheet, Text, View } from "react-native";

import { COLORS } from "../theme/colors";

type Props = {
  latitude: number;
  longitude: number;
  label?: string;
};

const NAV_APPS = [
  {
    name: "Google Maps",
    url: (lat: number, lng: number) =>
      `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`,
  },
  {
    name: "Apple Maps",
    url: (lat: number, lng: number) =>
      `https://maps.apple.com/?daddr=${lat},${lng}`,
  },
  {
    name: "Waze",
    url: (lat: number, lng: number) =>
      `https://waze.com/ul?ll=${lat},${lng}&navigate=yes`,
  },
];

export function NavigationLinks({ latitude, longitude, label = "Get directions" }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.heading}>{label}</Text>
      <View style={styles.row}>
        {NAV_APPS.map((app) => (
          <Pressable
            key={app.name}
            style={styles.pill}
            onPress={() => void Linking.openURL(app.url(latitude, longitude))}
          >
            <Text style={styles.pillText}>{app.name}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 12 },
  heading: {
    color: COLORS.inkMuted,
    fontSize: 12,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  pill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: COLORS.primary,
  },
  pillText: { color: COLORS.primary, fontSize: 13, fontWeight: "800" },
});

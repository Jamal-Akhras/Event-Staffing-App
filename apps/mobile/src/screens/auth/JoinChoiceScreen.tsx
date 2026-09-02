import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { COLORS } from "../../theme/colors";
import { TYPE } from "../../theme/type";
import { authStyles } from "./authStyles";

type Props = {
  onJoinVenue: () => void;
  onFindShifts: () => void;
  onBack: () => void;
};

const OPTIONS = [
  {
    key: "venue",
    title: "I work at a venue",
    body: "Your manager has given you a code. You will see your rota and the shifts they offer you.",
    cta: "I have a code",
  },
  {
    key: "shifts",
    title: "I'm looking for shifts",
    body: "Browse open shifts near you and apply. Venues you work for can invite you back.",
    cta: "Find shifts",
  },
] as const;

export function JoinChoiceScreen({ onJoinVenue, onFindShifts, onBack }: Props) {
  const press = { venue: onJoinVenue, shifts: onFindShifts };
  return (
    <SafeAreaView style={authStyles.container}>
      <ScrollView contentContainerStyle={authStyles.scroll}>
        <View style={authStyles.brand}>
          <View style={authStyles.brandMark}>
            <Text style={authStyles.brandMarkText}>V</Text>
          </View>
          <Text style={authStyles.brandName}>Venue OS</Text>
          <Text style={authStyles.brandTagline}>How will you be working?</Text>
        </View>

        {OPTIONS.map((option) => (
          <Pressable key={option.key} style={styles.card} onPress={press[option.key]}>
            <Text style={styles.title}>{option.title}</Text>
            <Text style={styles.body}>{option.body}</Text>
            <Text style={styles.cta}>{option.cta} →</Text>
          </Pressable>
        ))}

        <View style={authStyles.footer}>
          <Text style={authStyles.footerText}>Already have an account? </Text>
          <Pressable onPress={onBack}>
            <Text style={authStyles.footerLink}>Sign in</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 20,
    marginBottom: 14,
  },
  title: { ...TYPE.venueSmall, color: COLORS.ink },
  body: { ...TYPE.body, color: COLORS.inkMuted, marginTop: 6, lineHeight: 20 },
  cta: { ...TYPE.action, color: COLORS.primary, marginTop: 14 },
});

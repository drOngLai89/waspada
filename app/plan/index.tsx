import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { ACTION_PLANS, Scenario } from "../../src/lib/actionPlans";

const scenarios: { key: Scenario; label: string }[] = [
  { key: "money-moved", label: "Money moved" },
  { key: "asked-to-pay", label: "Asked to pay" },
  { key: "otp-password", label: "OTP / password" },
  { key: "courier", label: "Courier" },
  { key: "investment", label: "Investment" },
  { key: "job", label: "Job" },
  { key: "romance", label: "Romance" },
  { key: "impersonation", label: "Impersonation" },
  { key: "other", label: "Other" },
];

export default function PlanHome() {
  return (
    <ScrollView style={styles.page} contentContainerStyle={{ paddingBottom: 26 }}>
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>Action Plan</Text>
        <Text style={styles.heroSub}>
          Pick what’s happening, then follow the steps. (Malaysia-focused)
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Pick a scenario</Text>
        <View style={styles.grid}>
          {scenarios.map((s) => (
            <TouchableOpacity
              key={s.key}
              style={styles.pill}
              onPress={() => router.push(`/plan/${s.key}`)}
              activeOpacity={0.9}
            >
              <Text style={styles.pillText}>{s.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity
          style={styles.secondary}
          onPress={() => router.push("/(tabs)/verify")}
          activeOpacity={0.9}
        >
          <Text style={styles.secondaryText}>Or verify a screenshot</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#F6F7FB" },
  hero: { padding: 16, paddingTop: 18, backgroundColor: "#0B3D91" },
  heroTitle: { fontSize: 26, fontWeight: "900", color: "white" },
  heroSub: { marginTop: 8, fontSize: 13.5, lineHeight: 19, color: "rgba(255,255,255,0.92)" },

  card: { margin: 16, backgroundColor: "white", borderRadius: 18, padding: 16, borderWidth: 1, borderColor: "#E7E9F2" },
  cardTitle: { fontSize: 18, fontWeight: "900", color: "#0B1220" },

  grid: { marginTop: 12, flexDirection: "row", flexWrap: "wrap", gap: 10 },
  pill: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 999, backgroundColor: "#EEF2FF", borderWidth: 1, borderColor: "#DDE3FF" },
  pillText: { fontWeight: "900", color: "#1E3A8A" },

  secondary: { marginTop: 14, paddingVertical: 12, borderRadius: 14, backgroundColor: "#111827", alignItems: "center" },
  secondaryText: { color: "white", fontWeight: "900" },
});

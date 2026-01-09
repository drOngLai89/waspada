import React from "react";
import { ScrollView, Text, TouchableOpacity, View } from "react-native";
import { useRouter } from "expo-router";
import { styles } from "../../src/ui/styles";

type Scenario = { id: string; label: string; emoji: string };

const SCENARIOS: Scenario[] = [
  { id: "money-moved", label: "Money moved", emoji: "🚨" },
  { id: "asked-to-pay", label: "Asked to pay", emoji: "💳" },
  { id: "otp-password", label: "OTP / password", emoji: "🔐" },
  { id: "courier", label: "Courier", emoji: "📦" },
  { id: "investment", label: "Investment", emoji: "📈" },
  { id: "job", label: "Job", emoji: "🧑‍💼" },
  { id: "romance", label: "Romance", emoji: "❤️" },
  { id: "impersonation", label: "Impersonation", emoji: "🎭" },
  { id: "other", label: "Other", emoji: "🧩" },
];

export default function ToolkitScreen() {
  const router = useRouter();

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>Waspada</Text>
        <Text style={styles.heroSub}>
          Malaysia anti-scam toolkit: action steps first, official contacts, and AI screenshot verification.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.h}>Pick a scenario</Text>
        <Text style={styles.p}>
          Start here. We’ll give the steps and who to contact. After that you can optionally verify a screenshot.
        </Text>

        <View style={styles.chipGrid}>
          {SCENARIOS.map((s) => (
            <TouchableOpacity
              key={s.id}
              style={styles.chip}
              onPress={() => router.push(`/plan/${s.id}`)}
            >
              <Text style={styles.chipText}>{s.emoji} {s.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.btnDark} onPress={() => router.push("/verify")}>
          <Text style={styles.btnTextDark}>Skip: Verify a screenshot</Text>
        </TouchableOpacity>

        <Text style={styles.metaCenter}>Waspada focuses on Malaysia cases only.</Text>
      </View>

      <View style={styles.bottomSpace} />
    </ScrollView>
  );
}

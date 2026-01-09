import { View, Text, Pressable } from "react-native";
import { useRouter } from "expo-router";

export default function NotFound() {
  const router = useRouter();
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 24 }}>
      <Text style={{ fontSize: 28, fontWeight: "900" }}>Page not found</Text>
      <Text style={{ marginTop: 8, opacity: 0.7, textAlign: "center" }}>
        Something routed to a screen that no longer exists.
      </Text>
      <Pressable
        onPress={() => router.replace("/(tabs)/toolkit")}
        style={{ marginTop: 16, paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12, backgroundColor: "#2563EB" }}
      >
        <Text style={{ color: "white", fontWeight: "900" }}>Back to Toolkit</Text>
      </Pressable>
    </View>
  );
}

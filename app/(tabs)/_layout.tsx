import React from "react";
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

export default function TabsLayout() {
  return (
    <Tabs
      initialRouteName="toolkit"
      screenOptions={{
        headerShown: true,
        tabBarShowLabel: true,
        tabBarActiveTintColor: "#1D4ED8",
      }}
    >
      <Tabs.Screen
        name="toolkit"
        options={{
          title: "Toolkit",
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? "shield-checkmark" : "shield-checkmark-outline"} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="verify"
        options={{
          title: "Verify",
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? "scan" : "scan-outline"} size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="resources"
        options={{
          title: "Resources",
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons name={focused ? "call" : "call-outline"} size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

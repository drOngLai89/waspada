import React from 'react';
import { NavigationContainer, DefaultTheme, DarkTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useColorScheme, Text } from 'react-native';

import NewReportScreen from './src/screens/NewReportScreen';
import AIScreen from './src/screens/AIScreen';
import VaultScreen from './src/screens/VaultScreen';
import HelpScreen from './src/screens/HelpScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  const scheme = useColorScheme();

  return (
    <SafeAreaProvider>
      <NavigationContainer theme={scheme === 'dark' ? DarkTheme : DefaultTheme}>
        <Tab.Navigator
          screenOptions={{
            headerStyle: { backgroundColor: '#0B1226' },
            headerTitleStyle: { color: '#E8ECF3', fontWeight: '800' },
            headerTitleAlign: 'center',
            tabBarStyle: { backgroundColor: '#0B1226', borderTopColor: '#1E2A4A' },
            tabBarActiveTintColor: '#E8ECF3',
            tabBarInactiveTintColor: '#A8B7D9',
            tabBarHideOnKeyboard: true,
            tabBarShowLabel: true,
          }}
        >
          <Tab.Screen
            name="NewReport"
            component={NewReportScreen}
            options={{
              title: 'New Report',
              tabBarLabel: 'New Report',
              tabBarIcon: ({ size = 22 }) => (
                <Text style={{ fontSize: size, lineHeight: size + 2 }}>📄</Text>
              ),
            }}
          />
          <Tab.Screen
            name="AI"
            component={AIScreen}
            options={{
              title: 'Your AI Counselling Buddy',
              tabBarLabel: 'Counselling Buddy',
              tabBarIcon: ({ size = 22 }) => (
                <Text style={{ fontSize: size, lineHeight: size + 2 }}>💬</Text>
              ),
            }}
          />
          <Tab.Screen
            name="Vault"
            component={VaultScreen}
            options={{
              title: 'Vault',
              tabBarLabel: 'Vault',
              tabBarIcon: ({ size = 22 }) => (
                <Text style={{ fontSize: size, lineHeight: size + 2 }}>🔒</Text>
              ),
            }}
          />
          <Tab.Screen
            name="Help"
            component={HelpScreen}
            options={{
              title: 'Help Pages',
              tabBarLabel: 'Help Pages',
              tabBarIcon: ({ size = 22 }) => (
                <Text style={{ fontSize: size, lineHeight: size + 2 }}>❓</Text>
              ),
            }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}

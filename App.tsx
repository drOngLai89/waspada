import * as React from 'react';
import { NavigationContainer, DefaultTheme, Theme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import NewReportScreen from './src/screens/NewReportScreen';
import AIScreen from './src/screens/AIScreen';
import VaultScreen from './src/screens/VaultScreen';
import HelpScreen from './src/screens/HelpScreen';

const Tab = createBottomTabNavigator();

const DarkTheme: Theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: '#0B1220',
    card: '#111830',
    text: '#E8ECF3',
    border: '#1E2A4A',
    primary: '#6EA8FE'
  }
};

export default function App() {
  return (
    <NavigationContainer theme={DarkTheme}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerTitleStyle: { fontWeight: '700' },
          tabBarStyle: { backgroundColor: '#111830', borderTopColor: '#1E2A4A' },
          tabBarActiveTintColor: '#6EA8FE',
          tabBarInactiveTintColor: '#9BB7E6',
          tabBarIcon: ({ color, size, focused }) => {
            let name: React.ComponentProps<typeof Ionicons>['name'] = 'help-circle-outline';
            if (route.name === 'New Report') name = focused ? 'document-text' : 'document-text-outline';
            if (route.name === 'AI Assistant') name = focused ? 'chatbubble-ellipses' : 'chatbubble-ellipses-outline';
            if (route.name === 'Vault') name = focused ? 'lock-closed' : 'lock-closed-outline';
            if (route.name === 'Help') name = focused ? 'help-circle' : 'help-circle-outline';
            return <Ionicons name={name} size={size} color={color} />;
          }
        })}
      >
        <Tab.Screen name="New Report" component={NewReportScreen} />
        <Tab.Screen name="AI Assistant" component={AIScreen} />
        <Tab.Screen name="Vault" component={VaultScreen} />
        <Tab.Screen name="Help" component={HelpScreen} options={{ title: 'Help Pages' }} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

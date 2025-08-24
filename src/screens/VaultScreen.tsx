import React, { useCallback, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFocusEffect } from '@react-navigation/native';

type Item = {
  id: string;
  category: string;
  date: string;
  time: string;
  locationText: string;
  description: string;
  aiText: string;
};

const KEY = 'berani_vault';

export default function VaultScreen() {
  const [items, setItems] = useState<Item[]>([]);

  const load = useCallback(async () => {
    try {
      const raw = await AsyncStorage.getItem(KEY);
      setItems(raw ? JSON.parse(raw) : []);
    } catch {
      setItems([]);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const onDelete = async (id: string) => {
    const next = items.filter(i => i.id !== id);
    setItems(next);
    await AsyncStorage.setItem(KEY, JSON.stringify(next));
    Alert.alert('Deleted', 'Removed from Vault.');
  };

  return (
    <View style={{ flex:1, backgroundColor:'#0B1226', padding:16 }}>
      <Text style={{ color:'#E8ECF3', fontSize:22, fontWeight:'700', marginBottom:8 }}>Vault</Text>
      <FlatList
        data={items}
        keyExtractor={(it) => it.id}
        ListEmptyComponent={<Text style={{ color:'#9CA3AF' }}>Nothing saved yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.title}>{item.category}</Text>
            <Text style={styles.meta}>{new Date(item.date).toLocaleDateString()} • {new Date(item.time).toLocaleTimeString()}</Text>
            {item.locationText ? <Text style={styles.meta}>{item.locationText}</Text> : null}
            {item.aiText ? <Text style={styles.body}>{item.aiText}</Text> : null}
            <TouchableOpacity style={styles.deleteBtn} onPress={() => onDelete(item.id)}>
              <Text style={{ color:'white', fontWeight:'700' }}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor:'#111830', borderColor:'#1E2A4A', borderWidth:1, borderRadius:12, padding:12, marginBottom:12 },
  title: { color:'#E8ECF3', fontWeight:'700', marginBottom:4 },
  meta: { color:'#9CA3AF', marginBottom:4 },
  body: { color:'#C9D7F3', marginTop:6 },
  deleteBtn: { alignSelf:'flex-end', marginTop:8, backgroundColor:'#ef4444', paddingVertical:8, paddingHorizontal:12, borderRadius:8 }
});

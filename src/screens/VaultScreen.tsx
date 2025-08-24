import React, { useCallback, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { getReports, removeReport, Report } from '../utils/storage';
import { useFocusEffect } from '@react-navigation/native';

export default function VaultScreen() {
  const [items, setItems] = useState<Report[]>([]);

  const load = useCallback(async () => {
    const list = await getReports();
    setItems(list);
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const onDelete = async (id: string) => {
    await removeReport(id);
    await load();
    Alert.alert('Deleted', 'Item removed from Vault.');
  };

  return (
    <View style={styles.wrap}>
      <Text style={styles.h1}>Your Vault</Text>
      <FlatList
        data={items}
        keyExtractor={(it) => it.id}
        ListEmptyComponent={<Text style={{color:'#6b7280'}}>Nothing saved yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.date}>{new Date(item.createdAt).toLocaleString()}</Text>
            {item.summary ? <Text style={styles.summary}>{item.summary}</Text> : null}
            <TouchableOpacity style={styles.deleteBtn} onPress={() => onDelete(item.id)}>
              <Text style={styles.deleteText}>Delete</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, padding: 16 },
  h1: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  card: { backgroundColor: 'white', borderRadius: 12, borderWidth: 1, borderColor: '#e5e7eb', padding: 12, marginBottom: 12 },
  date: { color: '#64748b', marginBottom: 6 },
  summary: { color: '#0f172a' },
  deleteBtn: { alignSelf: 'flex-end', marginTop: 10, paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8, backgroundColor: '#ef4444' },
  deleteText: { color: 'white', fontWeight: '700' },
});

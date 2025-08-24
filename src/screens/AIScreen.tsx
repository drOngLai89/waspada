import React, { useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { saveReport, Report } from '../utils/storage';
import * as Clipboard from 'expo-clipboard';

// If you already have an API util, import that instead and delete this fallback:
async function generateSummaryFallback(text: string): Promise<string> {
  // Replace with your actual API if you have one (e.g., from ../utils/api)
  // This is a safe fallback so the screen still works if API_BASE_URL is missing.
  await new Promise(r => setTimeout(r, 1500));
  return `AI Summary:\n${text.slice(0, 300)}${text.length > 300 ? '…' : ''}`;
}

export default function AIScreen() {
  const [text, setText] = useState('');
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onGenerate = async () => {
    if (!text.trim()) return;
    try {
      setLoading(true);
      setSummary(null);

      // swap this for your real API call if you have one:
      const s = await generateSummaryFallback(text.trim());

      setSummary(s);
    } catch (e: any) {
      Alert.alert('Error', e?.message || 'Failed to generate summary.');
    } finally {
      setLoading(false);
    }
  };

  const onCopy = async () => {
    if (!summary) return;
    await Clipboard.setStringAsync(summary);
    Alert.alert('Copied', 'Summary copied to clipboard.');
  };

  const onSave = async () => {
    try {
      if (!summary) {
        Alert.alert('Nothing to save', 'Generate a summary first.');
        return;
      }
      const report: Report = {
        id: `r_${Date.now()}`,
        createdAt: Date.now(),
        text: text.trim(),
        summary
      };
      await saveReport(report);
      Alert.alert('Saved', 'Saved to your Vault.');
      setText('');
      // keep summary visible or clear it—up to you:
      // setSummary(null);
    } catch (e: any) {
      Alert.alert('Save failed', e?.message || 'Could not save to Vault.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.wrap}>
      <Text style={styles.h1}>AI Summary</Text>
      <TextInput
        placeholder="Describe what happened…"
        value={text}
        onChangeText={setText}
        style={styles.input}
        multiline
        editable={!loading}
      />

      <TouchableOpacity
        style={[styles.btn, loading || !text.trim() ? styles.btnDisabled : null]}
        onPress={onGenerate}
        disabled={loading || !text.trim()}
      >
        {loading ? <ActivityIndicator/> : <Text style={styles.btnText}>Generate AI Summary</Text>}
      </TouchableOpacity>

      {summary && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Summary</Text>
          <Text style={styles.cardBody}>{summary}</Text>

          <View style={styles.row}>
            <TouchableOpacity style={styles.secondaryBtn} onPress={onCopy}>
              <Text style={styles.secondaryText}>Copy</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.primaryBtn} onPress={onSave}>
              <Text style={styles.primaryText}>Save to Vault</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { padding: 16 },
  h1: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  input: {
    minHeight: 140,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 12,
    backgroundColor: 'white',
    textAlignVertical: 'top',
    marginBottom: 12,
  },
  btn: { backgroundColor: '#2563eb', padding: 14, borderRadius: 12, alignItems: 'center', marginBottom: 12 },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: 'white', fontWeight: '600' },

  card: { borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 12, padding: 12, backgroundColor: 'white' },
  cardTitle: { fontWeight: '700', marginBottom: 8 },
  cardBody: { color: '#111827', marginBottom: 12 },

  row: { flexDirection: 'row', gap: 10 },
  secondaryBtn: { flex: 1, borderWidth: 1, borderColor: '#cbd5e1', padding: 12, borderRadius: 10, alignItems: 'center' },
  secondaryText: { color: '#334155', fontWeight: '600' },
  primaryBtn: { flex: 1, backgroundColor: '#0ea5e9', padding: 12, borderRadius: 10, alignItems: 'center' },
  primaryText: { color: 'white', fontWeight: '700' }
});

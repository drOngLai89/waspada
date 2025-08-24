import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { View, Text, TextInput, StyleSheet, TouchableOpacity, ActivityIndicator, FlatList, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { sendCounsellorMessage } from '../utils/api';

type Msg = { id: string; role: 'user' | 'assistant'; text: string };

export default function AIScreen() {
  const nav = useNavigation();
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: 'm1',
      role: 'assistant',
      text:
        "I'm here to support you. Tell me what happened and what you need right now. " +
        "If you’re in immediate danger, call 999 (Malaysia) or your local emergency number. " +
        "24/7 help: Talian Kasih 15999 (WhatsApp 019-2615999)."
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<FlatList<Msg>>(null);

  // Make the header readable on dark background
  useLayoutEffect(() => {
    nav.setOptions?.({
      headerStyle: { backgroundColor: '#0B1226' },
      headerTintColor: '#ffffff',
      headerTitleStyle: { color: '#ffffff' }
    } as any);
  }, [nav]);

  useEffect(() => {
    listRef.current?.scrollToEnd({ animated: true });
  }, [messages.length]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Msg = { id: `u_${Date.now()}`, role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      setLoading(true);
      // Call your backend (Render) with chat history
      const reply = await sendCounsellorMessage(
        messages.concat(userMsg).map(m => ({ role: m.role, content: m.text }))
      );

      const aiMsg: Msg = { id: `a_${Date.now()}`, role: 'assistant', text: reply };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e: any) {
      Alert.alert('AI error', e?.message ?? 'Failed to get a reply.');
    } finally {
      setLoading(false);
    }
  }

  const renderItem = ({ item }: { item: Msg }) => (
    <View style={[styles.bubble, item.role === 'user' ? styles.me : styles.ai]}>
      <Text style={styles.bubbleText}>{item.text}</Text>
    </View>
  );

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
      <FlatList
        ref={listRef}
        contentContainerStyle={styles.list}
        data={messages}
        keyExtractor={(m) => m.id}
        renderItem={renderItem}
      />
      {loading && (
        <View style={styles.typing}><ActivityIndicator /><Text style={{ color:'#94a3b8', marginLeft: 8 }}>Assistant is typing…</Text></View>
      )}
      <View style={styles.inputRow}>
        <TextInput
          placeholder="Type how you're feeling or what happened…"
          placeholderTextColor="#64748b"
          style={styles.textbox}
          value={input}
          onChangeText={setInput}
          editable={!loading}
          onSubmitEditing={send}
          returnKeyType="send"
        />
        <TouchableOpacity style={[styles.sendBtn, (!input.trim() || loading) && { opacity: 0.5 }]} onPress={send} disabled={!input.trim() || loading}>
          <Text style={{ color: 'white', fontWeight: '700' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, backgroundColor: '#0B1226' },
  bubble: { maxWidth: '80%', padding: 12, borderRadius: 14, marginBottom: 10 },
  me: { alignSelf: 'flex-end', backgroundColor: '#2563eb' },
  ai: { alignSelf: 'flex-start', backgroundColor: '#1f2937' },
  bubbleText: { color: 'white' },
  inputRow: { flexDirection: 'row', padding: 12, backgroundColor: '#0B1226', borderTopWidth: 1, borderTopColor: '#111827' },
  textbox: { flex: 1, backgroundColor: '#0f172a', borderWidth: 1, borderColor: '#1f2937', borderRadius: 10, padding: 12, color: '#e5e7eb', marginRight: 8 },
  sendBtn: { backgroundColor: '#0ea5e9', paddingHorizontal: 16, borderRadius: 10, justifyContent: 'center' },
  typing: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, marginBottom: 6 }
});

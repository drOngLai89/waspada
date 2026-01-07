import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Msg = { id: string; role: 'user' | 'assistant'; content: string };

export default function AIAssistantScreen() {
  const insets = useSafeAreaInsets();
  const listRef = useRef<FlatList<Msg>>(null);

  const [input, setInput] = useState('');
  const [messages] = useState<Msg[]>([
    {
      id: 'seed',
      role: 'assistant',
      content:
        "I'm here to support you. Tell me what happened and what you need right now. If you're in immediate danger, call 999 (Malaysia) or your local emergency number.\n24/7 help: Talian Kasih 15999 (WhatsApp 019-2615999).",
    },
  ]);

  useEffect(() => {
    const sub = Keyboard.addListener('keyboardDidShow', () => {
      requestAnimationFrame(() => listRef.current?.scrollToEnd?.({ animated: true }));
    });
    return () => sub.remove();
  }, []);

  function Bubble({ me, children }: { me?: boolean; children: React.ReactNode }) {
    return (
      <View style={{ alignSelf: me ? 'flex-end' : 'flex-start', maxWidth: '80%', marginVertical: 6 }}>
        <View style={{ backgroundColor: me ? '#2A4AAC' : '#1E293B', paddingVertical: 12, paddingHorizontal: 14, borderRadius: 14 }}>
          <Text style={{ color: '#E8ECF3', lineHeight: 22 }}>{children}</Text>
        </View>
      </View>
    );
  }

  const keyboardOffset = Platform.OS === 'ios' ? insets.top + 64 : 0;

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: '#0B1226' }}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={keyboardOffset}
    >
      <FlatList
        ref={listRef}
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={{ padding: 16, paddingBottom: 88 + insets.bottom }}
        style={{ flex: 1 }}
        data={messages}
        keyExtractor={(m) => m.id}
        renderItem={({ item }) => <Bubble me={item.role === 'user'}>{item.content}</Bubble>}
      />

      <View style={{ paddingHorizontal: 12, paddingTop: 8, paddingBottom: Math.max(12, insets.bottom + 8), borderTopColor: '#1E2A4A', borderTopWidth: 1, backgroundColor: '#0B1226', flexDirection: 'row', gap: 8 }}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Type here…"
          placeholderTextColor="#6E7AA3"
          style={{ flex: 1, backgroundColor: '#111830', color: '#E8ECF3', borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, borderWidth: 1, borderColor: '#1E2A4A', maxHeight: 140 }}
          multiline
          returnKeyType="send"
        />
        <TouchableOpacity onPress={() => setInput('')} style={{ backgroundColor: '#1B2340', borderColor: '#2B3963', borderWidth: 1, paddingHorizontal: 18, borderRadius: 12, justifyContent: 'center' }}>
          <Text style={{ color: '#E8ECF3', fontWeight: '700' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

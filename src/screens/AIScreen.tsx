import React, { useLayoutEffect, useRef, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { sendCounsellorMessage } from '../utils/api';

type Msg = { id: string; role: 'user'|'assistant'; content: string };

export default function AIScreen() {
  const navigation = useNavigation<any>();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: 'hello',
      role: 'assistant',
      content:
        "I'm here to support you. Tell me what happened and what you need right now. If you're in immediate danger, call 999 (Malaysia) or your local emergency number.\n24/7 help: Talian Kasih 15999 (WhatsApp 019-2615999).",
    },
  ]);
  const [sending, setSending] = useState(false);
  const listRef = useRef<FlatList>(null);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerStyle: { backgroundColor: '#0B1226' },
      headerTitleStyle: { color: '#E8ECF3' },
      title: 'AI Assistant',
    });
  }, [navigation]);

  async function onSend() {
    const text = input.trim();
    if (!text || sending) return;
    const userMsg: Msg = { id: Date.now() + '_u', role: 'user', content: text };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setSending(true);

    try {
      const convo = [
        ...messages.map(m => ({ role: m.role, content: m.content })),
        { role: 'user' as const, content: text },
      ];
      const r = await sendCounsellorMessage(convo);
      const assistant: Msg = { id: Date.now() + '_a', role: 'assistant', content: r.reply || "I'm here with you." };
      setMessages(m => [...m, assistant]);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 50);
    } catch (e:any) {
      Alert.alert('AI error', e?.message || String(e));
    } finally {
      setSending(false);
    }
  }

  function Bubble({me, children}:{me?:boolean; children:React.ReactNode}) {
    return (
      <View style={{ alignSelf: me ? 'flex-end' : 'flex-start', maxWidth: '80%', marginVertical: 6 }}>
        <View style={{
          backgroundColor: me ? '#2A4AAC' : '#1E293B',
          paddingVertical: 12, paddingHorizontal: 14, borderRadius: 14
        }}>
          <Text style={{ color:'#E8ECF3', lineHeight:22 }}>{children}</Text>
        </View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={{ flex:1, backgroundColor:'#0B1226' }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <FlatList
        ref={listRef}
        contentContainerStyle={{ padding:16 }}
        style={{ flex:1 }}
        data={messages}
        keyExtractor={m => m.id}
        renderItem={({item}) => (<Bubble me={item.role==='user'}>{item.content}</Bubble>)}
      />

      <View style={{ padding:12, borderTopColor:'#1E2A4A', borderTopWidth:1, backgroundColor:'#0B1226', flexDirection:'row', gap:8 }}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Type how you're feeling or what happened…"
          placeholderTextColor="#6E7AA3"
          style={{ flex:1, backgroundColor:'#111830', color:'#E8ECF3', borderRadius:12, paddingHorizontal:14, paddingVertical:12, borderWidth:1, borderColor:'#1E2A4A' }}
          onSubmitEditing={onSend}
          returnKeyType="send"
        />
        <TouchableOpacity onPress={onSend} disabled={sending} style={{ backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingHorizontal:18, borderRadius:12, justifyContent:'center', opacity: sending ? 0.6 : 1 }}>
          <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

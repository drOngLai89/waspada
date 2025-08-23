import * as React from 'react';
import { useState } from 'react';
import { View, Text, TextInput, StyleSheet, Pressable, ActivityIndicator, ScrollView } from 'react-native';
import { askAssistant } from '../utils/api';

export default function AIScreen() {
  const [q, setQ] = useState(''); const [a, setA] = useState(''); const [loading, setLoading] = useState(false);
  async function onAsk() {
    if (!q.trim()) return; setLoading(true); setA('');
    try { const res = await askAssistant(q.trim()); setA(res.answer); }
    catch (e: any) { setA(`(Error) ${e.message}`); }
    finally { setLoading(false); }
  }
  return (
    <ScrollView contentContainerStyle={{ padding: 16 }}>
      <Text style={styles.label}>Ask Berani Assistant</Text>
      <TextInput placeholder="E.g., How do I write a bullying report politely?" placeholderTextColor="#9BB7E6" value={q} onChangeText={setQ} style={[styles.input,{height:120}]} multiline />
      <View style={{ height: 12 }} />
      <Pressable style={styles.button} onPress={onAsk} disabled={loading}>{loading ? <ActivityIndicator color="#E8ECF3" /> : <Text style={styles.buttonText}>Ask</Text>}</Pressable>
      <View style={{ height: 16 }} />
      <Text style={styles.label}>Answer</Text>
      <TextInput value={a} placeholder="Assistant answer will appear here." placeholderTextColor="#9BB7E6" style={[styles.input,{minHeight:160}]} multiline editable={false}/>
    </ScrollView>
  );
}
const styles = StyleSheet.create({
  label:{color:'#E8ECF3',fontSize:14,fontWeight:'700',marginBottom:8},
  input:{backgroundColor:'#0F1730',borderColor:'#1E2A4A',borderWidth:1,borderRadius:12,color:'#E8ECF3',padding:12},
  button:{backgroundColor:'#20335F',borderRadius:12,paddingVertical:12,alignItems:'center'},
  buttonText:{color:'#E8ECF3',fontWeight:'700'}
});

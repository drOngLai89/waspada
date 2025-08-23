import * as React from 'react';
import { useEffect, useState } from 'react';
import { View, Text, FlatList, Pressable, StyleSheet, Modal, Image, ScrollView, Alert } from 'react-native';
import { getAllReports, deleteReport } from '../utils/storage';
import { ReportItem } from '../types';

export default function VaultScreen() {
  const [items, setItems] = useState<ReportItem[]>([]);
  const [open, setOpen] = useState<ReportItem | null>(null);
  async function load(){ setItems(await getAllReports()); }
  useEffect(()=>{ load(); },[]);
  async function onDelete(id:string){ await deleteReport(id); await load(); Alert.alert('Deleted','Report removed from Vault.'); setOpen(null); }
  return (
    <View style={{ flex:1, padding:16 }}>
      <FlatList
        data={items} keyExtractor={(it)=>it.id}
        ItemSeparatorComponent={()=><View style={{height:10}}/>}
        renderItem={({item})=>(
          <Pressable style={styles.card} onPress={()=>setOpen(item)}>
            <Text style={styles.title}>{item.category}</Text>
            <Text style={styles.sub}>{new Date(item.dateISO).toDateString()} • {new Date(item.timeISO).toLocaleTimeString()}</Text>
            <Text style={styles.loc} numberOfLines={1}>{item.locationText || '(no location)'}</Text>
          </Pressable>
        )}
        ListEmptyComponent={<Text style={{ color:'#9BB7E6',textAlign:'center',marginTop:20 }}>No saved reports yet.</Text>}
      />
      <Modal visible={!!open} animationType="slide" onRequestClose={()=>setOpen(null)}>
        <View style={{ flex:1, backgroundColor:'#0B1220' }}>
          <ScrollView contentContainerStyle={{ padding:16 }}>
            <Text style={styles.title}>{open?.category}</Text>
            {open && <>
              <Text style={styles.sub}>{new Date(open.dateISO).toDateString()} • {new Date(open.timeISO).toLocaleTimeString()}</Text>
              <Text style={styles.loc}>{open.locationText}</Text>
              <Text style={styles.section}>Description</Text><Text style={styles.body}>{open.description}</Text>
              <Text style={styles.section}>AI Report</Text><Text style={styles.body}>{open.aiReport}</Text>
              <Text style={styles.section}>Photos</Text>
              <View style={{ flexDirection:'row', flexWrap:'wrap', gap:8 }}>
                {open.photoUris.map(u => <Image key={u} source={{ uri:u }} style={{ width:120, height:120, borderRadius:12 }}/>)}
              </View>
            </>}
            <View style={{ height:20 }}/>
            {open && <Pressable style={styles.btnDanger} onPress={()=>onDelete(open.id)}><Text style={styles.btnTxt}>Delete from Vault</Text></Pressable>}
            <View style={{ height:20 }}/>
            <Pressable style={styles.btn} onPress={()=>setOpen(null)}><Text style={styles.btnTxt}>Close</Text></Pressable>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}
const styles = StyleSheet.create({
  card:{ backgroundColor:'#111830', borderRadius:14, padding:14, borderWidth:1, borderColor:'#1E2A4A' },
  title:{ color:'#E8ECF3', fontSize:18, fontWeight:'800' },
  sub:{ color:'#9BB7E6', marginTop:4 },
  loc:{ color:'#C3D7FF', marginTop:6 },
  section:{ color:'#E8ECF3', marginTop:16, fontWeight:'800' },
  body:{ color:'#D5E2FF', marginTop:8, lineHeight:20 },
  btn:{ backgroundColor:'#20335F', padding:12, borderRadius:12, alignItems:'center' },
  btnDanger:{ backgroundColor:'#8B1C1C', padding:12, borderRadius:12, alignItems:'center' },
  btnTxt:{ color:'#fff', fontWeight:'700' }
});

import React, { useMemo, useState } from 'react';
import {
  View, Text, ScrollView, TextInput, TouchableOpacity, Platform,
  Image, Alert, Share, Modal, ActivityIndicator
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import { generateReport } from '../utils/api';

const categories = [
  'Verbal Harassment','Discrimination','Vandalism','Theft',
  'Bullying','Physical Assault','Cyberbullying','Sexual Harassment',
  'Stalking','Hate Speech','Domestic Violence','Workplace Harassment',
  'Online Scam','Other',
];

function Pill({ children, onPress, disabled }:{
  children: React.ReactNode; onPress?: ()=>void; disabled?: boolean;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.8}
      style={{
        backgroundColor: '#1B2340',
        borderColor: '#2B3963',
        borderWidth: 1,
        paddingVertical: 14,
        paddingHorizontal: 16,
        borderRadius: 14,
        opacity: disabled ? 0.6 : 1,
      }}
    >
      <Text style={{ color: '#E8ECF3', fontWeight: '700' }}>{children}</Text>
    </TouchableOpacity>
  );
}

export default function NewReportScreen() {
  const [category, setCategory] = useState(categories[0]);
  const [date, setDate] = useState<Date>(new Date());
  const [time, setTime] = useState<Date>(new Date());
  const [locationText, setLocationText] = useState('');
  const [description, setDescription] = useState('');
  const [photos, setPhotos] = useState<string[]>([]);
  const [aiText, setAiText] = useState('AI-generated report will appear here.');
  const [isGen, setIsGen] = useState(false);

  const [showDateA, setShowDateA] = useState(false);
  const [showTimeA, setShowTimeA] = useState(false);
  const [iosSheet, setIosSheet] = useState<null | 'date' | 'time'>(null);

  const dateLabel = useMemo(
    () => date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: '2-digit', year: 'numeric' }),
    [date]
  );
  const timeLabel = useMemo(
    () => time.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit', second: '2-digit' }),
    [time]
  );

  async function onUseCurrentLocation() {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'Location permission was not granted.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({});
      const rev = await Location.reverseGeocodeAsync(loc.coords);
      if (rev && rev[0]) {
        const r = rev[0];
        const line = [r.name, r.street, r.postalCode, r.city, r.region, r.country].filter(Boolean).join(', ');
        setLocationText(line);
      } else {
        setLocationText(`${loc.coords.latitude.toFixed(5)}, ${loc.coords.longitude.toFixed(5)}`);
      }
    } catch (e:any) {
      Alert.alert('Location error', e?.message ?? String(e));
    }
  }

  async function onAddPhoto() {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) {
      Alert.alert('Permission needed', 'Photo library permission is required.');
      return;
    }
    const res = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: false,
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (!res.canceled && res.assets?.[0]?.uri) {
      setPhotos(p => [...p, res.assets[0].uri!]);
    }
  }

  function removePhoto(idx: number) {
    setPhotos(p => p.filter((_, i) => i !== idx));
  }

  async function onGenerate() {
    try {
      setIsGen(true);
      const payload = {
        category,
        dateISO: date.toISOString(),
        timeISO: time.toISOString(),
        locationText,
        description,
      };
      const out = await generateReport(payload);
      setAiText(out.report || 'No result.');
    } catch (e:any) {
      setAiText('(Error) ' + (e?.message ?? 'Failed to generate'));
    } finally {
      setIsGen(false);
    }
  }

  async function onSaveToVault() {
    const item = {
      id: String(Date.now()),
      category,
      date: date.toISOString(),
      time: time.toISOString(),
      locationText,
      description,
      photos,     // <- photos are saved
      aiText,
    };
    const key = 'berani_vault';
    const existing = await AsyncStorage.getItem(key);
    const arr = existing ? JSON.parse(existing) : [];
    arr.unshift(item);
    await AsyncStorage.setItem(key, JSON.stringify(arr));
    Alert.alert('Saved', 'Report saved to Vault.');
  }

  function escapeHtml(s: string) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  async function onShare() {
    try {
      const textFallback =
        `Category: ${category}\nDate: ${date.toISOString()}\nTime: ${time.toISOString()}\n` +
        `Location: ${locationText}\n\nDescription:\n${description}\n\nAI Report:\n${aiText}`;

      const canShareFile = await Sharing.isAvailableAsync();
      if (!canShareFile) {
        await Share.share({ message: textFallback });
        return;
      }

      const imgHtmlParts: string[] = [];
      for (const uri of photos) {
        try {
          const b64 = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
          imgHtmlParts.push(`<div class="photo"><img src="data:image/jpeg;base64,${b64}" /></div>`);
        } catch {}
      }

      const html = `
<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; color:#111; padding:18px; }
h1{margin:0 0 10px;font-size:22px} h2{margin:18px 0 8px;font-size:17px}
.mono{color:#333;font-family: ui-monospace, Menlo, 'SF Mono', monospace; font-size:12px}
.tag{font-weight:600} .box{border:1px solid #e6e6e6;border-radius:10px;padding:12px;background:#fafafa}
.photo img{width:100%;height:auto;border-radius:10px}
.ai{white-space:pre-wrap}
</style></head><body>
  <h1>Berani Incident Report</h1>
  <div class="mono">${escapeHtml(new Date().toLocaleString())}</div>
  <div class="meta"><span class="tag">Category:</span> ${escapeHtml(category)}</div>
  <div class="meta"><span class="tag">Date:</span> ${escapeHtml(date.toISOString())}</div>
  <div class="meta"><span class="tag">Time:</span> ${escapeHtml(time.toISOString())}</div>
  <div class="meta"><span class="tag">Location:</span> ${escapeHtml(locationText)}</div>
  <h2>Description</h2><div class="box">${escapeHtml(description)}</div>
  <h2>AI Report</h2><div class="box ai">${escapeHtml(aiText)}</div>
  ${imgHtmlParts.length ? `<h2>Photos</h2>` : ''}${imgHtmlParts.join('')}
</body></html>`;
      const { uri } = await Print.printToFileAsync({ html });
      const target = `${FileSystem.documentDirectory}Berani_Report_${Date.now()}.pdf`;
      await FileSystem.moveAsync({ from: uri, to: target });
      await Sharing.shareAsync(target, { mimeType: 'application/pdf', dialogTitle: 'Share Berani report' });
    } catch (e:any) {
      const fallback =
        `Category: ${category}\nDate: ${date.toISOString()}\nTime: ${time.toISOString()}\n` +
        `Location: ${locationText}\n\nDescription:\n${description}\n\nAI Report:\n${aiText}`;
      try { await Share.share({ message: fallback }); }
      catch { Alert.alert('Share error', e?.message ?? String(e)); }
    }
  }

  function onChangeDateAndroid(_: any, d?: Date) { setShowDateA(false); if (d) setDate(d); }
  function onChangeTimeAndroid(_: any, d?: Date) { setShowTimeA(false); if (d) setTime(d); }

  function IOSPickerSheet({ mode, onClose }:{ mode:'date'|'time'; onClose:()=>void }) {
    const value = mode === 'date' ? date : time;
    function onChange(_: any, d?: Date) {
      if (d) { if (mode === 'date') setDate(d); else setTime(d); }
    }
    return (
      <Modal transparent animationType="slide" visible onRequestClose={onClose}>
        <View style={{ flex:1, backgroundColor:'rgba(0,0,0,0.35)', justifyContent:'flex-end' }}>
          <TouchableOpacity style={{ flex:1 }} activeOpacity={1} onPress={onClose} />
          <View style={{ backgroundColor:'#0B1226', borderTopLeftRadius:16, borderTopRightRadius:16, borderColor:'#1E2A4A', borderWidth:1, paddingTop:8 }}>
            <View style={{ flexDirection:'row', justifyContent:'space-between', paddingHorizontal:12, paddingBottom:6 }}>
              <TouchableOpacity onPress={onClose}><Text style={{ color:'#9BB7E6', fontWeight:'600' }}>Done</Text></TouchableOpacity>
              <Text style={{ color:'#C9D7F3', fontWeight:'700' }}>{mode === 'date' ? 'Select Date' : 'Select Time'}</Text>
              <View style={{ width:48 }} />
            </View>
            <View style={{ height:216, borderTopColor:'#1E2A4A', borderTopWidth:1, paddingVertical:6 }}>
              <DateTimePicker value={value} mode={mode} display="spinner" themeVariant="dark" onChange={onChange} style={{ height:216 }} />
            </View>
            <View style={{ height:10 }} />
          </View>
        </View>
      </Modal>
    );
  }

  return (
    <ScrollView style={{ flex:1, backgroundColor:'#0B1226' }} contentContainerStyle={{ padding:16, paddingBottom:40 }}>
      <Text style={{ color:'#E8ECF3', fontWeight:'700', fontSize:28, textAlign:'center', marginBottom:10 }}>New Report</Text>

      <Text style={{ color:'#C9D7F3', fontWeight:'700', marginBottom:6 }}>Category</Text>
      <View style={{ backgroundColor:'#111830', borderRadius:16, borderWidth:1, borderColor:'#1E2A4A', overflow:'hidden', marginBottom:12 }}>
        <Picker
          selectedValue={category}
          onValueChange={(v) => setCategory(String(v))}
          dropdownIconColor="#E8ECF3"
          style={{ color:'#E8ECF3' }}
          itemStyle={{ color:'#E8ECF3' }}
          mode={Platform.OS === 'android' ? 'dropdown' : undefined}
        >
          {categories.map(c => <Picker.Item key={c} label={c} value={c} />)}
        </Picker>
      </View>

      <View style={{ flexDirection:'row', justifyContent:'space-between' }}>
        <Text style={{ color:'#C9D7F3', fontWeight:'700', marginBottom:6 }}>Date</Text>
        <Text style={{ color:'#C9D7F3', fontWeight:'700', marginBottom:6 }}>Time</Text>
      </View>
      <View style={{ flexDirection:'row', gap:14, marginBottom:8 }}>
        <View style={{ flex:1 }}>
          <Pill onPress={() => { Platform.OS === 'ios' ? setIosSheet('date') : setShowDateA(true); }}>{dateLabel}</Pill>
        </View>
        <View style={{ width:160 }}>
          <Pill onPress={() => { Platform.OS === 'ios' ? setIosSheet('time') : setShowTimeA(true); }}>{timeLabel}</Pill>
        </View>
      </View>

      {Platform.OS === 'android' && showDateA && <DateTimePicker value={date} mode="date" display="default" onChange={onChangeDateAndroid} />}
      {Platform.OS === 'android' && showTimeA && <DateTimePicker value={time} mode="time" is24Hour={false} display="default" onChange={onChangeTimeAndroid} />}
      {Platform.OS === 'ios' && iosSheet === 'date' && <IOSPickerSheet mode="date" onClose={() => setIosSheet(null)} />}
      {Platform.OS === 'ios' && iosSheet === 'time' && <IOSPickerSheet mode="time" onClose={() => setIosSheet(null)} />}

      <Text style={{ color:'#C9D7F3', fontWeight:'700', marginTop:12, marginBottom:6 }}>Location</Text>
      <View style={{ flexDirection:'row', gap:10 }}>
        <TextInput
          value={locationText}
          onChangeText={setLocationText}
          placeholder="Enter a place or address"
          placeholderTextColor="#6E7AA3"
          style={{ flex:1, backgroundColor:'#111830', color:'#E8ECF3', borderRadius:12, paddingHorizontal:14, paddingVertical:12, borderWidth:1, borderColor:'#1E2A4A' }}
        />
        <TouchableOpacity onPress={onUseCurrentLocation} style={{ backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingHorizontal:14, borderRadius:12, justifyContent:'center' }}>
          <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Use current</Text>
        </TouchableOpacity>
      </View>

      <Text style={{ color:'#C9D7F3', fontWeight:'700', marginTop:16, marginBottom:6 }}>Description</Text>
      <TextInput
        value={description}
        onChangeText={setDescription}
        multiline
        placeholder="Describe what happened…"
        placeholderTextColor="#6E7AA3"
        style={{ minHeight:120, textAlignVertical:'top', backgroundColor:'#111830', color:'#E8ECF3', borderRadius:12, padding:14, borderWidth:1, borderColor:'#1E2A4A' }}
      />

      <Text style={{ color:'#C9D7F3', fontWeight:'700', marginTop:16, marginBottom:6 }}>Photos</Text>
      <View style={{ flexDirection:'row', alignItems:'center', gap:14, flexWrap:'wrap' }}>
        <TouchableOpacity onPress={onAddPhoto} style={{ backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingHorizontal:18, paddingVertical:14, borderRadius:12 }}>
          <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Add photo</Text>
        </TouchableOpacity>
        {photos.map((uri, idx) => (
          <View key={uri} style={{ position:'relative' }}>
            <Image source={{ uri }} style={{ width:132, height:132, borderRadius:10 }} />
            <TouchableOpacity onPress={() => removePhoto(idx)} style={{ position:'absolute', top:-8, right:-8, backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, borderRadius:12, paddingHorizontal:8, paddingVertical:4 }}>
              <Text style={{ color:'#E8ECF3', fontWeight:'800' }}>×</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      <Text style={{ color:'#C9D7F3', fontWeight:'700', marginTop:18, marginBottom:8 }}>AI Report</Text>
      <TouchableOpacity onPress={onGenerate} disabled={isGen} style={{ backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingVertical:14, borderRadius:12, alignItems:'center', marginBottom:10, opacity: isGen ? 0.6 : 1 }}>
        {isGen ? <ActivityIndicator /> : <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Generate</Text>}
      </TouchableOpacity>

      <View style={{ backgroundColor:'#111830', borderColor:'#1E2A4A', borderWidth:1, borderRadius:12, padding:14, minHeight:120 }}>
        <Text style={{ color:'#A8B7D9', lineHeight:22 }}>{aiText}</Text>
      </View>

      <View style={{ flexDirection:'row', gap:14, marginTop:16 }}>
        <TouchableOpacity onPress={onShare} style={{ flex:1, backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingVertical:14, borderRadius:12, alignItems:'center' }}>
          <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Share</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onSaveToVault} style={{ flex:1, backgroundColor:'#1B2340', borderColor:'#2B3963', borderWidth:1, paddingVertical:14, borderRadius:12, alignItems:'center' }}>
          <Text style={{ color:'#E8ECF3', fontWeight:'700' }}>Save to Vault</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

import * as React from 'react';
import { View, Image, Pressable, StyleSheet, Text } from 'react-native';

export default function ImageGrid({ uris, onRemove }: { uris: string[]; onRemove: (uri: string) => void; }) {
  if (!uris?.length) return null;
  return (
    <View style={styles.wrap}>
      {uris.map((u) => (
        <View key={u} style={styles.cell}>
          <Image source={{ uri: u }} style={styles.img} />
          <Pressable style={styles.close} onPress={() => onRemove(u)}>
            <Text style={styles.x}>×</Text>
          </Pressable>
        </View>
      ))}
    </View>
  );
}
const styles = StyleSheet.create({
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  cell: { width: 96, height: 96, borderRadius: 12, overflow: 'hidden', position: 'relative', backgroundColor: '#1A2442' },
  img: { width: '100%', height: '100%' },
  close: { position: 'absolute', top: 4, right: 4, width: 24, height: 24, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0008' },
  x: { color: '#fff', fontSize: 18, fontWeight: '700' }
});

import AsyncStorage from '@react-native-async-storage/async-storage';
import { ReportItem } from '../types';

const KEY = 'BERANI_VAULT_V1';

export async function getAllReports(): Promise<ReportItem[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { const list = JSON.parse(raw) as ReportItem[]; return Array.isArray(list) ? list : []; }
  catch { return []; }
}
export async function saveReport(item: ReportItem) {
  const all = await getAllReports(); all.unshift(item);
  await AsyncStorage.setItem(KEY, JSON.stringify(all));
}
export async function deleteReport(id: string) {
  const all = await getAllReports();
  await AsyncStorage.setItem(KEY, JSON.stringify(all.filter(r => r.id !== id)));
}

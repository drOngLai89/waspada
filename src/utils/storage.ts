import AsyncStorage from '@react-native-async-storage/async-storage';

export type Report = {
  id: string;
  createdAt: number;
  text: string;
  summary?: string;
  photos?: string[]; // file:// URIs if you store images
};

const KEY = 'berani:reports:v1';

export async function getReports(): Promise<Report[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as Report[]; } catch { return []; }
}

export async function saveReport(r: Report): Promise<void> {
  const list = await getReports();
  const idx = list.findIndex(x => x.id === r.id);
  if (idx >= 0) list[idx] = r; else list.unshift(r);
  await AsyncStorage.setItem(KEY, JSON.stringify(list));
}

export async function removeReport(id: string): Promise<void> {
  const list = await getReports();
  const next = list.filter(r => r.id !== id);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
}

export async function clearReports(): Promise<void> {
  await AsyncStorage.removeItem(KEY);
}

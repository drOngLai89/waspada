export const DEV = false;

// ← if you ever run a local backend, change DEV=true and use localhost below.
export const API_BASE_URL = DEV
  ? 'http://localhost:5000'
  : 'https://berani-backend.onrender.com';

export type ReportPayload = {
  category: string;
  dateISO: string;
  timeISO: string;
  locationText: string;
  description: string;
};

async function postJSON<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`HTTP ${res.status} ${t}`);
  }
  return (await res.json()) as T;
}

// ---- Named exports used by the screens ----
export async function generateReport(payload: ReportPayload) {
  return await postJSON<{ report: string; meta?: any }>('/generate_report', payload);
}

export async function askAssistant(question: string) {
  return await postJSON<{ answer: string; meta?: any }>('/assistant', { question });
}

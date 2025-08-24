import Constants from 'expo-constants';

function getBaseUrl(): string {
  // Prefer app.config.ts -> extra.API_BASE_URL, then env/globals
  const expoCfg: any = (Constants as any).expoConfig || (Constants as any).manifest || {};
  const extra = (expoCfg && expoCfg.extra) || {};
  const fromExtra = extra.API_BASE_URL;
  const fromEnv = (process as any)?.env?.API_BASE_URL;
  const fromGlobal = (global as any)?.API_BASE_URL;
  const base = (fromExtra || fromEnv || fromGlobal || '').toString().trim();
  return base.replace(/\/+$/, ''); // strip trailing slash
}

/** Generate the long-form report from the New Report screen */
export async function generateReport(payload: {
  category: string; dateISO: string; timeISO: string; locationText: string; description: string;
}): Promise<{ report: string }> {
  const base = getBaseUrl();
  if (!base) throw new Error('API_BASE_URL is not set');
  const res = await fetch(`${base}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Report failed: ${res.status}`);
  return await res.json();
}

/** Counsellor-style chat for the AI Assistant screen */
export async function sendCounsellorMessage(messages: { role: 'user' | 'assistant'; content: string }[]): Promise<string> {
  const base = getBaseUrl();
  if (!base) throw new Error('API_BASE_URL is not set');
  // Change path if your server uses /api/chat, etc.
  const res = await fetch(`${base}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      system:
        "You are a compassionate counsellor for users in Malaysia. Ensure safety first: if risk of harm, advise calling 999 immediately. " +
        "Offer practical next steps and local resources when relevant: Talian Kasih 15999 (WhatsApp 019-2615999), Befrienders 03-7627 2929, WAO +603-7956 3488 / WhatsApp +6018-988 8058. " +
        "Avoid medical/legal diagnosis; be brief, clear, and supportive.",
      messages,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  const data = await res.json();
  // Accept a few common shapes
  return (data.reply ?? data.text ?? data.message ?? '').toString() || JSON.stringify(data);
}

import Constants from 'expo-constants';

function getBaseUrl(): string {
  const expoCfg: any = (Constants as any).expoConfig || (Constants as any).manifest || {};
  const extra = (expoCfg && expoCfg.extra) || {};
  const fromExtra = extra.API_BASE_URL;
  const fromEnv = (process as any)?.env?.API_BASE_URL;
  const fromGlobal = (global as any)?.API_BASE_URL;
  const base = (fromExtra || fromEnv || fromGlobal || '').toString().trim();
  console.log('API_BASE_URL ⇒', base || '(empty)');
  return base.replace(/\/+$/, '');
}

async function tryPostJSON<T>(base: string, paths: string[], body: any): Promise<T> {
  let lastErr: any = null;
  for (const p of paths) {
    const url = `${base}${p.startsWith('/') ? '' : '/'}${p}`;
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.status === 404) {
        console.log('Endpoint 404, trying next →', url);
        continue; // try next candidate
      }
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status} at ${url} ${text ? '— ' + text : ''}`);
      }
      // assume JSON, but allow text
      const ct = res.headers.get('content-type') || '';
      if (ct.includes('application/json')) return (await res.json()) as T;
      const text = await res.text();
      return { reply: text } as unknown as T;
    } catch (e) {
      lastErr = e;
      console.log('POST failed:', url, String(e));
    }
  }
  throw lastErr ?? new Error(`No working endpoint. Tried: ${paths.join(', ')}`);
}

/** Generate the long-form report used by New Report screen */
export async function generateReport(payload: {
  category: string; dateISO: string; timeISO: string; locationText: string; description: string;
}): Promise<{ report: string }> {
  const base = getBaseUrl();
  if (!base) throw new Error('API_BASE_URL is not set');

  const expoCfg: any = (Constants as any).expoConfig || (Constants as any).manifest || {};
  const extra = (expoCfg && expoCfg.extra) || {};
  const override = (extra.REPORT_PATH || (process as any)?.env?.REPORT_PATH) as string | undefined;

  const candidates = [
    ...(override ? [override] : []),
    '/report',
    '/api/report',
    '/v1/report',
    '/generate',
    '/api/generate',
  ];

  const data: any = await tryPostJSON<any>(base, candidates, payload);
  const text = data.report ?? data.summary ?? data.text ?? data.message;
  return { report: (text ?? JSON.stringify(data)).toString() };
}

/** Counsellor-style chat for the AI Assistant screen */
export async function sendCounsellorMessage(
  messages: { role: 'user' | 'assistant'; content: string }[]
): Promise<string> {
  const base = getBaseUrl();
  if (!base) throw new Error('API_BASE_URL is not set');

  const expoCfg: any = (Constants as any).expoConfig || (Constants as any).manifest || {};
  const extra = (expoCfg && expoCfg.extra) || {};
  const override = (extra.CHAT_PATH || (process as any)?.env?.CHAT_PATH) as string | undefined;

  const candidates = [
    ...(override ? [override] : []),
    '/chat',
    '/api/chat',
    '/v1/chat',
    '/messages',
    '/api/messages',
    '/respond',
  ];

  const data: any = await tryPostJSON<any>(base, candidates, {
    system:
      "You are a compassionate counsellor for users in Malaysia. Ensure safety first: if risk of harm, advise calling 999 immediately. " +
      "Offer practical next steps and local resources when relevant: Talian Kasih 15999 (WhatsApp 019-2615999), Befrienders 03-7627 2929, WAO +603-7956 3488 / WhatsApp +6018-988 8058. " +
      "Avoid medical/legal diagnosis; be brief, clear, and supportive.",
    messages,
  });

  return (data.reply ?? data.text ?? data.message ?? JSON.stringify(data)).toString();
}

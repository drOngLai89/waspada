import Constants from 'expo-constants';

type ReportPayload = {
  category: string;
  dateISO: string;
  timeISO: string;
  locationText: string;
  description: string;
};

function getFromExtra(key: string): string | undefined {
  const cfg: any = (Constants as any).expoConfig || (Constants as any).manifest || {};
  return cfg?.extra?.[key];
}

const BASE = (getFromExtra('API_BASE_URL') || process.env.API_BASE_URL || '').trim();
const REPORT_PATH = (getFromExtra('REPORT_PATH') || process.env.REPORT_PATH || '/report').trim();
const CHAT_PATH   = (getFromExtra('CHAT_PATH')   || process.env.CHAT_PATH   || '/chat').trim();

console.log('API_BASE_URL ⇒', BASE || '(not set)');

function full(base: string, path: string) {
  const b = base.replace(/\/+$/,'');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${b}${p}`;
}

async function tryPostJSON<T>(url: string, body: any): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type':'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} at ${url}`);
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return await res.json();
  const text = await res.text();
  return { reply: text } as unknown as T;
}

export async function generateReport(payload: ReportPayload): Promise<{report:string}> {
  if (BASE) {
    const candidates = [
      REPORT_PATH, '/api/report', '/v1/report', '/generate', '/api/generate'
    ];
    for (const path of candidates) {
      try { 
        const data: any = await tryPostJSON(full(BASE, path), payload);
        const text = data.report ?? data.summary ?? data.text ?? data.message;
        if (text) return { report: String(text) };
      } catch (e) { console.log('Endpoint failed →', path, String(e)); }
    }
  }
  // offline fallback
  const { description } = payload;
  const fallback =
`### Description of the Incident:
${description || 'No description provided.'}

### Impact:
We are still gathering details. Consider any injuries and how you feel.

### Next Steps:
1) If you’re in immediate danger, call **999** (Malaysia).
2) Save evidence safely in the Vault.
3) Reach out: Talian Kasih **15999** (WhatsApp **019-2615999**),
   Befrienders **03-7627 2929**, WAO **+603-7956 3488** (WhatsApp **+6018-988 8058**).`;
  return { report: fallback };
}

export async function sendCounsellorMessage(
  messages: { role:'user'|'assistant'|'system'; content:string }[]
): Promise<{ reply: string }> {
  if (BASE) {
    const candidates = [CHAT_PATH, '/api/chat', '/v1/chat', '/messages', '/api/messages', '/respond'];
    for (const path of candidates) {
      try {
        const data: any = await tryPostJSON(full(BASE, path), { messages });
        const text = data.reply ?? data.text ?? data.message;
        if (text) return { reply: String(text) };
      } catch (e) { console.log('Endpoint failed →', path, String(e)); }
    }
  }
  // fallback reply (keeps UX working)
  return {
    reply:
`I'm here with you. If you’re in immediate danger, call **999** now.

24/7 Malaysia helplines:
• **Talian Kasih 15999** (WhatsApp **019-2615999**)
• **Befrienders** **03-7627 2929**
• **WAO Hotline** **+603-7956 3488** (WhatsApp **+6018-988 8058**)`
  };
}

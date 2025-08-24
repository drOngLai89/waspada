import { Platform } from 'react-native';

type ReportPayload = {
  category: string;
  dateISO: string;
  timeISO: string;
  locationText: string;
  description: string;
};

const BASE = (process.env.API_BASE_URL || '').trim();
console.log('API_BASE_URL ⇒', BASE || '(not set)');

function candidates(base: string | undefined, paths: string[]) {
  if (!base) return [];
  const norm = base.replace(/\/+$/,'');
  return paths.map(p => norm + (p.startsWith('/') ? p : '/' + p));
}

export async function generateReport(payload: ReportPayload): Promise<{report:string}> {
  const urls = candidates(BASE, [
    process.env.REPORT_PATH || '/report',
    '/api/report', '/v1/report', '/generate', '/api/generate'
  ]);

  for (const url of urls) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const j = await res.json();
        if (j?.report) return { report: j.report };
      } else {
        console.log(`Endpoint ${res.status}, trying next → ${url}`);
      }
    } catch (e:any) {
      console.log(`Endpoint error, trying next → ${url}`, e?.message || String(e));
    }
  }

  // ---- Local fallback so the app still works without a server ----
  const { category, dateISO, timeISO, locationText, description } = payload;
  const fallback =
`### Description of the Incident:
${description || 'No description provided.'}

### Impact:
We are still gathering details. Consider any injuries and how you feel.

### Next Steps:
1) If you’re in immediate danger, call **999** (Malaysia) now.
2) Save evidence (photos, messages) safely in the Vault.
3) Reach out: Talian Kasih **15999** (WhatsApp **019-2615999**),
   Befrienders **03-7627 2929**, WAO **+603-7956 3488** (WhatsApp **+6018-988 8058**).`;
  return { report: fallback };
}

export async function sendCounsellorMessage(messages: {role:'user'|'assistant'|'system', content:string}[]) {
  const urls = candidates(BASE, [
    process.env.CHAT_PATH || '/chat',
    '/api/chat', '/v1/chat', '/messages', '/api/messages', '/respond'
  ]);

  for (const url of urls) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ messages }),
      });
      if (res.ok) {
        const j = await res.json();
        if (j?.reply) return { reply: j.reply };
      } else {
        console.log(`Endpoint ${res.status}, trying next → ${url}`);
      }
    } catch (e:any) {
      console.log(`Endpoint error, trying next → ${url}`, e?.message || String(e));
    }
  }

  // Local supportive fallback
  const reply =
`I'm here with you. If you’re in immediate danger, call **999** now.

24/7 Malaysia helplines:
• **Talian Kasih 15999** (WhatsApp **019-2615999**)
• **Befrienders** **03-7627 2929**
• **WAO Hotline** **+603-7956 3488** (WhatsApp **+6018-988 8058**)

You can keep talking to me here and I’ll listen.`;
  return { reply };
}

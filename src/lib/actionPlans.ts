export type SourceRef = {
  id: string;
  title: string;
  org: string;
  date: string;
  url: string;
};

export type ActionPlan = {
  key: string;
  title: string;
  when: string;
  doNow: string[];
  nextSteps: string[];
  whoToContact: string[];
  evidence: string[];
  caveat: string;
  sources: SourceRef[];
};

const SOURCES: SourceRef[] = [
  {
    id: "NFCC-NSRC-997-2026-01-05",
    title: "Hubungi Pusat Respons Scam Kebangsaan (NSRC) di talian 997",
    org: "NFCC (JPM)",
    date: "2026-01-05",
    url: "https://nfcc.jpm.gov.my/index.php?speech-hubungi-pusat-respons-scam-kebangsaan-nsrc-di-talian-997/",
  },
  {
    id: "PDRM-SEMAK-MULE-2020-10-07",
    title: "Portal dan aplikasi Semak Mule bantu pengguna kesan akaun 'scammer'",
    org: "PDRM",
    date: "2020-10-07",
    url: "https://www.rmp.gov.my/news-detail/2020/10/07/portal-dan-aplikasi-semak-mule-bantu-pengguna-kesan-akaun-scammer",
  },
];

function basePlan(key: string, title: string, when: string): ActionPlan {
  return {
    key,
    title,
    when,
    doNow: [
      "Stop engaging. Don’t click links, scan QR codes, or install apps requested by the other party.",
      "Do not share OTP/TAC/passwords or let anyone ‘remote-control’ your device.",
      "Verify using official numbers from official websites, not numbers given by the scammer.",
      "If money has moved, contact your bank immediately and call NSRC 997.",
      "Check account numbers (if provided) using PDRM Semak Mule.",
    ],
    nextSteps: [
      "Save evidence (screenshots, chat logs, phone numbers, URLs, bank details, receipts).",
      "Warn a trusted person before taking any next step.",
      "If you’re unsure or it feels urgent, treat it as high risk and escalate to your bank / authorities.",
    ],
    whoToContact: [
      "NSRC 997 (if money has moved / online financial fraud)",
      "Your bank’s fraud hotline (immediately if funds were transferred)",
      "PDRM (make a police report where appropriate)",
    ],
    evidence: [
      "Screenshots of the full conversation (including the profile + timestamps)",
      "Phone number(s), usernames, URLs, QR codes",
      "Bank account number(s) / beneficiary details",
      "Payment receipts / transaction references",
    ],
    caveat:
      "This is informational guidance. It may be incomplete. For urgent cases or if money has moved, contact your bank and the relevant authorities immediately.",
    sources: SOURCES,
  };
}

export const ACTION_PLANS: Record<string, ActionPlan> = {
  money_moved: {
    ...basePlan("money_moved", "Money moved", "Immediately"),
    doNow: [
      "Call your bank immediately to freeze/stop further transfers and flag the transaction as suspected scam.",
      "Call NSRC 997 as soon as possible and follow their instructions.",
      "Do not make additional transfers to ‘recover’ money or to any ‘safe account’.",
      "Preserve evidence and note the exact time the transfer happened.",
      "Check any recipient accounts via PDRM Semak Mule and record the result.",
    ],
  },
  asked_to_pay: { ...basePlan("asked_to_pay", "Asked to pay", "Before paying anything") },
  otp_password: { ...basePlan("otp_password", "OTP / password", "Immediately") },
  courier: { ...basePlan("courier", "Courier / parcel", "Before paying ‘fees’ or sharing details") },
  investment: { ...basePlan("investment", "Investment", "Before transferring any funds") },
  job: { ...basePlan("job", "Job offer / recruitment", "Before paying ‘processing’ fees") },
  romance: { ...basePlan("romance", "Romance / love scam", "Before sending money or gifts") },
  impersonation: { ...basePlan("impersonation", "Impersonation", "Immediately") },
  other: { ...basePlan("other", "Other", "Now") },
};

export function getActionPlan(key: string): ActionPlan {
  return ACTION_PLANS[key] ?? ACTION_PLANS.other;
}

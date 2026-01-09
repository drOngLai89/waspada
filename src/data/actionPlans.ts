export type Scenario =
  | "money_moved"
  | "asked_to_pay"
  | "otp_password"
  | "impersonation"
  | "courier"
  | "investment"
  | "job"
  | "romance"
  | "other";

export type Ref = { title: string; org: string; date: string; url: string };

export type Plan = {
  scenario: Scenario;
  title: string;
  oneLine: string;
  doNow: string[];
  saveEvidence: string[];
  contacts: { label: string; value: string; type: "phone" | "url" }[];
  references: Ref[];
  caveat: string;
};

const REF_KOMUNIKASI_NSRC: Ref = {
  title: "NSRC 997 guidance (what to do, info to prepare, NSRC won’t call you)",
  org: "Portal Rasmi Kementerian Komunikasi",
  date: "2026-01-05 (page update)",
  url: "https://www.komunikasi.gov.my/en/awam/berita/79374-nsrc-no-incoming-call-from-997-scam",
};

const REF_PDRM_SEMAKMULE: Ref = {
  title: "Semak Mule / akaun keldai + CCID Response Centre numbers",
  org: "Polis Diraja Malaysia (PDRM) – rmp.gov.my",
  date: "Accessed 2026-01-08",
  url: "https://www.rmp.gov.my/infor-korporate/polis-diraja-malaysia/pusat-semak-mule-ccid",
};

const BASE_CAVEAT =
  "This guidance is generated to help you decide your next steps. It may be wrong or incomplete and is not official advice. If money is involved or you feel unsafe, contact your bank and the relevant authorities immediately.";

export const PLANS: Record<Scenario, Plan> = {
  money_moved: {
    scenario: "money_moved",
    title: "Money already moved",
    oneLine: "Act fast. Time matters.",
    doNow: [
      "Call NSRC 997 immediately (Malaysia).",
      "Call your bank’s official hotline and request an urgent transfer recall / fraud case.",
      "Do not share OTP/TAC/passwords with anyone (including callers claiming to be from NSRC).",
      "Prepare key details: transaction time, amount, bank, account number, phone number, and any messages/screenshots.",
    ],
    saveEvidence: [
      "Screenshots of chat/SMS/email and the payment confirmation page.",
      "Phone numbers, bank account numbers, usernames, URLs, and timestamps.",
    ],
    contacts: [
      { label: "NSRC", value: "997", type: "phone" },
      { label: "Semak Mule (PDRM)", value: "https://semakmule.rmp.gov.my/", type: "url" },
    ],
    references: [REF_KOMUNIKASI_NSRC, REF_PDRM_SEMAKMULE],
    caveat: BASE_CAVEAT,
  },

  asked_to_pay: {
    scenario: "asked_to_pay",
    title: "Asked to pay urgently",
    oneLine: "Pause. Verify independently.",
    doNow: [
      "Do not transfer money, buy gift cards, or send crypto under pressure.",
      "Verify using official channels (numbers from official websites), not numbers provided in the message.",
      "If it claims to be a bank/government, hang up and call the official line yourself.",
    ],
    saveEvidence: ["Screenshot the request, profile, and any payment instructions."],
    contacts: [
      { label: "Semak Mule (PDRM)", value: "https://semakmule.rmp.gov.my/", type: "url" },
      { label: "NSRC", value: "997", type: "phone" },
    ],
    references: [REF_KOMUNIKASI_NSRC, REF_PDRM_SEMAKMULE],
    caveat: BASE_CAVEAT,
  },

  otp_password: {
    scenario: "otp_password",
    title: "OTP / password / TAC requested",
    oneLine: "Never share. Stop immediately.",
    doNow: [
      "Do not share OTP/TAC/passwords.",
      "If you already shared it, immediately contact your bank and change passwords.",
      "Enable MFA and review recent logins.",
    ],
    saveEvidence: ["Keep the message and caller details."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },

  impersonation: {
    scenario: "impersonation",
    title: "Impersonation (bank/government/police)",
    oneLine: "Hang up. Verify via official numbers.",
    doNow: [
      "Hang up. Do not stay on the line.",
      "Do not transfer to ‘safe accounts’.",
      "Verify by calling official numbers from official websites (not the caller).",
    ],
    saveEvidence: ["Record the story they told you, plus numbers and any documents they sent."],
    contacts: [
      { label: "NSRC", value: "997", type: "phone" },
      { label: "Semak Mule (PDRM)", value: "https://semakmule.rmp.gov.my/", type: "url" },
    ],
    references: [REF_KOMUNIKASI_NSRC, REF_PDRM_SEMAKMULE],
    caveat: BASE_CAVEAT,
  },

  courier: {
    scenario: "courier",
    title: "Courier / delivery scam",
    oneLine: "Don’t pay to “release” a parcel.",
    doNow: [
      "Do not pay fees via random links or personal accounts.",
      "Check tracking using the courier’s official app/website only.",
      "Treat threats (‘police case’, ‘fine’) as red flags.",
    ],
    saveEvidence: ["Screenshots of tracking pages and payment requests."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },

  investment: {
    scenario: "investment",
    title: "Investment / get-rich-quick",
    oneLine: "High returns + urgency is a classic pattern.",
    doNow: [
      "Do not deposit more money to ‘unlock’ withdrawals.",
      "Ask for a licensed entity name and verify independently before paying.",
      "Save everything before the chat disappears.",
    ],
    saveEvidence: ["Receipts, bank account details, group chat messages."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },

  job: {
    scenario: "job",
    title: "Job / recruiter scam",
    oneLine: "Never pay to get a job.",
    doNow: [
      "Do not pay ‘processing fees’ or share banking logins.",
      "Verify company details via official websites and real HR contacts.",
      "Be cautious with IC/passport requests early.",
    ],
    saveEvidence: ["Offer letter, WhatsApp chats, email headers."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },

  romance: {
    scenario: "romance",
    title: "Romance scam",
    oneLine: "Emotion + secrecy + money is the trap.",
    doNow: [
      "Do not send money to someone you have not met and verified.",
      "Watch for urgent emergencies and secrecy demands.",
      "Talk to a trusted person before you do anything.",
    ],
    saveEvidence: ["Photos, voice notes, money requests, transfer proof."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },

  other: {
    scenario: "other",
    title: "Other / unsure",
    oneLine: "If money moved, treat it as urgent.",
    doNow: [
      "If money moved: call NSRC 997 immediately.",
      "If asked to pay: pause and verify independently.",
      "Save evidence first before confronting the scammer.",
    ],
    saveEvidence: ["Screenshots, phone numbers, URLs, payment instructions."],
    contacts: [{ label: "NSRC", value: "997", type: "phone" }],
    references: [REF_KOMUNIKASI_NSRC],
    caveat: BASE_CAVEAT,
  },
};

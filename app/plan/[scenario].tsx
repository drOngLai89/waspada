import React, { useMemo } from "react";
import { Linking, ScrollView, Text, TouchableOpacity, View, StyleSheet, Platform } from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { styles as S } from "../../src/ui/styles";

type Source = { id: string; org: string; title: string; url: string; last_verified?: string };
type Step = { step: string; why?: string; source_ids?: string[] };

type Plan = {
  id: string;
  title: string;
  emoji: string;
  when: string;
  do_now: Step[];
  next_steps: Step[];
  who_to_contact: Step[];
  evidence_to_save: Step[];
  caveat: string;
  sources: Source[];
};

function openUrl(url: string) {
  if (!url) return;
  Linking.openURL(url);
}

function normalizeScenario(raw: string) {
  const s = (raw || "").toLowerCase().trim();
  const x = s
    .replaceAll("%20", " ")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\s+/g, " ")
    .trim();

  if (["money moved", "money already moved", "bank transfer", "funds moved"].includes(x)) return "money_moved";
  if (["asked to pay", "asked to pay money", "payment request", "pay now"].includes(x)) return "asked_to_pay";
  if (["otp", "otp password", "otp / password", "password", "tac", "otp tac", "otp tac password"].includes(x)) return "otp_password";
  if (["courier", "delivery", "parcel", "poslaju", "j&t", "jnt", "dhl"].includes(x)) return "courier";
  if (["investment", "crypto", "forex", "high return", "trading"].includes(x)) return "investment";
  if (["job", "recruitment", "interview", "work offer"].includes(x)) return "job";
  if (["romance", "love", "tinder", "dating"].includes(x)) return "romance";
  if (["impersonation", "scammer pretending", "police", "bank officer", "gov officer"].includes(x)) return "impersonation";
  if (["other", "see all", "unknown"].includes(x)) return "other";

  if (
    ["money_moved", "asked_to_pay", "otp_password", "courier", "investment", "job", "romance", "impersonation", "other"].includes(
      x.replaceAll(" ", "_")
    )
  ) {
    return x.replaceAll(" ", "_");
  }

  return "other";
}

function sourceMap(sources: Source[]) {
  const m = new Map<string, Source>();
  sources.forEach((s) => m.set(s.id, s));
  return m;
}

function getSources(): Source[] {
  return [
    {
      id: "NFCC_NSRC_997",
      org: "NFCC (Prime Minister’s Department)",
      title: "National Scam Response Centre (NSRC) 997",
      url: "https://nfcc.jpm.gov.my/?page_id=16693",
      last_verified: "2026-01-08",
    },
    {
      id: "PDRM_SEMAK_MULE_INFO",
      org: "PDRM (Royal Malaysia Police)",
      title: "Semak Mule + CCID response centre info",
      url: "https://www.rmp.gov.my/infor-korporate/berita/detail/2020/10/15/semak-mule-ccid-response-centre",
      last_verified: "2026-01-08",
    },
    {
      id: "SC_INVESTOR_ALERT_UPDATE",
      org: "Securities Commission Malaysia (SC)",
      title: "Investor Alert List update (includes hotline/email + investor-alert link)",
      url: "https://www.sc.com.my/resources/media/investor-alert-updates/investor-alert-list-as-at-23092025",
      last_verified: "2026-01-08",
    },
  ];
}

function buildPlans(): Record<string, Plan> {
  const sources = getSources();

  const commonEvidence: Step[] = [
    { step: "Screenshot the full conversation (include profile + timestamps).", why: "Context helps banks/authorities connect the dots." },
    { step: "Keep phone numbers, usernames, links/URLs, QR codes, and bank details shown.", why: "These are the identifiers investigators can act on." },
    { step: "Keep payment proof if any (receipts, transfer reference, wallet address, transaction hash).", why: "This is crucial if money already moved." },
  ];

  const commonCaveat =
    "This is AI-generated guidance and not official diagnostics. If you feel unsafe, if money has moved, or if you’re unsure, contact your bank and Malaysian authorities immediately.";

  return {
    money_moved: {
      id: "money_moved",
      title: "Money moved",
      emoji: "🚨",
      when: "Immediately",
      do_now: [
        { step: "Call your bank’s fraud hotline now and ask for urgent action (freeze/recall if possible).", why: "Speed matters. Early reporting gives the best chance of limiting loss.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Call NSRC 997 and follow their instructions.", why: "NSRC is the national channel for scam cases where funds may have moved.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Stop communicating with the scammer. Do not follow any further instructions.", why: "Scammers often push urgency and try to move you to another step quickly.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "Make a police report (Commercial Crime) as soon as possible.", why: "Formal reporting is often needed for investigation and follow-ups.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
        { step: "Check the recipient account/phone using PDRM Semak Mule if you have details.", why: "This can show whether the account has prior scam reports.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (for scams where funds may have moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (urgent).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (Commercial Crime / CCID channels remind public about Semak Mule & response centre).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    asked_to_pay: {
      id: "asked_to_pay",
      title: "Asked to pay",
      emoji: "💳",
      when: "Before paying anything",
      do_now: [
        { step: "Do not transfer money, buy gift cards, or send crypto, even if they threaten you.", why: "Urgency/threats are classic tells. If it’s real, you can verify via official channels.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Verify using official numbers from official websites (not numbers given by the other party).", why: "Fake “support” numbers are common in scams.", source_ids: ["NFCC_NSRC_997"] },
        { step: "If a bank account is provided, check it using PDRM Semak Mule.", why: "It may show whether the account has prior scam reports.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      next_steps: [
        { step: "If you already paid, treat it as ‘Money moved’: contact your bank and call NSRC 997 immediately.", why: "Reporting early increases the chance of recovery actions.", source_ids: ["NFCC_NSRC_997"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money already moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (if transfer/payment happened).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (report if fraud occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    otp_password: {
      id: "otp_password",
      title: "OTP / password",
      emoji: "🔐",
      when: "Immediately",
      do_now: [
        { step: "Stop engaging. Don’t click links, scan QR codes, or install apps requested by the other party.", why: "Scammers push urgency so you act before verifying through official channels.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Never share OTP/TAC/passwords. Do not allow remote access to your device.", why: "OTP/TAC and remote-control apps are commonly used to hijack accounts and move funds quickly.", source_ids: ["NFCC_NSRC_997", "PDRM_SEMAK_MULE_INFO"] },
        { step: "If money has moved, call your bank immediately and contact NSRC 997 right away.", why: "Speed matters. Early reporting can help banks/authorities respond faster.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "Change passwords (banking/email/social), enable 2FA, and review account activity.", why: "Assume credentials may be compromised if you clicked links or shared info.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Check any account numbers provided using PDRM Semak Mule.", why: "It may show whether the account has prior scam reports.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money has moved / online financial fraud).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (immediately if funds were transferred).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (make a police report where appropriate).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    courier: {
      id: "courier",
      title: "Courier",
      emoji: "📦",
      when: "Before clicking anything",
      do_now: [
        { step: "Do not click tracking links in SMS/WhatsApp if you weren’t expecting a parcel.", why: "Scam links often lead to fake payment pages or malware installs.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Check delivery status by typing the courier’s official website yourself (no link tapping).", why: "This avoids lookalike domains used in phishing.", source_ids: ["NFCC_NSRC_997"] },
        { step: "If they ask for ‘small fees’ to release a parcel, treat as suspicious until verified.", why: "Small-fee traps are a common pattern.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "If you paid or entered banking details, treat it as ‘Money moved’: call your bank + NSRC 997.", why: "Rapid reporting is the safest move.", source_ids: ["NFCC_NSRC_997"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if you entered info / paid / money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (if any payment happened).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if fraud occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    investment: {
      id: "investment",
      title: "Investment",
      emoji: "📈",
      when: "Before investing",
      do_now: [
        { step: "Be cautious of guaranteed returns, urgency, or pressure to move chat off-platform.", why: "These are classic red flags in investment scams.", source_ids: ["SC_INVESTOR_ALERT_UPDATE"] },
        { step: "Check whether the entity is flagged on SC’s Investor Alert information (guide list).", why: "SC publishes updates and encourages reports on suspicious capital market activities.", source_ids: ["SC_INVESTOR_ALERT_UPDATE"] },
        { step: "Do not transfer funds to personal accounts or unknown crypto wallets.", why: "Once funds are moved, recovery can be difficult.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "If you already transferred funds, call your bank immediately and contact NSRC 997.", why: "Faster reporting improves odds of intervention.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Make a police report if you suspect fraud and keep all proof.", why: "Formal reporting supports investigation.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      who_to_contact: [
        { step: "Securities Commission Malaysia: hotline/email are listed on SC’s investor alert update page.", source_ids: ["SC_INVESTOR_ALERT_UPDATE"] },
        { step: "NSRC 997 (if money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if scam/fraud occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    job: {
      id: "job",
      title: "Job",
      emoji: "🧑‍💼",
      when: "Before paying fees / sharing documents",
      do_now: [
        { step: "Do not pay ‘processing fees’, ‘training fees’, or ‘equipment fees’ to get a job.", why: "Upfront payments are a common job-scam pattern.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Verify the company via official channels and avoid WhatsApp-only ‘HR’ processes.", why: "Scammers mimic real companies but use unofficial contact routes.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "If you already paid, contact your bank and call NSRC 997 immediately.", why: "Treat it as money moved.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Make a police report if fraud is telling you to pay/transfer.", why: "Reporting helps enforcement follow up.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (if payment happened).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if scam occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    romance: {
      id: "romance",
      title: "Romance",
      emoji: "❤️",
      when: "Before sending money or gifts",
      do_now: [
        { step: "Do not send money, gift cards, or crypto to someone you haven’t met and verified.", why: "Romance scams often build trust, then trigger a money request.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Watch for secrecy, urgency, emotional pressure, or excuses to avoid video calls.", why: "These are common manipulation patterns.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "Talk to a trusted friend/family member before taking any action.", why: "A second opinion helps break the emotional pressure cycle.", source_ids: ["NFCC_NSRC_997"] },
        { step: "If money already moved, contact your bank and call NSRC 997 immediately.", why: "Treat it as money moved.", source_ids: ["NFCC_NSRC_997"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (if payment happened).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if fraud occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    impersonation: {
      id: "impersonation",
      title: "Impersonation",
      emoji: "🎭",
      when: "Before following instructions",
      do_now: [
        { step: "Do not follow instructions from someone claiming to be police/bank/government without verifying via official channels.", why: "Impersonation scams rely on authority pressure and urgency.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Call back using official numbers from official websites (not the caller’s number).", why: "Call spoofing is common; the displayed number may be fake.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "If money moved or details were shared, call your bank and contact NSRC 997 immediately.", why: "Treat as high risk.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Make a police report if you suspect fraud.", why: "Helps enforcement investigate patterns and accounts involved.", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "Your bank’s fraud hotline (if account access/payment risk).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if impersonation scam occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },

    other: {
      id: "other",
      title: "Other",
      emoji: "🧩",
      when: "As soon as you feel something is off",
      do_now: [
        { step: "Pause. Don’t click links, don’t install apps, and don’t send money until verified.", why: "Most scam damage happens when urgency wins.", source_ids: ["NFCC_NSRC_997"] },
        { step: "Verify using official numbers from official websites, not numbers provided by the other party.", why: "Scammers often provide fake hotline numbers.", source_ids: ["NFCC_NSRC_997"] },
      ],
      next_steps: [
        { step: "If you already transferred funds, contact your bank and call NSRC 997 immediately.", why: "Treat as money moved.", source_ids: ["NFCC_NSRC_997"] },
        { step: "If it looks like an investment pitch, check SC’s investor alert guidance and contact SC if suspicious.", why: "SC encourages reporting suspicious capital market activities (hotline/email listed).", source_ids: ["SC_INVESTOR_ALERT_UPDATE"] },
      ],
      who_to_contact: [
        { step: "NSRC 997 (if money moved).", source_ids: ["NFCC_NSRC_997"] },
        { step: "PDRM (if scam/fraud occurred).", source_ids: ["PDRM_SEMAK_MULE_INFO"] },
        { step: "Securities Commission Malaysia (for suspicious investment activities).", source_ids: ["SC_INVESTOR_ALERT_UPDATE"] },
      ],
      evidence_to_save: commonEvidence,
      caveat: commonCaveat,
      sources,
    },
  };
}

export default function ActionPlanScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ scenario?: string | string[] }>();

  const scenarioRaw = Array.isArray(params.scenario) ? params.scenario[0] : params.scenario || "";
  const scenario = normalizeScenario(String(scenarioRaw || ""));
  const plans = useMemo(() => buildPlans(), []);
  const plan = plans[scenario] || plans.other;

  const sources = useMemo(() => sourceMap(plan.sources), [plan.sources]);

  const renderSteps = (items: Step[]) =>
    items.map((a, i) => (
      <View key={i} style={SS.itemCard}>
        <Text style={SS.itemStep}>• {a.step}</Text>
        {!!a.why && <Text style={SS.itemWhy}>{a.why}</Text>}

        {!!(a.source_ids && a.source_ids.length) && (
          <View style={SS.refsRow}>
            <Text style={SS.refsLabel}>Refs: </Text>
            {a.source_ids.slice(0, 3).map((sid, j) => {
              const s = sources.get(sid);
              const label = s?.org || sid;
              const url = s?.url;
              return (
                <Text key={sid} style={SS.refsLink} onPress={() => (url ? openUrl(url) : null)}>
                  {label}
                  {j < Math.min(2, (a.source_ids?.length || 0) - 1) ? "  " : ""}
                </Text>
              );
            })}
          </View>
        )}
      </View>
    ));

  return (
    <>
      <Stack.Screen options={{ headerShown: false }} />
      <ScrollView style={S.screen} contentContainerStyle={S.container}>
        {/* Make the top tap targets comfortable under the notch */}
        <View style={{ paddingTop: Math.max(insets.top, 10) + 8 }}>
          <TouchableOpacity style={SS.backPill} onPress={() => router.back()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Text style={SS.backText}>‹ Back</Text>
          </TouchableOpacity>
        </View>

        <View style={S.hero}>
          <Text style={S.heroTitle}>
            {plan.emoji} {plan.title}
          </Text>
          <Text style={S.heroSub}>Malaysia-first steps with official references.</Text>
          <Text style={SS.whenText}>When: {plan.when}</Text>
        </View>

        <View style={SS.section}>
          <View style={SS.sectionHeader}>
            <Text style={SS.sectionEmoji}>✅</Text>
            <Text style={SS.sectionTitle}>Do this now</Text>
          </View>
          {renderSteps(plan.do_now)}
        </View>

        <View style={SS.section}>
          <View style={SS.sectionHeader}>
            <Text style={SS.sectionEmoji}>➡️</Text>
            <Text style={SS.sectionTitle}>Next steps</Text>
          </View>
          {renderSteps(plan.next_steps)}
        </View>

        <View style={SS.section}>
          <View style={SS.sectionHeader}>
            <Text style={SS.sectionEmoji}>📞</Text>
            <Text style={SS.sectionTitle}>Who to contact</Text>
          </View>
          {renderSteps(plan.who_to_contact)}
        </View>

        <View style={SS.section}>
          <View style={SS.sectionHeader}>
            <Text style={SS.sectionEmoji}>🧾</Text>
            <Text style={SS.sectionTitle}>Evidence to save</Text>
          </View>
          {renderSteps(plan.evidence_to_save)}
        </View>

        <View style={S.caveatBox}>
          <Text style={S.caveatTitle}>Caveat</Text>
          <Text style={S.caveatText}>{plan.caveat}</Text>
        </View>

        <View style={SS.refsBox}>
          <Text style={SS.refsBoxTitle}>Official references used</Text>
          {plan.sources.slice(0, 8).map((s) => (
            <Text key={s.id} style={SS.refItem} onPress={() => openUrl(s.url)}>
              • {s.org}: {s.title} (verified {s.last_verified || "—"})
            </Text>
          ))}
        </View>

        <View style={SS.bottomSpace} />
      </ScrollView>
    </>
  );
}

const SS = StyleSheet.create({
  backPill: {
    alignSelf: "flex-start",
    marginBottom: 10,
    borderRadius: 999,
    paddingVertical: 10,
    paddingHorizontal: 14,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E6E8F2",
  },
  backText: { fontSize: 14, fontWeight: "800", color: "#0F172A" },
  whenText: { marginTop: 10, fontSize: 13, fontWeight: "800", color: "rgba(255,255,255,0.95)" },

  section: { marginTop: 12 },
  sectionHeader: { flexDirection: "row", alignItems: "center", marginBottom: 8, paddingLeft: 6 },
  sectionEmoji: { fontSize: 18, marginRight: 8 },
  sectionTitle: { fontSize: 16, fontWeight: "900", color: "#0F172A" },

  itemCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: "#E6E8F2",
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
  },
  itemStep: { fontSize: 14.5, fontWeight: "900", color: "#0F172A", lineHeight: 20 },
  itemWhy: { marginTop: 8, fontSize: 13.5, color: "#475569", lineHeight: 18, fontWeight: "600" },

  refsRow: { flexDirection: "row", flexWrap: "wrap", marginTop: 10, alignItems: "center" },
  refsLabel: { fontSize: 12, fontWeight: "900", color: "#64748B", marginRight: 6 },
  refsLink: { fontSize: 12, fontWeight: "900", color: "#1D4ED8", marginRight: 10 },

  refsBox: { marginTop: 12, borderRadius: 14, backgroundColor: "#F7F8FC", borderWidth: 1, borderColor: "#E6E8F2", padding: 12 },
  refsBoxTitle: { fontSize: 13.5, fontWeight: "900", color: "#0F172A", marginBottom: 8 },
  refItem: { fontSize: 12.5, color: "#334155", lineHeight: 18, fontWeight: "700", marginBottom: 6 },

  bottomSpace: { height: 18 },
});

import React, { useMemo, useState } from "react";
import { Alert, Image, Linking, ScrollView, Text, TouchableOpacity, View, Switch } from "react-native";
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from "expo-file-system/legacy";
import { analyzeScreenshot } from "../../src/lib/api";
import { styles } from "../../src/ui/styles";

type Source = { id: string; title: string; org: string; url: string; notes?: string; last_verified?: string };
type Action = { step: string; why?: string; source_ids?: string[] };
type Contact = { name: string; type: "phone" | "url" | "email"; value: string; notes?: string; source_ids?: string[] };

type Result = {
  verdict?: string;
  risk?: string;
  malaysia_relevance?: string;
  scenario?: string;
  out_of_scope?: boolean;

  what_the_screenshot_shows?: string[];
  analysis?: string;
  findings?: string[];
  recommended_next_actions?: Action[];
  who_to_contact?: Contact[];
  evidence_to_save?: string[];
  caveat?: string;
  sources?: Source[];
};

function mediaTypesOption() {
  const anyPicker: any = ImagePicker as any;
  // support older + newer Expo
  return anyPicker.MediaType?.Images ?? anyPicker.MediaTypeOptions?.Images;
}

function sourceMap(sources?: Source[]) {
  const m = new Map<string, Source>();
  (sources || []).forEach((s) => m.set(s.id, s));
  return m;
}

function openValue(c: Contact) {
  if (c.type === "phone") return Linking.openURL(`tel:${c.value}`);
  if (c.type === "email") return Linking.openURL(`mailto:${c.value}`);
  return Linking.openURL(c.value);
}

// 👇 Critical: normalize any risky/defamatory-sounding labels coming from API
function displayVerdict(v?: string, risk?: string) {
  const raw = (v || "").toString().trim();
  const up = raw.toUpperCase();

  // If backend still sends old labels like "LIKELY SCAM" / "SCAM" / "FRAUD"
  if (up.includes("SCAM") || up.includes("FRAUD")) {
    if ((risk || "").toUpperCase() === "HIGH") return "HIGH RISK INDICATORS";
    if ((risk || "").toUpperCase() === "MEDIUM") return "SUSPICIOUS INDICATORS";
    return "UNCLEAR • NEEDS VERIFICATION";
  }

  // New enum style: HIGH_RISK_INDICATORS, etc
  if (up.includes("HIGH_RISK")) return "HIGH RISK INDICATORS";
  if (up.includes("SUSPICIOUS")) return "SUSPICIOUS INDICATORS";
  if (up.includes("UNCLEAR")) return "UNCLEAR • NEEDS VERIFICATION";

  // Fallback: still avoid accusatory phrasing
  if (!raw) return "UNCLEAR • NEEDS VERIFICATION";
  return raw.replaceAll("_", " ");
}

function displayRisk(r?: string) {
  const up = (r || "").toUpperCase();
  if (up === "HIGH" || up === "MEDIUM" || up === "LOW") return up;
  return "LOW";
}

/**
 * Redaction helpers
 * Goal: reduce identification risk in the AI-generated text (not the screenshot image itself).
 * This is NOT perfect, but it prevents the app from repeating phone numbers/emails in its own output.
 */
function redactEmails(text: string) {
  // Basic email pattern
  return text.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted email]");
}

function redactPhones(text: string) {
  // Replace "phone-like" sequences: optional +, digits/spaces/hyphens, total digits >= 8
  // Keeps short numbers like 997 untouched.
  return text.replace(/(\+?\d[\d\s-]{6,}\d)/g, (m) => {
    const digits = (m.match(/\d/g) || []).length;
    if (digits >= 8) return "[redacted number]";
    return m;
  });
}

function redactIdentifiers(text: string) {
  return redactPhones(redactEmails(text));
}

function safeText(text: string | undefined, redactOn: boolean) {
  const t = (text || "").toString();
  return redactOn ? redactIdentifiers(t) : t;
}

function safeList(list: string[] | undefined, redactOn: boolean) {
  return (list || []).filter(Boolean).map((t) => safeText(t, redactOn));
}

function safeActions(actions: Action[] | undefined, redactOn: boolean): Action[] {
  return (actions || []).map((a) => ({
    ...a,
    step: safeText(a.step, redactOn),
    why: a.why ? safeText(a.why, redactOn) : a.why,
  }));
}

export default function VerifyScreen() {
  const [image, setImage] = useState<string | null>(null);
  const [kb, setKb] = useState<number>(0);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  // Safety toggles
  const [redactOn, setRedactOn] = useState(true);
  const [showReportOptions, setShowReportOptions] = useState(false);

  const pick = async () => {
    setResult(null);

    const mt = mediaTypesOption();
    const opts: any = {
      quality: 0.85,
      allowsEditing: false,
      base64: true,
    };
    if (mt) opts.mediaTypes = mt;

    const res = await ImagePicker.launchImageLibraryAsync(opts);
    if (res.canceled) return;

    const asset = res.assets?.[0];
    if (!asset?.uri) return;

    // Approx KB for UX only
    const info = await FileSystem.getInfoAsync(asset.uri);
    const sizeKb = info.exists && info.size ? Math.round(info.size / 1024) : 0;
    setKb(sizeKb);

    // Prefer base64 from picker if available; otherwise read it
    let b64 = (asset as any).base64;
    if (!b64) {
      b64 = await FileSystem.readAsStringAsync(asset.uri, { encoding: FileSystem.EncodingType.Base64 });
    }
    const mime = (asset as any).mimeType || "image/jpeg";
    const dataUrl = `data:${mime};base64,${b64}`;
    setImage(dataUrl);
  };

  const verify = async () => {
    if (!image) {
      Alert.alert("Pick a screenshot first", "Choose a screenshot before verifying.");
      return;
    }

    setBusy(true);
    try {
      const out = await analyzeScreenshot(image, "EN");
      setResult(out as Result);
    } catch (e: any) {
      // Make errors readable (avoid [object Object])
      const msg =
        typeof e?.message === "string"
          ? e.message
          : typeof e === "string"
          ? e
          : JSON.stringify(e);
      Alert.alert("Verification failed", msg || "Unknown error");
    } finally {
      setBusy(false);
    }
  };

  const sources = useMemo(() => sourceMap(result?.sources), [result?.sources]);

  const whatShows = safeList(result?.what_the_screenshot_shows, redactOn);
  const whatShowsSafe =
    whatShows.length > 0
      ? whatShows
      : ["Couldn’t reliably read the text. Try a clearer screenshot with the full message visible."];

  const analysisSafe = safeText(result?.analysis, redactOn);
  const findingsSafe = safeList(result?.findings, redactOn);
  const actionsSafe = safeActions(result?.recommended_next_actions, redactOn);

  const risk = displayRisk(result?.risk);
  const verdictLabel = displayVerdict(result?.verdict, risk);

  // For extra safety: do not show reporting-oriented actions until user explicitly opts in.
  const filteredActions = showReportOptions
    ? actionsSafe
    : actionsSafe.filter((a) => {
        const up = (a.step || "").toUpperCase();
        // hide report/police keywords unless user enables it
        if (up.includes("REPORT") || up.includes("POLICE") || up.includes("PDRM") || up.includes("CYBER") || up.includes("CCID")) return false;
        return true;
      });

  const hasHiddenReportActions = actionsSafe.length !== filteredActions.length;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>Verify</Text>
        <Text style={styles.heroSub}>
          We’ll interpret a screenshot and suggest Malaysia-first next steps with official references.
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.h}>Screenshot</Text>
        <Text style={styles.p}>
          Pick a screenshot of a suspicious message, payment request, bank screen, courier SMS, investment pitch, or impersonation.
        </Text>

        {!!image && (
          <View style={styles.previewBox}>
            <Image source={{ uri: image }} style={styles.previewImg} />
          </View>
        )}

        <TouchableOpacity style={styles.btnDark} onPress={pick}>
          <Text style={styles.btnTextDark}>{image ? "Pick another screenshot" : "Pick screenshot"}</Text>
        </TouchableOpacity>

        <Text style={styles.meta}>Payload (approx): {kb ? `${kb} KB` : "—"}</Text>

        <TouchableOpacity style={[styles.btn, { marginTop: 10, opacity: busy ? 0.7 : 1 }]} onPress={verify} disabled={busy}>
          <Text style={styles.btnText}>{busy ? "Verifying…" : "Verify"}</Text>
        </TouchableOpacity>
      </View>

      {result ? (
        <View style={styles.card}>
          <View style={styles.badgeRow}>
            <View
              style={[
                styles.badge,
                risk === "HIGH" ? styles.badgeHigh : risk === "MEDIUM" ? styles.badgeMed : styles.badgeLow,
              ]}
            >
              <Text style={styles.badgeText}>
                {verdictLabel} • {risk}
              </Text>
            </View>
          </View>

          {/* Strong, upfront non-accusation notice */}
          <View style={[styles.caveatBox, { marginTop: 12 }]}>
            <Text style={styles.caveatTitle}>About this assessment</Text>
            <Text style={styles.caveatText}>
              This is an automated, pattern-based risk signal from a screenshot. It cannot verify legitimacy, licensing, intent, or identity.
              Waspada does not accuse any person or organisation of being a scammer or committing a crime.
            </Text>

            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 10 }}>
              <View style={{ flex: 1, paddingRight: 12 }}>
                <Text style={[styles.p, { marginBottom: 0 }]}>Redact identifiers in the AI text (recommended)</Text>
                <Text style={styles.meta}>
                  Hides phone numbers/emails in the written analysis to reduce accidental naming or sharing.
                </Text>
              </View>
              <Switch value={redactOn} onValueChange={setRedactOn} />
            </View>
          </View>

          <Text style={styles.h}>Malaysia relevance</Text>
          <Text style={styles.p}>{safeText(result.malaysia_relevance, redactOn) || "—"}</Text>

          <Text style={[styles.h, { marginTop: 14 }]}>What the screenshot shows</Text>
          {whatShowsSafe.map((t, i) => (
            <Text key={i} style={styles.bullet}>• {t}</Text>
          ))}

          {!!analysisSafe && (
            <>
              <Text style={[styles.h, { marginTop: 14 }]}>Analysis (pattern-based)</Text>
              <Text style={styles.p}>{analysisSafe}</Text>
            </>
          )}

          {!!(findingsSafe && findingsSafe.length) && (
            <>
              <Text style={[styles.h, { marginTop: 14 }]}>Signals detected</Text>
              {findingsSafe.slice(0, 10).map((t, i) => (
                <Text key={i} style={styles.bullet}>• {t}</Text>
              ))}
            </>
          )}

          {!!(actionsSafe && actionsSafe.length) && (
            <>
              <Text style={[styles.h, { marginTop: 14 }]}>Suggested next steps (options)</Text>
              <Text style={styles.p}>
                These are optional precautions, not allegations. Reporting is appropriate only if you reasonably suspect wrongdoing or if money/details were shared.
                Avoid posting public accusations based on this result.
              </Text>

              {/* Default: hide report/police actions unless user opts in */}
              {hasHiddenReportActions && !showReportOptions && (
                <View style={[styles.actionCard, { marginTop: 10 }]}>
                  <Text style={styles.actionStep}>• Show reporting options?</Text>
                  <Text style={styles.actionWhy}>
                    If you’ve lost money, shared bank details, or strongly believe it’s fraud, you can view official reporting channels here.
                  </Text>
                  <TouchableOpacity
                    style={[styles.btnDark, { marginTop: 10 }]}
                    onPress={() => setShowReportOptions(true)}
                  >
                    <Text style={styles.btnTextDark}>Show reporting options</Text>
                  </TouchableOpacity>
                </View>
              )}

              {filteredActions.slice(0, 10).map((a, i) => (
                <View key={i} style={styles.actionCard}>
                  <Text style={styles.actionStep}>• {a.step}</Text>
                  {!!a.why && <Text style={styles.actionWhy}>{a.why}</Text>}
                  {!!(a.source_ids && a.source_ids.length) && (
                    <View style={styles.refsRow}>
                      <Text style={styles.refsLabel}>Refs: </Text>
                      {a.source_ids.slice(0, 3).map((sid) => {
                        const s = sources.get(sid);
                        if (!s) return (
                          <Text key={sid} style={styles.refsText}>{sid}</Text>
                        );
                        return (
                          <Text
                            key={sid}
                            style={styles.refsLink}
                            onPress={() => Linking.openURL(s.url)}
                          >
                            {s.org}
                          </Text>
                        );
                      })}
                    </View>
                  )}
                </View>
              ))}
            </>
          )}

          {!!(result.who_to_contact && result.who_to_contact.length) && (
            <>
              <Text style={[styles.h, { marginTop: 14 }]}>Official contacts</Text>
              <Text style={styles.p}>
                Use these official channels to verify legitimacy or to report privately if needed. Don’t contact unknown numbers from the message itself.
              </Text>

              {result.who_to_contact.slice(0, 8).map((c, i) => (
                <TouchableOpacity key={i} style={styles.contactRow} onPress={() => openValue(c)}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.contactName}>{c.name}</Text>
                    <Text style={styles.contactValue}>{c.value}</Text>
                    {!!c.notes && <Text style={styles.contactNotes}>{safeText(c.notes, redactOn)}</Text>}
                    {!!(c.source_ids && c.source_ids.length) && (
                      <Text style={styles.contactRefs}>
                        Refs: {c.source_ids.filter(Boolean).slice(0, 2).join(", ")}
                      </Text>
                    )}
                  </View>
                  <Text style={styles.contactGo}>Open</Text>
                </TouchableOpacity>
              ))}
            </>
          )}

          {/* Stronger, anti-defamation caveat */}
          <View style={styles.caveatBox}>
            <Text style={styles.caveatTitle}>Caveat and safe sharing</Text>
            <Text style={styles.caveatText}>
              {result.caveat
                ? safeText(result.caveat, redactOn)
                : "This is automated, pattern-based guidance and not an official finding. It may be wrong or incomplete."}
            </Text>
            <Text style={[styles.caveatText, { marginTop: 8 }]}>
              • Don’t name, tag, or publicly accuse individuals/companies based on this screen.
            </Text>
            <Text style={styles.caveatText}>
              • If you need help, use official channels listed here and report privately.
            </Text>
            <Text style={styles.caveatText}>
              • If money moved or bank details were shared, contact your bank immediately and call NSRC 997.
            </Text>
          </View>

          {!!(result.sources && result.sources.length) && (
            <>
              <Text style={[styles.h, { marginTop: 14 }]}>Official references used</Text>
              {result.sources.slice(0, 8).map((s) => (
                <Text key={s.id} style={styles.refItem} onPress={() => Linking.openURL(s.url)}>
                  • {s.org}: {s.title} (verified {s.last_verified || "—"})
                </Text>
              ))}
            </>
          )}
        </View>
      ) : null}
    </ScrollView>
  );
}

import React, { useEffect, useMemo, useState } from "react";
import {
  Linking,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  ActivityIndicator,
  StyleSheet,
  Platform,
} from "react-native";
import { getResources } from "../../src/lib/api";
import { styles } from "../../src/ui/styles";

type Source = {
  id: string;
  title: string;
  org: string;
  url: string; // can be https://... or tel:... or mailto:...
  notes?: string;
  last_verified?: string;
};

type Cat = { id: string; title: string; items: Source[] };

type Payload = {
  last_verified?: string;
  categories: Cat[];
};

function emojiForCategory(title: string, id: string) {
  const t = (title || id || "").toLowerCase();
  if (t.includes("urgent") || t.includes("money moved") || t.includes("transfer")) return "🚨";
  if (t.includes("check before you pay") || t.includes("accounts") || t.includes("investment")) return "🧾";
  if (t.includes("bank") || t.includes("bnm") || t.includes("financial")) return "🏦";
  if (t.includes("report") || t.includes("police") || t.includes("pdrm") || t.includes("ccid")) return "🛡️";
  if (t.includes("courier") || t.includes("delivery") || t.includes("parcel")) return "📦";
  if (t.includes("job") || t.includes("employment")) return "💼";
  if (t.includes("romance") || t.includes("love")) return "💔";
  if (t.includes("otp") || t.includes("tac") || t.includes("password")) return "🔐";
  if (t.includes("tech") || t.includes("online") || t.includes("scam")) return "🕵️";
  return "📌";
}

function emojiForLink(url: string) {
  const u = (url || "").toLowerCase().trim();
  if (u.startsWith("tel:")) return "☎️";
  if (u.startsWith("mailto:")) return "✉️";
  return "🔗";
}

function safeOpen(url: string) {
  if (!url) return;
  Linking.openURL(url).catch(() => {
    // no alert spam here, keep it calm
  });
}

function matchesQuery(s: Source, q: string) {
  if (!q) return true;
  const qq = q.toLowerCase();
  const hay = `${s.org} ${s.title} ${s.notes || ""} ${s.url}`.toLowerCase();
  return hay.includes(qq);
}

export default function ResourcesScreen() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [data, setData] = useState<Payload | null>(null);
  const [query, setQuery] = useState("");

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const out = await getResources();
      setData(out as Payload);
    } catch (e: any) {
      setErr(e?.message || "Couldn’t load resources.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const lastVerified = data?.last_verified || data?.categories?.[0]?.items?.[0]?.last_verified || "—";

  const filteredCats = useMemo(() => {
    const cats = data?.categories || [];
    const q = query.trim();
    const res: Cat[] = [];
    for (const c of cats) {
      const items = (c.items || []).filter((it) => matchesQuery(it, q));
      if (items.length) res.push({ ...c, items });
    }
    return res;
  }, [data, query]);

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <View style={[styles.hero, local.heroAlt]}>
        <Text style={styles.heroTitle}>Resources</Text>
        <Text style={styles.heroSub}>Official Malaysia anti-scam contacts and reference lists.</Text>

        <View style={local.heroMetaRow}>
          <Text style={local.heroMeta}>Last verified: {lastVerified}</Text>
          <TouchableOpacity onPress={load} style={local.refreshPill}>
            <Text style={local.refreshText}>↻ Refresh</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={[styles.card, local.searchCard]}>
        <Text style={local.searchLabel}>Find a hotline / site</Text>
        <View style={local.searchRow}>
          <Text style={local.searchIcon}>🔎</Text>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Try: 997, NSRC, Semak Mule, BNM, PDRM, CCID…"
            placeholderTextColor="#7A8092"
            style={local.searchInput}
            autoCapitalize="none"
            autoCorrect={false}
            clearButtonMode="while-editing"
          />
        </View>
        <Text style={local.searchHint}>
          Tip: If money already moved, look for <Text style={local.bold}>NSRC 997</Text> first.
        </Text>
      </View>

      {loading ? (
        <View style={[styles.card, local.centerCard]}>
          <ActivityIndicator />
          <Text style={[styles.meta, { marginTop: 10 }]}>Loading…</Text>
        </View>
      ) : err ? (
        <View style={[styles.card, local.centerCard]}>
          <Text style={local.errTitle}>Couldn’t load</Text>
          <Text style={local.errText}>{err}</Text>
          <TouchableOpacity style={[styles.btn, { marginTop: 12 }]} onPress={load}>
            <Text style={styles.btnText}>Try again</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      {!loading && !err && filteredCats.length === 0 ? (
        <View style={[styles.card, local.centerCard]}>
          <Text style={local.errTitle}>No matches</Text>
          <Text style={local.errText}>Try a different keyword, e.g. “BNM”, “Semak Mule”, “997”.</Text>
        </View>
      ) : null}

      {!loading &&
        !err &&
        filteredCats.map((cat) => {
          const emoji = emojiForCategory(cat.title, cat.id);
          return (
            <View key={cat.id} style={[styles.card, local.catCard]}>
              <View style={local.catHeader}>
                <View style={local.catHeaderLeft}>
                  <Text style={local.catEmoji}>{emoji}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={local.catTitle}>{cat.title}</Text>
                    <Text style={local.catCount}>{cat.items.length} items</Text>
                  </View>
                </View>
              </View>

              <View style={local.listWrap}>
                {cat.items.map((s) => {
                  const linkEmoji = emojiForLink(s.url);
                  const isTel = (s.url || "").toLowerCase().startsWith("tel:");
                  const primaryAction = isTel ? "Call" : "Open";

                  return (
                    <View key={s.id} style={local.itemCard}>
                      <View style={local.itemTopRow}>
                        <Text style={local.itemIcon}>{linkEmoji}</Text>
                        <View style={{ flex: 1 }}>
                          <Text style={local.itemTitle}>{s.title}</Text>
                          <Text style={local.itemOrg}>{s.org}</Text>
                        </View>
                        <TouchableOpacity
                          style={[local.actionBtn, isTel ? local.actionBtnCall : local.actionBtnOpen]}
                          onPress={() => safeOpen(s.url)}
                        >
                          <Text style={local.actionBtnText}>{primaryAction}</Text>
                        </TouchableOpacity>
                      </View>

                      {!!s.notes && <Text style={local.itemNotes}>{s.notes}</Text>}

                      <View style={local.itemMetaRow}>
                        <Text style={local.itemMeta}>
                          Verified: <Text style={local.bold}>{s.last_verified || "—"}</Text>
                        </Text>
                        <Text style={local.itemMetaDim}>ID: {s.id}</Text>
                      </View>
                    </View>
                  );
                })}
              </View>

              <View style={local.footerHint}>
                <Text style={local.footerHintText}>
                  If you’re unsure which one applies, start with <Text style={local.bold}>NSRC 997</Text> (money moved) or{" "}
                  <Text style={local.bold}>PDRM e-Reporting</Text>.
                </Text>
              </View>
            </View>
          );
        })}

      <View style={local.bottomSpace} />
    </ScrollView>
  );
}

const local = StyleSheet.create({
  heroAlt: {
    backgroundColor: "#1E5AD7",
  },
  heroMetaRow: {
    marginTop: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  heroMeta: {
    color: "rgba(255,255,255,0.92)",
    fontSize: 13,
    fontWeight: "600",
  },
  refreshPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.18)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.25)",
  },
  refreshText: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "700",
  },

  searchCard: {
    marginTop: 10,
  },
  searchLabel: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0D1220",
    marginBottom: 8,
  },
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    backgroundColor: "#F7F8FC",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: Platform.OS === "ios" ? 10 : 8,
  },
  searchIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#0D1220",
    paddingVertical: 2,
  },
  searchHint: {
    marginTop: 8,
    fontSize: 12.5,
    color: "#5B6275",
    lineHeight: 18,
  },
  bold: {
    fontWeight: "800",
    color: "#0D1220",
  },

  centerCard: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 18,
  },
  errTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: "#0D1220",
  },
  errText: {
    marginTop: 6,
    fontSize: 13.5,
    color: "#5B6275",
    textAlign: "center",
    lineHeight: 19,
  },

  catCard: {
    marginTop: 14,
    paddingBottom: 14,
  },
  catHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  catHeaderLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    flex: 1,
  },
  catEmoji: {
    fontSize: 22,
  },
  catTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: "#0D1220",
  },
  catCount: {
    marginTop: 2,
    fontSize: 12.5,
    color: "#6A7186",
    fontWeight: "600",
  },

  listWrap: {
    gap: 10,
  },
  itemCard: {
    borderWidth: 1,
    borderColor: "#E7E9F2",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 12,
  },
  itemTopRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  itemIcon: {
    fontSize: 18,
    width: 26,
    textAlign: "center",
  },
  itemTitle: {
    fontSize: 14.5,
    fontWeight: "900",
    color: "#0D1220",
    lineHeight: 19,
  },
  itemOrg: {
    marginTop: 2,
    fontSize: 12.5,
    color: "#4F5770",
    fontWeight: "700",
  },
  itemNotes: {
    marginTop: 10,
    fontSize: 13,
    color: "#30374C",
    lineHeight: 18,
  },
  itemMetaRow: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#EEF0F7",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  itemMeta: {
    fontSize: 12,
    color: "#5B6275",
    fontWeight: "700",
  },
  itemMetaDim: {
    fontSize: 12,
    color: "#8A92A8",
    fontWeight: "700",
  },

  actionBtn: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 12,
    borderWidth: 1,
  },
  actionBtnOpen: {
    backgroundColor: "#EAF1FF",
    borderColor: "#CFE0FF",
  },
  actionBtnCall: {
    backgroundColor: "#E9FFF1",
    borderColor: "#C6F3D6",
  },
  actionBtnText: {
    fontSize: 13,
    fontWeight: "900",
    color: "#0D1220",
  },

  footerHint: {
    marginTop: 12,
    borderRadius: 14,
    backgroundColor: "#F7F8FC",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 12,
  },
  footerHintText: {
    fontSize: 12.5,
    color: "#4F5770",
    lineHeight: 18,
    fontWeight: "600",
  },

  bottomSpace: {
    height: 18,
  },
});

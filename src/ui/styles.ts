import { StyleSheet } from "react-native";

export const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#FFFFFF" },

  screen: { flex: 1, backgroundColor: "#F5F7FF" },
  container: { padding: 16, paddingBottom: 24 },

  hero: {
    borderRadius: 18,
    backgroundColor: "#1D5BD6",
    padding: 16,
    marginBottom: 12,
  },
  heroTitle: { fontSize: 38, fontWeight: "900", color: "#FFFFFF", letterSpacing: -0.8 },
  heroSub: { marginTop: 6, fontSize: 14, color: "rgba(255,255,255,0.92)", lineHeight: 20, fontWeight: "600" },
  heroMeta: { marginTop: 8, fontSize: 13, color: "rgba(255,255,255,0.95)", fontWeight: "800" },

  card: {
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 14,
    marginTop: 12,
  },

  h: { fontSize: 18, fontWeight: "900", color: "#0F172A" },
  p: { marginTop: 8, fontSize: 14, color: "#334155", lineHeight: 20, fontWeight: "600" },

  meta: { marginTop: 10, fontSize: 12.5, color: "#64748B", fontWeight: "700" },
  metaCenter: { marginTop: 14, fontSize: 12.5, color: "#64748B", fontWeight: "700", textAlign: "center" },

  btn: {
    borderRadius: 14,
    backgroundColor: "#1D4ED8",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnText: { color: "#FFFFFF", fontWeight: "900", fontSize: 15 },

  btnDark: {
    marginTop: 12,
    borderRadius: 14,
    backgroundColor: "#0F172A",
    paddingVertical: 14,
    alignItems: "center",
  },
  btnTextDark: { color: "#FFFFFF", fontWeight: "900", fontSize: 15 },

  chipGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10, marginTop: 12 },
  chip: {
    borderRadius: 999,
    backgroundColor: "#EEF2FF",
    borderWidth: 1,
    borderColor: "#DDE3FF",
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  chipText: { fontSize: 13.5, fontWeight: "900", color: "#1E3A8A" },

  badgeRow: { flexDirection: "row", marginBottom: 10 },
  badge: { borderRadius: 999, paddingVertical: 8, paddingHorizontal: 12 },
  badgeHigh: { backgroundColor: "#B91C1C" },
  badgeMed: { backgroundColor: "#92400E" },
  badgeLow: { backgroundColor: "#1F2937" },
  badgeText: { color: "#FFFFFF", fontWeight: "900", fontSize: 12.5 },

  bullet: { marginTop: 8, fontSize: 14, color: "#0F172A", lineHeight: 20, fontWeight: "650" },

  actionCard: {
    marginTop: 10,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 12,
  },
  actionStep: { fontSize: 14, color: "#0F172A", fontWeight: "900", lineHeight: 20 },
  actionWhy: { marginTop: 6, fontSize: 13, color: "#334155", lineHeight: 18, fontWeight: "650" },
  refsRow: { marginTop: 8, flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "center" },
  refsLabel: { fontSize: 12, color: "#64748B", fontWeight: "900" },
  refsText: { fontSize: 12, color: "#64748B", fontWeight: "800" },
  refsLink: { fontSize: 12, color: "#1D4ED8", fontWeight: "900" },

  contactRow: {
    marginTop: 10,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 12,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  contactName: { fontSize: 14, fontWeight: "900", color: "#0F172A" },
  contactValue: { marginTop: 2, fontSize: 13, fontWeight: "800", color: "#1E3A8A" },
  contactNotes: { marginTop: 4, fontSize: 12.5, fontWeight: "650", color: "#475569", lineHeight: 17 },
  contactRefs: { marginTop: 6, fontSize: 11.5, fontWeight: "800", color: "#64748B" },
  contactGo: { fontSize: 12.5, fontWeight: "900", color: "#1D4ED8" },

  caveatBox: {
    marginTop: 14,
    borderRadius: 16,
    backgroundColor: "#FFF7ED",
    borderWidth: 1,
    borderColor: "#FDBA74",
    padding: 12,
  },
  caveatTitle: { fontSize: 14, fontWeight: "900", color: "#9A3412" },
  caveatText: { marginTop: 6, fontSize: 13, fontWeight: "650", color: "#7C2D12", lineHeight: 18 },

  refItem: { marginTop: 8, fontSize: 13, fontWeight: "700", color: "#1D4ED8", lineHeight: 18 },

  previewBox: {
    marginTop: 12,
    borderRadius: 16,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#E7E9F2",
    backgroundColor: "#F3F4F6",
  },
  previewImg: {
    width: "100%",
    height: 220,
    resizeMode: "cover",
  },

  sectionCard: {
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 12,
    marginTop: 12,
  },
  sectionHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  sectionTitle: { fontSize: 16.5, fontWeight: "950", color: "#0F172A" },
  sectionMeta: { fontSize: 12.5, fontWeight: "800", color: "#64748B" },

  itemCard: {
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#EEF0F8",
    padding: 12,
    marginTop: 10,
  },
  itemTopRow: { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between", gap: 10 },
  itemTitle: { flex: 1, fontSize: 14, fontWeight: "950", color: "#0F172A", lineHeight: 20 },
  itemOrg: { marginTop: 4, fontSize: 12.5, fontWeight: "850", color: "#475569" },
  itemDesc: { marginTop: 8, fontSize: 13, fontWeight: "650", color: "#334155", lineHeight: 18 },
  itemMetaRow: { marginTop: 8, flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "center" },
  itemMetaText: { fontSize: 11.5, fontWeight: "900", color: "#64748B" },

  refPillLink: { fontSize: 11.5, fontWeight: "900", color: "#1D4ED8" },
  refPillTextDim: { fontSize: 11.5, fontWeight: "900", color: "#64748B" },

  openPillLight: {
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: "#F1F5FF",
    borderWidth: 1,
    borderColor: "#E1E9FF",
  },
  openPillTextLight: { fontSize: 12, fontWeight: "900", color: "#1D4ED8" },

  planHeaderRow: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  backPill: {
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.85)",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    paddingVertical: 10,
    paddingHorizontal: 14,
  },
  backPillText: { fontSize: 14, fontWeight: "900", color: "#0F172A" },

  footerHint: {
    marginTop: 12,
    borderRadius: 14,
    backgroundColor: "#F7F8FC",
    borderWidth: 1,
    borderColor: "#E6E8F2",
    padding: 12,
  },
  footerHintText: { fontSize: 12.5, color: "#4F5770", lineHeight: 18, fontWeight: "600" },

  bottomSpace: { height: 18 },
});

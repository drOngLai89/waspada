import fs from "fs";

const cand = [
  "app/(tabs)/_layout.tsx",
  "app/tabs/_layout.tsx",
  "app/(main)/_layout.tsx",
  "app/_layout.tsx",
];
const file = cand.find(f => fs.existsSync(f));
if (!file) { console.error("❌ Could not find a Tabs _layout.tsx file."); process.exit(1); }

let s = fs.readFileSync(file, "utf8");
let before = s;

// Ensure <Tabs.Screen name="index" ... />
const rxScreen = /<Tabs\.Screen\s+name=['"]index['"][^>]*\/>/s;
if (!rxScreen.test(s)) {
  console.error("⚠️ Could not find <Tabs.Screen name=\"index\" ... /> in", file);
  process.exit(1);
}

// Case A: already has options={{ ... }}
s = s.replace(
  /<Tabs\.Screen\s+name=['"]index['"]([^>]*?)options=\{\{([^}]*)\}\}([^>]*?)\/>/s,
  (m, pre, opts, post) => {
    if (/headerTitle\s*:/.test(opts)) return m; // already there
    const injected = `headerTitle: "", ${opts}`;
    return `<Tabs.Screen name="index"${pre}options={{${injected}}}${post}/>`;
  }
);

// Case B: no options prop yet -> add one
s = s.replace(
  /<Tabs\.Screen\s+name=['"]index['"]([^>]*?)\/>/s,
  (m, rest) => `<Tabs.Screen name="index"${rest} options={{ headerTitle: "" }} />`
);

if (s !== before) {
  fs.writeFileSync(file, s);
  console.log(`✅ Patched ${file}: set headerTitle:"" for index tab (hides duplicate title).`);
} else {
  console.log("ℹ️ No changes were necessary.");
}

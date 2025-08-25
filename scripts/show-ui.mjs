import fs from "fs"; import path from "path";
const roots = [
  "app/(tabs)/_layout.tsx",
  "app/tabs/_layout.tsx",
  "app/_layout.tsx"
].filter(f => fs.existsSync(f));

function banner(fp){ console.log(`\n===== ${fp} =====\n`); }
function print(fp){ banner(fp); console.log(fs.readFileSync(fp,"utf8")); }

roots.forEach(print);

const keywords = /New Report|headerTitle|headerShown|Use current|Location|Add photo/i;

function walk(dir, out=[]) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const s = fs.statSync(p);
    if (s.isDirectory()) {
      if (name === "node_modules" || name.startsWith(".")) continue;
      walk(p, out);
    } else if (/\.(tsx|jsx|ts|js)$/.test(name)) {
      const txt = fs.readFileSync(p, "utf8");
      if (keywords.test(txt)) out.push(p);
    }
  }
  return out;
}

const hits = Array.from(new Set(walk("app")));
// Print likely New Report screen first if present
const prioritized = hits.sort((a,b) => {
  const score = fp => (/(^|\/)(index|new[-_]report)\.(tsx|jsx|ts|js)$/i.test(fp) ? 1 : 0);
  return score(b) - score(a) || a.localeCompare(b);
});

prioritized.forEach(print);

import fs from "fs";
import path from "path";

function patchFile(fp) {
  let s = fs.readFileSync(fp, "utf8");
  let changed = false;

  // Tabs: add/replace screenOptions with headerShown:false
  s = s.replace(
    /<Tabs(\s[^>]*)?screenOptions=\{\{([\s\S]*?)\}\}(\s*?)>/,
    (m, pre="", opts="", post="") => {
      if (/headerShown\s*:/.test(opts)) {
        opts = opts.replace(/headerShown\s*:\s*(true|false)/, "headerShown: false");
      } else {
        opts = `headerShown: false, ${opts}`.replace(/,\s*$/, "");
      }
      changed = true;
      return `<Tabs${pre || ""}screenOptions={{${opts}}}${post}>`;
    }
  );
  if (!/screenOptions=\{\{/.test(s) && /<Tabs(\s[^>]*)?>/.test(s)) {
    s = s.replace(/<Tabs(\s[^>]*)?>/, (m, rest="") =>
      `<Tabs${rest || ""} screenOptions={{ headerShown: false }}>`
    );
    changed = true;
  }

  // Stack (in case you use a Stack in tabs)
  s = s.replace(
    /<Stack(\s[^>]*)?screenOptions=\{\{([\s\S]*?)\}\}(\s*?)>/,
    (m, pre="", opts="", post="") => {
      if (/headerShown\s*:/.test(opts)) {
        opts = opts.replace(/headerShown\s*:\s*(true|false)/, "headerShown: false");
      } else {
        opts = `headerShown: false, ${opts}`.replace(/,\s*$/, "");
      }
      changed = true;
      return `<Stack${pre || ""}screenOptions={{${opts}}}${post}>`;
    }
  );
  if (!/screenOptions=\{\{/.test(s) && /<Stack(\s[^>]*)?>/.test(s)) {
    s = s.replace(/<Stack(\s[^>]*)?>/, (m, rest="") =>
      `<Stack${rest || ""} screenOptions={{ headerShown: false }}>`
    );
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(fp, s);
    console.log("✅ Patched:", fp);
  }
}

function walk(dir) {
  for (const f of fs.readdirSync(dir)) {
    const fp = path.join(dir, f);
    const stat = fs.statSync(fp);
    if (stat.isDirectory()) walk(fp);
    else if (/_layout\.tsx?$/.test(f)) patchFile(fp);
  }
}

walk(path.join(process.cwd(), "app"));

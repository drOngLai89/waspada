set -euo pipefail

echo "==> Checking project..."
[ -d .git ] || git init

echo "==> Verifying icon..."
if [ ! -f assets/icon.png ]; then
  echo "❌ assets/icon.png not found. Put your 1024x1024 icon at assets/icon.png and run again."
  exit 1
fi

echo "==> Writing config patcher..."
cat > scripts/apply-brand-config.mjs <<'JS'
import fs from "fs";
const files = ["app.json","app.config.ts","app.config.js"];
const file = files.find(f=>fs.existsSync(f));
if(!file){ console.error("❌ No app.json or app.config.* found."); process.exit(1); }
let text = fs.readFileSync(file,"utf8");

const iconPath = "./assets/icon.png";
const whenInUse = "Berani uses your location to tag reports with a nearby area for faster help and accurate routing.";
const alwaysUse = "Berani may access your location while the app is active to attach accurate incident locations.";
const bgColor = "#0B2E4A";

if (file.endsWith(".json")) {
  const cfg = JSON.parse(text);
  cfg.expo = cfg.expo || {};
  cfg.expo.icon = iconPath;
  cfg.expo.ios = cfg.expo.ios || {};
  cfg.expo.ios.infoPlist = cfg.expo.ios.infoPlist || {};
  cfg.expo.ios.infoPlist.NSLocationWhenInUseUsageDescription = whenInUse;
  cfg.expo.ios.infoPlist.NSLocationAlwaysAndWhenInUseUsageDescription = alwaysUse;
  cfg.expo.android = cfg.expo.android || {};
  cfg.expo.android.adaptiveIcon = cfg.expo.android.adaptiveIcon || {};
  cfg.expo.android.adaptiveIcon.foregroundImage = iconPath;
  cfg.expo.android.adaptiveIcon.backgroundColor = bgColor;
  fs.writeFileSync(file, JSON.stringify(cfg,null,2));
  console.log(`Patched ${file} (icon + iOS Info.plist + Android adaptive icon)`);
  process.exit(0);
}

// TS/JS config heuristic
let s = text, changed=false;
function ins(re, rep){ const t=s; s=s.replace(re, rep); if(s!==t) changed=true; }

ins(/icon\s*:\s*["'][^"']+["']/, `icon: "${iconPath}"`);
ins(/expo\s*:\s*{/, m => `${m}\n    icon: "${iconPath}",`);

if(/infoPlist\s*:\s*{/.test(s)){
  ins(/infoPlist\s*:\s*{/, m => `${m}
      NSLocationWhenInUseUsageDescription: "${whenInUse}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${alwaysUse}",`);
}else if(/ios\s*:\s*{/.test(s)){
  ins(/ios\s*:\s*{/, m => `${m}
    infoPlist: {
      NSLocationWhenInUseUsageDescription: "${whenInUse}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${alwaysUse}"
    },`);
}else{
  ins(/expo\s*:\s*{/, m => `${m}
  ios: {
    infoPlist: {
      NSLocationWhenInUseUsageDescription: "${whenInUse}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${alwaysUse}"
    }
  },`);
}

if(/android\s*:\s*{/.test(s)){
  if(/adaptiveIcon\s*:\s*{/.test(s)){
    ins(/adaptiveIcon\s*:\s*{[^}]*}/s, `adaptiveIcon: { foregroundImage: "${iconPath}", backgroundColor: "${bgColor}" }`);
  } else {
    ins(/android\s*:\s*{/, m => `${m}
    adaptiveIcon: { foregroundImage: "${iconPath}", backgroundColor: "${bgColor}" },`);
  }
}else{
  ins(/expo\s*:\s*{/, m => `${m}
  android: { adaptiveIcon: { foregroundImage: "${iconPath}", backgroundColor: "${bgColor}" } },`);
}

if(changed){ fs.writeFileSync(file,s); console.log(`Patched ${file} (icon + iOS Info.plist + Android adaptive icon)`); }
else { console.log("No config changes needed."); }
JS

echo "==> Applying config..."
node scripts/apply-brand-config.mjs

echo "==> Ensuring expo-location is installed..."
npx expo install expo-location

echo "==> Bumping versions..."
cat > scripts/bump-versions.mjs <<'JS'
import fs from "fs";
const files=["app.config.ts","app.config.js","app.json"]; const f=files.find(p=>fs.existsSync(p));
if(!f){ console.error("❌ No app config found."); process.exit(1); }
let t=fs.readFileSync(f,"utf8"); const isJson=f.endsWith(".json");
const bumpPatch=v=>{const a=(v||"1.0.0").split(".").map(n=>parseInt(n,10)); while(a.length<3)a.push(0); a[2]=(isFinite(a[2])?a[2]:0)+1; return `${a[0]}.${a[1]}.${a[2]}`;};
const bumpNum=(n,f=1)=>{const x=parseInt(String(n||"").replace(/[^0-9]/g,""),10); return isFinite(x)?x+1:f;};
let ch=[];
if(isJson){
  t=t.replace(/"version"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version: ${v} -> ${nv}`); return `"version":"${nv}"`;});
  t=t.replace(/"buildNumber"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`ios.buildNumber: ${v} -> ${nv}`); return `"buildNumber":"${nv}"`;});
  t=t.replace(/"versionCode"\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`android.versionCode: ${v} -> ${nv}`); return `"versionCode":${nv}`;});
}else{
  t=t.replace(/version\s*:\s*["'](\d+\.\d+\.\d+)["']/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version: ${v} -> ${nv}`); return `version: "${nv}"`;});
  t=t.replace(/buildNumber\s*:\s*["']([^"']+)["']/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`ios.buildNumber: ${v} -> ${nv}`); return `buildNumber: "${nv}"`;});
  t=t.replace(/versionCode\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`android.versionCode: ${v} -> ${nv}`); return `versionCode: ${nv}`;});
}
fs.writeFileSync(f,t,"utf8"); console.log("Updated:",f); for(const c of ch) console.log(" •",c);
JS

node scripts/bump-versions.mjs

echo "==> Committing..."
git add -A
git commit -m "chore(ios): icon + Info.plist location strings; version bump" || true

echo "==> Expo/EAS login check..."
npx expo whoami || npx expo login
npx eas whoami   || npx eas login

echo "==> Building iOS with EAS..."
npx eas build --platform ios --profile production

echo "==> Submitting to App Store Connect..."
npx eas submit --platform ios

echo "✅ Done. Check App Store Connect > TestFlight for processing."

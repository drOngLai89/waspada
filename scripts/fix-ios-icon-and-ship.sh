set -euo pipefail

# 0) Go to project root
if [ -d "$HOME/berani" ]; then cd "$HOME/berani"; elif [ -d "$HOME/Bersuara" ]; then cd "$HOME/Bersuara"; fi
mkdir -p assets scripts

# 1) Put the icon in place (must be 1024x1024, no alpha)
if [ -f "$HOME/Downloads/berani-appstore-icon-1024-noalpha.png" ]; then
  cp -f "$HOME/Downloads/berani-appstore-icon-1024-noalpha.png" assets/icon.png
fi
if [ ! -f assets/icon.png ]; then
  echo "❌ assets/icon.png missing. Save the PNG to ~/Downloads as 'berani-appstore-icon-1024-noalpha.png' and re-run."
  exit 1
fi
echo "Icon info:"
sips -g pixelWidth -g pixelHeight -g hasAlpha assets/icon.png

# 2) Patch config: set icon + iOS location strings
cat > scripts/fix-icon.mjs <<'JS'
import fs from "fs";
const files=["app.json","app.config.ts","app.config.js"];
const file=files.find(f=>fs.existsSync(f));
if(!file){console.error("No app.json or app.config.* found");process.exit(1);}
let t=fs.readFileSync(file,"utf8");
const icon="./assets/icon.png";
const when="Berani uses your location to tag reports with a nearby area for faster help and accurate routing.";
const always="Berani may access your location while the app is active to attach accurate incident locations.";
if(file.endsWith(".json")){
  const cfg=JSON.parse(t);
  cfg.expo=cfg.expo||{};
  cfg.expo.icon=icon;
  cfg.expo.ios=cfg.expo.ios||{};
  cfg.expo.ios.infoPlist=cfg.expo.ios.infoPlist||{};
  cfg.expo.ios.infoPlist.NSLocationWhenInUseUsageDescription=when;
  cfg.expo.ios.infoPlist.NSLocationAlwaysAndWhenInUseUsageDescription=always;
  fs.writeFileSync(file,JSON.stringify(cfg,null,2));
  console.log("Patched",file);
  process.exit(0);
}
function ins(re,after){const b=t; t=t.replace(re,after); return t!==b;}
let changed=false;
changed = ins(/icon\s*:\s*["'][^"']+["']/, `icon: "${icon}"`) || changed;
changed = ins(/expo\s*:\s*{/, m=>`${m}\n    icon: "${icon}",`) || changed;
if(/infoPlist\s*:\s*{/.test(t)){
  changed = ins(/infoPlist\s*:\s*{/, m=>`${m}
      NSLocationWhenInUseUsageDescription: "${when}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${always}",`) || changed;
}else if(/ios\s*:\s*{/.test(t)){
  changed = ins(/ios\s*:\s*{/, m=>`${m}
    infoPlist: {
      NSLocationWhenInUseUsageDescription: "${when}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${always}"
    },`) || changed;
}else{
  changed = ins(/expo\s*:\s*{/, m=>`${m}
  ios: { infoPlist: {
      NSLocationWhenInUseUsageDescription: "${when}",
      NSLocationAlwaysAndWhenInUseUsageDescription: "${always}"
  } },`) || changed;
}
fs.writeFileSync(file,t); console.log("Patched",file);
JS
node scripts/fix-icon.mjs

# 3) Bump versions so Apple accepts the new build
cat > scripts/bump.mjs <<'JS'
import fs from "fs";
const files=["app.config.ts","app.config.js","app.json"]; const f=files.find(p=>fs.existsSync(p));
if(!f){console.error("No app config found");process.exit(1);}
let t=fs.readFileSync(f,"utf8"); const isJson=f.endsWith(".json");
const bumpPatch=v=>{const a=(v||"1.0.0").split(".").map(n=>parseInt(n,10)); while(a.length<3)a.push(0); a[2]=(isFinite(a[2])?a[2]:0)+1; return `${a[0]}.${a[1]}.${a[2]}`;}
const bumpNum=(n,d=1)=>{const x=parseInt(String(n||"").replace(/[^0-9]/g,""),10); return isFinite(x)?x+1:d;}
let ch=[];
if(isJson){
  t=t.replace(/"version"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version ${v}→${nv}`); return `"version":"${nv}"`});
  t=t.replace(/"buildNumber"\s*:\s*"([^"]+)"/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`iOS buildNumber ${v}→${nv}`); return `"buildNumber":"${nv}"`});
  t=t.replace(/"versionCode"\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`Android versionCode ${v}→${nv}`); return `"versionCode":${nv}`});
}else{
  t=t.replace(/version\s*:\s*["'](\d+\.\d+\.\d+)["']/,(m,v)=>{const nv=bumpPatch(v); ch.push(`version ${v}→${nv}`); return `version: "${nv}"`});
  t=t.replace(/buildNumber\s*:\s*["']([^"']+)["']/,(m,v)=>{const nv=String(bumpNum(v,1)); ch.push(`iOS buildNumber ${v}→${nv}`); return `buildNumber: "${nv}"`});
  t=t.replace(/versionCode\s*:\s*([0-9]+)/,(m,v)=>{const nv=bumpNum(v,1); ch.push(`Android versionCode ${v}→${nv}`); return `versionCode: ${nv}`});
}
fs.writeFileSync(f,t,"utf8"); console.log("Bumped",f, ch.join(" | "));
JS
node scripts/bump.mjs

git add -A
git commit -m "fix: iOS icon (1024 no-alpha) + Info.plist strings; bump versions" || true

# 4) Build & submit fresh iOS binary (clear cache => new asset catalog)
npx expo whoami || npx expo login
npx eas whoami   || npx eas login

npx eas build --platform ios --profile production --clear-cache
npx eas submit --platform ios

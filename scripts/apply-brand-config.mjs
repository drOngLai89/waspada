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

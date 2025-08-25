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

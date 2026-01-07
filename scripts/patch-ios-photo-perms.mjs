import fs from "fs";
const file = ["app.config.ts","app.config.js","app.json"].find(f=>fs.existsSync(f));
if (!file) { console.error("No app config found"); process.exit(1); }
let t = fs.readFileSync(file, "utf8");

// Ensure an ios.infoPlist block exists and contains required keys
function ensureKey(txt, key, val){
  if (new RegExp(`${key}\\s*:`).test(txt)) return txt;
  return txt.replace(/infoPlist\s*:\s*{/, m => `${m}
      ${key}: "${val}",`);
}
if (/infoPlist\s*:\s*{/.test(t)) {
  t = ensureKey(t, "NSPhotoLibraryUsageDescription", "Berani needs photo access to let you attach images to reports.");
  t = ensureKey(t, "NSPhotoLibraryAddUsageDescription", "Berani may save processed images you attach to your reports.");
  t = ensureKey(t, "NSCameraUsageDescription", "Berani uses the camera so you can capture photos for your report.");
} else if (/ios\s*:\s*{/.test(t)) {
  t = t.replace(/ios\s*:\s*{/, m => `${m}
    infoPlist: {
      NSPhotoLibraryUsageDescription: "Berani needs photo access to let you attach images to reports.",
      NSPhotoLibraryAddUsageDescription: "Berani may save processed images you attach to your reports.",
      NSCameraUsageDescription: "Berani uses the camera so you can capture photos for your report."
    },`);
} else {
  t = t.replace(/export default config;|module\.exports\s*=\s*config;?/, s => 
`  ios: {
    infoPlist: {
      NSPhotoLibraryUsageDescription: "Berani needs photo access to let you attach images to reports.",
      NSPhotoLibraryAddUsageDescription: "Berani may save processed images you attach to your reports.",
      NSCameraUsageDescription: "Berani uses the camera so you can capture photos for your report."
    }
  },
${s}`);
}

fs.writeFileSync(file, t);
console.log("✅ iOS photo/camera usage descriptions ensured in", file);

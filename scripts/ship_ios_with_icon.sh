set -euo pipefail

# 0) Sanity: icon exists and is 1024x1024 with no alpha
sips -g pixelWidth -g pixelHeight -g hasAlpha assets/icon.png

# 1) Overwrite app.config.ts with explicit icon + perms (keeps your IDs)
cat > app.config.ts <<'TS'
import { ExpoConfig } from "expo/config";
const config: ExpoConfig = {
  name: "Berani",
  slug: "berani",
  version: "1.0.1",
  icon: "./assets/icon.png",
  runtimeVersion: { policy: "sdkVersion" },
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  ios: {
    bundleIdentifier: "com.drsherman.berani",
    buildNumber: "12",
    supportsTablet: true,
    infoPlist: {
      NSLocationWhenInUseUsageDescription:
        "Berani uses your location to tag reports with a nearby area for faster help and accurate routing.",
      NSLocationAlwaysAndWhenInUseUsageDescription:
        "Berani may access your location while the app is active to attach accurate incident locations."
    }
  },
  android: {
    package: "com.drsherman.berani",
    versionCode: 12,
    adaptiveIcon: {
      foregroundImage: "./assets/icon.png",
      backgroundColor: "#0B2E4A"
    }
  },
  plugins: ["expo-router"],
  experiments: { typedRoutes: true }
};
export default config;
TS

# 2) Confirm Expo prebuild sees the icon
npx expo config --type prebuild --json > .prebuild.json
node - <<'NODE'
const fs = require('fs');
const j = JSON.parse(fs.readFileSync('.prebuild.json','utf8'));
const icon = j.icon || (j.ios && j.ios.icon);
if (!icon) { console.error('❌ Prebuild config is missing icon'); process.exit(2); }
console.log('✅ Prebuild icon =', icon);
NODE

# 3) Local prebuild just to validate the generated asset catalog contains 1024
npx expo prebuild --platform ios --clean --skip-install
if ! test -f ios/*/Images.xcassets/AppIcon.appiconset/Contents.json; then
  echo "❌ AppIcon.appiconset missing"; exit 2
fi
grep -n '1024x1024' ios/*/Images.xcassets/AppIcon.appiconset/Contents.json || {
  echo "❌ 1024x1024 marketing icon not found in asset catalog"; exit 2;
}
echo "✅ 1024x1024 icon present in asset catalog."
rm -rf ios  # keep repo managed

# 4) Build & submit fresh TestFlight build (clean cache)
npx expo whoami || npx expo login
npx eas whoami   || npx eas login
npx eas build --platform ios --profile production --clear-cache
npx eas submit --platform ios --latest

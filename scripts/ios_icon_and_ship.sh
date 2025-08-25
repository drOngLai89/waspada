set -euo pipefail

# 0) Verify icon
if [ ! -f assets/icon.png ]; then
  echo "❌ assets/icon.png missing. Put your 1024x1024 NO-ALPHA icon there and re-run."
  exit 1
fi
sips -g pixelWidth -g pixelHeight -g hasAlpha assets/icon.png

# 1) Overwrite app.config.ts with explicit icon + permissions
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
    buildNumber: "13",
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
    versionCode: 13,
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

# 2) Confirm prebuild sees the icon
npx expo config --type prebuild --json > .prebuild.json
node - <<'NODE'
const fs = require('fs');
const j = JSON.parse(fs.readFileSync('.prebuild.json','utf8'));
const icon = j.icon || (j.ios && j.ios.icon);
if (!icon) { console.error('❌ Prebuild config missing icon'); process.exit(2); }
console.log('✅ Prebuild icon =', icon);
NODE

# 3) Validate iOS asset catalog contains 1024x1024 icon
npx expo prebuild --platform ios --clean --skip-install
test -f ios/*/Images.xcassets/AppIcon.appiconset/Contents.json
grep -n '1024x1024' ios/*/Images.xcassets/AppIcon.appiconset/Contents.json >/dev/null && echo "✅ 1024x1024 icon present"
rm -rf ios

# 4) Build & submit to TestFlight
npx expo whoami || npx expo login
npx eas whoami   || npx eas login
npx eas build --platform ios --profile production --clear-cache
npx eas submit --platform ios --latest

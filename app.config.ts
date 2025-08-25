import { ExpoConfig } from "expo/config";

const config: ExpoConfig = {
  name: "Berani",
  slug: "berani",
  version: "1.0.3",
  icon: "./assets/icon.png",
  runtimeVersion: { policy: "sdkVersion" },
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  ios: {
    bundleIdentifier: "com.drsherman.berani",
    buildNumber: "15",
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
    versionCode: 15,
    adaptiveIcon: {
      foregroundImage: "./assets/icon.png",
      backgroundColor: "#0B2E4A"
    }
  },
  plugins: ["expo-router"],
  experiments: { typedRoutes: true }
};

export default config;

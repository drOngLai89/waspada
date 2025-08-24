import { ConfigContext, ExpoConfig } from "@expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  name: "Berani",
  slug: "berani",
  scheme: "berani",
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "automatic",
  splash: {
    image: "./assets/splash.png",
    resizeMode: "contain",
    backgroundColor: "#ffffff"
  },
  updates: { fallbackToCacheTimeout: 0 },
  assetBundlePatterns: ["**/*"],
  ios: {
    bundleIdentifier: "com.drsherman.berani",
    supportsTablet: false,
    infoPlist: {
      NSCameraUsageDescription: "Berani needs camera access to capture photos as evidence for your reports.",
      NSPhotoLibraryUsageDescription: "Berani needs photo library access to attach evidence photos to your reports.",
      NSPhotoLibraryAddUsageDescription: "Berani may save exports to your photo library if you choose to share."
    }
  },
  android: {
    package: "com.drsherman.berani",
    permissions: []
  },
  extra: {
    // If you read envs in code, reference them with process.env.MY_KEY via EAS Secrets
    API_BASE_URL: process.env.API_BASE_URL
  },
  plugins: []
});

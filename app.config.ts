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
    // Your backend env if you use it:
    API_BASE_URL: process.env.API_BASE_URL,
    // <<< This links the local project to your EAS project >>>
    eas: { projectId: "ea4d8f65-62de-4361-ab6d-37952c73e0f1" }
  },
  plugins: []
});

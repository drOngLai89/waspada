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
  assetBundlePatterns: ["**/*"],
  ios: {
    bundleIdentifier: "com.drsherman.berani",
    supportsTablet: false,
    icon: "./assets/icon.png",
    infoPlist: {
      NSCameraUsageDescription: "Berani needs camera access to capture photos as evidence for your reports.",
      NSPhotoLibraryUsageDescription: "Berani needs photo library access to attach evidence photos to your reports.",
      NSPhotoLibraryAddUsageDescription: "Berani may save exports to your photo library if you choose to share.",
      ITSAppUsesNonExemptEncryption: false
    }
  },
  android: {
    package: "com.drsherman.berani",
    adaptiveIcon: { foregroundImage: "./assets/icon.png", backgroundColor: "#0b2943" },
    permissions: []
  },
  extra: {
    API_BASE_URL: process.env.API_BASE_URL,
    eas: { projectId: "ea4d8f65-62de-4361-ab6d-37952c73e0f1" }
  }
});

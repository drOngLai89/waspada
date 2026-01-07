import { ExpoConfig } from "expo/config";

const config: ExpoConfig = {
  name: "Waspada",
  slug: "waspada",
  version: "1.0.0",
  icon: "./assets/icon.png",
  runtimeVersion: { policy: "sdkVersion" },
  orientation: "portrait",
  userInterfaceStyle: "automatic",

  ios: {
    bundleIdentifier: "com.drshermankoh.waspada",
    buildNumber: "3",
    supportsTablet: true,
    infoPlist: {
      NSCameraUsageDescription: "Waspada uses the camera so you can capture screenshots for analysis.",
      NSPhotoLibraryAddUsageDescription: "Waspada may save processed images you attach to your reports.",
      NSPhotoLibraryUsageDescription: "Waspada needs photo access to let you attach screenshots to reports."
    }
  },

  android: {
    package: "com.drsherman.waspada",
    versionCode: 1,
    adaptiveIcon: {
      foregroundImage: "./assets/icon.png",
      backgroundColor: "#0B2E4A"
    }
  },

  extra: {
    eas: { projectId: "1cbd19f5-cc40-43bf-bdf2-4ba451ff66a6" },
    env: "prod",
    // CHANGE THIS to your Waspada backend if different:
    apiBaseUrl: "https://waspada.onrender.com",
    API_BASE_URL: "https://waspada.onrender.com",},

  plugins: ["expo-router"],
  experiments: { typedRoutes: true }
};

export default config;

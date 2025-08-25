import { ExpoConfig } from 'expo-config';

export default (): ExpoConfig => ({
  name: "Berani",
  slug: "berani",
  scheme: "berani",
  ios: {
    bundleIdentifier: "com.drsherman.berani",
    supportsTablet: false,
    infoPlist: {
      NSCameraUsageDescription: "Berani needs camera access to capture photos as evidence for your reports.",
      NSPhotoLibraryUsageDescription: "Berani needs photo library access to attach evidence photos to your reports.",
      NSPhotoLibraryAddUsageDescription: "Berani may save exports to your photo library if you choose to share.",
      ITSAppUsesNonExemptEncryption: false
    }
  },
  android: {
    package: "com.drsherman.berani",
    permissions: []
  },
  extra: {
    // HARD-CODED so Expo sees it (change if your URL differs)
    API_BASE_URL: "https://berani-backend.onrender.com",
    REPORT_PATH: "/report",
    CHAT_PATH: "/chat",
    eas: { projectId: "ea4d8f65-62de-4361-ab6d-37952c73e0f1" }
  },
  plugins: []
});

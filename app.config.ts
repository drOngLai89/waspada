import type { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: config?.name ?? "Waspada",
  slug: config?.slug ?? "waspada",
  scheme: "waspada",
});

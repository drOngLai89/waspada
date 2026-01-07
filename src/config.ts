import Constants from "expo-constants";
import * as Updates from "expo-updates";

type Extra = { env?: string; apiBaseUrl?: string };

const extra: Extra =
  (Constants.expoConfig?.extra as Extra) ??
  ((Updates.manifest as any)?.extra as Extra) ??
  {};

export const APP_ENV = (extra.env ?? "prod") as "prod" | "staging" | "dev";
export const API_BASE_URL = extra.apiBaseUrl ?? "";

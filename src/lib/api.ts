const BASE_URL =
  process.env.EXPO_PUBLIC_WASPADA_API_BASE_URL?.replace(/\/+$/, "") ||
  "http://localhost:8000";

type Json = any;

async function fetchJson(path: string, init?: RequestInit): Promise<Json> {
  const url = `${BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;

  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  const text = await res.text();

  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    // if backend returns non-json, we still show something readable
  }

  if (!res.ok) {
    // FastAPI often returns {"detail": ...}
    const detail = data?.detail ?? data?.error ?? data?.message;
    const msg =
      typeof detail === "string"
        ? detail
        : detail
        ? JSON.stringify(detail)
        : text || `HTTP ${res.status}`;
    throw new Error(msg);
  }

  return data;
}

/**
 * Verify screenshot (Malaysia-only).
 * IMPORTANT: backend expects "image_data_url" (NOT "image").
 */
export async function analyzeScreenshot(
  imageDataUrl: string,
  lang: "EN" | "MS" | "ZH" | "TA" = "EN"
) {
  const body = {
    image_data_url: imageDataUrl,
    lang,
  };

  const data = await fetchJson("/analyze", {
    method: "POST",
    body: JSON.stringify(body),
  });

  // Support both styles: {result: ...} or direct object
  return data?.result ?? data;
}

export async function getResources() {
  const data = await fetchJson("/resources", { method: "GET" });
  return data?.result ?? data;
}

export async function getActionPlan(scenario: string) {
  const data = await fetchJson(`/plan/${encodeURIComponent(scenario)}`, {
    method: "GET",
  });
  return data?.result ?? data;
}

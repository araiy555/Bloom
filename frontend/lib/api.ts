export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const TOKEN_KEY = "bloom_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

type FetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  raw?: boolean;
};

export async function api<T = any>(path: string, opts: FetchOptions = {}): Promise<T> {
  const headers = new Headers(opts.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let body: BodyInit | undefined;
  if (opts.body !== undefined) {
    if (opts.raw) {
      body = opts.body as BodyInit;
    } else {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(opts.body);
    }
  }

  const res = await fetch(`${API_URL}${path}`, { ...opts, headers, body });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {}
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Domain types
export type User = { id: number; email: string; name: string };
export type Project = {
  id: number;
  name: string;
  status: "draft" | "ready" | string;
  goal: string;
  system_prompt: string;
  created_at: string;
  updated_at: string;
  file_count: number;
};
export type DatasetFile = {
  id: number;
  project_id: number;
  filename: string;
  kind: string;
  size_bytes: number;
  created_at: string;
  extracted_preview: string;
};
export type ChatMessage = {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
};
export type AssistReport = {
  classification: string;
  quality_score: number;
  feasibility: "low" | "medium" | "high" | string;
  suggestions: string[];
  summary: string;
};

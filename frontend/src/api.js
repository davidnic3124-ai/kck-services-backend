import { API_BASE } from "./supabaseClient";

// One fetch helper for every FastAPI call: adds the Bearer token and turns errors into readable messages
export async function api(path, { token, method = "GET", body, formData } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined)
  });
  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((d) => `${d.loc.slice(-1)}: ${d.msg}`).join("; ")
      : data.detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return data;
}

export const rm = (n) => `RM ${Number(n || 0).toFixed(2)}`;
export const stars = (n) => "★".repeat(Math.round(n || 0)) + "☆".repeat(5 - Math.round(n || 0));
export const label = (s) => String(s || "").replace(/_/g, " ");

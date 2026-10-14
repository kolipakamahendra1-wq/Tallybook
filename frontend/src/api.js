const BASE = import.meta.env.VITE_API_URL || "";
const TOKEN_KEY = "tallybook.token";

export const getToken = () => {
  try { return localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; }
};
export const setToken = (t) => {
  try { localStorage.setItem(TOKEN_KEY, t); } catch { /* storage blocked: token lasts for this page only */ }
};

async function call(path, opts = {}) {
  const token = getToken();
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
  } catch {
    throw new Error("Cannot reach the API. Start the backend on port 8030.");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  return body;
}

export const api = {
  health: () => call("/api/health"),
  research: (payload) => call("/api/research", { method: "POST", body: JSON.stringify(payload) }),
  reports: () => call("/api/reports"),
  report: (id) => call(`/api/reports/${id}`),
};

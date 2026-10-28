// Shared inline styles (same approach as Trax Work)
export const colors = { navy: "#0f172a", brand: "#dc2626", accent: "#f59e0b", muted: "#64748b", border: "#e2e8f0", bg: "#f8fafc" };

export const card = { background: "#fff", border: `1px solid ${colors.border}`, borderRadius: 10, padding: 18, fontFamily: "sans-serif" };
export const page = { maxWidth: 1080, margin: "0 auto", fontFamily: "sans-serif" };
export const input = { padding: 9, borderRadius: 6, border: "1px solid #cbd5e1", fontSize: 14, boxSizing: "border-box", width: "100%" };
export const th = { textAlign: "left", padding: "8px 6px", fontSize: 12, color: "#475569", borderBottom: `1px solid ${colors.border}` };
export const td = { padding: "8px 6px", fontSize: 13, borderBottom: "1px solid #f1f5f9", verticalAlign: "top" };
export const grid = (min = 240) => ({ display: "grid", gridTemplateColumns: `repeat(auto-fill, minmax(${min}px, 1fr))`, gap: 16 });
export const btn = (bg = colors.brand, color = "#fff") => ({
  padding: "8px 14px", background: bg, color, border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13, fontWeight: "bold"
});
export const badge = (bg, color = "#fff") => ({ display: "inline-block", padding: "2px 8px", borderRadius: 999, fontSize: 11, fontWeight: "bold", background: bg, color });
export const statusColors = { pending: "#f59e0b", confirmed: "#0284c7", completed: "#16a34a", cancelled: "#94a3b8" };

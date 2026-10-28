import React, { useState, useEffect } from "react";
import { api, stars } from "../api";
import { badge, btn, card, colors, grid, input, page } from "../styles";

const EMPTY = { rating: 5, title: "", comment: "", car_id: "" };

export default function FeedbackWall({ token, userId, onNeedLogin }) {
  const [reviews, setReviews] = useState([]);
  const [mine, setMine] = useState([]);
  const [cars, setCars] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");

  const loadAll = () => {
    api("/feedback").then(setReviews).catch((err) => setMessage(err.message));
    api("/cars").then(setCars).catch(() => setCars([]));
    if (token) api("/feedback/me", { token }).then(setMine).catch(() => setMine([]));
  };

  useEffect(() => {
    loadAll();
  }, [token]);

  const average = reviews.length ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length : 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return onNeedLogin();
    const body = { rating: Number(form.rating), title: form.title || null, comment: form.comment };
    try {
      if (editingId) {
        await api(`/feedback/${editingId}`, { token, method: "PUT", body });
        setMessage("Review updated. It will be visible again once KCK approves it.");
      } else {
        await api("/feedback", { token, method: "POST", body: { ...body, car_id: form.car_id || null } });
        setMessage("Thank you! Your review has been sent and will appear after KCK approves it.");
      }
      setForm(EMPTY);
      setEditingId(null);
      loadAll();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const startEdit = (r) => {
    setEditingId(r.id);
    setForm({ rating: r.rating, title: r.title || "", comment: r.comment, car_id: r.car_id || "" });
  };

  const remove = async (r) => {
    if (!confirm("Delete this review?")) return;
    try {
      await api(`/feedback/${r.id}`, { token, method: "DELETE" });
      loadAll();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={page}>
      <div style={{ ...card, display: "flex", flexWrap: "wrap", gap: 24, alignItems: "center", marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 40, fontWeight: "bold", color: colors.navy }}>{average.toFixed(1)}</div>
          <div style={{ color: colors.accent, fontSize: 20 }}>{stars(average)}</div>
          <div style={{ fontSize: 12, color: colors.muted }}>{reviews.length} published review(s)</div>
        </div>
        <div style={{ flex: 1, minWidth: 240 }}>
          <h3 style={{ margin: "0 0 6px 0" }}>What our customers say</h3>
          <div style={{ fontSize: 14, color: "#334155" }}>Rented with KCK SERVICES? Share your experience below to help other customers.</div>
        </div>
      </div>

      <div style={grid(300)}>
        {reviews.map((r) => (
          <div key={r.id} style={card}>
            <div style={{ color: colors.accent, fontSize: 18 }}>{stars(r.rating)}</div>
            {r.title && <h4 style={{ margin: "6px 0" }}>{r.title}</h4>}
            <div style={{ fontSize: 14, color: "#334155" }}>{r.comment}</div>
            <div style={{ fontSize: 12, color: colors.muted, marginTop: 8 }}>
              — {r.customer_name || "Customer"}{r.car_label && ` · rented ${r.car_label}`} · {r.created_at.slice(0, 10)}
            </div>
            {r.admin_reply && (
              <div style={{ marginTop: 10, padding: 10, background: colors.bg, borderLeft: `3px solid ${colors.brand}`, fontSize: 13 }}>
                <b>KCK SERVICES replied:</b> {r.admin_reply}
              </div>
            )}
          </div>
        ))}
      </div>
      {reviews.length === 0 && <div style={{ color: colors.muted }}>No published reviews yet.</div>}

      <form onSubmit={handleSubmit} style={{ ...card, marginTop: 24, display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0 }}>{editingId ? "Edit your review" : "Write a review"}</h3>
        <div style={grid(200)}>
          <select value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} style={input}>
            {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{stars(n)} ({n})</option>)}
          </select>
          {!editingId && (
            <select value={form.car_id} onChange={(e) => setForm({ ...form, car_id: e.target.value })} style={input}>
              <option value="">General feedback (no specific car)</option>
              {cars.map((c) => <option key={c.id} value={c.id}>{c.brand} {c.model} ({c.plate_number})</option>)}
            </select>
          )}
          <input placeholder="Title (optional)" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} style={input} />
        </div>
        <textarea placeholder="Tell us about your experience..." value={form.comment} onChange={(e) => setForm({ ...form, comment: e.target.value })} style={{ ...input, minHeight: 80 }} required minLength={3} />
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit" style={btn()}>{token ? (editingId ? "Save Changes" : "Submit Review") : "Log in to Review"}</button>
          {editingId && <button type="button" onClick={() => { setEditingId(null); setForm(EMPTY); }} style={btn("#e2e8f0", colors.navy)}>Cancel</button>}
        </div>
        {message && <div style={{ fontSize: 13, color: colors.muted }}>{message}</div>}
      </form>

      {token && mine.length > 0 && (
        <div style={{ ...card, marginTop: 20 }}>
          <h3 style={{ marginTop: 0 }}>My reviews</h3>
          {mine.map((r) => (
            <div key={r.id} style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: `1px solid ${colors.border}` }}>
              <div style={{ fontSize: 14 }}>
                <span style={{ color: colors.accent }}>{stars(r.rating)}</span> {r.title || r.comment.slice(0, 60)}{" "}
                <span style={badge(r.is_published ? "#16a34a" : colors.accent)}>{r.is_published ? "Published" : "Awaiting approval"}</span>
              </div>
              {r.customer_id === userId && (
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => startEdit(r)} style={btn("#e0f2fe", "#0369a1")}>Edit</button>
                  <button onClick={() => remove(r)} style={btn("#fee2e2", colors.brand)}>Delete</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

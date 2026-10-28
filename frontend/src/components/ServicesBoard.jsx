import React, { useState, useEffect } from "react";
import { api, label, rm } from "../api";
import { badge, card, colors, grid, page } from "../styles";

export default function ServicesBoard() {
  const [services, setServices] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api("/services"), api("/promotions")])
      .then(([s, p]) => {
        setServices(s);
        setPromotions(p);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div style={page}>
      {error && <div style={{ color: colors.brand }}>{error}</div>}

      <h2 style={{ color: colors.navy }}>Current Promotions</h2>
      <div style={grid(260)}>
        {promotions.map((p) => (
          <div key={p.id} style={{ ...card, background: "#fff7ed", borderColor: colors.accent }}>
            <div style={{ fontSize: 30, fontWeight: "bold", color: colors.brand }}>{p.discount_percent}% OFF</div>
            <h3 style={{ margin: "6px 0" }}>{p.title}</h3>
            <div style={{ fontSize: 14, color: "#334155" }}>{p.description}</div>
            {p.promo_code && (
              <div style={{ marginTop: 10 }}>
                Use code <span style={{ ...badge(colors.navy), fontSize: 13, letterSpacing: 1 }}>{p.promo_code}</span>
              </div>
            )}
            <div style={{ fontSize: 12, color: colors.muted, marginTop: 8 }}>Valid {p.valid_from} to {p.valid_until}</div>
          </div>
        ))}
        {promotions.length === 0 && <div style={{ color: colors.muted }}>No promotions running right now.</div>}
      </div>

      <h2 style={{ color: colors.navy, marginTop: 32 }}>Our Rental Services</h2>
      <div style={grid(260)}>
        {services.map((s) => (
          <div key={s.id} style={card}>
            <h3 style={{ margin: "0 0 8px 0" }}>{s.title}</h3>
            <div style={{ fontSize: 14, color: "#334155", minHeight: 40 }}>{s.description}</div>
            <div style={{ marginTop: 12 }}>
              <b style={{ fontSize: 20, color: colors.brand }}>{Number(s.price) === 0 ? "Included" : rm(s.price)}</b>
              {Number(s.price) > 0 && <span style={{ fontSize: 12, color: colors.muted }}> {label(s.price_unit)}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

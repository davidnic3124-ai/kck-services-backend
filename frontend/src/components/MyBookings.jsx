import React, { useState, useEffect } from "react";
import { api, rm } from "../api";
import { badge, btn, card, colors, page, statusColors, td, th } from "../styles";

export default function MyBookings({ token }) {
  const [bookings, setBookings] = useState([]);
  const [message, setMessage] = useState("");

  const fetchBookings = () => {
    api("/bookings/me", { token })
      .then(setBookings)
      .catch((err) => setMessage(err.message));
  };

  useEffect(() => {
    fetchBookings();
  }, [token]);

  const cancel = async (b) => {
    if (!confirm(`Cancel your booking for ${b.car_label}?`)) return;
    try {
      await api(`/bookings/${b.id}/cancel`, { token, method: "PATCH" });
      setMessage("Booking cancelled.");
      fetchBookings();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={{ ...page, ...card }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>My Bookings</h3>
        <button onClick={fetchBookings} style={btn("#f1f5f9", colors.navy)}>Refresh</button>
      </div>
      {message && <div style={{ margin: "10px 0", fontSize: 13, color: colors.muted }}>{message}</div>}
      <div style={{ overflowX: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={th}>Car</th><th style={th}>Dates</th><th style={th}>Service</th>
              <th style={th}>Pick-up</th><th style={th}>Total</th><th style={th}>Status</th><th style={th}></th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id}>
                <td style={td}>{b.car_label}</td>
                <td style={td}>{b.start_date} → {b.end_date}<br /><span style={{ color: colors.muted }}>{b.rental_days} day(s)</span></td>
                <td style={td}>{b.service_title || "Self-drive"}</td>
                <td style={td}>{b.pickup_location}</td>
                <td style={td}>
                  <b>{rm(b.total_price)}</b>
                  {b.discount_amount > 0 && <div style={{ fontSize: 11, color: "#16a34a" }}>saved {rm(b.discount_amount)} ({b.promo_code})</div>}
                </td>
                <td style={td}><span style={badge(statusColors[b.status])}>{b.status}</span></td>
                <td style={td}>
                  {["pending", "confirmed"].includes(b.status) && (
                    <button onClick={() => cancel(b)} style={btn("#fee2e2", colors.brand)}>Cancel</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {bookings.length === 0 && <div style={{ color: colors.muted, padding: 12 }}>No bookings yet. Head to "Our Cars" to book one.</div>}
      </div>
    </div>
  );
}

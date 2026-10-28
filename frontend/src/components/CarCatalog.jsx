import React, { useState, useEffect } from "react";
import { api, label, rm, stars } from "../api";
import { badge, btn, card, colors, grid, input, page } from "../styles";

const CATEGORIES = ["sedan", "hatchback", "suv", "mpv", "pickup", "van", "luxury"];
const today = () => new Date().toISOString().slice(0, 10);

function BookingForm({ car, token, onNeedLogin, onDone }) {
  const [services, setServices] = useState([]);
  const [form, setForm] = useState({ start_date: today(), end_date: today(), service_id: "", pickup_location: "", promo_code: "", notes: "" });
  const [quote, setQuote] = useState(null);
  const [message, setMessage] = useState("");
  const set = (k) => (e) => {
    setForm({ ...form, [k]: e.target.value });
    setQuote(null);
  };

  useEffect(() => {
    api("/services").then(setServices).catch(() => setServices([]));
  }, []);

  const payload = () => ({
    car_id: car.id,
    start_date: form.start_date,
    end_date: form.end_date,
    pickup_location: form.pickup_location || "KCK HQ",
    service_id: form.service_id || null,
    promo_code: form.promo_code || null,
    notes: form.notes || null
  });

  const getQuote = async () => {
    setMessage("");
    try {
      setQuote(await api("/bookings/quote", { method: "POST", body: payload() }));
    } catch (err) {
      setMessage(err.message);
    }
  };

  const confirm = async () => {
    if (!token) return onNeedLogin();
    setMessage("");
    try {
      const booking = await api("/bookings", { token, method: "POST", body: payload() });
      onDone(`Booking received! ${booking.car_label}, ${booking.start_date} → ${booking.end_date}, total ${rm(booking.total_price)}. Status: pending.`);
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={{ ...card, borderColor: colors.brand, marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Book {car.brand} {car.model} — {rm(car.daily_rate)}/day</h3>
        <button onClick={() => onDone("")} style={btn("#e2e8f0", colors.navy)}>Close</button>
      </div>
      <div style={{ ...grid(200), marginTop: 14 }}>
        <label style={{ fontSize: 12 }}>Pick-up date<input type="date" min={today()} value={form.start_date} onChange={set("start_date")} style={input} /></label>
        <label style={{ fontSize: 12 }}>Return date<input type="date" min={form.start_date} value={form.end_date} onChange={set("end_date")} style={input} /></label>
        <label style={{ fontSize: 12 }}>Service package
          <select value={form.service_id} onChange={set("service_id")} style={input}>
            <option value="">Self-drive (no extra)</option>
            {services.map((s) => <option key={s.id} value={s.id}>{s.title} (+{rm(s.price)} {label(s.price_unit)})</option>)}
          </select>
        </label>
        <label style={{ fontSize: 12 }}>Pick-up location<input placeholder="e.g. KLIA Terminal 1" value={form.pickup_location} onChange={set("pickup_location")} style={input} /></label>
        <label style={{ fontSize: 12 }}>Promo code<input placeholder="e.g. WELCOME10" value={form.promo_code} onChange={set("promo_code")} style={input} /></label>
        <label style={{ fontSize: 12 }}>Notes<input placeholder="Child seat, etc." value={form.notes} onChange={set("notes")} style={input} /></label>
      </div>

      {quote && (
        <div style={{ marginTop: 14, padding: 12, background: colors.bg, borderRadius: 6, fontSize: 14, lineHeight: 1.7 }}>
          {quote.rental_days} day(s) car rental: <b>{rm(quote.car_cost)}</b><br />
          Service package: <b>{rm(quote.service_cost)}</b><br />
          Discount ({quote.discount_percent}%): <b>-{rm(quote.discount_amount)}</b><br />
          <span style={{ fontSize: 18 }}>Total: <b style={{ color: colors.brand }}>{rm(quote.total_price)}</b></span>
        </div>
      )}
      {message && <div style={{ marginTop: 10, color: colors.brand, fontSize: 13 }}>{message}</div>}

      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button onClick={getQuote} style={btn(colors.navy)}>Get Price Quote</button>
        <button onClick={confirm} style={btn()}>{token ? "Confirm Booking" : "Log in to Book"}</button>
      </div>
    </div>
  );
}

export default function CarCatalog({ token, onNeedLogin }) {
  const [cars, setCars] = useState(null);
  const [filters, setFilters] = useState({ search: "", category: "", available_only: false });
  const [selected, setSelected] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const fetchCars = () => {
    const params = new URLSearchParams();
    if (filters.search) params.set("search", filters.search);
    if (filters.category) params.set("category", filters.category);
    if (filters.available_only) params.set("available_only", "true");
    api(`/cars?${params}`)
      .then((data) => {
        setCars(data);
        setError("");
      })
      .catch((err) => setError(`Cannot reach the KCK API: ${err.message}`));
  };

  useEffect(() => {
    fetchCars();
  }, [filters.category, filters.available_only]);

  return (
    <div style={page}>
      <div style={{ ...card, background: colors.navy, color: "#fff", marginBottom: 20 }}>
        <h2 style={{ margin: "0 0 6px 0" }}>Rent a car with KCK SERVICES</h2>
        <div style={{ color: "#cbd5e1", fontSize: 14 }}>Clean, well-maintained cars at honest daily rates. Pick a car, choose your dates and book online.</div>
      </div>

      {notice && <div style={{ ...card, borderColor: "#16a34a", color: "#166534", marginBottom: 16 }}>{notice}</div>}
      {selected && (
        <BookingForm
          car={selected}
          token={token}
          onNeedLogin={onNeedLogin}
          onDone={(msg) => {
            setSelected(null);
            setNotice(msg);
          }}
        />
      )}

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 16, alignItems: "center" }}>
        <input
          placeholder="Search brand, model or plate..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && fetchCars()}
          style={{ ...input, width: 260 }}
        />
        <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })} style={{ ...input, width: 160 }}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c.toUpperCase()}</option>)}
        </select>
        <label style={{ fontSize: 13 }}>
          <input type="checkbox" checked={filters.available_only} onChange={(e) => setFilters({ ...filters, available_only: e.target.checked })} /> Available only
        </label>
        <button onClick={fetchCars} style={btn(colors.navy)}>Search</button>
      </div>

      {error && <div style={{ color: colors.brand, marginBottom: 12 }}>{error}</div>}

      <div style={grid(240)}>
        {(cars || []).map((car) => (
          <div key={car.id} style={{ ...card, padding: 0, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            {car.image_url ? (
              <img src={car.image_url} alt={`${car.brand} ${car.model}`} style={{ width: "100%", height: 150, objectFit: "cover" }} />
            ) : (
              <div style={{ height: 150, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 60, background: "#f1f5f9" }}>🚗</div>
            )}
            <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <b>{car.brand} {car.model}</b>
                <span style={badge(car.is_available ? "#16a34a" : "#94a3b8")}>{car.is_available ? "Available" : "Unavailable"}</span>
              </div>
              <div style={{ fontSize: 12, color: colors.muted }}>
                {car.year} · {car.category.toUpperCase()} · {car.transmission} · {car.seats} seats · {car.fuel_type}
              </div>
              <div style={{ fontSize: 13, color: colors.accent }}>
                {car.review_count > 0 ? `${stars(car.average_rating)} ${car.average_rating} (${car.review_count})` : "No reviews yet"}
              </div>
              {car.description && <div style={{ fontSize: 13, color: "#334155" }}>{car.description}</div>}
              <div style={{ marginTop: "auto", display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8 }}>
                <span><b style={{ fontSize: 20, color: colors.brand }}>{rm(car.daily_rate)}</b><span style={{ fontSize: 12, color: colors.muted }}> /day</span></span>
                <button
                  disabled={!car.is_available}
                  onClick={() => {
                    setSelected(car);
                    setNotice("");
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                  style={{ ...btn(car.is_available ? colors.brand : "#cbd5e1"), cursor: car.is_available ? "pointer" : "not-allowed" }}
                >
                  Book Now
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {!error && cars === null && <div style={{ color: colors.muted }}>Loading cars...</div>}
      {!error && cars?.length === 0 && <div style={{ color: colors.muted }}>No cars match your search.</div>}
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { api, label, rm, stars } from "../api";
import { badge, btn, card, colors, grid, input, page, statusColors, td, th } from "../styles";
import EntityManager from "./EntityManager";

const today = () => new Date().toISOString().slice(0, 10);

// ---------------------------------------------------------------- Dashboard
function Dashboard({ token }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/dashboard/summary", { token }).then(setData).catch((err) => setError(err.message));
  }, [token]);

  if (error) return <div style={{ color: colors.brand }}>{error}</div>;
  if (!data) return <div>Loading...</div>;

  const tiles = [
    ["Total revenue", rm(data.total_revenue)],
    ["Bookings", data.total_bookings],
    ["Cars available", `${data.available_cars} / ${data.total_cars}`],
    ["Customers", data.total_customers],
    ["Average rating", data.average_rating ? `${data.average_rating} ★` : "—"],
    ["Reviews to approve", data.pending_feedback]
  ];

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={grid(170)}>
        {tiles.map(([name, value]) => (
          <div key={name} style={card}>
            <div style={{ fontSize: 12, color: colors.muted }}>{name}</div>
            <div style={{ fontSize: 24, fontWeight: "bold", color: colors.navy }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={grid(300)}>
        <div style={card}>
          <h4 style={{ marginTop: 0 }}>Bookings by status</h4>
          {Object.entries(data.bookings_by_status).map(([s, n]) => (
            <div key={s} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
              <span style={badge(statusColors[s])}>{s}</span><b>{n}</b>
            </div>
          ))}
        </div>
        <div style={card}>
          <h4 style={{ marginTop: 0 }}>Top cars</h4>
          {data.top_cars.map((c) => (
            <div key={c.car_id} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 13 }}>
              <span>{c.car_label}</span>
              <span>{c.bookings} booking(s) · {c.average_rating ? `${c.average_rating}★` : "no rating"}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Bookings
function BookingsAdmin({ token }) {
  const [bookings, setBookings] = useState([]);
  const [filter, setFilter] = useState("");
  const [message, setMessage] = useState("");

  const load = () => {
    api(`/bookings${filter ? `?booking_status=${filter}` : ""}`, { token })
      .then(setBookings)
      .catch((err) => setMessage(err.message));
  };

  useEffect(() => {
    load();
  }, [token, filter]);

  const setStatus = async (b, status) => {
    try {
      await api(`/bookings/${b.id}/status`, { token, method: "PUT", body: { status } });
      setMessage(`Booking for ${b.customer_name} is now ${status}.`);
      load();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const remove = async (b) => {
    if (!confirm("Permanently delete this booking record?")) return;
    try {
      await api(`/bookings/${b.id}`, { token, method: "DELETE" });
      load();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>All Bookings</h3>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ ...input, width: 180 }}>
          <option value="">All statuses</option>
          {Object.keys(statusColors).map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      {message && <div style={{ margin: "10px 0", fontSize: 13, color: colors.muted }}>{message}</div>}
      <div style={{ overflowX: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={th}>Customer</th><th style={th}>Car</th><th style={th}>Dates</th>
              <th style={th}>Service / Pick-up</th><th style={th}>Total</th><th style={th}>Status</th><th style={th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id}>
                <td style={td}>{b.customer_name}<br /><span style={{ color: colors.muted, fontSize: 11 }}>{b.customer_email}</span></td>
                <td style={td}>{b.car_label}</td>
                <td style={td}>{b.start_date} → {b.end_date}<br /><span style={{ color: colors.muted }}>{b.rental_days} day(s)</span></td>
                <td style={td}>{b.service_title || "Self-drive"}<br /><span style={{ color: colors.muted }}>{b.pickup_location}</span></td>
                <td style={td}><b>{rm(b.total_price)}</b>{b.promo_code && <div style={{ fontSize: 11 }}>{b.promo_code}</div>}</td>
                <td style={td}>
                  <select value={b.status} onChange={(e) => setStatus(b, e.target.value)} style={{ ...input, width: 120, borderColor: statusColors[b.status] }}>
                    {Object.keys(statusColors).map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </td>
                <td style={td}><button onClick={() => remove(b)} style={btn("#fee2e2", colors.brand)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {bookings.length === 0 && <div style={{ color: colors.muted, padding: 12 }}>No bookings found.</div>}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Feedback moderation
function FeedbackAdmin({ token }) {
  const [items, setItems] = useState([]);
  const [replies, setReplies] = useState({});
  const [message, setMessage] = useState("");

  const load = () => {
    api("/feedback?include_unpublished=true", { token })
      .then((data) => {
        setItems(data);
        setReplies(Object.fromEntries(data.map((f) => [f.id, f.admin_reply || ""])));
      })
      .catch((err) => setMessage(err.message));
  };

  useEffect(() => {
    load();
  }, [token]);

  const moderate = async (f, body) => {
    try {
      await api(`/feedback/${f.id}/moderate`, { token, method: "PUT", body });
      setMessage("Feedback updated.");
      load();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const remove = async (f) => {
    if (!confirm("Delete this review?")) return;
    try {
      await api(`/feedback/${f.id}`, { token, method: "DELETE" });
      load();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={card}>
      <h3 style={{ marginTop: 0 }}>Customer Feedback Moderation</h3>
      {message && <div style={{ marginBottom: 10, fontSize: 13, color: colors.muted }}>{message}</div>}
      {items.map((f) => (
        <div key={f.id} style={{ padding: 12, borderBottom: `1px solid ${colors.border}`, display: "grid", gap: 6 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
            <span style={{ color: colors.accent }}>{stars(f.rating)}</span>
            <b>{f.title || "(no title)"}</b>
            <span style={badge(f.is_published ? "#16a34a" : colors.accent)}>{f.is_published ? "Published" : "Pending"}</span>
            <span style={{ fontSize: 12, color: colors.muted }}>by {f.customer_name}{f.car_label && ` · ${f.car_label}`} · {f.created_at.slice(0, 10)}</span>
          </div>
          <div style={{ fontSize: 14 }}>{f.comment}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <input
              placeholder="Public reply from KCK (optional)"
              value={replies[f.id] ?? ""}
              onChange={(e) => setReplies({ ...replies, [f.id]: e.target.value })}
              style={{ ...input, flex: 1, minWidth: 220 }}
            />
            <button onClick={() => moderate(f, { admin_reply: replies[f.id] })} style={btn("#e0f2fe", "#0369a1")}>Save Reply</button>
            {f.is_published ? (
              <button onClick={() => moderate(f, { is_published: false })} style={btn("#94a3b8")}>Unpublish</button>
            ) : (
              <button onClick={() => moderate(f, { is_published: true, admin_reply: replies[f.id] || null })} style={btn("#16a34a")}>Approve & Publish</button>
            )}
            <button onClick={() => remove(f)} style={btn("#fee2e2", colors.brand)}>Delete</button>
          </div>
        </div>
      ))}
      {items.length === 0 && <div style={{ color: colors.muted }}>No feedback yet.</div>}
    </div>
  );
}

// ---------------------------------------------------------------- Users
function UsersAdmin({ token, adminId }) {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState("");

  const load = () => api("/auth/users", { token }).then(setUsers).catch((err) => setMessage(err.message));

  useEffect(() => {
    load();
  }, [token]);

  const toggleRole = async (u) => {
    const role = u.role === "admin" ? "customer" : "admin";
    try {
      await api(`/auth/users/${u.id}/role`, { token, method: "PUT", body: { role } });
      load();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div style={card}>
      <h3 style={{ marginTop: 0 }}>Users</h3>
      {message && <div style={{ marginBottom: 10, fontSize: 13, color: colors.brand }}>{message}</div>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><th style={th}>Name</th><th style={th}>Email</th><th style={th}>Phone</th><th style={th}>Role</th><th style={th}></th></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td style={td}>{u.full_name}</td>
              <td style={td}>{u.email}</td>
              <td style={td}>{u.phone || "—"}</td>
              <td style={td}><span style={badge(u.role === "admin" ? colors.brand : "#64748b")}>{u.role}</span></td>
              <td style={td}>
                {u.id !== adminId && (
                  <button onClick={() => toggleRole(u)} style={btn("#f1f5f9", colors.navy)}>
                    {u.role === "admin" ? "Make customer" : "Make admin"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------- Car photo upload button
function CarPhotoButton({ car, token, reload, setMessage }) {
  const upload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("image", file);
    try {
      await api(`/cars/${car.id}/image`, { token, method: "POST", formData });
      setMessage(`Photo uploaded for ${car.plate_number}.`);
      reload();
    } catch (err) {
      setMessage(`Upload failed: ${err.message}`);
    }
    e.target.value = "";
  };
  return (
    <label style={{ ...btn("#fef3c7", "#92400e"), display: "inline-block" }}>
      Photo
      <input type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} style={{ display: "none" }} />
    </label>
  );
}

// ---------------------------------------------------------------- Admin shell
export default function AdminPanel({ token, adminId }) {
  const [section, setSection] = useState("dashboard");

  const sections = [
    ["dashboard", "Dashboard"], ["cars", "Cars"], ["services", "Services"], ["promotions", "Promotions"],
    ["bookings", "Bookings"], ["feedback", "Feedback"], ["users", "Users"]
  ];

  return (
    <div style={page}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
        {sections.map(([id, name]) => (
          <button key={id} onClick={() => setSection(id)} style={btn(section === id ? colors.navy : "#e2e8f0", section === id ? "#fff" : colors.navy)}>
            {name}
          </button>
        ))}
      </div>

      {section === "dashboard" && <Dashboard token={token} />}

      {section === "cars" && (
        <EntityManager
          token={token}
          title="Manage Cars"
          endpoint="/cars"
          emptyItem={{ plate_number: "", brand: "", model: "", year: new Date().getFullYear(), category: "sedan", transmission: "auto", seats: 5, fuel_type: "petrol", daily_rate: "", description: "", is_available: true }}
          rowKeyLabel={(c) => c.plate_number || "car"}
          fields={[
            { name: "plate_number", label: "Plate number", type: "text", required: true },
            { name: "brand", label: "Brand", type: "text", required: true },
            { name: "model", label: "Model", type: "text", required: true },
            { name: "year", label: "Year", type: "number", required: true },
            { name: "category", label: "Category", type: "select", options: ["sedan", "hatchback", "suv", "mpv", "pickup", "van", "luxury"] },
            { name: "transmission", label: "Transmission", type: "select", options: ["auto", "manual"] },
            { name: "seats", label: "Seats", type: "number", required: true },
            { name: "fuel_type", label: "Fuel", type: "select", options: ["petrol", "diesel", "hybrid", "electric"] },
            { name: "daily_rate", label: "Daily rate (RM)", type: "number", required: true },
            { name: "is_available", label: "Available for rent", type: "checkbox" },
            { name: "description", label: "Description", type: "textarea" }
          ]}
          columns={[
            { label: "Plate", render: (c) => <b>{c.plate_number}</b> },
            { label: "Car", render: (c) => `${c.brand} ${c.model} (${c.year})` },
            { label: "Type", render: (c) => `${c.category} · ${c.transmission} · ${c.seats} seats` },
            { label: "Rate", render: (c) => rm(c.daily_rate) },
            { label: "Photo", render: (c) => (c.image_url ? <img src={c.image_url} alt="" style={{ width: 60, height: 40, objectFit: "cover", borderRadius: 4 }} /> : "—") },
            { label: "Status", render: (c) => <span style={badge(c.is_available ? "#16a34a" : "#94a3b8")}>{c.is_available ? "Available" : "Hidden"}</span> }
          ]}
          extraActions={(car, reload, setMessage) => <CarPhotoButton car={car} token={token} reload={reload} setMessage={setMessage} />}
        />
      )}

      {section === "services" && (
        <EntityManager
          token={token}
          title="Manage Rental Services"
          endpoint="/services"
          listPath="/services?include_unpublished=true"
          emptyItem={{ title: "", description: "", price: 0, price_unit: "per_trip", is_published: true }}
          rowKeyLabel={(s) => s.title || "service"}
          fields={[
            { name: "title", label: "Title", type: "text", required: true },
            { name: "price", label: "Price (RM)", type: "number", required: true },
            { name: "price_unit", label: "Charged", type: "select", options: ["per_trip", "per_day", "per_hour", "per_month"] },
            { name: "is_published", label: "Published on website", type: "checkbox" },
            { name: "description", label: "Description", type: "textarea" }
          ]}
          columns={[
            { label: "Title", render: (s) => <b>{s.title}</b> },
            { label: "Price", render: (s) => `${rm(s.price)} ${label(s.price_unit)}` },
            { label: "Status", render: (s) => <span style={badge(s.is_published ? "#16a34a" : "#94a3b8")}>{s.is_published ? "Published" : "Draft"}</span> }
          ]}
        />
      )}

      {section === "promotions" && (
        <EntityManager
          token={token}
          title="Manage Promotions"
          endpoint="/promotions"
          listPath="/promotions?include_inactive=true"
          emptyItem={{ title: "", description: "", discount_percent: 10, promo_code: "", valid_from: today(), valid_until: today(), is_active: true }}
          rowKeyLabel={(p) => p.title || "promotion"}
          fields={[
            { name: "title", label: "Title", type: "text", required: true },
            { name: "promo_code", label: "Promo code", type: "text" },
            { name: "discount_percent", label: "Discount %", type: "number", required: true },
            { name: "valid_from", label: "Valid from", type: "date", required: true },
            { name: "valid_until", label: "Valid until", type: "date", required: true },
            { name: "is_active", label: "Active", type: "checkbox" },
            { name: "description", label: "Description", type: "textarea" }
          ]}
          columns={[
            { label: "Title", render: (p) => <b>{p.title}</b> },
            { label: "Code", render: (p) => p.promo_code || "—" },
            { label: "Discount", render: (p) => `${p.discount_percent}%` },
            { label: "Valid", render: (p) => `${p.valid_from} → ${p.valid_until}` },
            { label: "Status", render: (p) => <span style={badge(p.is_active ? "#16a34a" : "#94a3b8")}>{p.is_active ? "Active" : "Inactive"}</span> }
          ]}
        />
      )}

      {section === "bookings" && <BookingsAdmin token={token} />}
      {section === "feedback" && <FeedbackAdmin token={token} />}
      {section === "users" && <UsersAdmin token={token} adminId={adminId} />}
    </div>
  );
}

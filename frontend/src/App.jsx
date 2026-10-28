import React, { useState, useEffect } from "react";
import { supabase } from "./supabaseClient";
import { api } from "./api";
import { btn, colors, input } from "./styles";
import CarCatalog from "./components/CarCatalog";
import ServicesBoard from "./components/ServicesBoard";
import FeedbackWall from "./components/FeedbackWall";
import MyBookings from "./components/MyBookings";
import AdminPanel from "./components/AdminPanel";

function AuthBox({ onClose }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "" });
  const [message, setMessage] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    if (mode === "login") {
      const { error } = await supabase.auth.signInWithPassword({ email: form.email, password: form.password });
      if (error) return setMessage(error.message);
      onClose();
    } else {
      const { data, error } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: { data: { full_name: form.full_name, phone: form.phone } }
      });
      if (error) return setMessage(error.message);
      if (data.session) onClose();
      else setMessage("Registered! Check your email to confirm, then log in.");
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10, padding: 16 }}>
      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: 360, padding: 24, background: "#fff", borderRadius: 10, fontFamily: "sans-serif", display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0, color: colors.navy }}>{mode === "login" ? "Log in to KCK SERVICES" : "Create a KCK account"}</h3>
        {mode === "register" && (
          <>
            <input placeholder="Full name" value={form.full_name} onChange={set("full_name")} style={input} required />
            <input placeholder="Phone (e.g. 012-3456789)" value={form.phone} onChange={set("phone")} style={input} />
          </>
        )}
        <input type="email" placeholder="Email" value={form.email} onChange={set("email")} style={input} required />
        <input type="password" placeholder="Password (min 6 characters)" value={form.password} onChange={set("password")} style={input} minLength={6} required />
        <button type="submit" style={{ ...btn(), padding: 12 }}>{mode === "login" ? "Log In" : "Register"}</button>
        {message && <div style={{ fontSize: 13, color: colors.brand }}>{message}</div>}
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
          <a href="#" onClick={(e) => { e.preventDefault(); setMode(mode === "login" ? "register" : "login"); setMessage(""); }}>
            {mode === "login" ? "New customer? Register" : "Have an account? Log in"}
          </a>
          <a href="#" onClick={(e) => { e.preventDefault(); onClose(); }} style={{ color: colors.muted }}>Close</a>
        </div>
      </form>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [tab, setTab] = useState("cars");
  const [showAuth, setShowAuth] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => setSession(session));
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!session) {
      setProfile(null);
      return;
    }
    api("/auth/me", { token: session.access_token })
      .then(setProfile)
      .catch((err) => console.error("Profile error:", err));
  }, [session]);

  const token = session?.access_token;
  const isAdmin = profile?.role === "admin";

  const tabs = [
    { id: "cars", label: "Our Cars" },
    { id: "services", label: "Services & Promos" },
    { id: "feedback", label: "Customer Feedback" },
    ...(session ? [{ id: "bookings", label: "My Bookings" }] : []),
    ...(isAdmin ? [{ id: "admin", label: "Admin" }] : [])
  ];

  const handleLogout = () => {
    supabase.auth.signOut();
    setTab("cars");
  };

  return (
    <div style={{ minHeight: "100vh", background: colors.bg }}>
      <header style={{ background: colors.navy, color: "#fff", padding: "14px 20px" }}>
        <div style={{ maxWidth: 1080, margin: "0 auto", display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "space-between", alignItems: "center", fontFamily: "sans-serif" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, letterSpacing: 1 }}>
              <span style={{ color: colors.brand }}>KCK</span> SERVICES
            </h2>
            <div style={{ fontSize: 12, color: "#94a3b8" }}>Car Rental · Chauffeur · Airport Transfer</div>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
            {tabs.map((t) => (
              <button key={t.id} onClick={() => setTab(t.id)} style={btn(tab === t.id ? colors.brand : "#334155")}>
                {t.label}
              </button>
            ))}
            {session ? (
              <>
                <span style={{ fontSize: 13, color: "#cbd5e1" }}>
                  {profile?.full_name || session.user.email} {isAdmin && "(admin)"}
                </span>
                <button onClick={handleLogout} style={btn("#475569")}>Logout</button>
              </>
            ) : (
              <button onClick={() => setShowAuth(true)} style={btn(colors.accent, colors.navy)}>Login / Register</button>
            )}
          </div>
        </div>
      </header>

      <main style={{ padding: 20 }}>
        {tab === "cars" && <CarCatalog token={token} onNeedLogin={() => setShowAuth(true)} />}
        {tab === "services" && <ServicesBoard />}
        {tab === "feedback" && <FeedbackWall token={token} userId={session?.user.id} onNeedLogin={() => setShowAuth(true)} />}
        {tab === "bookings" && session && <MyBookings token={token} />}
        {tab === "admin" && isAdmin && <AdminPanel token={token} adminId={session.user.id} />}
      </main>

      <footer style={{ textAlign: "center", padding: 20, fontSize: 12, color: colors.muted, fontFamily: "sans-serif" }}>
        © {new Date().getFullYear()} KCK SERVICES COMPANY · Powered by FastAPI + Supabase
      </footer>

      {showAuth && <AuthBox onClose={() => setShowAuth(false)} />}
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { api } from "../api";
import { btn, card, colors, grid, input, td, th } from "../styles";

// Reusable admin CRUD screen: a create/edit form + a table with Edit / Delete.
// Used for Cars, Rental Services and Promotions.
// fields: [{ name, label, type: "text" | "number" | "date" | "select" | "checkbox" | "textarea", options, required }]
export default function EntityManager({ token, title, endpoint, listPath, fields, columns, emptyItem, rowKeyLabel, extraActions }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyItem);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");

  const load = () => {
    api(listPath || endpoint, { token })
      .then(setItems)
      .catch((err) => setMessage(`Load failed: ${err.message}`));
  };

  useEffect(() => {
    load();
  }, [token, endpoint]);

  const resetForm = () => {
    setForm(emptyItem);
    setEditingId(null);
  };

  const toPayload = () => {
    const body = {};
    for (const f of fields) {
      let v = form[f.name];
      if (f.type === "number") v = v === "" || v === null ? null : Number(v);
      if ((f.type === "text" || f.type === "textarea" || f.type === "date") && v === "") v = null;
      body[f.name] = v;
    }
    return body;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await api(`${endpoint}/${editingId}`, { token, method: "PUT", body: toPayload() });
        setMessage(`Updated ${rowKeyLabel(form)}.`);
      } else {
        await api(endpoint, { token, method: "POST", body: toPayload() });
        setMessage(`Created ${rowKeyLabel(form)}.`);
      }
      resetForm();
      load();
    } catch (err) {
      setMessage(`Save failed: ${err.message}`);
    }
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    const next = {};
    for (const f of fields) next[f.name] = item[f.name] ?? (f.type === "checkbox" ? false : "");
    setForm(next);
    setMessage("");
  };

  const remove = async (item) => {
    if (!confirm(`Delete ${rowKeyLabel(item)}? This cannot be undone.`)) return;
    try {
      await api(`${endpoint}/${item.id}`, { token, method: "DELETE" });
      setMessage(`Deleted ${rowKeyLabel(item)}.`);
      if (editingId === item.id) resetForm();
      load();
    } catch (err) {
      setMessage(`Delete failed: ${err.message}`);
    }
  };

  const renderField = (f) => {
    const value = form[f.name] ?? "";
    const onChange = (e) => setForm({ ...form, [f.name]: f.type === "checkbox" ? e.target.checked : e.target.value });
    if (f.type === "checkbox") {
      return (
        <label key={f.name} style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
          <input type="checkbox" checked={!!form[f.name]} onChange={onChange} /> {f.label}
        </label>
      );
    }
    if (f.type === "select") {
      return (
        <label key={f.name} style={{ fontSize: 12 }}>{f.label}
          <select value={value} onChange={onChange} style={input} required={f.required}>
            {f.options.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        </label>
      );
    }
    if (f.type === "textarea") {
      return (
        <label key={f.name} style={{ fontSize: 12, gridColumn: "1 / -1" }}>{f.label}
          <textarea value={value} onChange={onChange} style={{ ...input, minHeight: 60 }} />
        </label>
      );
    }
    return (
      <label key={f.name} style={{ fontSize: 12 }}>{f.label}
        <input type={f.type} step={f.type === "number" ? "any" : undefined} value={value} onChange={onChange} style={input} required={f.required} />
      </label>
    );
  };

  return (
    <div style={card}>
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <form onSubmit={handleSubmit} style={{ background: colors.bg, padding: 14, borderRadius: 8, marginBottom: 16 }}>
        <div style={{ fontWeight: "bold", fontSize: 14, marginBottom: 10 }}>{editingId ? `Editing: ${rowKeyLabel(form)}` : "Add new"}</div>
        <div style={grid(180)}>{fields.map(renderField)}</div>
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button type="submit" style={btn(editingId ? "#0284c7" : "#16a34a")}>{editingId ? "Save Changes" : "Create"}</button>
          {editingId && <button type="button" onClick={resetForm} style={btn("#e2e8f0", colors.navy)}>Cancel</button>}
        </div>
      </form>
      {message && <div style={{ marginBottom: 10, fontSize: 13, color: colors.muted }}>{message}</div>}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {columns.map((c) => <th key={c.label} style={th}>{c.label}</th>)}
              <th style={th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                {columns.map((c) => <td key={c.label} style={td}>{c.render(item)}</td>)}
                <td style={{ ...td, whiteSpace: "nowrap" }}>
                  <button onClick={() => startEdit(item)} style={{ ...btn("#e0f2fe", "#0369a1"), marginRight: 6 }}>Edit</button>
                  <button onClick={() => remove(item)} style={{ ...btn("#fee2e2", colors.brand), marginRight: 6 }}>Delete</button>
                  {extraActions && extraActions(item, load, setMessage)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

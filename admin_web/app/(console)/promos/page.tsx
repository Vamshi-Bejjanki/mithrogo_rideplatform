"use client";

import { FormEvent, useState } from "react";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { dateTime, money } from "@/lib/format";
import type { Promo } from "@/lib/types";
import { useAction } from "@/lib/useApi";
import { usePagedList } from "@/lib/usePagedList";

const EMPTY = {
  code: "", description: "", discount_type: "FLAT", value: "", max_discount: "", min_fare: "0", valid_until: "",
  max_uses_total: "", max_uses_per_user: "1", first_ride_only: false,
};

export default function PromosPage() {
  const list = usePagedList<Promo>("admin/promos/", { search: "", is_active: "" });
  const action = useAction();
  const [form, setForm] = useState(EMPTY);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [open, setOpen] = useState(false);

  const set = (key: keyof typeof EMPTY, value: string | boolean) => setForm((f) => ({ ...f, [key]: value }));

  async function create(event: FormEvent) {
    event.preventDefault();
    setFieldErrors({});
    const body = {
      ...form,
      max_discount: form.max_discount || null,
      max_uses_total: form.max_uses_total || null,
      valid_until: form.valid_until ? new Date(`${form.valid_until}T23:59:59`).toISOString() : null,
    };
    const created = await action.run(async () => {
      try {
        return await api<Promo>("admin/promos/", { method: "POST", body });
      } catch (e) {
        if (e instanceof ApiError) setFieldErrors(e.fields);
        throw e;
      }
    });
    if (created) {
      setForm(EMPTY);
      setOpen(false);
      list.reload();
    }
  }

  async function toggle(promo: Promo) {
    const done = await action.run(() => api(`admin/promos/${promo.id}/`, { method: "PATCH", body: { is_active: !promo.is_active } }));
    if (done) list.reload();
  }

  const err = (k: string) => fieldErrors[k] && <span className="field-error">{fieldErrors[k]}</span>;

  return (
    <>
      <PageHead title="Promo codes" sub="Discounts riders enter at booking. The platform funds them; captains earn the full fare."
                actions={<button className="btn" onClick={() => setOpen((v) => !v)}>{open ? "Close" : "New promo code"}</button>} />
      <ErrorBox message={action.error} />
      {open && (
        <form className="card" onSubmit={create} style={{ marginBottom: 16 }}>
          <h2>New promo code</h2>
          <div className="form-grid">
            <label className="field"><span>Code</span><input value={form.code} onChange={(e) => set("code", e.target.value.toUpperCase())} required maxLength={24} />{err("code")}</label>
            <label className="field"><span>Type</span>
              <select value={form.discount_type} onChange={(e) => set("discount_type", e.target.value)}>
                <option value="FLAT">Flat ₹ off</option><option value="PERCENT">Percent off</option>
              </select></label>
            <label className="field"><span>{form.discount_type === "FLAT" ? "Amount (₹)" : "Percent"}</span><input type="number" step="0.01" value={form.value} onChange={(e) => set("value", e.target.value)} required />{err("value")}</label>
            {form.discount_type === "PERCENT" && (
              <label className="field"><span>Max discount (₹)</span><input type="number" step="0.01" value={form.max_discount} onChange={(e) => set("max_discount", e.target.value)} /></label>
            )}
            <label className="field"><span>Minimum fare (₹)</span><input type="number" step="0.01" value={form.min_fare} onChange={(e) => set("min_fare", e.target.value)} /></label>
            <label className="field"><span>Valid until</span><input type="date" value={form.valid_until} onChange={(e) => set("valid_until", e.target.value)} /></label>
            <label className="field"><span>Total uses (blank = unlimited)</span><input type="number" value={form.max_uses_total} onChange={(e) => set("max_uses_total", e.target.value)} /></label>
            <label className="field"><span>Uses per rider</span><input type="number" min={1} value={form.max_uses_per_user} onChange={(e) => set("max_uses_per_user", e.target.value)} /></label>
            <label className="field"><span>Description</span><input value={form.description} onChange={(e) => set("description", e.target.value)} maxLength={160} /></label>
            <label className="check"><input type="checkbox" checked={form.first_ride_only} onChange={(e) => set("first_ride_only", e.target.checked)} /> First ride only</label>
          </div>
          <div className="btn-row" style={{ marginTop: 14 }}><button className="btn" disabled={action.busy}>Create code</button></div>
        </form>
      )}
      <div className="toolbar">
        <label className="field"><span>Search</span><input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} /></label>
        <label className="field"><span>Active</span>
          <select value={list.filters.is_active} onChange={(e) => list.setFilter("is_active", e.target.value)}>
            <option value="">Any</option><option value="true">Active</option><option value="false">Inactive</option>
          </select></label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(p) => p.id}
        empty={list.loading ? "Loading…" : "No promo codes yet."}
        columns={[
          { key: "code", title: "Code", render: (p) => <><span className="mono"><strong>{p.code}</strong></span><div className="sub">{p.description}</div></> },
          { key: "value", title: "Discount", render: (p) => p.discount_type === "FLAT" ? money(p.value) : `${Number(p.value)}%${p.max_discount ? ` (max ${money(p.max_discount)})` : ""}` },
          { key: "rules", title: "Rules", render: (p) => (
            <div className="sub">
              {Number(p.min_fare) > 0 && <div>Min fare {money(p.min_fare)}</div>}
              <div>{p.max_uses_per_user} use(s) per rider{p.first_ride_only ? " · first ride" : ""}</div>
            </div>
          ) },
          { key: "used", title: "Used", className: "num", render: (p) => `${p.times_used}${p.max_uses_total ? ` / ${p.max_uses_total}` : ""}` },
          { key: "until", title: "Valid until", render: (p) => p.valid_until ? dateTime(p.valid_until) : "No end" },
          { key: "active", title: "Status", render: (p) => <Badge value={p.is_active ? "ACTIVE" : "EXPIRED"} tone={p.is_active ? "ok" : ""} /> },
          { key: "a", title: "", render: (p) => (
            <button className="btn secondary small" disabled={action.busy} onClick={() => toggle(p)}>{p.is_active ? "Deactivate" : "Activate"}</button>
          ) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

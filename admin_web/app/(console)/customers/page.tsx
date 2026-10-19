"use client";

import Link from "next/link";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime } from "@/lib/format";
import type { Customer } from "@/lib/types";
import { useAction } from "@/lib/useApi";
import { usePagedList } from "@/lib/usePagedList";

export default function CustomersPage() {
  const list = usePagedList<Customer>("admin/customers/", { search: "", is_active: "" });
  const action = useAction();

  async function toggle(c: Customer) {
    const verb = c.is_active ? "suspend" : "reactivate";
    if (c.is_active && !window.confirm(`Suspend ${c.name || c.phone}? They will not be able to book rides.`)) return;
    const done = await action.run(() => api(`admin/customers/${c.id}/${verb}/`, { method: "POST" }));
    if (done) list.reload();
  }

  return (
    <>
      <PageHead title="Customers" sub="Riders, their activity, and account status." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Name, phone, email" />
        </label>
        <label className="field"><span>Account</span>
          <select value={list.filters.is_active} onChange={(e) => list.setFilter("is_active", e.target.value)}>
            <option value="">Any</option><option value="true">Active</option><option value="false">Suspended or deleted</option>
          </select>
        </label>
      </div>
      <ErrorBox message={list.error || action.error} />
      <Table
        rows={list.rows}
        rowKey={(c) => c.id}
        empty={list.loading ? "Loading…" : "No customers match."}
        columns={[
          { key: "name", title: "Customer", render: (c) => <><div>{c.name || "—"}</div><div className="sub">{c.phone}</div></> },
          { key: "email", title: "Email", render: (c) => c.email || "—" },
          { key: "rides", title: "Rides", className: "num", render: (c) => (
            <Link href={`/rides?customer=${c.id}`}>{c.completed_rides} / {c.total_rides}</Link>
          ) },
          { key: "sos", title: "Emergency contact", render: (c) => c.emergency_contact_phone ? `${c.emergency_contact_name} ${c.emergency_contact_phone}` : "—" },
          { key: "ref", title: "Referral", render: (c) => c.referral_code ? <span className="mono">{c.referral_code}</span> : "—" },
          { key: "status", title: "Account", render: (c) => c.deleted_at ? <Badge value="DELETED" tone="" /> : <Badge value={c.is_active ? "ACTIVE" : "SUSPENDED"} /> },
          { key: "joined", title: "Joined", render: (c) => dateTime(c.created_at) },
          { key: "a", title: "", render: (c) => c.deleted_at ? null : (
            <button className={`btn small ${c.is_active ? "secondary" : ""}`} disabled={action.busy} onClick={() => toggle(c)}>
              {c.is_active ? "Suspend" : "Reactivate"}
            </button>
          ) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

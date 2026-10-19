"use client";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { dateTime, label, money } from "@/lib/format";
import type { Payment } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

const TYPES = ["RIDE_PAYMENT", "CAPTAIN_SUBSCRIPTION", "DUES_SETTLEMENT", "WALLET_TOP_UP", "CANCELLATION_FEE"];

export default function PaymentsPage() {
  const list = usePagedList<Payment>("admin/payments/", { search: "", status: "", payment_type: "", from: "", to: "" });

  return (
    <>
      <PageHead title="Payments" sub="Every gateway order. A payment counts only once the gateway webhook confirms it." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Order ID, payment ID, phone" />
        </label>
        <label className="field"><span>Type</span>
          <select value={list.filters.payment_type} onChange={(e) => list.setFilter("payment_type", e.target.value)}>
            <option value="">Any</option>{TYPES.map((t) => <option key={t} value={t}>{label(t)}</option>)}
          </select>
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            <option value="">Any</option>{["PENDING", "SUCCESS", "FAILED", "REFUNDED"].map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </label>
        <label className="field"><span>From</span><input type="date" value={list.filters.from} onChange={(e) => list.setFilter("from", e.target.value)} /></label>
        <label className="field"><span>To</span><input type="date" value={list.filters.to} onChange={(e) => list.setFilter("to", e.target.value)} /></label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(p) => p.id}
        empty={list.loading ? "Loading…" : "No payments match."}
        columns={[
          { key: "when", title: "Created", render: (p) => dateTime(p.created_at) },
          { key: "type", title: "Type", render: (p) => label(p.payment_type) },
          { key: "user", title: "User", render: (p) => p.user.phone },
          { key: "status", title: "Status", render: (p) => <Badge value={p.status} /> },
          { key: "order", title: "Order", render: (p) => <span className="mono">{p.provider_order_id}</span> },
          { key: "provider", title: "Gateway", render: (p) => p.provider },
          { key: "amount", title: "Amount", className: "num", render: (p) => money(p.amount) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

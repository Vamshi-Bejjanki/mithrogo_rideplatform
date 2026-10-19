"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { ago, label } from "@/lib/format";
import type { Ticket } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

function TicketList() {
  const params = useSearchParams();
  const list = usePagedList<Ticket>("admin/tickets/", { search: "", status: params.get("status") ?? "", category: "" }, 50, 30000);

  return (
    <>
      <PageHead title="Support tickets" sub="Reply to riders and captains. Replies arrive in their app." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Phone or text" />
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            <option value="">Any</option>
            {["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"].map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </label>
        <label className="field"><span>Category</span>
          <select value={list.filters.category} onChange={(e) => list.setFilter("category", e.target.value)}>
            <option value="">Any</option>
            {["RIDE_ISSUE", "PAYMENT", "SAFETY", "ACCOUNT", "OTHER"].map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(t) => t.id}
        empty={list.loading ? "Loading…" : "No tickets match."}
        columns={[
          { key: "id", title: "#", render: (t) => <Link href={`/tickets/${t.id}`}>#{t.id}</Link> },
          { key: "status", title: "Status", render: (t) => <Badge value={t.status} /> },
          { key: "cat", title: "Category", render: (t) => <>{label(t.category)} {t.is_sos && <span className="badge danger">SOS</span>}</> },
          { key: "desc", title: "Issue", render: (t) => <Link href={`/tickets/${t.id}`}>{t.description.slice(0, 90)}{t.description.length > 90 ? "…" : ""}</Link> },
          { key: "user", title: "From", render: (t) => <>{t.user.phone}<div className="sub">{label(t.user.role)}</div></> },
          { key: "upd", title: "Updated", render: (t) => ago(t.updated_at) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

export default function TicketsPage() {
  return <Suspense><TicketList /></Suspense>;
}

"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime, label, money } from "@/lib/format";
import type { Due } from "@/lib/types";
import { useAction } from "@/lib/useApi";
import { usePagedList } from "@/lib/usePagedList";

function DueList() {
  const params = useSearchParams();
  const list = usePagedList<Due>("admin/dues/", {
    search: "", status: params.get("status") ?? "", due_type: "", captain: params.get("captain") ?? "",
  });
  const action = useAction();

  async function act(due: Due, verb: "waive" | "settle") {
    const text = verb === "waive"
      ? `Waive ${money(due.amount)} for ${due.captain_phone}? The captain will not owe it.`
      : `Mark ${money(due.amount)} from ${due.captain_phone} as paid outside the app (cash or bank)?`;
    if (!window.confirm(text)) return;
    const done = await action.run(() => api(`admin/dues/${due.id}/${verb}/`, { method: "POST" }));
    if (done) list.reload();
  }

  return (
    <>
      <PageHead title="Platform dues" sub="Money captains owe: the platform's ride share and shortfall fees." />
      <div className="toolbar">
        <label className="field"><span>Captain phone</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} />
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            <option value="">Any</option><option value="PENDING">Pending</option><option value="SETTLED">Settled</option><option value="WAIVED">Waived</option>
          </select>
        </label>
        <label className="field"><span>Type</span>
          <select value={list.filters.due_type} onChange={(e) => list.setFilter("due_type", e.target.value)}>
            <option value="">Any</option><option value="RIDE_SHARE">Ride share</option><option value="SHORTFALL_FEE">Shortfall fee</option>
          </select>
        </label>
      </div>
      <ErrorBox message={list.error || action.error} />
      <Table
        rows={list.rows}
        rowKey={(d) => d.id}
        empty={list.loading ? "Loading…" : "No dues match."}
        columns={[
          { key: "captain", title: "Captain", render: (d) => <Link href={`/captains/${d.captain_id}`}>{d.captain_phone}</Link> },
          { key: "type", title: "Type", render: (d) => label(d.due_type) },
          { key: "ride", title: "Ride", render: (d) => d.ride_id ? <Link href={`/rides/${d.ride_id}`}>{d.ride_id.slice(0, 8)}</Link> : "—" },
          { key: "status", title: "Status", render: (d) => <Badge value={d.status} /> },
          { key: "created", title: "Created", render: (d) => dateTime(d.created_at) },
          { key: "amount", title: "Amount", className: "num", render: (d) => money(d.amount) },
          { key: "a", title: "", render: (d) => d.status !== "PENDING" ? null : (
            <div className="btn-row">
              <button className="btn secondary small" disabled={action.busy} onClick={() => act(d, "settle")}>Mark paid</button>
              <button className="btn secondary small" disabled={action.busy} onClick={() => act(d, "waive")}>Waive</button>
            </div>
          ) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

export default function DuesPage() {
  return <Suspense><DueList /></Suspense>;
}

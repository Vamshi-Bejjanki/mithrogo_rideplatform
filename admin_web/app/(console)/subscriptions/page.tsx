"use client";

import Link from "next/link";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { dateTime, label, money } from "@/lib/format";
import type { Subscription } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

export default function SubscriptionsPage() {
  const list = usePagedList<Subscription>("admin/subscriptions/", { search: "", status: "" });

  return (
    <>
      <PageHead title="Captain plans" sub="Daily plans and ride-share plans captains have bought or switched to." />
      <div className="toolbar">
        <label className="field"><span>Captain phone</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} />
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            <option value="">Any</option>{["ACTIVE", "PENDING", "EXPIRED", "FAILED", "CANCELLED"].map((s) => <option key={s} value={s}>{label(s)}</option>)}
          </select>
        </label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(s) => s.id}
        empty={list.loading ? "Loading…" : "No plans match."}
        columns={[
          { key: "captain", title: "Captain", render: (s) => <Link href={`/captains/${s.captain_id}`}>{s.captain_phone}</Link> },
          { key: "plan", title: "Plan", render: (s) => <>{s.plan_name}<div className="sub mono">{s.plan_code}</div></> },
          { key: "status", title: "Status", render: (s) => <>{<Badge value={s.status} />} {s.penalty_pending && <span className="badge warn">Penalty</span>}</> },
          { key: "start", title: "Started", render: (s) => dateTime(s.start_at) },
          { key: "end", title: "Ends", render: (s) => s.expires_at ? dateTime(s.expires_at) : "Open-ended" },
          { key: "amount", title: "Price", className: "num", render: (s) => money(s.amount) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

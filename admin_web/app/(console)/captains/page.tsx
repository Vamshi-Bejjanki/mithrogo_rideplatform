"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { ago, dateTime } from "@/lib/format";
import type { Captain } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

function CaptainList() {
  const params = useSearchParams();
  const list = usePagedList<Captain>("admin/captains/", {
    search: "", kyc_status: params.get("kyc_status") ?? "", online_status: params.get("online_status") ?? "",
  });

  return (
    <>
      <PageHead title="Captains & KYC" sub="Review documents, verify vehicles, and suspend or reactivate captains." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Name, phone, licence" />
        </label>
        <label className="field"><span>KYC</span>
          <select value={list.filters.kyc_status} onChange={(e) => list.setFilter("kyc_status", e.target.value)}>
            <option value="">Any</option>
            {["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "SUSPENDED"].map((s) => <option key={s} value={s}>{s.replace("_", " ").toLowerCase()}</option>)}
          </select>
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.online_status} onChange={(e) => list.setFilter("online_status", e.target.value)}>
            <option value="">Any</option><option value="ONLINE">Online</option><option value="BUSY">On a ride</option><option value="OFFLINE">Offline</option>
          </select>
        </label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(c) => c.id}
        empty={list.loading ? "Loading…" : "No captains match."}
        columns={[
          { key: "name", title: "Captain", render: (c) => (
            <Link href={`/captains/${c.id}`}><div>{c.user.name || "Unnamed"}</div><div className="sub">{c.user.phone}</div></Link>
          ) },
          { key: "kyc", title: "KYC", render: (c) => <Badge value={c.kyc_status} /> },
          { key: "online", title: "Status", render: (c) => <Badge value={c.online_status} /> },
          { key: "vehicle", title: "Today", render: (c) => c.day_vehicle_type ?? "—" },
          { key: "rating", title: "Rating", className: "num", render: (c) => Number(c.rating) ? `★ ${c.rating}` : "New" },
          { key: "rides", title: "Rides", className: "num", render: (c) => c.total_rides },
          { key: "cancels", title: "Cancelled", className: "num", render: (c) => c.cancelled_rides },
          { key: "seen", title: "Last location", render: (c) => ago(c.last_location_at) },
          { key: "joined", title: "Joined", render: (c) => dateTime(c.created_at) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

export default function CaptainsPage() {
  return <Suspense><CaptainList /></Suspense>;
}

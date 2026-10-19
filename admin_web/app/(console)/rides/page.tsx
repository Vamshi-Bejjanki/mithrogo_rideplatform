"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { Badge, ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { dateTime, money } from "@/lib/format";
import type { Ride } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

const STATUSES = ["", "SEARCHING", "ACCEPTED", "CAPTAIN_ARRIVED", "STARTED", "COMPLETED", "CANCELLED"];

function RidesList() {
  const params = useSearchParams();
  const list = usePagedList<Ride>("admin/rides/", {
    status: params.get("status") ?? "", search: "", vehicle_type: "", from: "", to: "",
    customer: params.get("customer") ?? "", captain: params.get("captain") ?? "",
  });

  return (
    <>
      <PageHead title="Rides" sub="Search by ride ID, phone number or address." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Phone, address, ride ID" />
        </label>
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replace("_", " ").toLowerCase() : "Any"}</option>)}
          </select>
        </label>
        <label className="field"><span>Vehicle</span>
          <select value={list.filters.vehicle_type} onChange={(e) => list.setFilter("vehicle_type", e.target.value)}>
            <option value="">Any</option><option value="BIKE">Bike</option><option value="AUTO">Auto</option>
          </select>
        </label>
        <label className="field"><span>From</span>
          <input type="date" value={list.filters.from} onChange={(e) => list.setFilter("from", e.target.value)} />
        </label>
        <label className="field"><span>To</span>
          <input type="date" value={list.filters.to} onChange={(e) => list.setFilter("to", e.target.value)} />
        </label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(r) => r.id}
        empty={list.loading ? "Loading…" : "No rides match."}
        columns={[
          { key: "when", title: "Requested", render: (r) => <Link href={`/rides/${r.id}`}>{dateTime(r.requested_at)}</Link> },
          { key: "status", title: "Status", render: (r) => <Badge value={r.status} /> },
          { key: "type", title: "Type", render: (r) => r.vehicle_type },
          { key: "route", title: "Route", render: (r) => (
            <div><div>{r.pickup_address}</div><div className="sub">→ {r.drop_address}</div></div>
          ) },
          { key: "rider", title: "Rider", render: (r) => r.customer.phone },
          { key: "captain", title: "Captain", render: (r) => r.captain_phone ?? <span className="sub">—</span> },
          { key: "pay", title: "Payment", render: (r) => <><div>{r.payment_method}</div><Badge value={r.payment_status} /></> },
          { key: "fare", title: "Fare", className: "num", render: (r) => money(r.payable_fare) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

export default function RidesPage() {
  return <Suspense><RidesList /></Suspense>;
}

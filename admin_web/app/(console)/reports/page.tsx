"use client";

import { useState } from "react";

import { BarChart, ErrorBox, PageHead, Table } from "@/components/ui";
import { downloadCsv } from "@/lib/api";
import { isoDate, money } from "@/lib/format";
import type { DayRow } from "@/lib/types";
import { useAction, useApi } from "@/lib/useApi";

type Daily = { from: string; to: string; rows: DayRow[]; totals: Record<string, string | number> };
type Earnings = { rows: { captain_id: number; phone: string; name: string; completed_rides: number; fare_total: string;
  platform_share: string; net_earnings: string }[] };

const MONEY = ["gross_fares", "discounts", "platform_share", "subscription_revenue", "ride_payments", "dues_collected", "wallet_top_ups", "fee_revenue"];

export default function ReportsPage() {
  const today = new Date();
  const [from, setFrom] = useState(isoDate(new Date(today.getTime() - 13 * 86400000)));
  const [to, setTo] = useState(isoDate(today));
  const daily = useApi<Daily>("admin/reports/daily/", { from, to });
  const earnings = useApi<Earnings>("admin/reports/captain-earnings/", { from, to });
  const download = useAction();

  const rows = daily.data?.rows ?? [];
  const totals = daily.data?.totals ?? {};

  return (
    <>
      <PageHead title="Reports" sub="Rides and money by day, and captain earnings. Dates are in the service timezone." />
      <div className="toolbar">
        <label className="field"><span>From</span><input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
        <label className="field"><span>To</span><input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label>
        <button className="btn secondary" disabled={download.busy}
                onClick={() => download.run(() => downloadCsv("admin/reports/daily/", { from, to }, `daily-${from}-to-${to}.csv`))}>
          Download daily CSV
        </button>
        <button className="btn secondary" disabled={download.busy}
                onClick={() => download.run(() => downloadCsv("admin/reports/captain-earnings/", { from, to }, `captain-earnings-${from}-to-${to}.csv`))}>
          Download earnings CSV
        </button>
      </div>
      <ErrorBox message={daily.error || earnings.error || download.error} />

      <div className="stats">
        {[
          ["rides_completed", "Rides completed"], ["rides_cancelled", "Rides cancelled"], ["gross_fares", "Gross fares"],
          ["platform_share", "Platform ride share"], ["subscription_revenue", "Plan revenue"], ["ride_payments", "Online ride payments"],
          ["dues_collected", "Dues collected"], ["fee_revenue", "Cancellation fees"], ["discounts", "Promo discounts"],
        ].map(([key, name]) => (
          <div className="stat" key={key}>
            <div className="value">{MONEY.includes(key) ? money(totals[key] as string) : (totals[key] ?? 0)}</div>
            <div className="name">{name}</div>
          </div>
        ))}
      </div>

      <div className="grid two">
        <div className="card"><h2>Completed rides per day</h2><BarChart data={rows} labelKey="date" valueKey="rides_completed" /></div>
        <div className="card"><h2>Gross fares per day</h2>
          <BarChart data={rows} labelKey="date" valueKey="gross_fares" format={(v) => (v >= 1000 ? `₹${(v / 1000).toFixed(1)}k` : `₹${Math.round(v)}`)} />
        </div>
      </div>

      <h2 style={{ marginTop: 22 }}>By day</h2>
      <Table
        rows={[...rows].reverse()}
        rowKey={(r) => r.date}
        columns={[
          { key: "date", title: "Date", render: (r) => r.date },
          { key: "req", title: "Requested", className: "num", render: (r) => r.rides_requested },
          { key: "done", title: "Completed", className: "num", render: (r) => r.rides_completed },
          { key: "cxl", title: "Cancelled", className: "num", render: (r) => r.rides_cancelled },
          { key: "mix", title: "Bike / Auto", className: "num", render: (r) => `${r.bike_rides} / ${r.auto_rides}` },
          { key: "fares", title: "Gross fares", className: "num", render: (r) => money(r.gross_fares) },
          { key: "share", title: "Platform share", className: "num", render: (r) => money(r.platform_share) },
          { key: "plans", title: "Plans", className: "num", render: (r) => money(r.subscription_revenue) },
          { key: "online", title: "Online rides", className: "num", render: (r) => money(r.ride_payments) },
          { key: "dues", title: "Dues", className: "num", render: (r) => money(r.dues_collected) },
        ]}
      />

      <h2 style={{ marginTop: 22 }}>Captain earnings</h2>
      <Table
        rows={earnings.data?.rows ?? []}
        rowKey={(r) => r.captain_id}
        empty="No completed rides in this period."
        columns={[
          { key: "c", title: "Captain", render: (r) => <a href={`/captains/${r.captain_id}`}>{r.name || r.phone}</a> },
          { key: "p", title: "Phone", render: (r) => r.phone },
          { key: "n", title: "Rides", className: "num", render: (r) => r.completed_rides },
          { key: "f", title: "Fares", className: "num", render: (r) => money(r.fare_total) },
          { key: "s", title: "Platform share", className: "num", render: (r) => money(r.platform_share) },
          { key: "e", title: "Net earnings", className: "num", render: (r) => <strong>{money(r.net_earnings)}</strong> },
        ]}
      />
    </>
  );
}

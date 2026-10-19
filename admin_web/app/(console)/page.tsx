"use client";

import Link from "next/link";

import { BarChart, ErrorBox, Loading, PageHead, Stat } from "@/components/ui";
import { money } from "@/lib/format";
import type { DayRow } from "@/lib/types";
import { useApi } from "@/lib/useApi";

type Dashboard = { metrics: Record<string, string | number>; last_7_days: DayRow[] };

export default function DashboardPage() {
  const { data, error } = useApi<Dashboard>("admin/dashboard/", undefined, 15000);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const m = data.metrics;
  const n = (key: string) => Number(m[key]) || 0;

  return (
    <>
      <PageHead title="Dashboard" sub="Live operations. Refreshes every 15 seconds." />

      {n("open_sos") > 0 && (
        <div className="banner danger">
          <span>⚠ {n("open_sos")} unresolved SOS alert{n("open_sos") === 1 ? " needs" : "s need"} attention.</span>
          <Link href="/sos">Handle now →</Link>
        </div>
      )}

      <div className="stats">
        <Stat value={n("active_rides")} name="Active rides" href="/live" />
        <Stat value={n("online_captains")} name="Captains online" href="/captains?online_status=ONLINE" />
        <Stat value={n("busy_captains")} name="Captains on a ride" href="/captains?online_status=BUSY" />
        <Stat value={n("completed_today")} name="Completed today" />
        <Stat value={n("cancelled_today")} name="Cancelled today" />
        <Stat value={n("pending_kyc")} name="KYC to review" href="/captains?kyc_status=UNDER_REVIEW" />
        <Stat value={n("open_tickets")} name="Open complaints" href="/tickets?status=OPEN" />
        <Stat value={n("open_sos")} name="Unresolved SOS" href="/sos" alert={n("open_sos") > 0} />
        <Stat value={n("total_customers")} name="Customers" href="/customers" />
        <Stat value={n("total_captains")} name="Captains" href="/captains" />
        <Stat value={money(m.subscription_revenue)} name="Plan revenue (all time)" href="/subscriptions" />
        <Stat value={money(m.ride_revenue)} name="Online ride payments" href="/payments" />
        <Stat value={money(m.fee_revenue)} name="Cancellation fees" />
        <Stat value={money(m.pending_platform_dues)} name="Dues outstanding" href="/dues?status=PENDING" />
      </div>

      <div className="grid two">
        <div className="card">
          <h2>Completed rides, last 7 days</h2>
          <BarChart data={data.last_7_days} labelKey="date" valueKey="rides_completed" />
        </div>
        <div className="card">
          <h2>Gross fares, last 7 days</h2>
          <BarChart data={data.last_7_days} labelKey="date" valueKey="gross_fares"
                    format={(v) => (v >= 1000 ? `₹${(v / 1000).toFixed(1)}k` : `₹${Math.round(v)}`)} />
        </div>
      </div>
    </>
  );
}

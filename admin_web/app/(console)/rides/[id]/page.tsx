"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { use, useMemo } from "react";

import type { MapLine, MapMarker } from "@/components/MapView";
import { Badge, ErrorBox, Loading, PageHead, Table, useReasonDialog } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime, label, money } from "@/lib/format";
import type { RideDetail } from "@/lib/types";
import { useAction, useApi } from "@/lib/useApi";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

const CANCELLABLE = ["REQUESTED", "SEARCHING", "ACCEPTED", "CAPTAIN_ARRIVED"];

export default function RideDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const ride = useApi<RideDetail>(`admin/rides/${id}/`);
  const route = useApi<{ latitude: string; longitude: string; recorded_at: string }[]>(`admin/rides/${id}/route/`);
  const action = useAction();
  const { ask, dialog } = useReasonDialog();

  const { markers, lines } = useMemo(() => {
    const r = ride.data;
    if (!r) return { markers: [] as MapMarker[], lines: [] as MapLine[] };
    const markers: MapMarker[] = [
      { id: "p", position: [Number(r.pickup_latitude), Number(r.pickup_longitude)], color: "#1565c0", popup: "Pickup" },
      { id: "d", position: [Number(r.drop_latitude), Number(r.drop_longitude)], color: "#c62828", popup: "Drop" },
    ];
    const trail = (route.data ?? []).map((p) => [Number(p.latitude), Number(p.longitude)] as [number, number]);
    return { markers, lines: trail.length > 1 ? [{ id: "trail", points: trail, color: "#0b8f5a", weight: 4 }] : [] };
  }, [ride.data, route.data]);

  if (ride.error) return <ErrorBox message={ride.error} />;
  if (!ride.data) return <Loading />;
  const r = ride.data;

  async function cancel() {
    const reason = await ask({ title: "Cancel this ride?", message: "The rider and captain are both notified.",
      confirm: "Cancel ride", danger: true });
    if (reason === null) return;
    const done = await action.run(() => api(`admin/rides/${id}/cancel/`, { method: "POST", body: { reason } }));
    if (done) ride.reload();
  }

  async function waive() {
    const done = await action.run(() => api(`admin/rides/${id}/waive-fee/`, { method: "POST" }));
    if (done) ride.reload();
  }

  return (
    <>
      {dialog}
      <PageHead
        title={`Ride ${r.id.slice(0, 8)}`}
        sub={<><Badge value={r.status} /> · {r.vehicle_type} · requested {dateTime(r.requested_at)}</>}
        actions={<>
          {r.cancellation_fee_status === "UNPAID" && (
            <button className="btn secondary" disabled={action.busy} onClick={waive}>Waive ₹{r.cancellation_fee} fee</button>
          )}
          {CANCELLABLE.includes(r.status) && (
            <button className="btn danger" disabled={action.busy} onClick={cancel}>Cancel ride</button>
          )}
        </>}
      />
      <ErrorBox message={action.error} />

      <div className="grid two">
        <div className="card">
          <h2>Trip</h2>
          <dl className="kv">
            <dt>Pickup</dt><dd>{r.pickup_address}</dd>
            <dt>Drop</dt><dd>{r.drop_address}</dd>
            <dt>Distance</dt><dd>{r.estimated_distance_km} km · ~{r.estimated_duration_minutes} min</dd>
            <dt>Rider</dt><dd>{r.customer.name || "—"} · {r.customer.phone}</dd>
            <dt>Captain</dt><dd>{r.captain_id ? <Link href={`/captains/${r.captain_id}`}>{r.captain_name || r.captain_phone}</Link> : "—"}</dd>
            <dt>Start PIN</dt><dd>{r.start_pin_attempts} wrong attempt(s)</dd>
            {r.rating && <><dt>Rating</dt><dd>{"★".repeat(r.rating.rating)} {r.rating.comment}</dd></>}
          </dl>
        </div>
        <div className="card">
          <h2>Money</h2>
          <dl className="kv">
            <dt>Fare</dt><dd>{money(r.final_fare ?? r.estimated_fare)}</dd>
            <dt>Discount</dt><dd>{money(r.discount_amount)} {r.promo_code && <span className="badge brand">{r.promo_code}</span>}</dd>
            <dt>Rider pays</dt><dd><strong>{money(r.payable_fare)}</strong></dd>
            <dt>Payment</dt><dd>{r.payment_method} · <Badge value={r.payment_status} /></dd>
            <dt>Platform ride</dt><dd>{r.is_platform_ride ? `Yes (${label(r.share_reason)}, ${money(r.platform_share_amount)})` : "No"}</dd>
            {r.status === "CANCELLED" && <>
              <dt>Cancelled by</dt><dd>{label(r.cancelled_by)} · {label(r.cancellation_reason)}</dd>
              {r.cancellation_note && <><dt>Note</dt><dd>{r.cancellation_note}</dd></>}
              <dt>Fee</dt><dd>{money(r.cancellation_fee)} <Badge value={r.cancellation_fee_status} /></dd>
            </>}
          </dl>
        </div>
      </div>

      <div className="card">
        <h2>Route</h2>
        <MapView markers={markers} lines={lines} className="map small" />
        <p className="sub" style={{ marginBottom: 0 }}>{route.data?.length ?? 0} location point(s) recorded from the captain&apos;s app.</p>
      </div>

      <div className="grid two" style={{ marginTop: 16 }}>
        <div className="card">
          <h2>Timeline</h2>
          <ul className="timeline">
            {r.events.map((e) => (
              <li key={e.id}>
                <strong>{label(e.to_status)}</strong> <span className="sub">{dateTime(e.created_at)}</span>
                <div className="sub">{e.actor ? `${label(e.actor.role)} ${e.actor.phone}` : "System"}{e.note ? ` · ${e.note}` : ""}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2>Offers to captains</h2>
          <Table rows={r.offers} rowKey={(o) => o.id} empty="No captains were offered this ride."
                 columns={[
                   { key: "n", title: "#", render: (o) => o.sequence },
                   { key: "c", title: "Captain", render: (o) => <Link href={`/captains/${o.captain_id}`}>{o.captain_phone}</Link> },
                   { key: "d", title: "Distance", render: (o) => `${o.distance_km} km` },
                   { key: "s", title: "Result", render: (o) => <Badge value={o.status} /> },
                 ]} />
        </div>
      </div>
    </>
  );
}

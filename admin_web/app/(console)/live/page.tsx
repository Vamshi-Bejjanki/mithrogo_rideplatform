"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useMemo } from "react";

import type { MapLine, MapMarker } from "@/components/MapView";
import { esc } from "@/components/MapView";
import { Badge, ErrorBox, PageHead, Table } from "@/components/ui";
import { ago, money } from "@/lib/format";
import type { Ride } from "@/lib/types";
import { useApi } from "@/lib/useApi";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

type Live = {
  rides: Ride[];
  captains: { id: number; name: string; status: string; latitude: string; longitude: string; updated_at: string }[];
};

export default function LivePage() {
  const { data, error } = useApi<Live>("admin/rides/live/", undefined, 5000);

  const { markers, lines } = useMemo(() => {
    const markers: MapMarker[] = [];
    const lines: MapLine[] = [];
    data?.captains.forEach((c) =>
      markers.push({
        id: `c${c.id}`,
        position: [Number(c.latitude), Number(c.longitude)],
        color: c.status === "BUSY" ? "#e67700" : "#0b8f5a",
        radius: 8,
        popup: `<b>${esc(c.name)}</b><br>${esc(c.status)} · ${esc(ago(c.updated_at))}<br><a href="/captains/${c.id}">Open captain</a>`,
      }),
    );
    data?.rides.forEach((r) => {
      const pickup: [number, number] = [Number(r.pickup_latitude), Number(r.pickup_longitude)];
      const drop: [number, number] = [Number(r.drop_latitude), Number(r.drop_longitude)];
      const popup = `<b>${esc(r.status)}</b> · ${esc(r.vehicle_type)}<br>${esc(r.pickup_address)} → ${esc(r.drop_address)}<br><a href="/rides/${r.id}">Open ride</a>`;
      markers.push({ id: `p${r.id}`, position: pickup, color: "#1565c0", radius: 6, popup });
      markers.push({ id: `d${r.id}`, position: drop, color: "#c62828", radius: 6, popup });
      lines.push({ id: `l${r.id}`, points: [pickup, drop], color: "#555", dashed: true, weight: 2 });
    });
    return { markers, lines };
  }, [data]);

  return (
    <>
      <PageHead title="Live map" sub="Active rides and captains online. Updates every 5 seconds." />
      <ErrorBox message={error} />
      <div className="btn-row" style={{ marginBottom: 10, gap: 16 }}>
        <span><span className="badge ok">●</span> Online captain</span>
        <span><span className="badge warn">●</span> On a ride</span>
        <span><span className="badge info">●</span> Pickup</span>
        <span><span className="badge danger">●</span> Drop</span>
        <span className="sub">{data ? `${data.rides.length} active ride(s), ${data.captains.length} captain(s)` : "Loading…"}</span>
      </div>
      <MapView markers={markers} lines={lines} />
      <h2 style={{ marginTop: 22 }}>Active rides</h2>
      <Table
        rows={data?.rides ?? []}
        rowKey={(r) => r.id}
        empty="No rides in progress right now."
        columns={[
          { key: "status", title: "Status", render: (r) => <Badge value={r.status} /> },
          { key: "route", title: "Route", render: (r) => <Link href={`/rides/${r.id}`}>{r.pickup_address} → {r.drop_address}</Link> },
          { key: "rider", title: "Rider", render: (r) => r.customer.phone },
          { key: "captain", title: "Captain", render: (r) => r.captain_phone ?? <span className="sub">Searching</span> },
          { key: "loc", title: "Captain seen", render: (r) => ago(r.captain_location?.updated_at) },
          { key: "fare", title: "Fare", className: "num", render: (r) => money(r.payable_fare) },
        ]}
      />
    </>
  );
}

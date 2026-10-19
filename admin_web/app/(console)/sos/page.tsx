"use client";

import Link from "next/link";

import { Badge, ErrorBox, PageHead, Pager, Table, useReasonDialog } from "@/components/ui";
import { api } from "@/lib/api";
import { ago, dateTime, label } from "@/lib/format";
import type { Sos } from "@/lib/types";
import { useAction } from "@/lib/useApi";
import { usePagedList } from "@/lib/usePagedList";

export default function SosPage() {
  const list = usePagedList<Sos>("admin/sos/", { status: "" }, 50, 10000);
  const action = useAction();
  const { ask, dialog } = useReasonDialog();

  async function acknowledge(alert: Sos) {
    const done = await action.run(() => api(`admin/sos/${alert.id}/acknowledge/`, { method: "POST" }));
    if (done) list.reload();
  }

  async function resolve(alert: Sos) {
    const reason = await ask({ title: "Resolve SOS", message: "What happened? Saved on the alert and its ticket.",
      confirm: "Resolve" });
    if (reason === null) return;
    const done = await action.run(() => api(`admin/sos/${alert.id}/resolve/`, { method: "POST", body: { reason } }));
    if (done) list.reload();
  }

  return (
    <>
      {dialog}
      <PageHead title="SOS alerts" sub="Emergencies from riders and captains. Refreshes every 10 seconds. Call the user first." />
      <div className="toolbar">
        <label className="field"><span>Status</span>
          <select value={list.filters.status} onChange={(e) => list.setFilter("status", e.target.value)}>
            <option value="">Any</option><option value="OPEN">Open</option><option value="ACKNOWLEDGED">Acknowledged</option><option value="RESOLVED">Resolved</option>
          </select>
        </label>
      </div>
      <ErrorBox message={list.error || action.error} />
      <Table
        rows={list.rows}
        rowKey={(a) => a.id}
        empty={list.loading ? "Loading…" : "No SOS alerts. 🎉"}
        columns={[
          { key: "when", title: "Raised", render: (a) => <><div>{ago(a.created_at)}</div><div className="sub">{dateTime(a.created_at)}</div></> },
          { key: "status", title: "Status", render: (a) => <Badge value={a.status} /> },
          { key: "who", title: "Who", render: (a) => <><div>{a.user.name || "—"}</div><div className="sub">{a.user.phone} · {label(a.user.role)}</div></> },
          { key: "where", title: "Location", render: (a) => a.latitude ? (
            <a href={`https://www.openstreetmap.org/?mlat=${a.latitude}&mlon=${a.longitude}#map=17/${a.latitude}/${a.longitude}`} target="_blank" rel="noreferrer">Open map</a>
          ) : <span className="sub">Not sent</span> },
          { key: "ride", title: "Ride", render: (a) => a.ride_id ? <><Link href={`/rides/${a.ride_id}`}>{a.ride_id.slice(0, 8)}</Link> <Badge value={a.ride_status} /></> : "—" },
          { key: "note", title: "Note", render: (a) => a.note || a.resolution_note || "—" },
          { key: "by", title: "Handled by", render: (a) => a.handled_by?.name || a.handled_by?.phone || "—" },
          { key: "a", title: "", render: (a) => (
            <div className="btn-row">
              {a.status === "OPEN" && <button className="btn danger small" disabled={action.busy} onClick={() => acknowledge(a)}>Acknowledge</button>}
              {a.status !== "RESOLVED" && <button className="btn secondary small" disabled={action.busy} onClick={() => resolve(a)}>Resolve</button>}
              {a.ticket_id && <Link className="btn secondary small" href={`/tickets/${a.ticket_id}`}>Ticket</Link>}
            </div>
          ) },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

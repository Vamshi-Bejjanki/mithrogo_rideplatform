"use client";

import Link from "next/link";
import { use } from "react";

import { Badge, ErrorBox, Loading, PageHead, Pager, Table, useReasonDialog } from "@/components/ui";
import { api, Page } from "@/lib/api";
import { ago, dateTime, label, money } from "@/lib/format";
import type { CaptainDetail, Due, Ride } from "@/lib/types";
import { useAction, useApi } from "@/lib/useApi";
import { usePagedList } from "@/lib/usePagedList";

const IMAGE = /\.(jpe?g|png|webp|gif)(\?|$)/i;

export default function CaptainDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const captain = useApi<CaptainDetail>(`admin/captains/${id}/`);
  const rides = usePagedList<Ride>("admin/rides/", { captain: id }, 10);
  const dues = useApi<Page<Due>>("admin/dues/", { captain: id, status: "PENDING", limit: 50 });
  const action = useAction();
  const { ask, dialog } = useReasonDialog();

  if (captain.error) return <ErrorBox message={captain.error} />;
  if (!captain.data) return <Loading />;
  const c = captain.data;

  async function act(path: string, body?: unknown) {
    const done = await action.run(() => api(path, { method: "POST", body }));
    if (done !== undefined) captain.reload();
  }

  async function reject() {
    const reason = await ask({
      title: "Reject KYC", message: "The captain sees this reason in their app. Say what to fix.", confirm: "Reject",
      danger: true,
    });
    if (reason) await act(`admin/captains/${id}/reject/`, { reason });
  }

  return (
    <>
      {dialog}
      <PageHead
        title={c.user.name || c.user.phone}
        sub={<><Badge value={c.kyc_status} /> <Badge value={c.online_status} /> · {c.user.phone} · joined {dateTime(c.created_at)}</>}
        actions={<>
          {c.kyc_status !== "APPROVED" && c.kyc_status !== "SUSPENDED" && (
            <button className="btn" disabled={action.busy} onClick={() => act(`admin/captains/${id}/approve/`)}>Approve KYC</button>
          )}
          {c.kyc_status !== "REJECTED" && c.kyc_status !== "SUSPENDED" && (
            <button className="btn secondary" disabled={action.busy} onClick={reject}>Reject KYC</button>
          )}
          {c.kyc_status === "SUSPENDED" ? (
            <button className="btn" disabled={action.busy} onClick={() => act(`admin/captains/${id}/reactivate/`)}>Reactivate</button>
          ) : (
            <button className="btn danger" disabled={action.busy} onClick={() => act(`admin/captains/${id}/suspend/`)}>Suspend</button>
          )}
        </>}
      />
      <ErrorBox message={action.error} />
      {c.kyc_rejection_reason && c.kyc_status === "REJECTED" && (
        <div className="banner info">Rejected: {c.kyc_rejection_reason}</div>
      )}

      <div className="grid two">
        <div className="card">
          <h2>Profile</h2>
          <dl className="kv">
            <dt>Licence</dt><dd>{c.license_number || "—"} {c.license_expiry && <span className="sub">expires {c.license_expiry}</span>}</dd>
            <dt>Date of birth</dt><dd>{c.date_of_birth || "—"}</dd>
            <dt>Address</dt><dd>{c.address || "—"}</dd>
            <dt>Rating</dt><dd>{Number(c.rating) ? `★ ${c.rating}` : "No ratings yet"}</dd>
            <dt>Rides</dt><dd>{c.total_rides} completed · {c.cancelled_rides} cancelled after accepting</dd>
            <dt>Vehicle today</dt><dd>{c.day_vehicle_type ?? "Not chosen"}</dd>
            <dt>Last location</dt><dd>{c.current_latitude ? `${c.current_latitude}, ${c.current_longitude} · ${ago(c.last_location_at)}` : "—"}</dd>
          </dl>
        </div>
        <div className="card">
          <h2>Vehicles</h2>
          <Table rows={c.vehicles} rowKey={(v) => v.id} empty="No vehicles registered."
                 columns={[
                   { key: "t", title: "Type", render: (v) => v.vehicle_type },
                   { key: "r", title: "Registration", render: (v) => <span className="mono">{v.registration_number}</span> },
                   { key: "m", title: "Vehicle", render: (v) => [v.color, v.make, v.model].filter(Boolean).join(" ") || "—" },
                   { key: "s", title: "Verified", render: (v) => v.is_verified ? <Badge value="APPROVED" /> : <Badge value="PENDING" /> },
                   { key: "a", title: "", render: (v) => (
                     <button className="btn secondary small" disabled={action.busy}
                             onClick={() => act(`admin/vehicles/${v.id}/${v.is_verified ? "unverify" : "verify"}/`)}>
                       {v.is_verified ? "Unverify" : "Verify"}
                     </button>
                   ) },
                 ]} />
        </div>
      </div>

      <div className="card">
        <h2>KYC documents</h2>
        {c.documents.length === 0 ? <p className="sub">No documents uploaded yet.</p> : (
          <div className="docs">
            {c.documents.map((d) => {
              const url = d.file_url.replace(/^https?:\/\/[^/]+/, ""); // served through this app's /media proxy
              return (
                <a key={d.id} className="doc" href={url} target="_blank" rel="noreferrer">
                  {IMAGE.test(url) ? <img src={url} alt={label(d.doc_type)} /> : <div className="empty">📄 Open file</div>}
                  <div className="doc-label">{label(d.doc_type)}<div className="sub">{dateTime(d.created_at)}</div></div>
                </a>
              );
            })}
          </div>
        )}
      </div>

      <div className="card">
        <h2>Pending dues</h2>
        <Table rows={dues.data?.results ?? []} rowKey={(d) => d.id} empty="No pending dues."
               columns={[
                 { key: "t", title: "Type", render: (d) => label(d.due_type) },
                 { key: "a", title: "Amount", className: "num", render: (d) => money(d.amount) },
                 { key: "c", title: "Created", render: (d) => dateTime(d.created_at) },
               ]} />
        <p style={{ marginBottom: 0 }}><Link href={`/dues?captain=${id}`}>Manage dues →</Link></p>
      </div>

      <div className="card">
        <h2>Recent rides</h2>
        <Table rows={rides.rows} rowKey={(r) => r.id} empty="No rides yet."
               columns={[
                 { key: "w", title: "Requested", render: (r) => <Link href={`/rides/${r.id}`}>{dateTime(r.requested_at)}</Link> },
                 { key: "s", title: "Status", render: (r) => <Badge value={r.status} /> },
                 { key: "r", title: "Route", render: (r) => `${r.pickup_address} → ${r.drop_address}` },
                 { key: "f", title: "Fare", className: "num", render: (r) => money(r.final_fare ?? r.estimated_fare) },
               ]} />
        <Pager count={rides.count} offset={rides.offset} limit={rides.limit} onChange={rides.setOffset} />
      </div>
    </>
  );
}

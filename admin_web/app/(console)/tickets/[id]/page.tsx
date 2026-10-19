"use client";

import Link from "next/link";
import { FormEvent, use, useState } from "react";

import { Badge, ErrorBox, Loading, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime, label } from "@/lib/format";
import type { TicketDetail } from "@/lib/types";
import { useAction, useApi } from "@/lib/useApi";

export default function TicketPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const ticket = useApi<TicketDetail>(`admin/tickets/${id}/`, undefined, 20000);
  const action = useAction();
  const [reply, setReply] = useState("");
  const [note, setNote] = useState("");

  if (ticket.error) return <ErrorBox message={ticket.error} />;
  if (!ticket.data) return <Loading />;
  const t = ticket.data;

  async function send(event: FormEvent) {
    event.preventDefault();
    const done = await action.run(() => api(`admin/tickets/${id}/reply/`, { method: "POST", body: { body: reply } }));
    if (done) {
      setReply("");
      ticket.reload();
    }
  }

  async function setStatus(status: string) {
    const done = await action.run(() => api(`admin/tickets/${id}/status/`, { method: "POST", body: { status, note } }));
    if (done) {
      setNote("");
      ticket.reload();
    }
  }

  return (
    <>
      <PageHead
        title={`Ticket #${t.id}`}
        sub={<><Badge value={t.status} /> · {label(t.category)} {t.is_sos && <span className="badge danger">SOS</span>} · opened {dateTime(t.created_at)}</>}
      />
      <ErrorBox message={action.error} />
      <div className="grid two">
        <div className="card">
          <h2>Issue</h2>
          <p style={{ whiteSpace: "pre-wrap", marginTop: 0 }}>{t.description}</p>
          <dl className="kv">
            <dt>From</dt><dd>{t.user.name || "—"} · {t.user.phone} ({label(t.user.role)})</dd>
            <dt>Ride</dt><dd>{t.ride_id ? <Link href={`/rides/${t.ride_id}`}>{t.ride_id.slice(0, 8)}</Link> : "Not about a ride"}</dd>
            {t.resolution_note && <><dt>Resolution</dt><dd>{t.resolution_note}</dd></>}
          </dl>
        </div>
        <div className="card">
          <h2>Status</h2>
          <label className="field" style={{ marginBottom: 10 }}>
            <span>Note to the user (optional, shown when resolving)</span>
            <textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <div className="btn-row">
            {t.status !== "IN_PROGRESS" && <button className="btn secondary" disabled={action.busy} onClick={() => setStatus("IN_PROGRESS")}>Mark in progress</button>}
            {t.status !== "RESOLVED" && <button className="btn" disabled={action.busy} onClick={() => setStatus("RESOLVED")}>Resolve</button>}
            {t.status !== "CLOSED" && <button className="btn secondary" disabled={action.busy} onClick={() => setStatus("CLOSED")}>Close</button>}
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Conversation</h2>
        {t.messages.length === 0 ? <p className="sub">No replies yet.</p> : (
          <div className="messages">
            {t.messages.map((m) => (
              <div key={m.id} className={`msg ${m.is_staff ? "staff" : ""}`}>
                <div className="meta">{m.is_staff ? `Support · ${m.author?.name || m.author?.phone || ""}` : t.user.phone} · {dateTime(m.created_at)}</div>
                <div style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
              </div>
            ))}
          </div>
        )}
        <form onSubmit={send} style={{ marginTop: 16 }}>
          <textarea rows={3} value={reply} onChange={(e) => setReply(e.target.value)} placeholder="Write a reply. The user gets it in the app." />
          <div className="btn-row" style={{ justifyContent: "flex-end", marginTop: 8 }}>
            <button className="btn" disabled={action.busy || !reply.trim()}>Send reply</button>
          </div>
        </form>
      </div>
    </>
  );
}

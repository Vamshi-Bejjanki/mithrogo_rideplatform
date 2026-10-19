"use client";

import { FormEvent, useState } from "react";

import { ErrorBox, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { useAction } from "@/lib/useApi";

export default function BroadcastPage() {
  const [audience, setAudience] = useState("CUSTOMERS");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState<number | null>(null);
  const action = useAction();

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!window.confirm("Send this announcement now? It cannot be recalled.")) return;
    setSent(null);
    const result = await action.run(() =>
      api<{ recipients: number }>("admin/broadcast/", { method: "POST", body: { audience, title, message } }),
    );
    if (result) {
      setSent(result.recipients);
      setTitle("");
      setMessage("");
    }
  }

  return (
    <>
      <PageHead title="Announcements" sub="Send an in-app notification (and a push, once push is set up) to every active user in a group." />
      <form className="card" onSubmit={submit} style={{ maxWidth: 640 }}>
        {sent !== null && <div className="notice">Sent to {sent} user(s).</div>}
        <ErrorBox message={action.error} />
        <label className="field" style={{ marginBottom: 12 }}>
          <span>Audience</span>
          <select value={audience} onChange={(e) => setAudience(e.target.value)}>
            <option value="CUSTOMERS">All customers</option>
            <option value="CAPTAINS">All captains</option>
            <option value="ALL">Everyone</option>
          </select>
        </label>
        <label className="field" style={{ marginBottom: 12 }}>
          <span>Title</span>
          <input value={title} maxLength={120} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className="field" style={{ marginBottom: 12 }}>
          <span>Message ({message.length}/500)</span>
          <textarea rows={4} value={message} maxLength={500} onChange={(e) => setMessage(e.target.value)} required />
        </label>
        <button className="btn" disabled={action.busy}>{action.busy ? "Sending…" : "Send announcement"}</button>
      </form>
    </>
  );
}

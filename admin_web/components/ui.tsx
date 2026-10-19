"use client";

import { ReactNode, useEffect, useState } from "react";

import { label } from "@/lib/format";

const TONE: Record<string, string> = {
  COMPLETED: "ok", APPROVED: "ok", SUCCESS: "ok", RESOLVED: "ok", ACTIVE: "ok", SETTLED: "ok", PAID: "ok",
  ONLINE: "ok", APPLIED: "ok", CLOSED: "ok",
  CANCELLED: "danger", REJECTED: "danger", FAILED: "danger", SUSPENDED: "danger", OPEN: "danger", UNPAID: "warn",
  EXPIRED: "warn", PENDING: "warn", UNDER_REVIEW: "warn", IN_PROGRESS: "info", ACKNOWLEDGED: "warn",
  SEARCHING: "warn", REQUESTED: "warn", ACCEPTED: "info", CAPTAIN_ARRIVED: "info", STARTED: "brand", BUSY: "brand",
  WAIVED: "", OFFLINE: "", NONE: "",
};

export function Badge({ value, tone }: { value: string | null | undefined; tone?: string }) {
  if (!value) return <span className="sub">—</span>;
  return <span className={`badge ${tone ?? TONE[value] ?? ""}`}>{label(value)}</span>;
}

export function PageHead({ title, sub, actions }: { title: string; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {sub && <p>{sub}</p>}
      </div>
      {actions && <div className="btn-row">{actions}</div>}
    </div>
  );
}

export function ErrorBox({ message }: { message: string | null | undefined }) {
  return message ? <div className="alert-box">{message}</div> : null;
}

export function Loading() {
  return <div className="empty">Loading…</div>;
}

export type Column<T> = { key: string; title: string; render: (row: T) => ReactNode; className?: string };

export function Table<T>({ rows, columns, empty = "Nothing here yet.", rowKey }: {
  rows: T[]; columns: Column<T>[]; empty?: string; rowKey: (row: T) => string | number;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c.key} className={c.className}>{c.title}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={columns.length} className="empty">{empty}</td></tr>
          ) : (
            rows.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((c) => <td key={c.key} className={c.className}>{c.render(row)}</td>)}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Pager({ count, offset, limit, onChange }: {
  count: number; offset: number; limit: number; onChange: (offset: number) => void;
}) {
  if (count <= limit) return <div className="pager"><span>{count} result{count === 1 ? "" : "s"}</span></div>;
  return (
    <div className="pager">
      <span>{offset + 1}–{Math.min(offset + limit, count)} of {count}</span>
      <div className="btn-row">
        <button className="btn secondary small" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>
          Previous
        </button>
        <button className="btn secondary small" disabled={offset + limit >= count} onClick={() => onChange(offset + limit)}>
          Next
        </button>
      </div>
    </div>
  );
}

/** Asks for a reason (or note) before an action. Resolves with the text, or null if cancelled. */
export function ReasonDialog({ open, title, message, confirm = "Confirm", required = true, danger = false, onClose }: {
  open: boolean; title: string; message?: string; confirm?: string; required?: boolean; danger?: boolean;
  onClose: (reason: string | null) => void;
}) {
  const [text, setText] = useState("");
  useEffect(() => { if (open) setText(""); }, [open]);
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={() => onClose(null)}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <h2>{title}</h2>
        {message && <p>{message}</p>}
        <textarea rows={3} autoFocus value={text} onChange={(e) => setText(e.target.value)}
                  placeholder={required ? "Reason (required)" : "Note (optional)"} />
        <div className="btn-row" style={{ justifyContent: "flex-end", marginTop: 14 }}>
          <button className="btn secondary" onClick={() => onClose(null)}>Cancel</button>
          <button className={`btn ${danger ? "danger" : ""}`} disabled={required && !text.trim()}
                  onClick={() => onClose(text.trim())}>{confirm}</button>
        </div>
      </div>
    </div>
  );
}

/** Small promise-based wrapper so pages can `await ask(...)`. */
export function useReasonDialog() {
  const [state, setState] = useState<null | {
    title: string; message?: string; confirm?: string; required?: boolean; danger?: boolean;
    resolve: (v: string | null) => void;
  }>(null);
  const ask = (opts: { title: string; message?: string; confirm?: string; required?: boolean; danger?: boolean }) =>
    new Promise<string | null>((resolve) => setState({ ...opts, resolve }));
  const dialog = (
    <ReasonDialog open={Boolean(state)} title={state?.title ?? ""} message={state?.message} confirm={state?.confirm}
                  required={state?.required ?? true} danger={state?.danger}
                  onClose={(v) => { state?.resolve(v); setState(null); }} />
  );
  return { ask, dialog };
}

export function BarChart({ data, valueKey, labelKey, format }: {
  data: Record<string, string | number>[]; valueKey: string; labelKey: string; format?: (v: number) => string;
}) {
  const values = data.map((d) => Number(d[valueKey]) || 0);
  const max = Math.max(...values, 1);
  return (
    <>
      <div className="bars">
        {data.map((d, i) => (
          <div className="col" key={String(d[labelKey])} title={`${d[labelKey]}: ${format ? format(values[i]) : values[i]}`}>
            <span className="n">{format ? format(values[i]) : values[i]}</span>
            <div className="bar" style={{ height: `${(values[i] / max) * 100}%` }} />
          </div>
        ))}
      </div>
      <div className="bar-labels">{data.map((d) => <span key={String(d[labelKey])}>{String(d[labelKey]).slice(5)}</span>)}</div>
    </>
  );
}

export function Stat({ value, name, href, alert }: { value: ReactNode; name: string; href?: string; alert?: boolean }) {
  const body = <><div className="value">{value}</div><div className="name">{name}</div></>;
  return href
    ? <a className={`stat ${alert ? "alert" : ""}`} href={href}>{body}</a>
    : <div className={`stat ${alert ? "alert" : ""}`}>{body}</div>;
}

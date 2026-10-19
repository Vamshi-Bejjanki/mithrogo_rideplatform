"use client";

import { ErrorBox, PageHead, Pager, Table } from "@/components/ui";
import { dateTime } from "@/lib/format";
import type { AuditEntry } from "@/lib/types";
import { usePagedList } from "@/lib/usePagedList";

export default function AuditPage() {
  const list = usePagedList<AuditEntry>("admin/audit-log/", { search: "" });

  return (
    <>
      <PageHead title="Audit log" sub="Every admin change, from this app and from Django Admin. Read-only." />
      <div className="toolbar">
        <label className="field"><span>Search</span>
          <input value={list.filters.search} onChange={(e) => list.setFilter("search", e.target.value)} placeholder="Action, object ID, admin phone" />
        </label>
      </div>
      <ErrorBox message={list.error} />
      <Table
        rows={list.rows}
        rowKey={(e) => e.id}
        empty={list.loading ? "Loading…" : "No entries."}
        columns={[
          { key: "when", title: "When", render: (e) => dateTime(e.created_at) },
          { key: "who", title: "Admin", render: (e) => e.actor?.name || e.actor?.phone || "System" },
          { key: "action", title: "Action", render: (e) => <span className="mono">{e.action}</span> },
          { key: "obj", title: "Object", render: (e) => <span className="mono">{e.model} #{e.object_id.slice(0, 12)}</span> },
          { key: "changes", title: "Changes", render: (e) => Object.keys(e.changes || {}).length
            ? <span className="mono sub">{JSON.stringify(e.changes).slice(0, 160)}</span> : "—" },
        ]}
      />
      <Pager count={list.count} offset={list.offset} limit={list.limit} onChange={list.setOffset} />
    </>
  );
}

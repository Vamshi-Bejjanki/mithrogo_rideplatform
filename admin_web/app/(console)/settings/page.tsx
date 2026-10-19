"use client";

import { useEffect, useState } from "react";

import { ErrorBox, Loading, PageHead } from "@/components/ui";
import { api } from "@/lib/api";
import { dateTime, label } from "@/lib/format";
import type { Fare, Plan } from "@/lib/types";
import { useAction, useApi } from "@/lib/useApi";

type Config = Record<string, string | number | boolean>;

const CONFIG_GROUPS: { title: string; fields: [string, string][] }[] = [
  { title: "Matching and pricing", fields: [
    ["search_radius_km", "Search radius (km)"], ["offer_timeout_seconds", "Offer timeout (seconds)"],
    ["max_offer_attempts", "Captains offered per ride"], ["location_freshness_seconds", "Location freshness (seconds)"],
    ["road_distance_factor", "Road distance factor"], ["average_speed_kmph", "Average speed (km/h)"],
    ["min_trip_km", "Minimum trip (km)"],
  ] },
  { title: "Captain plans", fields: [
    ["unpaid_dues_limit", "Unpaid dues limit (₹)"], ["service_timezone", "Service timezone"],
    ["plan_expiry_reminder_minutes", "Plan expiry reminder (minutes before)"],
  ] },
  { title: "Ride safety", fields: [
    ["require_start_pin", "Require ride start PIN"], ["start_pin_max_attempts", "Wrong PIN attempts allowed"],
    ["share_link_grace_minutes", "Trip share link grace (minutes)"],
  ] },
  { title: "Cancellations", fields: [
    ["customer_cancel_fee", "Rider cancellation fee (₹, 0 = off)"], ["cancel_free_window_seconds", "Free cancellation window (seconds)"],
    ["customer_no_show_fee", "Rider no-show fee (₹, 0 = off)"], ["no_show_wait_minutes", "No-show wait (minutes)"],
    ["block_booking_on_unpaid_fees", "Block booking while fees are unpaid"],
  ] },
  { title: "Referrals", fields: [
    ["referral_referee_reward", "New rider reward (₹, 0 = off)"], ["referral_referrer_reward", "Referrer reward (₹, 0 = off)"],
    ["referral_reward_valid_days", "Reward validity (days)"],
  ] },
];

function ConfigEditor() {
  const config = useApi<Config>("admin/config/");
  const action = useAction();
  const [draft, setDraft] = useState<Config>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => { if (config.data) setDraft(config.data); }, [config.data]);
  if (!config.data) return config.error ? <ErrorBox message={config.error} /> : <Loading />;

  const changed = Object.keys(draft).filter((k) => String(draft[k]) !== String(config.data![k]));

  async function save() {
    setSaved(false);
    const body = Object.fromEntries(changed.map((k) => [k, draft[k]]));
    const result = await action.run(() => api<Config>("admin/config/", { method: "PATCH", body }));
    if (result) {
      config.setData(result);
      setSaved(true);
    }
  }

  return (
    <div className="card">
      <div className="page-head" style={{ marginBottom: 6 }}>
        <h2 style={{ margin: 0 }}>Platform configuration</h2>
        <button className="btn" disabled={!changed.length || action.busy} onClick={save}>
          {changed.length ? `Save ${changed.length} change(s)` : "No changes"}
        </button>
      </div>
      <p className="sub" style={{ marginTop: 0 }}>Takes effect on the next request. Every change is recorded in the audit log. Last saved {dateTime(String(config.data.updated_at))}.</p>
      {saved && <div className="notice">Saved.</div>}
      <ErrorBox message={action.error} />
      {CONFIG_GROUPS.map((group) => (
        <div key={group.title} style={{ marginTop: 14 }}>
          <h3>{group.title}</h3>
          <div className="form-grid">
            {group.fields.map(([key, name]) =>
              typeof config.data![key] === "boolean" ? (
                <label key={key} className="check">
                  <input type="checkbox" checked={Boolean(draft[key])} onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.checked }))} /> {name}
                </label>
              ) : (
                <label key={key} className="field"><span>{name}</span>
                  <input value={String(draft[key] ?? "")} onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.value }))} />
                </label>
              ),
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function RowEditor<T extends { id: number }>({ path, row, fields, title, onSaved }: {
  path: string; row: T; fields: [keyof T & string, string][]; title: string; onSaved: () => void;
}) {
  const [draft, setDraft] = useState<Record<string, string | boolean>>({});
  const action = useAction();
  const value = (k: string) => (k in draft ? draft[k] : (row as Record<string, unknown>)[k]);
  const changed = Object.keys(draft).filter((k) => String(draft[k]) !== String((row as Record<string, unknown>)[k]));

  async function save() {
    const body = Object.fromEntries(changed.map((k) => [k, draft[k] === "" ? null : draft[k]]));
    const done = await action.run(() => api(`${path}${row.id}/`, { method: "PATCH", body }));
    if (done) { setDraft({}); onSaved(); }
  }

  return (
    <div style={{ borderTop: "1px solid var(--line)", paddingTop: 12, marginTop: 12 }}>
      <div className="page-head" style={{ marginBottom: 8 }}>
        <strong>{title}</strong>
        <button className="btn small" disabled={!changed.length || action.busy} onClick={save}>Save</button>
      </div>
      <ErrorBox message={action.error} />
      <div className="form-grid">
        {fields.map(([key, name]) =>
          typeof (row as Record<string, unknown>)[key] === "boolean" ? (
            <label key={key} className="check">
              <input type="checkbox" checked={Boolean(value(key))} onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.checked }))} /> {name}
            </label>
          ) : (
            <label key={key} className="field"><span>{name}</span>
              <input value={String(value(key) ?? "")} onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.value }))} />
            </label>
          ),
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const fares = useApi<Fare[]>("admin/fares/");
  const plans = useApi<Plan[]>("admin/plans/");

  return (
    <>
      <PageHead title="Pricing & config" sub="Fares, captain plans and platform rules. Nothing here is hard-coded in the apps." />
      <div className="card">
        <h2>Fares</h2>
        <ErrorBox message={fares.error} />
        {fares.data?.map((fare) => (
          <RowEditor key={fare.id} path="admin/fares/" row={fare} title={`${label(fare.vehicle_type)} fares`} onSaved={fares.reload}
                     fields={[["base_fare", "Base fare (₹)"], ["per_km", "Per km (₹)"], ["minimum_fare", "Minimum fare (₹)"],
                              ["platform_customer_fee", "Platform fee (₹)"], ["is_active", "Active"]]} />
        ))}
      </div>
      <div className="card">
        <h2>Captain plans</h2>
        <ErrorBox message={plans.error} />
        {plans.data?.map((plan) => (
          <RowEditor key={plan.id} path="admin/plans/" row={plan} title={`${plan.name} (${plan.code})`} onSaved={plans.reload}
                     fields={plan.plan_type === "DAILY_FLAT"
                       ? [["name", "Name"], ["amount", "Price (₹)"], ["duration_hours", "Duration (hours)"], ["is_active", "Active"]]
                       : [["name", "Name"], ["qualifying_rides", "Qualifying rides"], ["shortfall_fee", "Shortfall fee (₹)"], ["is_active", "Active"]]} />
        ))}
      </div>
      <ConfigEditor />
    </>
  );
}

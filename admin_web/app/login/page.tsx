"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { ApiError, login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const digits = phone.replace(/[\s-]/g, "");
      await login(/^\d{10}$/.test(digits) ? `+91${digits}` : digits, password);
      router.replace("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not sign in.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="brand">
          <span className="brand-mark">🛵</span> MithroGo Admin
        </div>
        <h2>Sign in</h2>
        <p className="sub" style={{ marginTop: -6, marginBottom: 16 }}>
          Admin accounts only. Use the phone number and password set with <span className="mono">createsuperuser</span>.
        </p>
        {error && <div className="alert-box">{error}</div>}
        <label className="field" style={{ marginBottom: 12 }}>
          <span>Phone number</span>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98765 43210"
                 autoComplete="username" required />
        </label>
        <label className="field" style={{ marginBottom: 18 }}>
          <span>Password</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 autoComplete="current-password" required />
        </label>
        <button className="btn" style={{ width: "100%" }} disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

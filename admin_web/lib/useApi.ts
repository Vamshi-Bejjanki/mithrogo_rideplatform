"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api, ApiError } from "./api";

type Query = Record<string, string | number | undefined | null>;

/** GET a path and keep it fresh. `reload()` refetches; `refreshMs` polls. */
export function useApi<T>(path: string | null, query?: Query, refreshMs?: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(path));
  const key = JSON.stringify([path, query]);
  const latest = useRef(key);

  const load = useCallback(async () => {
    if (!path) return;
    latest.current = key;
    setLoading(true);
    try {
      const result = await api<T>(path, { query });
      if (latest.current === key) {
        setData(result);
        setError(null);
      }
    } catch (e) {
      if (latest.current === key) setError(e instanceof ApiError ? e.message : "Something went wrong.");
    } finally {
      if (latest.current === key) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    load();
    if (!refreshMs) return;
    const id = setInterval(load, refreshMs);
    return () => clearInterval(id);
  }, [load, refreshMs]);

  return { data, error, loading, reload: load, setData };
}

/** Run a mutating call with a busy flag and an error message. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong.");
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);

  return { busy, error, setError, run };
}

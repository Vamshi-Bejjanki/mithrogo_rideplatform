// Thin client for the Django admin API. Same-origin: Next rewrites /api/v1/* to the backend.

const BASE = "/api/v1/";
const ACCESS_KEY = "mg_admin_access";
const REFRESH_KEY = "mg_admin_refresh";
const USER_KEY = "mg_admin_user";

export type AdminUser = { id: string; phone: string; first_name: string; last_name: string; role: string };

export class ApiError extends Error {
  status: number;
  code?: string;
  fields: Record<string, string>;

  constructor(status: number, message: string, code?: string, fields: Record<string, string> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

export const session = {
  get access() {
    return storage()?.getItem(ACCESS_KEY) ?? null;
  },
  get refresh() {
    return storage()?.getItem(REFRESH_KEY) ?? null;
  },
  get user(): AdminUser | null {
    const raw = storage()?.getItem(USER_KEY);
    try {
      return raw ? (JSON.parse(raw) as AdminUser) : null;
    } catch {
      return null;
    }
  },
  save(access: string, refresh: string, user?: AdminUser) {
    const s = storage();
    s?.setItem(ACCESS_KEY, access);
    s?.setItem(REFRESH_KEY, refresh);
    if (user) s?.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    const s = storage();
    [ACCESS_KEY, REFRESH_KEY, USER_KEY].forEach((k) => s?.removeItem(k));
  },
};

let onExpired: () => void = () => {};
export function setSessionExpiredHandler(handler: () => void) {
  onExpired = handler;
}

/** "rides/" + {status: "X"} -> "/api/v1/rides/?status=X". Paths always end in "/" like Django's. */
export function apiUrl(path: string, query?: Record<string, string | number | undefined | null>) {
  const [p, existing] = path.split("?");
  let url = BASE + p.replace(/^\//, "");
  if (!url.endsWith("/")) url += "/";
  const params = new URLSearchParams(existing || "");
  Object.entries(query || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  });
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

async function parseError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    /* not JSON */
  }
  if (body && typeof body === "object") {
    const data = body as Record<string, unknown>;
    if (typeof data.detail === "string") {
      return new ApiError(response.status, data.detail, typeof data.code === "string" ? data.code : undefined);
    }
    const fields: Record<string, string> = {};
    Object.entries(data).forEach(([k, v]) => {
      if (Array.isArray(v) && v.length) fields[k] = String(v[0]);
      else if (typeof v === "string") fields[k] = v;
    });
    const first = Object.entries(fields)[0];
    if (first) return new ApiError(response.status, `${first[0]}: ${first[1]}`, "validation_error", fields);
  }
  if (response.status === 403) return new ApiError(403, "You do not have access to this.");
  if (response.status === 404) return new ApiError(404, "Not found.");
  return new ApiError(response.status, "Something went wrong. Please try again.");
}

let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh = session.refresh;
  if (!refresh) return false;
  try {
    const response = await fetch(apiUrl("auth/refresh/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!response.ok) return false;
    const data = await response.json();
    session.save(data.access, data.refresh ?? refresh);
    return true;
  } catch {
    return false;
  }
}

type Options = { method?: string; body?: unknown; query?: Record<string, string | number | undefined | null> };

export async function rawRequest(path: string, options: Options = {}, retried = false): Promise<Response> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const token = session.access;
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(apiUrl(path, options.query), {
      method: options.method || "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check that the backend is running.");
  }

  if (response.status === 401 && !retried && session.refresh) {
    refreshing ??= refreshTokens().finally(() => {
      refreshing = null;
    });
    if (await refreshing) return rawRequest(path, options, true);
    session.clear();
    onExpired();
  }
  if (!response.ok) throw await parseError(response);
  return response;
}

export async function api<T = unknown>(path: string, options: Options = {}): Promise<T> {
  const response = await rawRequest(path, options);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Download a CSV (authenticated) by fetching it and saving the blob. */
export async function downloadCsv(path: string, query: Record<string, string>, filename: string) {
  const response = await rawRequest(path, { query: { ...query, export: "csv" } });
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

export async function login(phone: string, password: string): Promise<AdminUser> {
  const data = await api<{ user: AdminUser; access: string; refresh: string }>("auth/admin/login/", {
    method: "POST",
    body: { phone, password },
  });
  session.save(data.access, data.refresh, data.user);
  return data.user;
}

export async function logout() {
  const refresh = session.refresh;
  if (refresh) {
    try {
      await api("auth/logout/", { method: "POST", body: { refresh } });
    } catch {
      /* already invalid */
    }
  }
  session.clear();
}

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };

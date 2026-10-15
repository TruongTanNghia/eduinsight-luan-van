"use client";
// Gọi API backend /api/v1 (proxy qua next.config rewrites). Mọi hook trả về { data, error, loading, reload }.
import { useCallback, useEffect, useState } from "react";

export const API = "/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!r.ok) throw new ApiError(r.status, await readError(r));
  return r.json();
}

export async function apiSend<T>(path: string, method: "POST" | "DELETE", body?: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, { method, headers: body instanceof FormData ? undefined : { "Content-Type": "application/json" }, body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new ApiError(r.status, await readError(r));
  return r.json();
}

async function readError(r: Response) {
  try {
    const j = await r.json();
    return typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
  } catch {
    return `${r.status} ${r.statusText}`;
  }
}

export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!!path);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!path) { setData(null); setLoading(false); return; }
    let alive = true;
    setLoading(true);
    setError(null);
    apiGet<T>(path)
      .then((d) => { if (alive) setData(d); })
      .catch((e: Error) => { if (alive) setError(e.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [path, tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload };
}

export type Period = { key: string; grade: number; ky: number; kind: string; label: string; short: string; year: string };
export type Meta = { datasetVersion: string; updated: string; threshold: number; periods: Period[]; seq: string[]; defaultPeriod: string; hasSemesters: boolean; classes: string[]; classesByPeriod: Record<string, string[]>; subjects: { key: string; name: string; short: string }[]; students: number; school: string; showNames: boolean };

export function useMeta() {
  return useApi<Meta>("/meta");
}

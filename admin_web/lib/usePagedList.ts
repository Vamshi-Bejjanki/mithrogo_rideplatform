"use client";

import { useState } from "react";

import type { Page } from "./api";
import { useApi } from "./useApi";

/** A paged admin list with filters. Changing a filter goes back to the first page. */
export function usePagedList<T>(path: string, initial: Record<string, string> = {}, limit = 50, refreshMs?: number) {
  const [filters, setFilters] = useState<Record<string, string>>(initial);
  const [offset, setOffset] = useState(0);
  const result = useApi<Page<T>>(path, { ...filters, limit, offset }, refreshMs);

  return {
    ...result,
    rows: result.data?.results ?? [],
    count: result.data?.count ?? 0,
    filters,
    offset,
    limit,
    setOffset,
    setFilter: (key: string, value: string) => {
      setOffset(0);
      setFilters((f) => ({ ...f, [key]: value }));
    },
  };
}

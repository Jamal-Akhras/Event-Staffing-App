import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, fetchWorker } from "../../lib/api";
import type { FeedShift, Market, WorkerFeedPage } from "../../types";
import type { ShiftFilter } from "./browseUtils";

const PAGE_LIMIT = 20;
const SEARCH_DEBOUNCE_MS = 350;

export type FeedStatus = "loading" | "ready" | "error" | "missing-market";

type FeedFilters = { query: string; filter: ShiftFilter };

export function useWorkerFeed() {
  const [items, setItems] = useState<FeedShift[]>([]);
  const [market, setMarket] = useState<Market | null>(null);
  const [status, setStatus] = useState<FeedStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<ShiftFilter>("all");

  const requestSeq = useRef(0);
  const nextCursorRef = useRef<string | null>(null);
  const loadingMoreRef = useRef(false);
  const marketRef = useRef<Market | null>(null);
  const filtersRef = useRef<FeedFilters>({ query: "", filter: "all" });
  const lastQueryRef = useRef("");

  const runFirstPage = useCallback(async (asRefresh: boolean) => {
    const seq = ++requestSeq.current;
    loadingMoreRef.current = false;
    setIsLoadingMore(false);
    if (asRefresh) {
      setIsRefreshing(true);
    } else {
      setStatus("loading");
      setItems([]);
      nextCursorRef.current = null;
      setHasMore(false);
    }
    try {
      const page = await fetchWorker<WorkerFeedPage>(
        buildFeedPath(filtersRef.current, null, marketRef.current)
      );
      if (seq !== requestSeq.current) return;
      setItems(dedupeById(page.items));
      nextCursorRef.current = page.next_cursor;
      setHasMore(page.next_cursor !== null);
      marketRef.current = page.market;
      setMarket(page.market);
      setError(null);
      setStatus("ready");
    } catch (err) {
      if (seq !== requestSeq.current) return;
      if ((err as ApiError).status === 409) {
        setItems([]);
        nextCursorRef.current = null;
        setHasMore(false);
        setError(null);
        setStatus("missing-market");
      } else {
        setError((err as Error).message);
        setStatus("error");
      }
    } finally {
      if (seq === requestSeq.current && asRefresh) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    filtersRef.current = { query: searchQuery, filter: activeFilter };
    const queryChanged = searchQuery !== lastQueryRef.current;
    lastQueryRef.current = searchQuery;
    const timer = setTimeout(
      () => void runFirstPage(false),
      queryChanged ? SEARCH_DEBOUNCE_MS : 0
    );
    return () => clearTimeout(timer);
  }, [searchQuery, activeFilter, runFirstPage]);

  const loadMore = useCallback(async () => {
    if (loadingMoreRef.current || !nextCursorRef.current) return;
    const seq = requestSeq.current;
    loadingMoreRef.current = true;
    setIsLoadingMore(true);
    try {
      const page = await fetchWorker<WorkerFeedPage>(
        buildFeedPath(filtersRef.current, nextCursorRef.current, marketRef.current)
      );
      if (seq !== requestSeq.current) return;
      setItems((current) => appendUnique(current, page.items));
      nextCursorRef.current = page.next_cursor;
      setHasMore(page.next_cursor !== null);
      marketRef.current = page.market;
      setMarket(page.market);
    } catch (err) {
      if (seq === requestSeq.current) setError((err as Error).message);
    } finally {
      loadingMoreRef.current = false;
      setIsLoadingMore(false);
    }
  }, []);

  const refresh = useCallback(() => runFirstPage(true), [runFirstPage]);
  const retry = useCallback(() => runFirstPage(false), [runFirstPage]);

  const removeItem = useCallback((shiftId: string) => {
    setItems((current) => current.filter((item) => item.shift_id !== shiftId));
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    activeFilter,
    clearError,
    error,
    hasMore,
    isLoadingMore,
    isRefreshing,
    items,
    loadMore,
    market,
    refresh,
    removeItem,
    retry,
    searchQuery,
    setActiveFilter,
    setSearchQuery,
    status,
  };
}

function buildFeedPath(filters: FeedFilters, cursor: string | null, market: Market | null): string {
  const params = [`limit=${PAGE_LIMIT}`];
  const timing =
    filters.filter === "today" ? "today" : filters.filter === "weekend" ? "weekend" : "all";
  params.push(`timing=${timing}`);
  if (filters.filter === "highPay" && market) {
    params.push(`minimum_pay=${encodeURIComponent(market.high_pay_threshold)}`);
  }
  const query = filters.query.trim();
  if (query) params.push(`query=${encodeURIComponent(query)}`);
  if (cursor) params.push(`cursor=${encodeURIComponent(cursor)}`);
  return `/workers/me/feed?${params.join("&")}`;
}

function dedupeById(items: FeedShift[]): FeedShift[] {
  return appendUnique([], items);
}

function appendUnique(current: FeedShift[], added: FeedShift[]): FeedShift[] {
  const seen = new Set(current.map((item) => item.shift_id));
  const merged = [...current];
  for (const item of added) {
    if (seen.has(item.shift_id)) continue;
    seen.add(item.shift_id);
    merged.push(item);
  }
  return merged;
}

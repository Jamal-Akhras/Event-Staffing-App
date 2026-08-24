import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchNotificationsPage,
  markAllNotificationsRead,
  markNotificationRead,
  type AppNotification,
} from "./notificationsApi";

const REFRESH_INTERVAL_MS = 60_000;

export type InboxStatus = "loading" | "ready" | "error";

export function useNotificationInbox(enabled: boolean) {
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [status, setStatus] = useState<InboxStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);

  const requestSeq = useRef(0);
  const nextCursorRef = useRef<string | null>(null);
  const loadingMoreRef = useRef(false);

  const refresh = useCallback(async (showLoading: boolean) => {
    const seq = ++requestSeq.current;
    loadingMoreRef.current = false;
    setIsLoadingMore(false);
    if (showLoading) setStatus("loading");
    try {
      const page = await fetchNotificationsPage(null);
      if (seq !== requestSeq.current) return;
      setItems(dedupe(page.items));
      nextCursorRef.current = page.next_cursor;
      setHasMore(page.next_cursor !== null);
      setUnreadCount(page.unread_count);
      setError(null);
      setStatus("ready");
    } catch (err) {
      if (seq !== requestSeq.current) return;
      setError((err as Error).message);
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    void refresh(true);
    const onFocus = () => void refresh(false);
    window.addEventListener("focus", onFocus);
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") void refresh(false);
    }, REFRESH_INTERVAL_MS);
    return () => {
      window.removeEventListener("focus", onFocus);
      clearInterval(interval);
    };
  }, [enabled, refresh]);

  const loadMore = useCallback(async () => {
    if (loadingMoreRef.current || !nextCursorRef.current) return;
    const seq = requestSeq.current;
    loadingMoreRef.current = true;
    setIsLoadingMore(true);
    try {
      const page = await fetchNotificationsPage(nextCursorRef.current);
      if (seq !== requestSeq.current) return;
      setItems((current) => appendUnique(current, page.items));
      nextCursorRef.current = page.next_cursor;
      setHasMore(page.next_cursor !== null);
      setUnreadCount(page.unread_count);
    } catch (err) {
      if (seq === requestSeq.current) setError((err as Error).message);
    } finally {
      loadingMoreRef.current = false;
      setIsLoadingMore(false);
    }
  }, []);

  const markRead = useCallback((notificationId: string) => {
    let wasUnread = false;
    setItems((current) =>
      current.map((item) => {
        if (item.notification_id !== notificationId) return item;
        if (!item.read) wasUnread = true;
        return { ...item, read: true };
      })
    );
    if (wasUnread) setUnreadCount((count) => Math.max(0, count - 1));
    markNotificationRead(notificationId).catch(() => undefined);
  }, []);

  const markAllRead = useCallback(async () => {
    setItems((current) => current.map((item) => ({ ...item, read: true })));
    setUnreadCount(0);
    try {
      await markAllNotificationsRead();
    } catch {
      void refresh(false);
    }
  }, [refresh]);

  return {
    error,
    hasMore,
    isLoadingMore,
    items,
    loadMore,
    markAllRead,
    markRead,
    refresh,
    status,
    unreadCount,
  };
}

function dedupe(items: AppNotification[]): AppNotification[] {
  return appendUnique([], items);
}

function appendUnique(current: AppNotification[], added: AppNotification[]): AppNotification[] {
  const seen = new Set(current.map((item) => item.notification_id));
  const merged = [...current];
  for (const item of added) {
    if (seen.has(item.notification_id)) continue;
    seen.add(item.notification_id);
    merged.push(item);
  }
  return merged;
}

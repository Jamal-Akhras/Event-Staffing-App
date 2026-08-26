import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import { appendUnique } from "../lib/collections";
import {
  fetchNotificationsPage,
  markAllNotificationsRead,
  markNotificationRead,
  type AppNotification,
} from "../lib/notifications";

const REFRESH_INTERVAL_MS = 60_000;

export type NotificationStatus = "loading" | "ready" | "error";

type NotificationContextType = {
  notifications: AppNotification[];
  unreadCount: number;
  status: NotificationStatus;
  error: string | null;
  isLoadingMore: boolean;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  markRead: (notificationId: string) => void;
  markAllRead: () => Promise<void>;
};

const NotificationContext = createContext<NotificationContextType>({
  notifications: [],
  unreadCount: 0,
  status: "loading",
  error: null,
  isLoadingMore: false,
  isRefreshing: false,
  refresh: async () => {},
  loadMore: async () => {},
  markRead: () => {},
  markAllRead: async () => {},
});

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [status, setStatus] = useState<NotificationStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const requestSeq = useRef(0);
  const nextCursorRef = useRef<string | null>(null);
  const loadingMoreRef = useRef(false);

  const loadFirstPage = useCallback(async (asRefresh: boolean) => {
    const seq = ++requestSeq.current;
    loadingMoreRef.current = false;
    setIsLoadingMore(false);
    if (asRefresh) setIsRefreshing(true);
    try {
      const page = await fetchNotificationsPage(null);
      if (seq !== requestSeq.current) return;
      setNotifications(appendUnique([], page.items, getNotificationId));
      nextCursorRef.current = page.next_cursor;
      setUnreadCount(page.unread_count);
      setError(null);
      setStatus("ready");
    } catch (err) {
      if (seq !== requestSeq.current) return;
      setError((err as Error).message);
      setStatus((current) => (current === "ready" ? current : "error"));
    } finally {
      if (seq === requestSeq.current && asRefresh) setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadFirstPage(false);
    const interval = setInterval(() => void loadFirstPage(false), REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadFirstPage]);

  const refresh = useCallback(() => loadFirstPage(true), [loadFirstPage]);

  const loadMore = useCallback(async () => {
    if (loadingMoreRef.current || !nextCursorRef.current) return;
    const seq = requestSeq.current;
    loadingMoreRef.current = true;
    setIsLoadingMore(true);
    try {
      const page = await fetchNotificationsPage(nextCursorRef.current);
      if (seq !== requestSeq.current) return;
      setNotifications((current) => appendUnique(current, page.items, getNotificationId));
      nextCursorRef.current = page.next_cursor;
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
    setNotifications((current) =>
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
    setNotifications((current) => current.map((item) => ({ ...item, read: true })));
    setUnreadCount(0);
    try {
      await markAllNotificationsRead();
    } catch {
      void loadFirstPage(false);
    }
  }, [loadFirstPage]);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        status,
        error,
        isLoadingMore,
        isRefreshing,
        refresh,
        loadMore,
        markRead,
        markAllRead,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  return useContext(NotificationContext);
}

function getNotificationId(notification: AppNotification): string {
  return notification.notification_id;
}

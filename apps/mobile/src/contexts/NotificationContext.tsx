import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import { useAuth } from "./AuthContext";
import { fetchWorker, postWorker } from "../lib/api";

type Notification = {
  notification_id: string;
  type: string;
  title: string;
  body: string;
  shift_id: string | null;
  read: boolean;
  created_at: string;
};

type NotificationContextType = {
  notifications: Notification[];
  unreadCount: number;
  markAllRead: () => Promise<void>;
  refresh: () => void;
};

const NotificationContext = createContext<NotificationContextType>({
  notifications: [],
  unreadCount: 0,
  markAllRead: async () => {},
  refresh: () => {},
});

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const workerId = user?.worker_profile_id ?? null;
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const inFlight = useRef(false);

  const fetch = useCallback(async () => {
    if (!workerId || inFlight.current) return;
    inFlight.current = true;
    try {
      const data = await fetchWorker<Notification[]>(`/workers/${workerId}/notifications?limit=30`);
      setNotifications(data);
    } catch {
      // silent — notifications are non-critical
    } finally {
      inFlight.current = false;
    }
  }, [workerId]);

  useEffect(() => {
    if (!workerId) return;
    fetch();
    const interval = setInterval(fetch, 30_000);
    return () => clearInterval(interval);
  }, [workerId, fetch]);

  const markAllRead = async () => {
    if (!workerId) return;
    try {
      await postWorker(`/workers/${workerId}/notifications/read-all`);
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch {
      // silent
    }
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, markAllRead, refresh: fetch }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  return useContext(NotificationContext);
}

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { notificationActionPath } from "../lib/notificationActions";
import { useNotificationInbox } from "../lib/useNotificationInbox";
import type { AppNotification } from "../lib/notificationsApi";
import "./NotificationBell.css";

export function NotificationBell() {
  const navigate = useNavigate();
  const inbox = useNotificationInbox(true);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const bellRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    bellRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!open) return;
    dialogRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    const onPointerDown = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onPointerDown);
    };
  }, [open, close]);

  const toggleOpen = () => {
    setOpen((current) => {
      if (!current) void inbox.refresh(false);
      return !current;
    });
  };

  const openNotification = (notification: AppNotification) => {
    inbox.markRead(notification.notification_id);
    const path = notificationActionPath(notification.action);
    if (path) {
      setOpen(false);
      navigate(path);
    }
  };

  const badgeText = inbox.unreadCount > 99 ? "99+" : String(inbox.unreadCount);

  return (
    <div className="notif-bell-root" ref={rootRef}>
      <button
        ref={bellRef}
        type="button"
        className="notif-bell-btn"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={
          inbox.unreadCount > 0
            ? `Notifications, ${inbox.unreadCount} unread`
            : "Notifications"
        }
        onClick={toggleOpen}
      >
        <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 0 1-3.4 0" />
        </svg>
        {inbox.unreadCount > 0 && (
          <span className="notif-badge" aria-hidden="true">{badgeText}</span>
        )}
      </button>

      {open && (
        <div
          ref={dialogRef}
          className="notif-popover"
          role="dialog"
          aria-label="Notifications"
          tabIndex={-1}
        >
          <div className="notif-popover-header">
            <h2 className="notif-popover-title">Notifications</h2>
            <button
              type="button"
              className="notif-mark-all"
              disabled={inbox.unreadCount === 0}
              onClick={() => void inbox.markAllRead()}
            >
              Mark all read
            </button>
          </div>

          <div className="notif-list" role="list">
            {inbox.status === "loading" && <p className="notif-state">Loading notifications…</p>}

            {inbox.status === "error" && (
              <div className="notif-state">
                <p className="notif-error-text">{inbox.error ?? "Couldn't load notifications."}</p>
                <button type="button" className="notif-retry" onClick={() => void inbox.refresh(true)}>
                  Try again
                </button>
              </div>
            )}

            {inbox.status === "ready" && inbox.items.length === 0 && (
              <p className="notif-state">You're all caught up.</p>
            )}

            {inbox.status === "ready" &&
              inbox.items.map((notification) => (
                <button
                  key={notification.notification_id}
                  type="button"
                  role="listitem"
                  className={`notif-item${notification.read ? "" : " unread"}`}
                  onClick={() => openNotification(notification)}
                >
                  <span className="notif-item-dot" aria-hidden="true" />
                  <span className="notif-item-copy">
                    <span className="notif-item-title">{notification.title}</span>
                    <span className="notif-item-body">{notification.body}</span>
                    <span className="notif-item-time">{formatWhen(notification.created_at)}</span>
                  </span>
                  {!notification.read && <span className="sr-only">Unread.</span>}
                </button>
              ))}

            {inbox.status === "ready" && inbox.hasMore && (
              <button
                type="button"
                className="notif-load-more"
                disabled={inbox.isLoadingMore}
                onClick={() => void inbox.loadMore()}
              >
                {inbox.isLoadingMore ? "Loading…" : "Load older notifications"}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function formatWhen(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const minutes = Math.round((Date.now() - then) / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

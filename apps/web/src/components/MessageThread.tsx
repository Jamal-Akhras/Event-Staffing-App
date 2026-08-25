import { useState, useEffect, FormEvent, useRef } from "react";

import { fetchJson, postJson } from "../lib/api";

type Message = {
  message_id: string;
  shift_id: string;
  application_id: string | null;
  booking_id: string | null;
  sender_id: string;
  sender_role: string;
  content: string;
  read_at: string | null;
  created_at: string;
};

type MessageThreadProps = {
  shiftId: string;
  applicationId?: string;
  bookingId?: string;
  currentUserRole: "worker" | "operator";
};

const POLL_INTERVAL_MS = 5000;

export function MessageThread({ shiftId, applicationId, bookingId, currentUserRole }: MessageThreadProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const threadPath = buildThreadPath(shiftId, applicationId, bookingId);
  const threadBody = { application_id: applicationId, booking_id: bookingId };

  const loadMessages = async () => {
    try {
      const data = await fetchJson<Message[]>(threadPath);
      setMessages(data);
      setError(null);
      if (data.some((msg) => msg.sender_role !== currentUserRole && msg.read_at === null)) {
        await postJson(`/shifts/${shiftId}/messages/read`, threadBody);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [shiftId, applicationId, bookingId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    const content = newMessage.trim();
    if (!content) return;

    setSending(true);
    try {
      await postJson(`/shifts/${shiftId}/messages`, { content, ...threadBody });
      setNewMessage("");
      await loadMessages();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center" }}>
        <p style={{ color: "var(--ink-500)" }}>Loading messages...</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          minHeight: "300px",
          maxHeight: "500px",
        }}
      >
        {messages.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--ink-500)" }}>
            <p style={{ margin: 0 }}>No messages yet</p>
            <p style={{ margin: "8px 0 0", fontSize: "0.85rem" }}>
              Start a conversation by sending a message below
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.message_id} message={msg} isCurrentUser={msg.sender_role === currentUserRole} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <p className="status error" style={{ margin: 0, padding: "0 16px 8px", fontSize: "0.85rem" }}>
          {error}
        </p>
      )}

      <form
        onSubmit={handleSendMessage}
        style={{
          padding: "16px",
          borderTop: "1px solid rgba(15, 23, 32, 0.08)",
        }}
      >
        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            maxLength={4000}
            disabled={sending}
            style={{
              flex: 1,
              padding: "12px 14px",
              borderRadius: "14px",
              border: "1px solid rgba(15, 23, 32, 0.14)",
              fontSize: "0.95rem",
            }}
          />
          <button
            type="submit"
            className="btn primary"
            disabled={sending || !newMessage.trim()}
            style={{ minWidth: "80px" }}
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}

function MessageBubble({ message, isCurrentUser }: { message: Message; isCurrentUser: boolean }) {
  const senderLabel = message.sender_role === "operator" ? "Venue" : "Worker";
  return (
    <div style={{ display: "flex", justifyContent: isCurrentUser ? "flex-end" : "flex-start" }}>
      <div
        style={{
          maxWidth: "70%",
          padding: "12px 16px",
          borderRadius: "16px",
          background: isCurrentUser ? "var(--ocean-500)" : "rgba(15, 23, 32, 0.06)",
          color: isCurrentUser ? "#fff" : "var(--ink-900)",
        }}
      >
        <div style={{ fontSize: "0.75rem", marginBottom: "4px", opacity: 0.8, fontWeight: 600 }}>
          {isCurrentUser ? "You" : senderLabel}
        </div>
        <div style={{ fontSize: "0.95rem", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>{message.content}</div>
        <div style={{ fontSize: "0.7rem", marginTop: "6px", opacity: 0.7 }}>
          {formatTimestamp(message.created_at)}
          {isCurrentUser && message.read_at ? " · Read" : ""}
        </div>
      </div>
    </div>
  );
}

function buildThreadPath(shiftId: string, applicationId?: string, bookingId?: string) {
  const params = new URLSearchParams();
  if (applicationId) params.set("application_id", applicationId);
  if (bookingId) params.set("booking_id", bookingId);
  return `/shifts/${shiftId}/messages?${params.toString()}`;
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

import { useState, useEffect, FormEvent, useRef } from "react";

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

import { API_BASE, getAuthHeaders } from "../lib/api";

const resolvedApiBase = API_BASE;

export function MessageThread({ shiftId, applicationId, bookingId, currentUserRole }: MessageThreadProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadMessages = async () => {
    try {
      const params = new URLSearchParams();
      if (applicationId) params.set("application_id", applicationId);
      if (bookingId) params.set("booking_id", bookingId);

      const response = await fetch(
        `${resolvedApiBase}/shifts/${shiftId}/messages?${params.toString()}`,
        { headers: getAuthHeaders() }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
    // Poll for new messages every 5 seconds
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [shiftId, applicationId, bookingId]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      const response = await fetch(`${resolvedApiBase}/shifts/${shiftId}/messages`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          content: newMessage,
          application_id: applicationId,
          booking_id: bookingId,
        }),
      });

      if (response.ok) {
        setNewMessage("");
        await loadMessages();
      }
    } catch (err) {
      console.error("Failed to send message:", err);
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
      {/* Messages List */}
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
          messages.map((msg) => {
            const isCurrentUser = msg.sender_role === currentUserRole;
            const senderLabel = msg.sender_role === "operator" ? "Venue" : "Worker";

            return (
              <div
                key={msg.message_id}
                style={{
                  display: "flex",
                  justifyContent: isCurrentUser ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth: "70%",
                    padding: "12px 16px",
                    borderRadius: "16px",
                    background: isCurrentUser
                      ? "var(--ocean-500)"
                      : "rgba(15, 23, 32, 0.06)",
                    color: isCurrentUser ? "#fff" : "var(--ink-900)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.75rem",
                      marginBottom: "4px",
                      opacity: 0.8,
                      fontWeight: 600,
                    }}
                  >
                    {isCurrentUser ? "You" : senderLabel}
                  </div>
                  <div style={{ fontSize: "0.95rem", lineHeight: 1.5 }}>{msg.content}</div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      marginTop: "6px",
                      opacity: 0.7,
                    }}
                  >
                    {new Date(msg.created_at).toLocaleString("en-US", {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
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

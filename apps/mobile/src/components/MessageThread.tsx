import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { fetchWorker, postWorker } from "../lib/api";
import { COLORS } from "../theme/colors";

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

export function MessageThread({
  shiftId,
  applicationId,
  bookingId,
  currentUserRole,
}: MessageThreadProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollViewRef = useRef<ScrollView>(null);

  const loadMessages = async () => {
    try {
      const data = await fetchWorker<Message[]>(buildMessagePath(shiftId, applicationId, bookingId));
      setMessages(data);
      setError(null);
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [shiftId, applicationId, bookingId]);

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
      >
        {messages.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No messages yet</Text>
            <Text style={styles.emptyHint}>Send a note tied to this shift.</Text>
          </View>
        )}

        {groupMessagesByDate(messages).map((group) => (
          <View key={group.date}>
            <View style={styles.dateSeparator}>
              <Text style={styles.dateText}>{group.date}</Text>
            </View>
            {group.messages.map((message) => (
              <MessageBubble
                key={message.message_id}
                message={message}
                isCurrentUser={message.sender_role === currentUserRole}
              />
            ))}
          </View>
        ))}
      </ScrollView>

      {error && <Text style={styles.errorText}>{error}</Text>}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={newMessage}
          onChangeText={setNewMessage}
          placeholder="Type a message..."
          placeholderTextColor={COLORS.inkSubtle}
          multiline
          maxLength={500}
        />
        <Pressable
          style={[styles.sendButton, (!newMessage.trim() || sending) && styles.sendButtonDisabled]}
          onPress={sendMessage}
          disabled={!newMessage.trim() || sending}
        >
          {sending ? (
            <ActivityIndicator size="small" color={COLORS.onPrimary} />
          ) : (
            <Text style={styles.sendButtonText}>Send</Text>
          )}
        </Pressable>
      </View>
    </View>
  );

  async function sendMessage() {
    if (!newMessage.trim() || sending) return;
    setSending(true);
    try {
      const payload: Record<string, string> = { content: newMessage.trim() };
      if (applicationId) payload.application_id = applicationId;
      if (bookingId) payload.booking_id = bookingId;
      await postWorker(`/shifts/${shiftId}/messages`, payload);
      setNewMessage("");
      await loadMessages();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSending(false);
    }
  }
}

function MessageBubble({
  message,
  isCurrentUser,
}: {
  message: Message;
  isCurrentUser: boolean;
}) {
  return (
    <View style={[styles.messageBubble, isCurrentUser ? styles.messageRight : styles.messageLeft]}>
      <View style={[styles.messageContent, isCurrentUser && styles.messageContentRight]}>
        {!isCurrentUser && (
          <Text style={styles.senderLabel}>
            {message.sender_role === "operator" ? "Venue" : "Worker"}
          </Text>
        )}
        <Text style={[styles.messageText, isCurrentUser && styles.messageTextRight]}>
          {message.content}
        </Text>
        <Text style={[styles.messageTime, isCurrentUser && styles.messageTimeRight]}>
          {formatTime(message.created_at)}
        </Text>
      </View>
    </View>
  );
}

function buildMessagePath(
  shiftId: string,
  applicationId?: string,
  bookingId?: string
) {
  const params = new URLSearchParams();
  if (applicationId) params.set("application_id", applicationId);
  if (bookingId) params.set("booking_id", bookingId);
  return `/shifts/${shiftId}/messages?${params.toString()}`;
}

function groupMessagesByDate(messages: Message[]) {
  return messages.reduce<{ date: string; messages: Message[] }[]>((groups, message) => {
    const date = formatDate(message.created_at);
    const existing = groups.find((group) => group.date === date);
    if (existing) {
      existing.messages.push(message);
    } else {
      groups.push({ date, messages: [message] });
    }
    return groups;
  }, []);
}

function formatTime(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDate(timestamp: string) {
  const date = new Date(timestamp);
  if (date.toDateString() === new Date().toDateString()) {
    return "Today";
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  messagesContainer: { flex: 1 },
  messagesContent: { padding: 16 },
  emptyState: { alignItems: "center", justifyContent: "center", paddingVertical: 40 },
  emptyText: { color: COLORS.ink, fontSize: 16, fontWeight: "800", marginBottom: 4 },
  emptyHint: { color: COLORS.inkMuted, fontSize: 14 },
  dateSeparator: { alignItems: "center", marginVertical: 14 },
  dateText: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: COLORS.surfaceMuted,
    color: COLORS.inkMuted,
    fontSize: 12,
    fontWeight: "800",
  },
  messageBubble: { marginBottom: 12 },
  messageLeft: { alignItems: "flex-start" },
  messageRight: { alignItems: "flex-end" },
  messageContent: {
    maxWidth: "80%",
    padding: 12,
    borderRadius: 16,
    borderBottomLeftRadius: 4,
    backgroundColor: COLORS.surface,
  },
  messageContentRight: {
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 4,
    backgroundColor: COLORS.primary,
  },
  senderLabel: { color: COLORS.inkMuted, fontSize: 11, fontWeight: "800", marginBottom: 4 },
  messageText: { color: COLORS.ink, fontSize: 15, lineHeight: 20 },
  messageTextRight: { color: COLORS.onPrimary },
  messageTime: { color: COLORS.inkMuted, fontSize: 11, marginTop: 4 },
  messageTimeRight: { color: "rgba(255, 255, 255, 0.72)" },
  errorText: { paddingHorizontal: 16, color: COLORS.error, fontWeight: "700" },
  inputContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  input: {
    flex: 1,
    maxHeight: 104,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceMuted,
    color: COLORS.ink,
  },
  sendButton: {
    alignItems: "center",
    justifyContent: "center",
    minWidth: 62,
    paddingHorizontal: 18,
    paddingVertical: 11,
    borderRadius: 18,
    backgroundColor: COLORS.primary,
  },
  sendButtonDisabled: { backgroundColor: COLORS.borderStrong },
  sendButtonText: { color: COLORS.onPrimary, fontWeight: "900" },
});

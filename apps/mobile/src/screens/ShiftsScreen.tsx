import { useEffect, useMemo, useRef, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { EmptyState } from "../components/EmptyState";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";
import { fetchWorker, getWorkerId, postWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Application, Booking, Shift } from "../types";
import { MessagingModal } from "./shifts/MessagingModal";
import { RatingModal } from "./shifts/RatingModal";
import { SelectedBookingPanel } from "./shifts/SelectedBookingPanel";
import { ApplicationRow, BookingRow } from "./shifts/ShiftRows";
import { ShiftsTabBar } from "./shifts/ShiftsTabBar";
import {
  getPreviousBookings,
  getUpcomingBookings,
  type ShiftTab,
} from "./shifts/shiftsUtils";

export function ShiftsScreen() {
  const { user } = useAuth();
  const workerId = user?.worker_profile_id ?? getWorkerId();
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [selected, setSelected] = useState<Booking | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationsError, setApplicationsError] = useState<string | null>(null);
  const [shiftTab, setShiftTab] = useState<ShiftTab>("upcoming");
  const [messagingApplication, setMessagingApplication] = useState<Application | null>(null);
  const [messagingBooking, setMessagingBooking] = useState<Booking | null>(null);
  const [ratingBooking, setRatingBooking] = useState<Booking | null>(null);
  const [ratingShift, setRatingShift] = useState<Shift | null>(null);
  const pollInFlight = useRef(false);

  const loadBookings = async () => {
    try {
      const data = await fetchWorker<Booking[]>(
        `/bookings?worker_id=${encodeURIComponent(workerId)}`
      );
      setBookings(data);
      setBookingError(null);
      setSelected((current) => current ?? data[0] ?? null);
    } catch (err) {
      setBookingError((err as Error).message);
    }
  };

  const loadApplications = async () => {
    try {
      const data = await fetchWorker<Application[]>(
        `/applications?worker_id=${encodeURIComponent(workerId)}`
      );
      setApplications(data);
      setApplicationsError(null);
    } catch (err) {
      setApplications([]);
      setApplicationsError((err as Error).message);
    }
  };

  const pollAll = async () => {
    if (pollInFlight.current) return;
    pollInFlight.current = true;
    try {
      await Promise.all([loadBookings(), loadApplications()]);
    } finally {
      pollInFlight.current = false;
    }
  };

  useEffect(() => {
    pollAll();
    const interval = setInterval(pollAll, 15000);
    return () => clearInterval(interval);
  }, []);

  const upcomingBookings = useMemo(() => getUpcomingBookings(bookings), [bookings]);
  const previousBookings = useMemo(() => getPreviousBookings(bookings), [bookings]);

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>Worker schedule</Text>
          <Text style={styles.title}>Your shifts</Text>
          <Text style={styles.subtitle}>
            Check in, message venues, and track application decisions.
          </Text>
        </View>

        {unreadCount > 0 && (
          <NotificationBanner
            notifications={notifications.filter((n) => !n.read)}
            onDismiss={markAllRead}
          />
        )}

        <ShiftsTabBar activeTab={shiftTab} onChange={setShiftTab} />

        {shiftTab === "upcoming" && (
          <BookingList
            bookings={upcomingBookings}
            emptyTitle="No upcoming shifts"
            emptyMessage="Confirmed shifts and check-in actions will appear here."
            onSelect={setSelected}
            onMessage={setMessagingBooking}
          />
        )}

        {shiftTab === "previous" && (
          <BookingList
            bookings={previousBookings}
            emptyTitle="No previous shifts"
            emptyMessage="Completed, cancelled, and no-show records will appear here."
            onSelect={setSelected}
            onRate={async (booking) => {
              const shift = await fetchWorker<Shift>(`/shifts/${booking.shift_id}`).catch(() => null);
              setRatingBooking(booking);
              setRatingShift(shift);
            }}
          />
        )}

        {shiftTab === "applications" && (
          <>
            {applicationsError && <Text style={styles.errorText}>{applicationsError}</Text>}
            {applications.length === 0 ? (
              <EmptyState
                title="No applications yet"
                message="Apply from Browse to track venue decisions here."
              />
            ) : (
              applications.map((application) => (
                <ApplicationRow
                  key={application.application_id}
                  application={application}
                  onMessage={() => setMessagingApplication(application)}
                />
              ))
            )}
          </>
        )}

        <SelectedBookingPanel
          booking={selected}
          error={bookingError}
          onCheckIn={() => transition("check-in")}
          onCheckOut={() => transition("check-out")}
        />
      </ScrollView>

      <MessagingModal
        application={messagingApplication}
        booking={messagingBooking}
        onClose={() => {
          setMessagingApplication(null);
          setMessagingBooking(null);
        }}
      />

      {ratingBooking && (
        <RatingModal
          bookingId={ratingBooking.booking_id}
          shiftRole={ratingShift?.role ?? "Shift"}
          shiftLocation={ratingShift?.location ?? ""}
          onDone={() => { setRatingBooking(null); setRatingShift(null); }}
          onSkip={() => { setRatingBooking(null); setRatingShift(null); }}
        />
      )}
    </View>
  );

  async function transition(action: "check-in" | "check-out") {
    if (!selected) return;
    setBookingError(null);
    try {
      const data = await postWorker<Booking>(`/bookings/${selected.booking_id}/${action}`, {
        now: new Date().toISOString(),
      });
      setSelected(data);
      await loadBookings();
      if (action === "check-out") {
        const shift = await fetchWorker<Shift>(`/shifts/${data.shift_id}`).catch(() => null);
        setRatingBooking(data);
        setRatingShift(shift);
      }
    } catch (err) {
      setBookingError((err as Error).message);
    }
  }
}

type Notif = { notification_id: string; type: string; title: string; body: string; read: boolean };

function NotificationBanner({ notifications, onDismiss }: { notifications: Notif[]; onDismiss: () => void }) {
  return (
    <View style={notifStyles.banner}>
      <View style={notifStyles.bannerHeader}>
        <Text style={notifStyles.bannerTitle}>
          {notifications.length} new update{notifications.length > 1 ? "s" : ""}
        </Text>
        <Pressable onPress={onDismiss} hitSlop={8}>
          <Text style={notifStyles.bannerDismiss}>Mark all read</Text>
        </Pressable>
      </View>
      {notifications.slice(0, 3).map((n) => (
        <View key={n.notification_id} style={notifStyles.notifRow}>
          <Text style={notifStyles.notifDot}>{n.type === "approved" ? "✓" : "✕"}</Text>
          <View style={{ flex: 1 }}>
            <Text style={notifStyles.notifTitle}>{n.title}</Text>
            <Text style={notifStyles.notifBody}>{n.body}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

const notifStyles = StyleSheet.create({
  banner: {
    marginBottom: 14,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(14,90,58,0.18)",
    backgroundColor: "rgba(14,90,58,0.05)",
  },
  bannerHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  bannerTitle: { color: COLORS.primary, fontWeight: "800", fontSize: 13 },
  bannerDismiss: { color: COLORS.primary, fontWeight: "600", fontSize: 12 },
  notifRow: { flexDirection: "row", gap: 10, marginBottom: 6, alignItems: "flex-start" },
  notifDot: { color: COLORS.primary, fontWeight: "800", fontSize: 14, marginTop: 1 },
  notifTitle: { color: COLORS.ink, fontWeight: "700", fontSize: 13 },
  notifBody: { color: COLORS.inkMuted, fontSize: 12, marginTop: 1 },
});

function BookingList({
  bookings,
  emptyTitle,
  emptyMessage,
  onSelect,
  onMessage,
  onRate,
}: {
  bookings: Booking[];
  emptyTitle: string;
  emptyMessage: string;
  onSelect: (booking: Booking) => void;
  onMessage?: (booking: Booking) => void;
  onRate?: (booking: Booking) => void;
}) {
  if (bookings.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <>
      {bookings.map((booking) => (
        <BookingRow
          key={booking.booking_id}
          booking={booking}
          onSelect={() => onSelect(booking)}
          onMessage={onMessage ? () => onMessage(booking) : undefined}
          onRate={onRate && (booking.state === "checked_out" || booking.state === "approved")
            ? () => onRate(booking)
            : undefined}
        />
      ))}
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: 20, paddingBottom: 40 },
  header: { marginBottom: 16 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  subtitle: { color: COLORS.inkMuted, fontSize: 14, lineHeight: 20, marginTop: 6 },
  errorText: {
    marginBottom: 12,
    color: COLORS.error,
    fontWeight: "600",
  },
});

import { useEffect, useMemo, useRef, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { EmptyState } from "../components/EmptyState";
import { useNotifications } from "../contexts/NotificationContext";
import { useRatingPrompt } from "../contexts/RatingPromptContext";
import { ApiError, fetchWorker, getWorkerId, postWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Application, Booking } from "../types";
import { MessagingModal } from "./shifts/MessagingModal";
import { NotificationBanner } from "./shifts/NotificationBanner";
import { CancellationReasonModal } from "./shifts/CancellationReasonModal";
import { SelectedBookingPanel } from "./shifts/SelectedBookingPanel";
import { ShiftBookingList } from "./shifts/ShiftBookingList";
import { ApplicationRow } from "./shifts/ShiftRows";
import { ShiftsTabBar } from "./shifts/ShiftsTabBar";
import {
  getPreviousBookings,
  getUpcomingBookings,
  sortHighlightedFirst,
  type ShiftTab,
} from "./shifts/shiftsUtils";
import { useShiftNotificationTarget } from "./shifts/useShiftNotificationTarget";

export function ShiftsScreen() {
  const workerId = getWorkerId();
  const { notifications, unreadCount, markAllRead } = useNotifications();
  const { refreshRatingPrompt } = useRatingPrompt();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [bookingsLoaded, setBookingsLoaded] = useState(false);
  const [selected, setSelected] = useState<Booking | null>(null);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [checkInCode, setCheckInCode] = useState("");
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationsLoaded, setApplicationsLoaded] = useState(false);
  const [applicationsError, setApplicationsError] = useState<string | null>(null);
  const [shiftTab, setShiftTab] = useState<ShiftTab>("upcoming");
  const [messagingApplication, setMessagingApplication] = useState<Application | null>(null);
  const [messagingBooking, setMessagingBooking] = useState<Booking | null>(null);
  const [cancellationTarget, setCancellationTarget] = useState<CancellationTarget | null>(null);
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
    } finally {
      setBookingsLoaded(true);
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
    } finally {
      setApplicationsLoaded(true);
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
  const notificationTarget = useShiftNotificationTarget({
    applications,
    applicationsLoaded,
    bookings,
    bookingsLoaded,
    onOpenApplicationMessages: setMessagingApplication,
    onSelectBooking: setSelected,
    onSelectTab: setShiftTab,
  });
  const visibleApplications = useMemo(
    () =>
      sortHighlightedFirst(
        applications,
        notificationTarget.highlightedApplicationId,
        (application) => application.application_id
      ),
    [applications, notificationTarget.highlightedApplicationId]
  );

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
        {notificationTarget.targetError && (
          <Text style={styles.errorText}>{notificationTarget.targetError}</Text>
        )}

        {shiftTab === "upcoming" && (
          <ShiftBookingList
            bookings={upcomingBookings}
            highlightedBookingId={notificationTarget.highlightedBookingId}
            emptyTitle="No upcoming shifts"
            emptyMessage="Confirmed shifts and check-in actions will appear here."
            onSelect={setSelected}
            onMessage={setMessagingBooking}
          />
        )}

        {shiftTab === "previous" && (
          <ShiftBookingList
            bookings={previousBookings}
            highlightedBookingId={notificationTarget.highlightedBookingId}
            emptyTitle="No previous shifts"
            emptyMessage="Completed, cancelled, and no-show records will appear here."
            onSelect={setSelected}
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
              visibleApplications.map((application) => (
                <ApplicationRow
                  key={application.application_id}
                  application={application}
                  highlighted={application.application_id === notificationTarget.highlightedApplicationId}
                  onMessage={() => setMessagingApplication(application)}
                  onWithdraw={() => setCancellationTarget({ type: "application", value: application })}
                />
              ))
            )}
          </>
        )}

        <SelectedBookingPanel
          booking={selected}
          error={bookingError}
          checkInCode={checkInCode}
          onCheckInCodeChange={setCheckInCode}
          onCheckIn={() => transition("check-in")}
          onCheckOut={() => transition("check-out")}
          onCancel={() => selected && setCancellationTarget({ type: "booking", value: selected })}
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

      <CancellationReasonModal
        visible={cancellationTarget !== null}
        title={cancellationTarget?.type === "booking" ? "Cancel this booking?" : "Withdraw this application?"}
        consequence={cancellationTarget?.type === "booking"
          ? "The shift will be released immediately. Under the current reliability policy, worker cancellations count against your reliability score."
          : "The venue will no longer be able to approve this application. You can still message them before withdrawing."}
        confirmLabel={cancellationTarget?.type === "booking" ? "Cancel booking" : "Withdraw"}
        onClose={() => setCancellationTarget(null)}
        onConfirm={performCancellation}
      />

    </View>
  );

  async function transition(action: "check-in" | "check-out") {
    if (!selected) return;
    setBookingError(null);
    try {
      const data = await postWorker<Booking>(`/bookings/${selected.booking_id}/${action}`, {
        now: new Date().toISOString(),
        ...(action === "check-in" ? { code: checkInCode } : {}),
      });
      setSelected(data);
      setCheckInCode("");
      await loadBookings();
      if (action === "check-out") {
        await refreshRatingPrompt();
      }
    } catch (err) {
      setBookingError((err as Error).message);
    }
  }

  async function performCancellation(reason: string) {
    if (!cancellationTarget) return;
    try {
      if (cancellationTarget.type === "booking") {
        const updated = await postWorker<Booking>(
          `/bookings/${cancellationTarget.value.booking_id}/cancel/worker`,
          { reason, now: new Date().toISOString() }
        );
        setSelected(updated);
        await loadBookings();
      } else {
        await postWorker(`/applications/${cancellationTarget.value.application_id}/withdraw`, {
          reason,
          now: new Date().toISOString(),
        });
        await loadApplications();
      }
      setCancellationTarget(null);
    } catch (err) {
      if (err instanceof ApiError && err.serverDetail) {
        throw new Error(err.serverDetail);
      }
      throw err;
    }
  }
}

type CancellationTarget =
  | { type: "booking"; value: Booking }
  | { type: "application"; value: Application };

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

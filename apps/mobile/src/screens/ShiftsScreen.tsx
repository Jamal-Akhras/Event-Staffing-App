import { useEffect, useMemo, useRef, useState } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useNavigation } from "@react-navigation/native";

import { EmptyState } from "../components/EmptyState";
import { SectionHeader } from "../components/SectionHeader";
import { SegmentedTabs } from "../components/SegmentedTabs";
import { useRatingPrompt } from "../contexts/RatingPromptContext";
import { ApiError, fetchWorker, getWorkerId, postWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import { SPACE } from "../theme/space";
import { TYPE } from "../theme/type";
import type { Application, Booking } from "../types";
import { CancellationReasonModal } from "./shifts/CancellationReasonModal";
import { MessagingModal } from "./shifts/MessagingModal";
import { InvitationCard } from "./shifts/InvitationCard";
import { CoverAskCard } from "./shifts/CoverAskCard";
import { OfferCard } from "./shifts/OfferCard";
import { NextShiftCard } from "./shifts/NextShiftCard";
import { PastShiftItem, ShiftListItem } from "./shifts/ShiftListItem";
import {
  awaitingRating,
  getPreviousBookings,
  getUpcomingBookings,
  groupByMonth,
  nextLiveBooking,
  type ShiftTab,
} from "./shifts/shiftsUtils";
import { useShiftNotificationTarget } from "./shifts/useShiftNotificationTarget";

type VisibleTab = Exclude<ShiftTab, "applications">;

const TABS: { key: VisibleTab; label: string }[] = [
  { key: "upcoming", label: "Upcoming" },
  { key: "previous", label: "Previous" },
];

export function ShiftsScreen() {
  const workerId = getWorkerId();
  const navigation = useNavigation<{ navigate: (screen: "Applications") => void }>();
  const { refreshRatingPrompt } = useRatingPrompt();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<VisibleTab>("upcoming");
  const [messaging, setMessaging] = useState<Booking | null>(null);
  const [cancelling, setCancelling] = useState<Booking | null>(null);
  const [releasing, setReleasing] = useState<Booking | null>(null);
  const polling = useRef(false);

  const load = async () => {
    if (polling.current) return;
    polling.current = true;
    try {
      const data = await fetchWorker<Booking[]>(`/bookings?worker_id=${encodeURIComponent(workerId)}`);
      setBookings(data);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoaded(true);
      polling.current = false;
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const now = new Date();
  const upcoming = useMemo(() => getUpcomingBookings(bookings), [bookings]);
  const previous = useMemo(() => getPreviousBookings(bookings), [bookings]);
  const next = useMemo(() => nextLiveBooking(upcoming), [upcoming]);
  const later = useMemo(
    () => upcoming.filter((booking) => booking.booking_id !== next?.booking_id),
    [upcoming, next]
  );
  const unrated = useMemo(() => awaitingRating(previous), [previous]);
  const months = useMemo(() => groupByMonth(previous), [previous]);

  const target = useShiftNotificationTarget({
    applications: [] as Application[],
    applicationsLoaded: true,
    bookings,
    bookingsLoaded: loaded,
    onOpenApplicationMessages: () => undefined,
    onSelectBooking: () => undefined,
    onSelectTab: (requested) => {
      if (requested === "applications") navigation.navigate("Applications");
      else setTab(requested);
    },
  });

  return (
    <View style={styles.screen}>
      <SegmentedTabs tabs={TABS} active={tab} onChange={setTab} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {target.targetError ? <Text style={styles.error}>{target.targetError}</Text> : null}

        {tab === "upcoming" && <InvitationCard />}
        {tab === "upcoming" && <OfferCard onChanged={() => void load()} />}
        {tab === "upcoming" && <CoverAskCard onChanged={() => void load()} />}

        {tab === "upcoming" &&
          (next ? (
            <>
              <NextShiftCard
                booking={next}
                now={now}
                error={error}
                onCheckIn={(code) => transition(next, "check-in", code)}
                onCheckOut={() => transition(next, "check-out")}
                onMessage={() => setMessaging(next)}
                onRelease={() => setReleasing(next)}
              />
              {later.length > 0 && (
                <View>
                  <SectionHeader title="Later" count={String(later.length)} />
                  {later.map((booking) => (
                    <ShiftListItem
                      key={booking.booking_id}
                      booking={booking}
                      now={now}
                      highlighted={booking.booking_id === target.highlightedBookingId}
                      onPress={() => setMessaging(booking)}
                    />
                  ))}
                </View>
              )}
            </>
          ) : loaded ? (
            <EmptyState
              title="No shifts booked"
              message="Shifts you are confirmed for appear here, with check-in when the time comes."
            />
          ) : null)}

        {tab === "previous" &&
          (previous.length === 0 && loaded ? (
            <EmptyState title="No previous shifts" message="Finished shifts and their pay collect here." />
          ) : (
            <>
              {unrated.length > 0 && (
                <View>
                  <SectionHeader title="Waiting on your rating" count={String(unrated.length)} />
                  {unrated.map((booking) => (
                    <ShiftListItem
                      key={booking.booking_id}
                      booking={booking}
                      now={now}
                      highlighted
                      trailing="Rate venue"
                      onPress={() => refreshRatingPrompt()}
                    />
                  ))}
                </View>
              )}
              {months.map((group) => (
                <View key={group.month}>
                  <SectionHeader title={group.month} count={`${group.items.length} shifts`} />
                  {group.items.map((booking) => (
                    <PastShiftItem
                      key={booking.booking_id}
                      booking={booking}
                      onPress={() => setMessaging(booking)}
                    />
                  ))}
                </View>
              ))}
            </>
          ))}
      </ScrollView>

      <MessagingModal application={null} booking={messaging} onClose={() => setMessaging(null)} />

      <CancellationReasonModal
        visible={cancelling !== null}
        title="Cancel this booking?"
        consequence="The shift is released immediately, and worker cancellations count against your reliability score."
        confirmLabel="Cancel booking"
        onClose={() => setCancelling(null)}
        onConfirm={cancelBooking}
      />

      <CancellationReasonModal
        visible={releasing !== null}
        title="Ask to be released?"
        consequence="The manager decides. You stay on this shift until they approve, and an approved release does not count against you."
        confirmLabel="Send request"
        onClose={() => setReleasing(null)}
        onConfirm={requestRelease}
      />
    </View>
  );

  async function transition(booking: Booking, action: "check-in" | "check-out", code?: string) {
    setError(null);
    try {
      await postWorker<Booking>(`/bookings/${booking.booking_id}/${action}`, {
        now: new Date().toISOString(),
        ...(code ? { code } : {}),
      });
      await load();
      if (action === "check-out") await refreshRatingPrompt();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function requestRelease(reason: string) {
    if (!releasing) return;
    try {
      await postWorker("/me/shift-change-requests", {
        booking_id: releasing.booking_id,
        change_type: "release",
        reason,
        now: new Date().toISOString(),
      });
      setReleasing(null);
    } catch (err) {
      if (err instanceof ApiError && err.serverDetail) throw new Error(err.serverDetail);
      throw err;
    }
  }

  async function cancelBooking(reason: string) {
    if (!cancelling) return;
    try {
      await postWorker<Booking>(`/bookings/${cancelling.booking_id}/cancel/worker`, {
        reason,
        now: new Date().toISOString(),
      });
      await load();
      setCancelling(null);
    } catch (err) {
      if (err instanceof ApiError && err.serverDetail) throw new Error(err.serverDetail);
      throw err;
    }
  }
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.canvas },
  content: { padding: SPACE.s4, gap: SPACE.s5, paddingBottom: SPACE.s7 },
  error: { ...TYPE.meta, color: COLORS.error },
});

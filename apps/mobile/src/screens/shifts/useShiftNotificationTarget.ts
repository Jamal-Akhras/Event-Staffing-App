import type { BottomTabNavigationProp } from "@react-navigation/bottom-tabs";
import { useNavigation, useRoute, type RouteProp } from "@react-navigation/native";
import { useEffect, useRef, useState } from "react";

import type { RootTabParamList } from "../../navigation/navigationTypes";
import type { Application, Booking } from "../../types";
import { getUpcomingBookings, type ShiftTab } from "./shiftsUtils";

type Options = {
  applications: Application[];
  applicationsLoaded: boolean;
  bookings: Booking[];
  bookingsLoaded: boolean;
  onOpenApplicationMessages: (application: Application) => void;
  onSelectBooking: (booking: Booking) => void;
  onSelectTab: (tab: ShiftTab) => void;
};

export function useShiftNotificationTarget(options: Options) {
  const navigation = useNavigation<BottomTabNavigationProp<RootTabParamList, "Shifts">>();
  const route = useRoute<RouteProp<RootTabParamList, "Shifts">>();
  const handledKeyRef = useRef<string | null>(null);
  const [highlightedApplicationId, setHighlightedApplicationId] = useState<string | null>(null);
  const [highlightedBookingId, setHighlightedBookingId] = useState<string | null>(null);
  const [targetError, setTargetError] = useState<string | null>(null);
  const params = route.params;
  const {
    applications,
    applicationsLoaded,
    bookings,
    bookingsLoaded,
    onOpenApplicationMessages,
    onSelectBooking,
    onSelectTab,
  } = options;

  useEffect(() => {
    const targetKey = params?.notification_key;
    const waitingForApplications = Boolean(params?.application_id && !applicationsLoaded);
    const waitingForBookings = Boolean(params?.booking_id && !bookingsLoaded);
    if (!targetKey || waitingForApplications || waitingForBookings) return;
    if (handledKeyRef.current === targetKey) return;
    handledKeyRef.current = targetKey;
    setTargetError(null);
    setHighlightedApplicationId(null);
    setHighlightedBookingId(null);

    if (params.application_id) {
      const application = applications.find(
        (item) => item.application_id === params.application_id
      );
      if (!application) {
        setTargetError("That application is no longer available.");
      } else {
        onSelectTab("applications");
        setHighlightedApplicationId(application.application_id);
        if (params.open === "messages") onOpenApplicationMessages(application);
      }
    } else if (params.booking_id) {
      const booking = bookings.find((item) => item.booking_id === params.booking_id);
      if (!booking) {
        setTargetError("That booking is no longer available.");
      } else {
        onSelectBooking(booking);
        onSelectTab(getUpcomingBookings([booking]).length > 0 ? "upcoming" : "previous");
        setHighlightedBookingId(booking.booking_id);
      }
    }
    navigation.setParams({
      application_id: undefined,
      booking_id: undefined,
      focus: undefined,
      notification_key: undefined,
      open: undefined,
    });
  }, [
    applications,
    applicationsLoaded,
    bookings,
    bookingsLoaded,
    navigation,
    onOpenApplicationMessages,
    onSelectBooking,
    onSelectTab,
    params?.application_id,
    params?.booking_id,
    params?.notification_key,
    params?.open,
  ]);

  return { highlightedApplicationId, highlightedBookingId, targetError };
}

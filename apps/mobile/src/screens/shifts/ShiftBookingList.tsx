import { EmptyState } from "../../components/EmptyState";
import type { Booking } from "../../types";
import { BookingRow } from "./ShiftRows";

type ShiftBookingListProps = {
  bookings: Booking[];
  emptyTitle: string;
  emptyMessage: string;
  highlightedBookingId?: string | null;
  onSelect: (booking: Booking) => void;
  onMessage?: (booking: Booking) => void;
};

export function ShiftBookingList({
  bookings,
  emptyTitle,
  emptyMessage,
  highlightedBookingId,
  onSelect,
  onMessage,
}: ShiftBookingListProps) {
  if (bookings.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <>
      {[...bookings]
        .sort((left, right) =>
          Number(right.booking_id === highlightedBookingId) -
          Number(left.booking_id === highlightedBookingId)
        )
        .map((booking) => (
        <BookingRow
          key={booking.booking_id}
          booking={booking}
          highlighted={booking.booking_id === highlightedBookingId}
          onSelect={() => onSelect(booking)}
          onMessage={onMessage ? () => onMessage(booking) : undefined}
        />
        ))}
    </>
  );
}

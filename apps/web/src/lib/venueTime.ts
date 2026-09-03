import { addHours } from "date-fns";
import { formatInTimeZone, fromZonedTime, toZonedTime } from "date-fns-tz";

export function toVenueWallDate(value: Date | string, timezone: string) {
  return toZonedTime(value, timezone);
}

export function fromVenueWallDate(value: Date, timezone: string) {
  return fromZonedTime(value, timezone);
}

export function toVenueInput(value: Date | string, timezone: string) {
  return formatInTimeZone(value, timezone, "yyyy-MM-dd'T'HH:mm");
}

export function fromVenueInput(value: string, timezone: string) {
  return fromZonedTime(value, timezone).toISOString();
}

export function addVenueHours(value: string, hours: number, timezone: string) {
  return toVenueInput(addHours(fromZonedTime(value, timezone), hours), timezone);
}

export function venueClock(value: Date | string, timezone: string) {
  return formatInTimeZone(value, timezone, "HH:mm");
}

export function calendarDayLabel(value: string) {
  return new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
  });
}

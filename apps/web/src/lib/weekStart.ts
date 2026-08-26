const WEEK_START_KEY = "venueos.weekStart";

export const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export function readWeekStart() {
  const stored = Number(window.localStorage.getItem(WEEK_START_KEY));
  return Number.isInteger(stored) && stored >= 0 && stored <= 6 ? stored : 1;
}

export function saveWeekStart(day: number) {
  window.localStorage.setItem(WEEK_START_KEY, String(day));
}

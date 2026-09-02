const LOCALE = "en-GB";

const moneyFormatters = new Map<string, Intl.NumberFormat>();

function moneyFormatter(currency: string): Intl.NumberFormat {
  const cached = moneyFormatters.get(currency);
  if (cached) return cached;
  const formatter = new Intl.NumberFormat(LOCALE, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  moneyFormatters.set(currency, formatter);
  return formatter;
}

export function formatMoney(amount: number | string, currency = "GBP"): string {
  return moneyFormatter(currency).format(Number(amount));
}

export function splitMoney(amount: number | string, currency = "GBP"): { symbol: string; value: string } {
  const formatted = formatMoney(amount, currency);
  const firstDigit = formatted.search(/\d/);
  return { symbol: formatted.slice(0, firstDigit), value: formatted.slice(firstDigit) };
}

export function formatDayDate(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return date.toLocaleDateString(LOCALE, { weekday: "short", day: "numeric", month: "short" });
}

export function formatClock(value: string | Date): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return date.toLocaleTimeString(LOCALE, { hour: "2-digit", minute: "2-digit" });
}

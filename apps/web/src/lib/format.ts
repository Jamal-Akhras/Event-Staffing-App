const CURRENCY_SYMBOLS: Record<string, string> = {
  GBP: "£",
  AED: "AED ",
  USD: "$",
};

export function formatMoney(amount: number | string, currency = "GBP"): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${Number(amount).toFixed(2)}`;
}

export function formatDateTime(value: string) {
  return new Date(value).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

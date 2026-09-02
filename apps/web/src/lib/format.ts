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

export function currencySymbol(currency = "GBP"): string {
  return moneyFormatter(currency)
    .formatToParts(0)
    .filter((part) => part.type === "currency")
    .map((part) => part.value)
    .join("");
}

export function formatMoney(amount: number | string, currency = "GBP"): string {
  return moneyFormatter(currency).format(Number(amount));
}

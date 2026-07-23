const CURRENCY_SYMBOLS: Record<string, string> = {
  GBP: "£",
  AED: "AED ",
  USD: "$",
};

export function formatMoney(amount: number, currency = "GBP"): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${amount.toFixed(2)}`;
}

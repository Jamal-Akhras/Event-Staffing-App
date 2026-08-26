export function toLocalInput(value: Date | string) {
  const date = new Date(value);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

export function addHours(localInput: string, hours: number) {
  const date = new Date(localInput);
  date.setTime(date.getTime() + hours * 3_600_000);
  return toLocalInput(date);
}

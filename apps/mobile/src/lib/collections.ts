export function appendUnique<T>(current: T[], added: T[], getId: (item: T) => string): T[] {
  const seen = new Set(current.map(getId));
  const merged = [...current];
  for (const item of added) {
    const id = getId(item);
    if (seen.has(id)) continue;
    seen.add(id);
    merged.push(item);
  }
  return merged;
}

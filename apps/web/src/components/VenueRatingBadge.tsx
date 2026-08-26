type VenueRatingBadgeProps = {
  average?: number | null;
  total?: number;
  loading: boolean;
  unavailable: boolean;
};

export function VenueRatingBadge({ average, total = 0, loading, unavailable }: VenueRatingBadgeProps) {
  const value = loading ? "…" : unavailable ? "—" : average == null ? "New" : average.toFixed(1);
  const label = loading
    ? "Loading venue rating"
    : unavailable
      ? "Venue rating unavailable"
      : average == null
        ? "New venue with no ratings yet"
        : `${average.toFixed(1)} stars from ${total} ${total === 1 ? "rating" : "ratings"}`;

  return (
    <span className="venue-chip-rating" aria-label={label}>
      <span className="venue-chip-star" aria-hidden="true">★</span>
      <span>{value}</span>
      {!loading && !unavailable && total > 0 && <span className="venue-chip-rating-count">({total})</span>}
    </span>
  );
}

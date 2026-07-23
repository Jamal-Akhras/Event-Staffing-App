type SkeletonCardProps = {
  className?: string;
  lines?: number;
  variant?: "card" | "metric" | "row";
};

export function SkeletonCard({ className = "", lines = 3, variant = "card" }: SkeletonCardProps) {
  return (
    <div className={`skeleton-card ${variant} ${className}`} role="status" aria-label="Loading">
      <span className="skeleton-block skeleton-title" />
      <div className="skeleton-lines">
        {Array.from({ length: lines }, (_, index) => (
          <span key={index} className="skeleton-line" />
        ))}
      </div>
    </div>
  );
}

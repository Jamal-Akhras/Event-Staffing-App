export type MarketingIconName =
  | "arrow"
  | "briefcase"
  | "calendar"
  | "check"
  | "clock"
  | "location"
  | "message"
  | "people"
  | "shield"
  | "spark";

type MarketingIconProps = {
  name: MarketingIconName;
  size?: number;
  className?: string;
};

const PATHS: Record<MarketingIconName, string[]> = {
  arrow: ["M5 12h14", "M14 7l5 5-5 5"],
  briefcase: ["M4 7h16v12H4z", "M9 7V4h6v3", "M4 12h16"],
  calendar: ["M5 5h14v15H5z", "M5 9h14", "M8 3v4", "M16 3v4"],
  check: ["M5 12.5l4.5 4.5L19 7.5"],
  clock: ["M12 3a9 9 0 100 18 9 9 0 000-18z", "M12 7v5l3 2"],
  location: ["M12 21s6-5.2 6-11a6 6 0 10-12 0c0 5.8 6 11 6 11z", "M12 7.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"],
  message: ["M4 5h16v12H9l-5 4z", "M8 9h8", "M8 13h5"],
  people: ["M15 11a4 4 0 10-8 0 4 4 0 008 0z", "M3 21a7 7 0 0116 0", "M17 8a3 3 0 013 5", "M19 16a5 5 0 013 5"],
  shield: ["M12 3l7 3v5c0 4.8-2.8 8-7 10-4.2-2-7-5.2-7-10V6z", "M9 12l2 2 4-4"],
  spark: ["M12 2l1.7 5.3L19 9l-5.3 1.7L12 16l-1.7-5.3L5 9l5.3-1.7z", "M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z"],
};

export function MarketingIcon({ name, size = 20, className }: MarketingIconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name].map((path) => <path key={path} d={path} />)}
    </svg>
  );
}

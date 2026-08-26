type IconName =
  | "overview"
  | "shifts"
  | "applications"
  | "schedule"
  | "templates"
  | "workers"
  | "analytics"
  | "settings"
  | "refresh"
  | "alert-triangle"
  | "check";

type IconProps = {
  name: IconName;
  size?: number;
  className?: string;
};

const PATHS: Record<IconName, string> = {
  overview: "M3 12l9-9 9 9M5 10v10h14V10",
  shifts: "M4 7h16v13H4zM8 7V4h8v3",
  applications: "M14 3v5h5M14 3l5 5v11H6V3zM9 13h6M9 17h6",
  schedule: "M5 4h14v16H5zM5 9h14M8 2v4M16 2v4",
  templates: "M4 5h16v6H4zM4 14h7v5H4zM14 14h6v5h-6z",
  workers: "M16 11a4 4 0 10-8 0 4 4 0 008 0zM4 21a7 7 0 0116 0",
  analytics: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  settings: "M12 9a3 3 0 100 6 3 3 0 000-6zM19.4 13.5a7.6 7.6 0 000-3l1.7-1.3-2-3.4-2 .8a7.6 7.6 0 00-2.6-1.5L14 2h-4l-.5 2.1A7.6 7.6 0 006.9 5.6l-2-.8-2 3.4L4.6 9.5a7.6 7.6 0 000 3l-1.7 1.3 2 3.4 2-.8a7.6 7.6 0 002.6 1.5L10 22h4l.5-2.1a7.6 7.6 0 002.6-1.5l2 .8 2-3.4z",
  refresh: "M4 12a8 8 0 0113.7-5.7L20 8M20 4v4h-4M20 12a8 8 0 01-13.7 5.7L4 16M4 20v-4h4",
  "alert-triangle": "M12 3l9 16H3zM12 9v5M12 17h.01",
  check: "M5 13l4 4L19 7",
};

export function Icon({ name, size = 20, className }: IconProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}

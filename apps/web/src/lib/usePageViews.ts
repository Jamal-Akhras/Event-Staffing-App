import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

import { track } from "./analytics";

export function usePageViews() {
  const location = useLocation();
  const entered = useRef(Date.now());
  const previous = useRef<string | null>(null);

  useEffect(() => {
    const now = Date.now();
    if (previous.current !== null) {
      track("page.left", {
        subject_type: "route",
        subject_id: previous.current,
        context: { seconds: Math.round((now - entered.current) / 1000) },
      });
    }
    entered.current = now;
    previous.current = location.pathname;
    track("page.viewed", { subject_type: "route", subject_id: location.pathname });
  }, [location.pathname]);
}

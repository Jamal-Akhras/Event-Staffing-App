import { useCallback, useEffect, useRef } from "react";
import { AppState, type ViewToken } from "react-native";

import { track, trackOnce } from "../../lib/analytics";
import type { FeedShift } from "../../types";

const VIEWED = { itemVisiblePercentThreshold: 50, minimumViewTime: 1000 };
const DWELLED = { itemVisiblePercentThreshold: 75, minimumViewTime: 2000 };

type TimedViewToken = ViewToken & { timestamp?: number };
type Positions = Map<string, number>;

function report(
  name: string,
  tokens: TimedViewToken[],
  slateId: string | null,
  positions: Positions,
  suffix: string
) {
  for (const token of tokens) {
    const shift = token.item as FeedShift | undefined;
    if (!token.isViewable || !shift) continue;
    trackOnce(
      `${suffix}:${shift.shift_id}`,
      name,
      {
        subject_type: "shift",
        subject_id: shift.shift_id,
        slate_id: slateId ?? undefined,
        position: positions.get(shift.shift_id) ?? token.index ?? undefined,
        context: { role: shift.role },
      },
      token.timestamp
    );
  }
}

export function useFeedViewability(items: FeedShift[], slateId: string | null) {
  const slateRef = useRef(slateId);
  const positions = useRef<Positions>(new Map());
  const backgrounded = useRef(false);

  slateRef.current = slateId;
  positions.current = new Map(items.map((item, index) => [item.shift_id, index]));

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => {
      backgrounded.current = state !== "active";
    });
    return () => subscription.remove();
  }, []);

  const onViewed = useCallback((info: { viewableItems: ViewToken[] }) => {
    if (backgrounded.current) return;
    report("shift.viewed", info.viewableItems, slateRef.current, positions.current, "viewed");
  }, []);

  const onDwelled = useCallback((info: { viewableItems: ViewToken[] }) => {
    if (backgrounded.current) return;
    report("shift.dwelled", info.viewableItems, slateRef.current, positions.current, "dwelled");
  }, []);

  const pairs = useRef([
    { viewabilityConfig: VIEWED, onViewableItemsChanged: onViewed },
    { viewabilityConfig: DWELLED, onViewableItemsChanged: onDwelled },
  ]);

  const trackShiftEvent = useCallback((name: string, shift: FeedShift, extra: Record<string, unknown> = {}) => {
    track(name, {
      subject_type: "shift",
      subject_id: shift.shift_id,
      slate_id: slateRef.current ?? undefined,
      position: positions.current.get(shift.shift_id),
      context: extra,
    });
  }, []);

  const trackDwell = useCallback((shift: FeedShift, openedAt: number) => {
    track("shift.detail_closed", {
      subject_type: "shift",
      subject_id: shift.shift_id,
      slate_id: slateRef.current ?? undefined,
      position: positions.current.get(shift.shift_id),
      dwell_ms: Date.now() - openedAt,
    });
  }, []);

  return { viewabilityConfigCallbackPairs: pairs.current, trackShiftEvent, trackDwell };
}

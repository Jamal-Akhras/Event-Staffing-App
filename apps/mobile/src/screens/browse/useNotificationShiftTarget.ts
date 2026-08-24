import type { BottomTabNavigationProp } from "@react-navigation/bottom-tabs";
import { useNavigation, useRoute, type RouteProp } from "@react-navigation/native";
import { useEffect, useRef, useState } from "react";

import { fetchWorker } from "../../lib/api";
import type { RootTabParamList } from "../../navigation/navigationTypes";
import type { FeedShift } from "../../types";

type UseNotificationShiftTargetOptions = {
  items: FeedShift[];
  onOpen: (shift: FeedShift) => void;
  onShowFeed: () => void;
};

export function useNotificationShiftTarget({
  items,
  onOpen,
  onShowFeed,
}: UseNotificationShiftTargetOptions): string | null {
  const navigation = useNavigation<BottomTabNavigationProp<RootTabParamList, "Browse">>();
  const route = useRoute<RouteProp<RootTabParamList, "Browse">>();
  const itemsRef = useRef(items);
  const handledKeyRef = useRef<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  itemsRef.current = items;

  useEffect(() => {
    const shiftId = route.params?.shift_id;
    const targetKey = route.params?.notification_key ?? shiftId;
    if (!shiftId || !targetKey || handledKeyRef.current === targetKey) return;
    handledKeyRef.current = targetKey;
    let active = true;
    setError(null);
    onShowFeed();

    const loaded = itemsRef.current.find((item) => item.shift_id === shiftId);
    const openAndClear = (shift: FeedShift) => {
      if (!active) return;
      onOpen(shift);
      navigation.setParams({ shift_id: undefined, notification_key: undefined });
    };

    if (loaded) {
      openAndClear(loaded);
      return () => {
        active = false;
      };
    }

    fetchWorker<FeedShift>(`/shifts/${encodeURIComponent(shiftId)}`)
      .then(openAndClear)
      .catch(() => {
        if (!active) return;
        setError("This shift is no longer available in Browse.");
        navigation.setParams({ shift_id: undefined, notification_key: undefined });
      });
    return () => {
      active = false;
    };
  }, [navigation, onOpen, onShowFeed, route.params?.notification_key, route.params?.shift_id]);

  return error;
}

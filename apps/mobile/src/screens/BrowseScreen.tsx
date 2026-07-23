import type { BottomSheetModal } from "@gorhom/bottom-sheet";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppState, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";

import { EmptyState } from "../components/EmptyState";
import { SkeletonCard } from "../components/Skeleton";
import { useAuth } from "../contexts/AuthContext";
import { deleteWorker, fetchWorker, getWorkerId, postWorker, putWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { Shift, WorkerFeedState } from "../types";
import { ApplyPanel } from "./browse/ApplyPanel";
import { BrowseFeedCard } from "./browse/BrowseFeedCard";
import { BrowseFilters } from "./browse/BrowseFilters";
import { buildQuickApplyMessage, filterShifts, rankShiftsForFeed, type ShiftFilter } from "./browse/browseUtils";
import { addShiftId, removeShiftId, StatusCard } from "./browse/feedHelpers";
import { ShiftMapView } from "./browse/ShiftMapView";

type ViewMode = "feed" | "map";

export function BrowseScreen() {
  const { user } = useAuth();
  const workerId = user?.worker_profile_id ?? getWorkerId();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("feed");
  const [selectedShift, setSelectedShift] = useState<Shift | null>(null);
  const [applicationMessage, setApplicationMessage] = useState("");
  const [applicationStatus, setApplicationStatus] = useState<string | null>(null);
  const [dismissedShiftIds, setDismissedShiftIds] = useState<Set<string>>(() => new Set());
  const [appliedShiftIds, setAppliedShiftIds] = useState<Set<string>>(() => new Set());
  const [applyingShiftIds, setApplyingShiftIds] = useState<Set<string>>(() => new Set());
  const [lastPassedShift, setLastPassedShift] = useState<Shift | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<ShiftFilter>("all");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [appState, setAppState] = useState(AppState.currentState);
  const applySheetRef = useRef<BottomSheetModal>(null);

  const openApplySheet = useCallback((shift: Shift) => {
    setSelectedShift(shift);
    setApplicationMessage("");
    applySheetRef.current?.present();
  }, []);

  const dismissApplySheet = useCallback(() => {
    setSelectedShift(null);
    setApplicationMessage("");
  }, []);

  const loadShifts = useCallback(async () => {
    try {
      const data = await fetchWorker<Shift[]>("/shifts");
      setShifts(data.filter((shift) => shift.status === "open"));
      setError(null);
    } catch (err) {
      setShifts([]);
      setError((err as Error).message);
    } finally {
      setHasLoaded(true);
    }
  }, []);

  const loadFeedState = useCallback(async () => {
    try {
      const data = await fetchWorker<WorkerFeedState[]>(`/workers/${workerId}/feed-state`);
      setDismissedShiftIds(new Set(data.map((state) => state.shift_id)));
    } catch (err) {
      setError((err as Error).message);
    }
  }, [workerId]);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await loadShifts();
    } finally {
      setIsRefreshing(false);
    }
  }, [loadShifts]);

  useEffect(() => {
    void loadShifts();
    void loadFeedState();
  }, [loadFeedState, loadShifts]);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", setAppState);
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (appState !== "active") return;
    void loadShifts();
    const interval = setInterval(() => void loadShifts(), 15000);
    return () => clearInterval(interval);
  }, [appState, loadShifts]);

  const feedShifts = useMemo(() => {
    const hiddenIds = new Set([...dismissedShiftIds, ...appliedShiftIds]);
    return rankShiftsForFeed(filterShifts(shifts, activeFilter, searchQuery)).filter(
      (shift) => !hiddenIds.has(shift.shift_id)
    );
  }, [activeFilter, appliedShiftIds, dismissedShiftIds, searchQuery, shifts]);

  const feedHeader = (
    <>
      <View style={styles.summary}>
        <Text style={styles.eyebrow}>Recommended</Text>
        <Text style={styles.title}>{feedShifts.length} in your feed</Text>
        <Text style={styles.statsLine}>
          {shifts.length} open  ·  {dismissedShiftIds.size} passed  ·  {appliedShiftIds.size} applied
        </Text>
      </View>

      <BrowseFilters
        activeFilter={activeFilter}
        searchQuery={searchQuery}
        onFilterChange={setActiveFilter}
        onSearchChange={setSearchQuery}
      />

      {error && <StatusCard tone="error" message={error} />}
      {lastPassedShift && (
        <StatusCard
          actionLabel="Undo"
          message={`${lastPassedShift.role} hidden from this feed.`}
          tone="success"
          onAction={() => handleUndoPass(lastPassedShift)}
        />
      )}
      {applicationStatus && <StatusCard tone="success" message={applicationStatus} />}
    </>
  );

  return (
    <View style={styles.container}>
      <View style={styles.toggleRow}>
        <Pressable
          style={[styles.toggleBtn, viewMode === "feed" && styles.toggleBtnActive]}
          onPress={() => setViewMode("feed")}
        >
          <Text style={[styles.toggleText, viewMode === "feed" && styles.toggleTextActive]}>
            Feed
          </Text>
        </Pressable>
        <Pressable
          style={[styles.toggleBtn, viewMode === "map" && styles.toggleBtnActive]}
          onPress={() => setViewMode("map")}
        >
          <Text style={[styles.toggleText, viewMode === "map" && styles.toggleTextActive]}>
            Map
          </Text>
        </Pressable>
      </View>

      {viewMode === "map" ? (
        <ShiftMapView
          shifts={shifts}
          onApply={(shift) => { setViewMode("feed"); openApplySheet(shift); }}
        />
      ) : (
        <FlatList
          contentContainerStyle={styles.content}
          data={feedShifts}
          keyExtractor={(shift) => shift.shift_id}
          ListEmptyComponent={
            !hasLoaded ? (
              <View>
                <SkeletonCard lines={3} />
                <SkeletonCard lines={3} />
                <SkeletonCard lines={3} />
              </View>
            ) : !error ? (
              <EmptyState
                title="No shifts match"
                message="Try a broader filter or check back as venues post new work."
              />
            ) : null
          }
          ListHeaderComponent={feedHeader}
          refreshControl={
            <RefreshControl
              colors={[COLORS.primary]}
              refreshing={isRefreshing}
              tintColor={COLORS.primary}
              onRefresh={() => void handleRefresh()}
            />
          }
          renderItem={({ item }) => (
            <BrowseFeedCard
              isApplying={applyingShiftIds.has(item.shift_id)}
              shift={item}
              onDetails={() => openApplySheet(item)}
              onPass={() => void handlePass(item)}
              onQuickApply={() => void handleQuickApply(item)}
            />
          )}
          showsVerticalScrollIndicator={false}
        />
      )}

      <ApplyPanel
        ref={applySheetRef}
        shift={selectedShift}
        message={applicationMessage}
        onApply={handlePanelApply}
        onChangeMessage={setApplicationMessage}
        onDismiss={dismissApplySheet}
      />
    </View>
  );

  async function handlePass(shift: Shift) {
    addShiftId(setDismissedShiftIds, shift.shift_id);
    setLastPassedShift(shift);
    setApplicationStatus(null);
    try {
      await putWorker<WorkerFeedState>(`/workers/${workerId}/feed-state/${shift.shift_id}`, {
        action: "passed",
        now: new Date().toISOString(),
      });
    } catch (err) {
      removeShiftId(setDismissedShiftIds, shift.shift_id);
      setLastPassedShift(null);
      setApplicationStatus((err as Error).message);
      clearStatusSoon();
    }
  }

  async function handleUndoPass(shift: Shift) {
    removeShiftId(setDismissedShiftIds, shift.shift_id);
    setLastPassedShift(null);
    try {
      await deleteWorker(`/workers/${workerId}/feed-state/${shift.shift_id}`);
      setApplicationStatus(`${shift.role} restored to your feed.`);
      clearStatusSoon();
    } catch (err) {
      addShiftId(setDismissedShiftIds, shift.shift_id);
      setApplicationStatus((err as Error).message);
      clearStatusSoon();
    }
  }

  async function handleQuickApply(shift: Shift) {
    await applyToShift(shift, buildQuickApplyMessage(shift));
  }

  async function handlePanelApply() {
    if (!selectedShift) return;
    const message = applicationMessage.trim() || buildQuickApplyMessage(selectedShift);
    await applyToShift(selectedShift, message);
    applySheetRef.current?.dismiss();
  }

  async function applyToShift(shift: Shift, message: string) {
    addShiftId(setApplyingShiftIds, shift.shift_id);
    try {
      await postWorker("/applications", {
        shift_id: shift.shift_id,
        worker_id: workerId,
        message,
        now: new Date().toISOString(),
      });
      addShiftId(setAppliedShiftIds, shift.shift_id);
      setLastPassedShift(null);
      setApplicationStatus(`${shift.role} application submitted.`);
      clearStatusSoon();
    } catch (err) {
      setApplicationStatus((err as Error).message);
    } finally {
      removeShiftId(setApplyingShiftIds, shift.shift_id);
    }
  }

  function clearStatusSoon() {
    setTimeout(() => setApplicationStatus(null), 3000);
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.canvas },
  toggleRow: {
    flexDirection: "row",
    margin: 16,
    marginBottom: 0,
    padding: 3,
    borderRadius: 10,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: 8,
    alignItems: "center",
  },
  toggleBtnActive: { backgroundColor: COLORS.primary },
  toggleText: { color: COLORS.inkMuted, fontWeight: "700", fontSize: 13 },
  toggleTextActive: { color: COLORS.onPrimary },
  content: { padding: 16, paddingBottom: 44 },
  summary: { marginBottom: 16 },
  eyebrow: {
    color: COLORS.primary,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: { color: COLORS.ink, fontSize: 26, fontWeight: "800", marginTop: 4, letterSpacing: -0.3 },
  statsLine: {
    marginTop: 6,
    color: COLORS.inkMuted,
    fontSize: 13,
    fontWeight: "500",
  },
});

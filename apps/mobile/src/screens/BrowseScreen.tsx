import type { BottomSheetModal } from "@gorhom/bottom-sheet";
import { useFocusEffect, useNavigation } from "@react-navigation/native";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  AppState,
  FlatList,
  Pressable,
  RefreshControl,
  Text,
  View,
} from "react-native";

import { useAuth } from "../contexts/AuthContext";
import { deleteWorker, getWorkerId, postWorker, putWorker } from "../lib/api";
import { COLORS } from "../theme/colors";
import type { FeedShift } from "../types";
import { ApplyPanel } from "./browse/ApplyPanel";
import { BrowseFeedCard } from "./browse/BrowseFeedCard";
import { BrowseFilters } from "./browse/BrowseFilters";
import { browseScreenStyles as styles } from "./browse/browseScreenStyles";
import { buildQuickApplyMessage } from "./browse/browseUtils";
import { FeedEmptyState } from "./browse/FeedEmptyState";
import { addShiftId, removeShiftId, StatusCard } from "./browse/feedHelpers";
import { ShiftMapView } from "./browse/ShiftMapView";
import { useWorkerFeed } from "./browse/useWorkerFeed";
import { useNotificationShiftTarget } from "./browse/useNotificationShiftTarget";

type ViewMode = "feed" | "map";

export function BrowseScreen() {
  const { user } = useAuth();
  const navigation = useNavigation();
  const workerId = user?.worker_profile_id ?? getWorkerId();
  const feed = useWorkerFeed();
  const [viewMode, setViewMode] = useState<ViewMode>("feed");
  const [selectedShift, setSelectedShift] = useState<FeedShift | null>(null);
  const [applicationMessage, setApplicationMessage] = useState("");
  const [applicationStatus, setApplicationStatus] = useState<string | null>(null);
  const [applyingShiftIds, setApplyingShiftIds] = useState<Set<string>>(() => new Set());
  const [lastPassedShift, setLastPassedShift] = useState<FeedShift | null>(null);
  const applySheetRef = useRef<BottomSheetModal>(null);

  const { refresh } = feed;
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (next) => {
      if (next === "active") void refresh();
    });
    return () => subscription.remove();
  }, [refresh]);

  const hasFocusedRef = useRef(false);
  useFocusEffect(
    useCallback(() => {
      if (!hasFocusedRef.current) {
        hasFocusedRef.current = true;
        return;
      }
      void refresh();
    }, [refresh])
  );

  const openApplySheet = useCallback((shift: FeedShift) => {
    setSelectedShift(shift);
    setApplicationMessage("");
    applySheetRef.current?.present();
  }, []);
  const showFeed = useCallback(() => setViewMode("feed"), []);
  const notificationTargetError = useNotificationShiftTarget({
    items: feed.items,
    onOpen: openApplySheet,
    onShowFeed: showFeed,
  });

  const dismissApplySheet = useCallback(() => {
    setSelectedShift(null);
    setApplicationMessage("");
  }, []);

  const goToProfile = useCallback(() => {
    navigation.navigate("Profile" as never);
  }, [navigation]);

  const highPayThreshold = feed.market ? Number(feed.market.high_pay_threshold) : null;

  const feedHeader = (
    <>
      <View style={styles.summary}>
        <Text style={styles.eyebrow}>Recommended</Text>
        <Text style={styles.title}>
          {feed.items.length}
          {feed.hasMore ? "+" : ""} in your feed
        </Text>
        {feed.market && <Text style={styles.statsLine}>{feed.market.name} · newest first</Text>}
      </View>

      <BrowseFilters
        activeFilter={feed.activeFilter}
        searchQuery={feed.searchQuery}
        onFilterChange={feed.setActiveFilter}
        onSearchChange={feed.setSearchQuery}
      />

      {feed.error && feed.status === "ready" && (
        <StatusCard tone="error" message={feed.error} />
      )}
      {notificationTargetError && <StatusCard tone="error" message={notificationTargetError} />}
      {lastPassedShift && (
        <StatusCard
          actionLabel="Undo"
          message={`${lastPassedShift.role} hidden from this feed.`}
          tone="success"
          onAction={() => void handleUndoPass(lastPassedShift)}
        />
      )}
      {applicationStatus && <StatusCard tone="success" message={applicationStatus} />}
    </>
  );

  const emptyComponent = (
    <FeedEmptyState
      status={feed.status}
      error={feed.error}
      onRetry={() => void feed.retry()}
      onCompleteProfile={goToProfile}
    />
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
          shifts={feed.items}
          onApply={(shift) => {
            setViewMode("feed");
            openApplySheet(shift as FeedShift);
          }}
        />
      ) : (
        <FlatList
          contentContainerStyle={styles.content}
          data={feed.items}
          keyExtractor={(shift) => shift.shift_id}
          ListEmptyComponent={emptyComponent}
          ListHeaderComponent={feedHeader}
          ListFooterComponent={
            feed.isLoadingMore ? (
              <ActivityIndicator color={COLORS.primary} style={styles.footerSpinner} />
            ) : null
          }
          onEndReached={() => void feed.loadMore()}
          onEndReachedThreshold={0.4}
          refreshControl={
            <RefreshControl
              colors={[COLORS.primary]}
              refreshing={feed.isRefreshing}
              tintColor={COLORS.primary}
              onRefresh={() => void feed.refresh()}
            />
          }
          renderItem={({ item }) => (
            <BrowseFeedCard
              highPayThreshold={highPayThreshold}
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

  async function handlePass(shift: FeedShift) {
    feed.removeItem(shift.shift_id);
    setLastPassedShift(shift);
    setApplicationStatus(null);
    try {
      await putWorker(`/workers/${workerId}/feed-state/${shift.shift_id}`, {
        action: "passed",
        now: new Date().toISOString(),
      });
    } catch (err) {
      setLastPassedShift(null);
      setApplicationStatus((err as Error).message);
      clearStatusSoon();
      void feed.refresh();
    }
  }

  async function handleUndoPass(shift: FeedShift) {
    setLastPassedShift(null);
    try {
      await deleteWorker(`/workers/${workerId}/feed-state/${shift.shift_id}`);
      setApplicationStatus(`${shift.role} restored to your feed.`);
    } catch (err) {
      setApplicationStatus((err as Error).message);
    }
    clearStatusSoon();
    void feed.refresh();
  }

  async function handleQuickApply(shift: FeedShift) {
    await applyToShift(shift, buildQuickApplyMessage(shift));
  }

  async function handlePanelApply() {
    if (!selectedShift) return;
    const message = applicationMessage.trim() || buildQuickApplyMessage(selectedShift);
    await applyToShift(selectedShift, message);
    applySheetRef.current?.dismiss();
  }

  async function applyToShift(shift: FeedShift, message: string) {
    addShiftId(setApplyingShiftIds, shift.shift_id);
    try {
      await postWorker("/applications", {
        shift_id: shift.shift_id,
        worker_id: workerId,
        message,
        now: new Date().toISOString(),
      });
      feed.removeItem(shift.shift_id);
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

import { View } from "react-native";

import { EmptyState } from "../../components/EmptyState";
import { SkeletonCard } from "../../components/Skeleton";
import type { FeedStatus } from "./useWorkerFeed";

type FeedEmptyStateProps = {
  status: FeedStatus;
  error: string | null;
  onRetry: () => void;
  onCompleteProfile: () => void;
};

export function FeedEmptyState({ status, error, onRetry, onCompleteProfile }: FeedEmptyStateProps) {
  if (status === "loading") {
    return (
      <View>
        <SkeletonCard lines={3} />
        <SkeletonCard lines={3} />
        <SkeletonCard lines={3} />
      </View>
    );
  }

  if (status === "missing-market") {
    return (
      <EmptyState
        title="Choose your city"
        message="Pick the city you work in on your profile and we'll show shifts near you."
        actionLabel="Complete profile"
        onAction={onCompleteProfile}
      />
    );
  }

  if (status === "error") {
    return (
      <EmptyState
        title="Couldn't load your feed"
        message={error ?? "Something went wrong. Please try again."}
        actionLabel="Retry"
        onAction={onRetry}
      />
    );
  }

  return (
    <EmptyState
      title="No shifts match"
      message="Try a broader filter or check back as venues post new work."
    />
  );
}

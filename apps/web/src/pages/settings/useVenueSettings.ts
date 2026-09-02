import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { putJson, uploadFile } from "../../lib/api";
import { useVenue } from "../../lib/useVenue";
import type { Venue } from "../../types/operations";

export type VenueDraft = {
  name: string;
  venue_type: string;
  market_id: string;
  default_location: string;
  contact_email: string;
  contact_phone: string;
  photos: string[];
  pool_hours: number | null;
  market_lead_hours: number | null;
};

type Notify = (type: "success" | "error", message: string) => void;

function draftFrom(venue: Venue): VenueDraft {
  return {
    name: venue.name ?? "",
    venue_type: venue.venue_type ?? "",
    market_id: venue.market_id ?? "",
    default_location: venue.default_location ?? "",
    contact_email: venue.contact_email ?? "",
    contact_phone: venue.contact_phone ?? "",
    photos: venue.photos ?? [],
    pool_hours: venue.escalation_policy == null ? 24 : venue.escalation_policy.pool_hours,
    market_lead_hours: venue.escalation_policy == null ? 48 : venue.escalation_policy.market_lead_hours,
  };
}

export function useVenueSettings(notify: Notify) {
  const queryClient = useQueryClient();
  const venue = useVenue();
  const [draft, setDraft] = useState<VenueDraft | null>(null);

  useEffect(() => {
    if (venue.data && !draft) setDraft(draftFrom(venue.data));
  }, [venue.data, draft]);

  const saved = venue.data ? draftFrom(venue.data) : null;
  const dirty = Boolean(draft && saved && JSON.stringify(draft) !== JSON.stringify(saved));

  const save = useMutation({
    mutationFn: (next: VenueDraft) =>
      putJson<Venue>("/venues/me", {
        name: next.name || undefined,
        venue_type: next.venue_type || undefined,
        market_id: next.market_id || undefined,
        default_location: next.default_location || undefined,
        contact_email: next.contact_email || undefined,
        contact_phone: next.contact_phone || undefined,
        photos: next.photos,
        escalation_policy: { pool_hours: next.pool_hours, market_lead_hours: next.market_lead_hours },
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["venue"], updated);
      setDraft(draftFrom(updated));
      notify("success", "Settings saved.");
    },
    onError: (error: Error) => notify("error", error.message),
  });

  const upload = useMutation({
    mutationFn: ({ path, file }: { path: string; file: File }) => uploadFile<{ url: string }>(path, file),
    onError: (error: Error) => notify("error", error.message),
  });

  const uploadLogo = (file: File) =>
    upload.mutate(
      { path: "/uploads/venue-avatar", file },
      {
        onSuccess: (result) => {
          queryClient.setQueryData<Venue>(["venue"], (current) => current && { ...current, avatar_url: result.url });
          notify("success", "Logo updated.");
        },
      }
    );

  const uploadPhoto = (file: File) =>
    upload.mutate(
      { path: "/uploads/venue-photo", file },
      { onSuccess: (result) => setDraft((current) => current && { ...current, photos: [...current.photos, result.url] }) }
    );

  return {
    venue: venue.data,
    loading: venue.isPending,
    error: venue.error as Error | null,
    draft,
    update: (patch: Partial<VenueDraft>) => setDraft((current) => current && { ...current, ...patch }),
    dirty,
    saving: save.isPending,
    save: () => draft && save.mutate(draft),
    discard: () => setDraft(saved),
    uploading: upload.isPending,
    uploadLogo,
    uploadPhoto,
  };
}

export type VenueSettings = ReturnType<typeof useVenueSettings>;

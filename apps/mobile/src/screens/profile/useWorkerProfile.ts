import * as ImagePicker from "expo-image-picker";
import { useCallback, useEffect, useState } from "react";

import { fetchWorker, getWorkerId, putWorker, uploadWorkerAvatar } from "../../lib/api";
import type { WorkerProfile } from "../../types";
import { emptyProfileForm, formToPayload, profileToForm, type ProfileForm } from "./profileForm";

export function useWorkerProfile() {
  const workerId = getWorkerId();
  const [form, setForm] = useState<ProfileForm>({ ...emptyProfileForm, worker_id: workerId });
  const [profile, setProfile] = useState<WorkerProfile | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [allowRecontact, setAllowRecontact] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await fetchWorker<WorkerProfile>(`/workers/${workerId}`);
      setProfile(data);
      setForm(profileToForm(data));
      setAllowRecontact(data.allow_venue_recontact ?? false);
      setStatus(null);
    } catch (err) {
      setProfile(null);
      setStatus((err as Error).message);
    }
  }, [workerId]);

  useEffect(() => {
    load();
  }, [load]);

  const persist = useCallback(
    async (allowVenueRecontact: boolean) => {
      setStatus(null);
      try {
        const data = await putWorker<WorkerProfile>(`/workers/${workerId}`, {
          ...formToPayload(form),
          allow_venue_recontact: allowVenueRecontact,
        });
        setProfile(data);
        setStatus("Profile saved.");
      } catch (err) {
        setStatus((err as Error).message);
      }
    },
    [form, workerId]
  );

  const pickAvatar = useCallback(async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setStatus("Photo library access is required to change your avatar.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (result.canceled || !result.assets[0]) return;
    setUploading(true);
    try {
      const asset = result.assets[0];
      const data = await uploadWorkerAvatar(asset.uri, asset.mimeType ?? "image/jpeg");
      setProfile((current) => (current ? { ...current, avatar_url: data.url } : current));
      setStatus("Photo updated.");
    } catch (err) {
      setStatus((err as Error).message);
    } finally {
      setUploading(false);
    }
  }, []);

  return {
    workerId,
    form,
    setForm,
    profile,
    status,
    uploading,
    allowRecontact,
    setAllowRecontact,
    persist,
    save: () => persist(allowRecontact),
    pickAvatar,
    reload: load,
  };
}

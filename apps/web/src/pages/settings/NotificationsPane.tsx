import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "../../components/Toast";
import {
  fetchNotificationPreferences,
  saveNotificationPreferences,
  type NotificationPreferences,
} from "../../lib/notificationsApi";
import { Group, Switch } from "./SettingsRows";

const CHANNELS = [
  ["in_app", "In the app", "The bell in the top bar"],
  ["email", "Email", "A copy of important updates in your inbox"],
  ["push", "Push", "Phone alerts once the mobile app is installed"],
] as const;

const CATEGORIES = [
  ["applications", "Applications", "Someone applies or withdraws"],
  ["shift_changes", "Shift changes", "Edits, closures, cancellations"],
  ["messages", "Messages", "A worker writes to you"],
  ["reminders", "Reminders", "Tomorrow's shifts still need people"],
  ["attendance", "Attendance", "Check-ins, check-outs, no-shows"],
] as const;

export function NotificationsPane() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const prefs = useQuery({ queryKey: ["notification-preferences"], queryFn: fetchNotificationPreferences });
  const save = useMutation({
    mutationFn: saveNotificationPreferences,
    onSuccess: (saved) => queryClient.setQueryData(["notification-preferences"], saved),
    onError: (error: Error) => toast({ type: "error", message: error.message }),
  });

  if (prefs.error) return <p className="st-error">{(prefs.error as Error).message}</p>;
  if (!prefs.data) return <p className="st-muted">Loading preferences…</p>;
  const current: NotificationPreferences = prefs.data;
  const busy = save.isPending;

  return (
    <>
      <Group
        title="Where"
        hint="Saves as you toggle."
        rows={CHANNELS.map(([key, label, hint]) => ({
          key,
          label,
          hint,
          control: (
            <Switch
              checked={current.channels[key]}
              disabled={busy}
              label={label}
              onChange={() => save.mutate({ ...current, channels: { ...current.channels, [key]: !current.channels[key] } })}
            />
          ),
        }))}
      />
      <Group
        title="What"
        rows={CATEGORIES.map(([key, label, hint]) => ({
          key,
          label,
          hint,
          control: (
            <Switch
              checked={current.categories[key]}
              disabled={busy}
              label={label}
              onChange={() => save.mutate({ ...current, categories: { ...current.categories, [key]: !current.categories[key] } })}
            />
          ),
        }))}
      />
    </>
  );
}

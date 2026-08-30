import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteJson, fetchJson, postJson, putJson } from "../../lib/api";
import type { Shift } from "../../types/operations";
import type { Template, TemplateFormData } from "../../types/templates";

export type GenerateRequest = {
  templateId: string;
  startDate: string;
  endDate: string;
  startTime: string;
  daysOfWeek: number[];
};

type Notify = (type: "success" | "error", message: string) => void;

function pad(value: number) {
  return String(value).padStart(2, "0");
}

export function offsetOf(date: Date) {
  const minutes = -date.getTimezoneOffset();
  const sign = minutes >= 0 ? "+" : "-";
  const absolute = Math.abs(minutes);
  return `${sign}${pad(Math.floor(absolute / 60))}:${pad(absolute % 60)}`;
}

export function localIso(day: string, time: string) {
  return `${day}T${time}:00${offsetOf(new Date(`${day}T${time}:00`))}`;
}

export function crossesClockChange(startDay: string, endDay: string) {
  return offsetOf(new Date(`${startDay}T12:00:00`)) !== offsetOf(new Date(`${endDay}T12:00:00`));
}

export function matchingDays(startDay: string, endDay: string, daysOfWeek: number[]) {
  const start = new Date(`${startDay}T12:00:00`);
  const end = new Date(`${endDay}T12:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return 0;
  let count = 0;
  for (const cursor = new Date(start); cursor <= end; cursor.setDate(cursor.getDate() + 1)) {
    if (daysOfWeek.includes((cursor.getDay() + 6) % 7)) count += 1;
  }
  return count;
}

export function useTemplates() {
  return useQuery({ queryKey: ["templates"], queryFn: () => fetchJson<Template[]>("/templates") });
}

export function useTemplateActions(notify: Notify) {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["templates"] });

  const save = useMutation({
    mutationFn: ({ template, form }: { template: Template | null; form: TemplateFormData }) =>
      template
        ? putJson<Template>(`/templates/${template.template_id}`, form)
        : postJson<Template>("/templates", form),
    onSuccess: async (_result, { template }) => {
      await invalidate();
      notify("success", template ? "Template updated." : "Template saved.");
    },
    onError: (error: Error) => notify("error", error.message),
  });

  const remove = useMutation({
    mutationFn: (templateId: string) => deleteJson(`/templates/${templateId}`),
    onSuccess: async () => {
      await invalidate();
      notify("success", "Template deleted.");
    },
    onError: (error: Error) => notify("error", error.message),
  });

  const generate = useMutation({
    mutationFn: (request: GenerateRequest) =>
      postJson<Shift[]>(`/templates/${request.templateId}/generate`, {
        start_date: localIso(request.startDate, request.startTime),
        end_date: localIso(request.endDate, request.startTime),
        start_time: request.startTime,
        days_of_week: request.daysOfWeek,
      }),
    onSuccess: async (shifts) => {
      await queryClient.invalidateQueries({ queryKey: ["shifts"] });
      notify("success", `${shifts.length} ${shifts.length === 1 ? "shift" : "shifts"} posted.`);
    },
    onError: (error: Error) => notify("error", error.message),
  });

  return { save, remove, generate };
}

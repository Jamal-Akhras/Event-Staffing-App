export type Template = {
  template_id: string;
  operator_id: string;
  name: string;
  role: string;
  location: string;
  duration_hours: number;
  pay_rate: string;
  workers_needed: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type TemplateFormData = {
  name: string;
  role: string;
  location: string;
  duration_hours: number;
  pay_rate: number;
  workers_needed: number;
  notes: string;
};

export const emptyTemplateForm: TemplateFormData = {
  name: "",
  role: "",
  location: "",
  duration_hours: 4,
  pay_rate: 25,
  workers_needed: 1,
  notes: "",
};

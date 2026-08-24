import type { WorkerProfile } from "../../types";

export type ProfileForm = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  market_id: string;
  experience_years: string;
  bio: string;
  languages: string;
  email: string;
  phone: string;
  address: string;
  emergency_contact: string;
  pay_rate: string;
  notes: string;
};

export const emptyProfileForm: ProfileForm = {
  worker_id: "",
  display_name: "",
  role: "",
  city: "",
  market_id: "",
  experience_years: "0",
  bio: "",
  languages: "",
  email: "",
  phone: "",
  address: "",
  emergency_contact: "",
  pay_rate: "",
  notes: "",
};

export function profileToForm(profile: WorkerProfile): ProfileForm {
  return {
    worker_id: profile.worker_id,
    display_name: profile.display_name,
    role: profile.role,
    city: profile.city,
    market_id: profile.market_id ?? "",
    experience_years: String(profile.experience_years),
    bio: profile.bio ?? "",
    languages: profile.languages.join(", "),
    email: profile.email ?? "",
    phone: profile.phone ?? "",
    address: profile.address ?? "",
    emergency_contact: profile.emergency_contact ?? "",
    pay_rate: profile.pay_rate ? String(profile.pay_rate) : "",
    notes: profile.notes ?? "",
  };
}

export function formToPayload(form: ProfileForm) {
  return {
    display_name: form.display_name,
    role: form.role,
    city: form.city,
    market_id: form.market_id || null,
    experience_years: Number(form.experience_years || 0),
    bio: form.bio || null,
    languages: form.languages
      .split(",")
      .map((value) => value.trim())
      .filter((value) => value.length > 0),
    email: form.email || null,
    phone: form.phone || null,
    address: form.address || null,
    emergency_contact: form.emergency_contact || null,
    pay_rate: form.pay_rate ? Number(form.pay_rate) : null,
    notes: form.notes || null,
    now: new Date().toISOString(),
  };
}

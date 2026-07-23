export type Shift = {
  shift_id: string;
  operator_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number;
  notes?: string | null;
  status: string;
  workers_needed?: number;
  workers_filled?: number;
  currency?: string;
  latitude?: number | null;
  longitude?: number | null;
};

export type Booking = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  state: string;
  allowed_transitions: string[];
  checked_in_at?: string | null;
  checked_out_at?: string | null;
  confirmed_at?: string | null;
};

export type Application = {
  application_id: string;
  shift_id: string;
  worker_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
};

export type WorkerFeedState = {
  worker_id: string;
  shift_id: string;
  action: "passed";
  created_at: string;
  updated_at: string;
};

export type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  emergency_contact?: string | null;
  pay_rate?: number | null;
  notes?: string | null;
  updated_at: string;
  avatar_url?: string | null;
  allow_venue_recontact?: boolean;
};

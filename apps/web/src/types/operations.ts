export type Shift = {
  shift_id: string;
  operator_id?: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: string;
  status: string;
  created_at: string;
  notes?: string | null;
  workers_needed: number;
  workers_filled: number;
  currency?: string;
  updated_at?: string | null;
  closed_at?: string | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
  origin?: "assigned" | "pool" | "market";
  assigned_worker_id?: string | null;
  offer_pool_at?: string | null;
  publish_market_at?: string | null;
  rota_state?: "draft" | "published";
  needs_attention?: boolean;
};

export type Application = {
  application_id: string;
  worker_id: string;
  shift_id: string;
  operator_id: string;
  start_time: string;
  end_time: string;
  status: string;
  message?: string | null;
  booking_id?: string | null;
  created_at: string;
  decided_at?: string | null;
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
  updated_at: string;
};

export type Booking = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  start_time: string;
  end_time: string;
  state: string;
  created_at: string;
  checked_in_at?: string | null;
  checked_out_at?: string | null;
  no_show_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
  payment_method?: string | null;
  check_in_code?: string | null;
  completion_code?: string | null;
};

export type Venue = {
  venue_id: string;
  name: string;
  country: string;
  currency: string;
  market_id: string | null;
  timezone: string | null;
  venue_type?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  default_location?: string | null;
  avatar_url?: string | null;
  photos: string[];
  escalation_policy?: {
    named_offer_hours: number | null;
    team_hours: number | null;
    pool_hours: number | null;
    market_lead_hours: number | null;
  } | null;
};

export type VenueRatingSummary = {
  venue_id: string;
  avg_stars: number | null;
  total_ratings: number;
};

export type CompletedShift = {
  booking_id: string;
  shift_id: string;
  worker_id: string;
  start_time: string;
  role: string;
  location: string;
  operator_rating: number | null;
};

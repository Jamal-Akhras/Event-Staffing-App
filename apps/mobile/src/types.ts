export type Shift = {
  shift_id: string;
  operator_id: string;
  role: string;
  location: string;
  start_time: string;
  end_time: string;
  pay_rate: number | string;
  notes?: string | null;
  status: string;
  workers_needed?: number;
  workers_filled?: number;
  currency?: string;
  latitude?: number | null;
  longitude?: number | null;
};

export type Market = {
  market_id: string;
  name: string;
  country: string;
  currency: string;
  timezone: string;
  high_pay_threshold: string;
};

export type FeedVenue = {
  venue_id: string;
  name: string;
  avatar_url?: string | null;
};

export type FeedShift = Shift & {
  created_at?: string;
  venue?: FeedVenue | null;
};

export type WorkerFeedPage = {
  items: FeedShift[];
  next_cursor: string | null;
  market: Market;
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
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
  cancelled_by_user_id?: string | null;
  completion_code?: string | null;
};

export type PendingRating = {
  booking_id: string;
  shift_id: string;
  target_id: string;
  target_name: string;
  target_avatar_url?: string | null;
  shift_role: string;
  shift_location: string;
  start_time: string;
  end_time: string;
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
  withdrawn_at?: string | null;
  withdrawal_reason?: string | null;
};

export type WorkerProfile = {
  worker_id: string;
  display_name: string;
  role: string;
  city: string;
  market_id?: string | null;
  experience_years: number;
  reliability_score: number;
  badges: string[];
  bio?: string | null;
  languages: string[];
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  emergency_contact?: string | null;
  pay_rate?: number | string | null;
  notes?: string | null;
  updated_at: string;
  avatar_url?: string | null;
  allow_venue_recontact?: boolean;
};

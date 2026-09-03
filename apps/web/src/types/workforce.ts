export type RelationshipType = "permanent" | "part_time" | "bank" | "pool" | "one_off";

export type EmployedType = Extract<RelationshipType, "permanent" | "part_time" | "bank">;

export type JoinCode = {
  code: string;
  venue_id: string;
  relationship_type: RelationshipType;
  default_role: string | null;
  max_redemptions: number;
  redeemed: number;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
};

export type WorkerRelationship = {
  relationship_id: string;
  venue_id: string;
  worker_id: string;
  relationship_type: RelationshipType;
  status: "invited" | "active" | "ended";
  default_role: string | null;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  updated_at: string;
};

export const RELATIONSHIP_LABELS: Record<RelationshipType, string> = {
  permanent: "Permanent",
  part_time: "Part time",
  bank: "Bank",
  pool: "Pool",
  one_off: "Worked once",
};

export type TimeOffStatus = "pending" | "approved" | "declined" | "withdrawn";

export type TimeOffRequest = {
  request_id: string;
  worker_id: string;
  venue_id: string;
  start_time: string;
  end_time: string;
  status: TimeOffStatus;
  reason: string;
  created_at: string;
  updated_at: string;
  decided_at: string | null;
  decided_by_user_id: string | null;
};

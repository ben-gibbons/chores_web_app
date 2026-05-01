export type RecurrenceFreq = "daily" | "weekly" | "biweekly" | "monthly";
export type AssignmentMode = "pinned" | "round_robin";

export interface TeamMember {
  id: number;
  name: string;
  color: string;
  active: boolean;
}

export const MEMBER_COLORS = [
  "#ef4444",
  "#f97316",
  "#f59e0b",
  "#eab308",
  "#10b981",
  "#14b8a6",
  "#0ea5e9",
  "#3b82f6",
  "#8b5cf6",
  "#ec4899",
] as const;

export interface Chore {
  id: number;
  title: string;
  description: string;
  recurrence_freq: RecurrenceFreq;
  start_date: string;
  assignment_mode: AssignmentMode;
  pinned_member_id: number | null;
  rotation_order: number[] | null;
  active: boolean;
}

export interface ChoreInput {
  title: string;
  description: string;
  recurrence_freq: RecurrenceFreq;
  start_date: string;
  assignment_mode: AssignmentMode;
  pinned_member_id: number | null;
  rotation_order: number[] | null;
}

export interface Occurrence {
  id: number;
  chore_id: number;
  chore_title: string;
  scheduled_date: string;
  assigned_member_id: number | null;
  assigned_member_name: string | null;
  assigned_member_color: string | null;
  completed_at: string | null;
  completed_by_member_id: number | null;
}

export type RecurrenceFreq = "daily" | "weekly" | "biweekly" | "monthly";
export type AssignmentMode = "pinned" | "round_robin";

export interface TeamMember {
  id: number;
  name: string;
  active: boolean;
}

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
  completed_at: string | null;
  completed_by_member_id: number | null;
}

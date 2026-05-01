import type { Chore, ChoreInput, Occurrence, TeamMember } from "./types.js";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listMembers: () => request<TeamMember[]>("/api/team-members"),
  createMember: (name: string, color: string) =>
    request<TeamMember>("/api/team-members", {
      method: "POST",
      body: JSON.stringify({ name, color }),
    }),
  deleteMember: (id: number) =>
    request<void>(`/api/team-members/${id}`, { method: "DELETE" }),

  listChores: () => request<Chore[]>("/api/chores"),
  createChore: (input: ChoreInput) =>
    request<Chore>("/api/chores", {
      method: "POST",
      body: JSON.stringify(input),
    }),
  deleteChore: (id: number) =>
    request<void>(`/api/chores/${id}`, { method: "DELETE" }),

  listOccurrences: (start: string, end: string) =>
    request<Occurrence[]>(
      `/api/occurrences?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`,
    ),
  markComplete: (id: number) =>
    request<Occurrence>(`/api/occurrences/${id}/complete`, { method: "PATCH" }),
  unmarkComplete: (id: number) =>
    request<Occurrence>(`/api/occurrences/${id}/complete`, { method: "DELETE" }),
  reassign: (id: number, memberId: number) =>
    request<Occurrence>(`/api/occurrences/${id}/reassign`, {
      method: "PATCH",
      body: JSON.stringify({ member_id: memberId }),
    }),
};

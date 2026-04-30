import { Calendar } from "@fullcalendar/core";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

import { api } from "./api.js";
import { choreModal, memberModal, occurrenceModal } from "./modals.js";
import type { Chore, Occurrence, TeamMember } from "./types.js";

let cachedMembers: TeamMember[] = [];
let cachedChores: Chore[] = [];
let calendar: Calendar | null = null;

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((p) => p[0]!.toUpperCase())
    .slice(0, 2)
    .join("");
}

function freqLabel(c: Chore): string {
  return c.recurrence_freq.charAt(0).toUpperCase() + c.recurrence_freq.slice(1);
}

function memberName(id: number | null): string {
  if (id === null) return "Unassigned";
  return cachedMembers.find((m) => m.id === id)?.name ?? `#${id}`;
}

function renderMembers(): void {
  const list = document.getElementById("members-list") as HTMLUListElement | null;
  if (!list) return;
  list.innerHTML = "";
  if (cachedMembers.length === 0) {
    const empty = document.createElement("li");
    empty.className = "list-empty";
    empty.textContent = "No team members yet.";
    list.appendChild(empty);
    return;
  }
  for (const m of cachedMembers) {
    const li = document.createElement("li");
    li.className = "list-row";
    const name = document.createElement("span");
    name.textContent = m.name;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn ghost danger-text";
    remove.textContent = "Remove";
    remove.addEventListener("click", async () => {
      if (!confirm(`Remove ${m.name}? Their future chores will be reassigned.`)) return;
      try {
        await api.deleteMember(m.id);
        await refreshMembers();
        await refreshChores();
        calendar?.refetchEvents();
      } catch (err) {
        alert(`Failed: ${(err as Error).message}`);
      }
    });
    li.append(name, remove);
    list.appendChild(li);
  }
}

function renderChores(): void {
  const list = document.getElementById("chores-list") as HTMLUListElement | null;
  if (!list) return;
  list.innerHTML = "";
  if (cachedChores.length === 0) {
    const empty = document.createElement("li");
    empty.className = "list-empty";
    empty.textContent = "No chores yet.";
    list.appendChild(empty);
    return;
  }
  for (const c of cachedChores) {
    const li = document.createElement("li");
    li.className = "list-row";
    const main = document.createElement("div");
    main.className = "chore-main";
    const title = document.createElement("strong");
    title.textContent = c.title;
    const meta = document.createElement("small");
    const who =
      c.assignment_mode === "pinned"
        ? memberName(c.pinned_member_id)
        : `Rotates: ${(c.rotation_order ?? []).map((id) => memberName(id)).join(" → ")}`;
    meta.textContent = `${freqLabel(c)} • ${who}`;
    main.append(title, meta);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "btn ghost danger-text";
    remove.textContent = "Remove";
    remove.addEventListener("click", async () => {
      if (!confirm(`Remove chore "${c.title}"? Future occurrences will be deleted.`)) return;
      try {
        await api.deleteChore(c.id);
        await refreshChores();
        calendar?.refetchEvents();
      } catch (err) {
        alert(`Failed: ${(err as Error).message}`);
      }
    });
    li.append(main, remove);
    list.appendChild(li);
  }
}

async function refreshMembers(): Promise<void> {
  cachedMembers = await api.listMembers();
  renderMembers();
}

async function refreshChores(): Promise<void> {
  cachedChores = await api.listChores();
  renderChores();
}

function occurrenceTitle(o: Occurrence): string {
  const who = o.assigned_member_name ? ` (${initials(o.assigned_member_name)})` : "";
  return `${o.chore_title}${who}`;
}

function occurrenceColor(o: Occurrence): { bg: string; border: string } {
  if (o.completed_at) return { bg: "#d1d5db", border: "#9ca3af" };
  return { bg: "#3b82f6", border: "#2563eb" };
}

function setupCalendar(): void {
  const el = document.getElementById("calendar");
  if (!el) return;
  calendar = new Calendar(el, {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: "dayGridMonth",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    height: "100%",
    events: async (info, success, failure) => {
      try {
        const start = info.startStr.slice(0, 10);
        const end = info.endStr.slice(0, 10);
        const occs = await api.listOccurrences(start, end);
        success(
          occs.map((o) => {
            const colors = occurrenceColor(o);
            return {
              id: String(o.id),
              title: occurrenceTitle(o),
              start: o.scheduled_date,
              allDay: true,
              backgroundColor: colors.bg,
              borderColor: colors.border,
              classNames: o.completed_at ? ["completed"] : [],
              extendedProps: { occurrence: o },
            };
          }),
        );
      } catch (err) {
        failure(err as Error);
      }
    },
    eventClick: (info) => {
      const occ = info.event.extendedProps["occurrence"] as Occurrence | undefined;
      if (!occ) return;
      occurrenceModal(occ, cachedMembers, {
        onComplete: async () => {
          await api.markComplete(occ.id);
          calendar?.refetchEvents();
        },
        onUncomplete: async () => {
          await api.unmarkComplete(occ.id);
          calendar?.refetchEvents();
        },
        onReassign: async (memberId) => {
          await api.reassign(occ.id, memberId);
          calendar?.refetchEvents();
        },
      });
    },
  });
  calendar.render();
}

function wireAddButtons(): void {
  document.querySelector('[data-action="add-member"]')?.addEventListener("click", () => {
    memberModal(async (name) => {
      await api.createMember(name);
      await refreshMembers();
    });
  });
  document.querySelector('[data-action="add-chore"]')?.addEventListener("click", () => {
    choreModal(cachedMembers, async (input) => {
      await api.createChore(input);
      await refreshChores();
      calendar?.refetchEvents();
    });
  });
}

async function start(): Promise<void> {
  setupCalendar();
  wireAddButtons();
  await refreshMembers();
  await refreshChores();
}

void start();

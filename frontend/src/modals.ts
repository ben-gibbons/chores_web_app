import { MEMBER_COLORS } from "./types.js";
import type { ChoreInput, Occurrence, TeamMember } from "./types.js";

const ROOT_ID = "modal-root";

function root(): HTMLElement {
  const el = document.getElementById(ROOT_ID);
  if (!el) throw new Error("modal root missing");
  return el;
}

function close(): void {
  const r = root();
  r.innerHTML = "";
  r.classList.add("hidden");
  r.setAttribute("aria-hidden", "true");
}

function open(content: HTMLElement): void {
  const r = root();
  r.innerHTML = "";
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });
  const box = document.createElement("div");
  box.className = "modal-box";
  box.appendChild(content);
  overlay.appendChild(box);
  r.appendChild(overlay);
  r.classList.remove("hidden");
  r.setAttribute("aria-hidden", "false");
}

function makeButton(label: string, kind: "primary" | "ghost" | "danger" = "ghost"): HTMLButtonElement {
  const b = document.createElement("button");
  b.type = "button";
  b.className = `btn ${kind}`;
  b.textContent = label;
  return b;
}

function makeField(labelText: string, input: HTMLElement): HTMLLabelElement {
  const label = document.createElement("label");
  label.className = "field";
  const span = document.createElement("span");
  span.textContent = labelText;
  label.appendChild(span);
  label.appendChild(input);
  return label;
}

export function memberModal(
  onSubmit: (name: string, color: string) => Promise<void>,
): void {
  const form = document.createElement("form");
  form.className = "modal-form";

  const heading = document.createElement("h3");
  heading.textContent = "Add team member";
  form.appendChild(heading);

  const nameInput = document.createElement("input");
  nameInput.type = "text";
  nameInput.required = true;
  nameInput.maxLength = 100;
  nameInput.placeholder = "e.g. Alice";
  form.appendChild(makeField("Name", nameInput));

  let selectedColor: string = MEMBER_COLORS[0];
  const swatches = document.createElement("div");
  swatches.className = "color-swatches";
  const swatchButtons: HTMLButtonElement[] = [];
  MEMBER_COLORS.forEach((color, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "color-swatch";
    btn.style.backgroundColor = color;
    btn.setAttribute("aria-label", `Color ${idx + 1}`);
    if (idx === 0) btn.classList.add("selected");
    btn.addEventListener("click", () => {
      selectedColor = color;
      for (const b of swatchButtons) b.classList.remove("selected");
      btn.classList.add("selected");
    });
    swatchButtons.push(btn);
    swatches.appendChild(btn);
  });
  form.appendChild(makeField("Color", swatches));

  const actions = document.createElement("div");
  actions.className = "modal-actions";
  const cancel = makeButton("Cancel");
  cancel.addEventListener("click", close);
  const submit = makeButton("Add", "primary");
  submit.type = "submit";
  actions.appendChild(cancel);
  actions.appendChild(submit);
  form.appendChild(actions);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = nameInput.value.trim();
    if (!name) return;
    submit.disabled = true;
    try {
      await onSubmit(name, selectedColor);
      close();
    } catch (err) {
      submit.disabled = false;
      alert(`Failed: ${(err as Error).message}`);
    }
  });

  open(form);
  setTimeout(() => nameInput.focus(), 0);
}

export function choreModal(
  members: TeamMember[],
  onSubmit: (input: ChoreInput) => Promise<void>,
): void {
  if (members.length === 0) {
    alert("Add at least one team member before creating a chore.");
    return;
  }

  const form = document.createElement("form");
  form.className = "modal-form";

  const heading = document.createElement("h3");
  heading.textContent = "Add chore";
  form.appendChild(heading);

  const titleInput = document.createElement("input");
  titleInput.type = "text";
  titleInput.required = true;
  titleInput.maxLength = 200;
  titleInput.placeholder = "e.g. Take out the recycling";
  form.appendChild(makeField("Title", titleInput));

  const descInput = document.createElement("textarea");
  descInput.rows = 2;
  descInput.maxLength = 2000;
  form.appendChild(makeField("Description (optional)", descInput));

  const freqSelect = document.createElement("select");
  for (const f of ["daily", "weekly", "biweekly", "monthly"] as const) {
    const opt = document.createElement("option");
    opt.value = f;
    opt.textContent = f.charAt(0).toUpperCase() + f.slice(1);
    freqSelect.appendChild(opt);
  }
  freqSelect.value = "weekly";
  form.appendChild(makeField("Recurrence", freqSelect));

  const startInput = document.createElement("input");
  startInput.type = "date";
  startInput.required = true;
  startInput.value = new Date().toISOString().slice(0, 10);
  form.appendChild(makeField("Start date", startInput));

  const modeSelect = document.createElement("select");
  for (const [val, text] of [
    ["round_robin", "Rotate through members"],
    ["pinned", "Pinned to one member"],
  ] as const) {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = text;
    modeSelect.appendChild(opt);
  }
  form.appendChild(makeField("Assignment", modeSelect));

  const pinnedSelect = document.createElement("select");
  for (const m of members) {
    const opt = document.createElement("option");
    opt.value = String(m.id);
    opt.textContent = m.name;
    pinnedSelect.appendChild(opt);
  }
  const pinnedField = makeField("Assignee", pinnedSelect);
  pinnedField.classList.add("hidden");
  form.appendChild(pinnedField);

  const rotationContainer = document.createElement("div");
  rotationContainer.className = "rotation-list";
  const rotationOrder = members.map((m) => m.id);
  function renderRotation(): void {
    rotationContainer.innerHTML = "";
    rotationOrder.forEach((id, idx) => {
      const m = members.find((x) => x.id === id);
      if (!m) return;
      const row = document.createElement("div");
      row.className = "rotation-row";
      const pos = document.createElement("span");
      pos.className = "rotation-pos";
      pos.textContent = String(idx + 1);
      const name = document.createElement("span");
      name.className = "rotation-name";
      name.textContent = m.name;
      const up = makeButton("▲");
      up.disabled = idx === 0;
      up.addEventListener("click", () => {
        const a = rotationOrder[idx];
        const b = rotationOrder[idx - 1];
        if (a === undefined || b === undefined) return;
        rotationOrder[idx - 1] = a;
        rotationOrder[idx] = b;
        renderRotation();
      });
      const down = makeButton("▼");
      down.disabled = idx === rotationOrder.length - 1;
      down.addEventListener("click", () => {
        const a = rotationOrder[idx];
        const b = rotationOrder[idx + 1];
        if (a === undefined || b === undefined) return;
        rotationOrder[idx + 1] = a;
        rotationOrder[idx] = b;
        renderRotation();
      });
      row.append(pos, name, up, down);
      rotationContainer.appendChild(row);
    });
  }
  renderRotation();
  const rotationField = makeField("Rotation order", rotationContainer);
  form.appendChild(rotationField);

  function syncMode(): void {
    if (modeSelect.value === "pinned") {
      pinnedField.classList.remove("hidden");
      rotationField.classList.add("hidden");
    } else {
      pinnedField.classList.add("hidden");
      rotationField.classList.remove("hidden");
    }
  }
  modeSelect.addEventListener("change", syncMode);
  syncMode();

  const actions = document.createElement("div");
  actions.className = "modal-actions";
  const cancel = makeButton("Cancel");
  cancel.addEventListener("click", close);
  const submit = makeButton("Add", "primary");
  submit.type = "submit";
  actions.append(cancel, submit);
  form.appendChild(actions);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const mode = modeSelect.value as "pinned" | "round_robin";
    const input: ChoreInput = {
      title: titleInput.value.trim(),
      description: descInput.value,
      recurrence_freq: freqSelect.value as ChoreInput["recurrence_freq"],
      start_date: startInput.value,
      assignment_mode: mode,
      pinned_member_id: mode === "pinned" ? Number(pinnedSelect.value) : null,
      rotation_order: mode === "round_robin" ? [...rotationOrder] : null,
    };
    submit.disabled = true;
    try {
      await onSubmit(input);
      close();
    } catch (err) {
      submit.disabled = false;
      alert(`Failed: ${(err as Error).message}`);
    }
  });

  open(form);
  setTimeout(() => titleInput.focus(), 0);
}

export interface OccurrenceModalActions {
  onComplete: () => Promise<void>;
  onUncomplete: () => Promise<void>;
  onReassign: (memberId: number) => Promise<void>;
}

export function occurrenceModal(
  occ: Occurrence,
  members: TeamMember[],
  actions: OccurrenceModalActions,
): void {
  const wrap = document.createElement("div");
  wrap.className = "modal-form";

  const heading = document.createElement("h3");
  heading.textContent = occ.chore_title;
  wrap.appendChild(heading);

  const meta = document.createElement("p");
  meta.className = "modal-meta";
  meta.textContent = `${occ.scheduled_date} • ${
    occ.assigned_member_name ?? "Unassigned"
  }${occ.completed_at ? " • Completed" : ""}`;
  wrap.appendChild(meta);

  const reassignSelect = document.createElement("select");
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "Reassign to…";
  reassignSelect.appendChild(empty);
  for (const m of members) {
    const opt = document.createElement("option");
    opt.value = String(m.id);
    opt.textContent = m.name;
    reassignSelect.appendChild(opt);
  }
  reassignSelect.addEventListener("change", async () => {
    const v = reassignSelect.value;
    if (!v) return;
    try {
      await actions.onReassign(Number(v));
      close();
    } catch (err) {
      alert(`Failed: ${(err as Error).message}`);
    }
  });
  wrap.appendChild(makeField("Assignee", reassignSelect));

  const btns = document.createElement("div");
  btns.className = "modal-actions";
  const closeBtn = makeButton("Close");
  closeBtn.addEventListener("click", close);
  btns.appendChild(closeBtn);
  if (occ.completed_at) {
    const undo = makeButton("Mark not done", "ghost");
    undo.addEventListener("click", async () => {
      try {
        await actions.onUncomplete();
        close();
      } catch (err) {
        alert(`Failed: ${(err as Error).message}`);
      }
    });
    btns.appendChild(undo);
  } else {
    const done = makeButton("Mark done", "primary");
    done.addEventListener("click", async () => {
      try {
        await actions.onComplete();
        close();
      } catch (err) {
        alert(`Failed: ${(err as Error).message}`);
      }
    });
    btns.appendChild(done);
  }
  wrap.appendChild(btns);

  open(wrap);
}

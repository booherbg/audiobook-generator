// Library index: renders one card per book from the manifest. Books flagged `hidden`
// (work-in-progress editions) are rendered but kept out of sight until the visitor HOLDS
// SHIFT — a quiet "peek behind the curtain" for WIP titles. Pure rendering + a key toggle;
// the view-model math lives in logic.js so it stays unit-testable.

import { buildViewModel, totalDuration, formatTime } from "./logic.js";

export function bookCard(doc, m, b) {
  const vm = buildViewModel(m, b.id);
  const vid = vm.voices[0] && vm.voices[0].id;
  const a = doc.createElement("a");
  a.className = b.hidden ? "card wip" : "card";
  a.href = `player.html?book=${encodeURIComponent(b.id)}`;
  if (b.hidden) a.setAttribute("aria-hidden", "true");
  const badge = b.hidden ? '<span class="wip-badge">work in progress</span>' : "";
  a.innerHTML =
    `<img src="${vm.cover}" alt="" />` +
    `<div><div class="t">${vm.title}</div>` +
    `<div class="a">${vm.author}</div>` +
    `<div class="m">${vm.chapters.length} chapters · ${formatTime(totalDuration(vm, vid))}</div>` +
    badge +
    `</div>`;
  return a;
}

// Render every book; hidden ones get the .wip class (CSS keeps them out of view until the
// grid gains .show-wip). Returns counts for testing.
export function renderLibrary(doc, grid, m) {
  const books = (m && m.books) || [];
  if (!books.length) {
    grid.innerHTML = '<p class="muted">No books yet.</p>';
    return { total: 0, hidden: 0 };
  }
  let hidden = 0;
  for (const b of books) {
    grid.appendChild(bookCard(doc, m, b));
    if (b.hidden) hidden++;
  }
  return { total: books.length, hidden };
}

// Reveal WIP cards only while Shift is physically held. Clear on blur / tab-hide so the
// page can never get stuck in the revealed state.
export function wireShiftReveal(doc, grid, win) {
  const show = (on) => grid.classList.toggle("show-wip", on);
  win.addEventListener("keydown", (e) => { if (e.key === "Shift") show(true); });
  win.addEventListener("keyup", (e) => { if (e.key === "Shift") show(false); });
  win.addEventListener("blur", () => show(false));
  doc.addEventListener("visibilitychange", () => { if (doc.hidden) show(false); });
}

export async function initLibrary() {
  const grid = document.getElementById("grid");
  try {
    const m = await (await fetch("manifest.json", { cache: "no-cache" })).json();
    renderLibrary(document, grid, m);
    wireShiftReveal(document, grid, window);
  } catch {
    grid.innerHTML = '<p class="error">Could not load the library.</p>';
  }
}

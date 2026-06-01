// Library index: renders one card per book from the manifest. Books flagged `wip`
// (work-in-progress editions) are shown normally but carry a "work in progress" badge.
// The view-model math lives in logic.js so it stays unit-testable.

import { buildViewModel, totalDuration, formatTime } from "./logic.js";

// First 4-digit year in the date field ("1891", "2026-05-15" → "1891" / "2026").
export function bookYear(b) {
  const m = String(b.date || "").match(/\d{4}/);
  return m ? m[0] : "";
}

export function bookCard(doc, m, b) {
  const vm = buildViewModel(m, b.id);
  const vid = vm.voices[0] && vm.voices[0].id;
  const a = doc.createElement("a");
  a.className = b.wip ? "card wip" : "card";
  a.href = `player.html?book=${encodeURIComponent(b.id)}`;
  const badge = b.wip ? '<span class="wip-badge">work in progress</span>' : "";
  const year = bookYear(b);
  const author = year ? `${vm.author} · ${year}` : vm.author;
  a.innerHTML =
    `<img src="${vm.cover}" alt="" />` +
    `<div><div class="t">${vm.title}</div>` +
    `<div class="a">${author}</div>` +
    `<div class="m">${vm.chapters.length} chapters · ${formatTime(totalDuration(vm, vid))}</div>` +
    badge +
    `</div>`;
  return a;
}

// Render every book. Returns counts for testing.
export function renderLibrary(doc, grid, m) {
  const books = (m && m.books) || [];
  if (!books.length) {
    grid.innerHTML = '<p class="muted">No books yet.</p>';
    return { total: 0, wip: 0 };
  }
  let wip = 0;
  for (const b of books) {
    grid.appendChild(bookCard(doc, m, b));
    if (b.wip) wip++;
  }
  return { total: books.length, wip };
}

export async function initLibrary() {
  const grid = document.getElementById("grid");
  try {
    const m = await (await fetch("manifest.json", { cache: "no-cache" })).json();
    renderLibrary(document, grid, m);
  } catch {
    grid.innerHTML = '<p class="error">Could not load the library.</p>';
  }
}

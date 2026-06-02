// Library index: renders one card per book from the manifest. Books flagged `wip`
// (work-in-progress editions) are shown normally but carry a "work in progress" badge.
// The view-model math lives in logic.js so it stays unit-testable.

import { buildViewModel, totalDuration, formatTime, yearOf, resolveAsset } from "./logic.js";

// Re-exported for tests; the year logic lives in logic.js (shared with the player).
export const bookYear = (b) => yearOf(b && b.date);

// Minimal HTML-escape for values interpolated into card innerHTML.
function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

export function bookCard(doc, m, b) {
  const vm = buildViewModel(m, b.id);
  const vid = vm.voices[0] && vm.voices[0].id;
  const a = doc.createElement("a");
  a.className = b.wip ? "card wip" : "card";
  a.href = `player.html?book=${encodeURIComponent(b.id)}`;
  const badge = b.wip ? '<span class="wip-badge">work in progress</span>' : "";
  // Join author + year with " · " only when both exist (never a leading "· 2026").
  const author = [esc(vm.author), yearOf(vm.date)].filter(Boolean).join(" · ");
  const subtitle = vm.subtitle ? `<div class="s">${esc(vm.subtitle)}</div>` : "";
  a.innerHTML =
    `<img src="${esc(resolveAsset(vm.audioBase, vm.cover))}" alt="" />` +
    `<div><div class="t">${esc(vm.title)}</div>` +
    subtitle +
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

// The Audiobook Queue: editions committed to next, audio pending. These are NOT in the manifest
// (no player/audio yet) — teasers for the through-line the library follows. Ordered as the build
// queue; edit freely. Full rationale + copyright per item lives in docs/WORK-QUEUE.md.
// `preview` lists assets already built (companion / full text); shown only in admin mode (below).
export const QUEUE = [
  { id: "city-of-god", title: "The City of God", subtitle: "Book XIV — the two cities",
    author: "Augustine of Hippo", year: "c. 420", status: "queued", preview: [],
    note: "“Two loves have made two cities” — the source of Magnifica's central image." },
  { id: "udhr", title: "Universal Declaration of Human Rights", subtitle: "",
    author: "United Nations", year: "1948", status: "queued", preview: [],
    note: "The secular charter of human dignity — short, and explicitly cited by Magnifica." },
  { id: "zhuangzi-machine-heart", title: "Zhuangzi: The Machine Heart",
    subtitle: "from the “Heaven and Earth” chapter", author: "Zhuangzi, trans. Legge",
    year: "c. 300 BC", status: "queued", preview: [],
    note: "Use a machine and you grow a “machine heart” — what tools do to the inner life." },
  { id: "erewhon-machines", title: "Erewhon: The Book of the Machines", subtitle: "",
    author: "Samuel Butler", year: "1872", status: "queued", preview: [],
    note: "Could machines evolve a will of their own? The machine-consciousness urtext." },
  { id: "the-machine-stops", title: "The Machine Stops", subtitle: "",
    author: "E. M. Forster", year: "1909", status: "queued", preview: [],
    note: "Humanity underground, every need met by a global Machine — until it stops. Eerily early." },
  { id: "rur", title: "R.U.R.", subtitle: "Rossum's Universal Robots",
    author: "Karel Čapek", year: "1920", status: "queued", preview: [],
    note: "The play that gave us the word “robot,” and asked what we owe the things we make." },
  { id: "frankenstein", title: "Frankenstein", subtitle: "or, The Modern Prometheus",
    author: "Mary Shelley", year: "1818", status: "queued", preview: [],
    note: "The first modern myth of made life — and of a maker who abandons what he makes." },
  { id: "quadragesimo-anno", title: "Quadragesimo Anno", subtitle: "On the Reconstruction of the Social Order",
    author: "Pius XI", year: "1931", status: "queued", preview: [],
    note: "Forty years after Rerum Novarum — it names “subsidiarity,” a beam Magnifica leans on." },
];

export function queueCard(doc, item, i, admin = false) {
  const el = doc.createElement("div");
  el.className = "card queued" + (admin ? " admin" : "");
  const sub = item.subtitle ? `<div class="s">${esc(item.subtitle)}</div>` : "";
  const author = [esc(item.author), esc(item.year)].filter(Boolean).join(" · ");
  const isProd = /production/i.test(item.status || "");
  const badge = `<span class="queue-badge${isProd ? " production" : ""}">${esc(item.status || "queued")}</span>`;
  let preview = "";
  if (admin) {
    const links = item.preview || [];
    preview = links.length
      ? `<div class="queue-preview">` +
          links.map((p) => `<a href="${esc(p.href)}">${esc(p.label)} ▸</a>`).join("") +
        `</div>`
      : `<div class="queue-preview muted">nothing to preview yet</div>`;
  }
  el.innerHTML =
    `<div class="queue-num">${i + 1}</div>` +
    `<div><div class="t">${esc(item.title)}</div>` +
    sub +
    `<div class="a">${author}</div>` +
    `<div class="m">${esc(item.note)}</div>` +
    badge +
    preview +
    `</div>`;
  return el;
}

export function renderQueue(doc, el, items = QUEUE, admin = false) {
  for (let i = 0; i < items.length; i++) el.appendChild(queueCard(doc, items[i], i, admin));
  return items.length;
}

// ── Admin / preview mode ─────────────────────────────────────────────────────
// No public control. Tap the library title 5× to toggle (laptop + mobile; Shift was a footgun —
// Shift+click opens a new tab). Admin mode just reveals click-through to whatever a queued edition
// already has built (companion / full text), for QA before public launch. Persisted locally.
const ADMIN_KEY = "lib-admin";
export function adminOn() {
  try { return localStorage.getItem(ADMIN_KEY) === "1"; } catch { return false; }
}
function setAdmin(on) { try { localStorage.setItem(ADMIN_KEY, on ? "1" : "0"); } catch {} }

function wireAdminTap(triggerEl, onToggle) {
  if (!triggerEl || !triggerEl.addEventListener) return;
  let taps = 0, timer = null;
  triggerEl.addEventListener("click", () => {
    taps += 1;
    clearTimeout(timer);
    timer = setTimeout(() => { taps = 0; }, 1200);
    if (taps >= 5) { taps = 0; setAdmin(!adminOn()); onToggle(); }
  });
}

export async function initLibrary() {
  const grid = document.getElementById("grid");
  try {
    const m = await (await fetch("manifest.json", { cache: "no-cache" })).json();
    renderLibrary(document, grid, m);
  } catch {
    grid.innerHTML = '<p class="error">Could not load the library.</p>';
  }
  const queue = document.getElementById("queue");
  const drawQueue = () => {
    if (!queue) return;
    queue.innerHTML = "";
    renderQueue(document, queue, QUEUE, adminOn());
    document.body.classList.toggle("admin", adminOn());
  };
  drawQueue();
  wireAdminTap(document.getElementById("lib-title"), drawQueue);
}

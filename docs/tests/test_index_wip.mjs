// Exercises the real docs/app/index.js render + Shift-to-reveal logic under a DOM shim.
// Guards: (1) every book renders a card (no blank library), (2) hidden books get .wip,
// (3) holding Shift toggles .show-wip on the grid, (4) blur clears it.

import assert from "node:assert";
import { test } from "node:test";
import { bookCard, renderLibrary, wireShiftReveal } from "../app/index.js";

const MANIFEST = {
  books: [
    { id: "visible-book", title: "Visible", author: "A", cover: "c.svg",
      voices: [{ id: "v", label: "V" }],
      chapters: [{ index: 1, title: "1", files: { v: "x.mp3" }, duration: { v: 60 } }] },
    { id: "wip-book", title: "WIP", author: "B", cover: "c.svg", hidden: true,
      voices: [{ id: "v", label: "V" }],
      chapters: [{ index: 1, title: "1", files: { v: "x.mp3" }, duration: { v: 60 } }] },
  ],
};

function makeEl() {
  const el = {
    _cls: new Set(), children: [], _html: "", attrs: {}, _listeners: {},
    set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
    get className() { return [...this._cls].join(" "); },
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html; },
    classList: {
      toggle: (c, on) => { on ? el._cls.add(c) : el._cls.delete(c); },
      contains: (c) => el._cls.has(c),
      add: (c) => el._cls.add(c), remove: (c) => el._cls.delete(c),
    },
    setAttribute(k, v) { this.attrs[k] = v; },
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(ev, fn) { (this._listeners[ev] ||= []).push(fn); },
    fire(ev, arg) { (this._listeners[ev] || []).forEach((f) => f(arg)); },
  };
  return el;
}

const doc = { createElement: makeEl, addEventListener() {}, hidden: false };

test("hidden books render as .wip cards; visible ones don't", () => {
  const vis = bookCard(doc, MANIFEST, MANIFEST.books[0]);
  const wip = bookCard(doc, MANIFEST, MANIFEST.books[1]);
  assert.ok(!vis.classList.contains("wip"), "visible card is not .wip");
  assert.ok(wip.classList.contains("wip"), "hidden card is .wip");
  assert.equal(wip.attrs["aria-hidden"], "true");
  assert.match(wip.innerHTML, /work in progress/i, "wip card shows the badge");
});

test("renderLibrary renders every book and reports hidden count", () => {
  const grid = makeEl();
  const { total, hidden } = renderLibrary(doc, grid, MANIFEST);
  assert.equal(total, 2);
  assert.equal(hidden, 1);
  assert.equal(grid.children.length, 2, "no blank library — a card per book");
});

test("Shift toggles .show-wip; blur clears it", () => {
  const grid = makeEl();
  const win = makeEl();
  wireShiftReveal(doc, grid, win);

  assert.ok(!grid.classList.contains("show-wip"), "hidden by default");
  win.fire("keydown", { key: "Shift" });
  assert.ok(grid.classList.contains("show-wip"), "Shift down reveals WIP");
  win.fire("keyup", { key: "Shift" });
  assert.ok(!grid.classList.contains("show-wip"), "Shift up hides again");

  win.fire("keydown", { key: "Shift" });
  win.fire("blur");
  assert.ok(!grid.classList.contains("show-wip"), "blur never leaves it stuck revealed");
});

test("a non-Shift key does not reveal WIP", () => {
  const grid = makeEl();
  const win = makeEl();
  wireShiftReveal(doc, grid, win);
  win.fire("keydown", { key: "a" });
  assert.ok(!grid.classList.contains("show-wip"));
});

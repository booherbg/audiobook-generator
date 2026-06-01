// Exercises the real docs/app/index.js render logic under a DOM shim.
// Guards: (1) every book renders a card (no blank library), (2) wip books get a badge +
// .wip class but are NOT hidden, (3) the year is shown on the card.

import assert from "node:assert";
import { test } from "node:test";
import { bookCard, bookYear, renderLibrary } from "../app/index.js";

const MANIFEST = {
  books: [
    { id: "visible-book", title: "Visible", subtitle: "On Subtitles", author: "A",
      cover: "c.svg", date: "2026-05-15", voices: [{ id: "v", label: "V" }],
      chapters: [{ index: 1, title: "1", files: { v: "x.mp3" }, duration: { v: 60 } }] },
    { id: "wip-book", title: "WIP", author: "B", cover: "c.svg", date: "1891", wip: true,
      voices: [{ id: "v", label: "V" }],
      chapters: [{ index: 1, title: "1", files: { v: "x.mp3" }, duration: { v: 60 } }] },
  ],
};

function makeEl() {
  const el = {
    _cls: new Set(), children: [], _html: "", attrs: {},
    set className(v) { this._cls = new Set(String(v).split(/\s+/).filter(Boolean)); },
    get className() { return [...this._cls].join(" "); },
    set innerHTML(v) { this._html = v; },
    get innerHTML() { return this._html; },
    classList: { contains: (c) => el._cls.has(c) },
    setAttribute(k, v) { this.attrs[k] = v; },
    appendChild(c) { this.children.push(c); return c; },
  };
  return el;
}
const doc = { createElement: makeEl };

test("bookYear extracts the first 4-digit year from the date field", () => {
  assert.equal(bookYear({ date: "1891" }), "1891");
  assert.equal(bookYear({ date: "2026-05-15" }), "2026");
  assert.equal(bookYear({ date: "" }), "");
  assert.equal(bookYear({}), "");
});

test("wip books are visible with a badge; non-wip have neither", () => {
  const vis = bookCard(doc, MANIFEST, MANIFEST.books[0]);
  const wip = bookCard(doc, MANIFEST, MANIFEST.books[1]);
  assert.ok(!vis.classList.contains("wip"), "visible card is not .wip");
  assert.ok(wip.classList.contains("wip"), "wip card carries the .wip class");
  assert.match(wip.innerHTML, /work in progress/i, "wip card shows the badge");
  assert.doesNotMatch(vis.innerHTML, /work in progress/i, "non-wip card has no badge");
});

test("the year appears on the card", () => {
  const vis = bookCard(doc, MANIFEST, MANIFEST.books[0]);
  const wip = bookCard(doc, MANIFEST, MANIFEST.books[1]);
  assert.match(vis.innerHTML, /· 2026/, "visible card shows 2026");
  assert.match(wip.innerHTML, /· 1891/, "wip card shows 1891");
});

test("the subtitle appears on the card when present, and is omitted when absent", () => {
  const withSub = bookCard(doc, MANIFEST, MANIFEST.books[0]);
  const noSub = bookCard(doc, MANIFEST, MANIFEST.books[1]);
  assert.match(withSub.innerHTML, /class="s">On Subtitles</, "subtitle line rendered");
  assert.doesNotMatch(noSub.innerHTML, /class="s"/, "no empty subtitle line when absent");
});

test("renderLibrary renders every book and counts wip", () => {
  const grid = makeEl();
  const { total, wip } = renderLibrary(doc, grid, MANIFEST);
  assert.equal(total, 2);
  assert.equal(wip, 1);
  assert.equal(grid.children.length, 2, "no blank library — a card per book");
});

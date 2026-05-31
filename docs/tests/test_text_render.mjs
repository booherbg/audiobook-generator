// Executes the real docs/app/text.js against the real full-text JSON under a minimal DOM
// shim, asserting the reader renders chapters + paragraphs (guards against a silent blank
// page, the way the companion once regressed).

import assert from "node:assert";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(
  readFileSync(path.join(here, "../text/magnifica-humanitas.json"), "utf8"),
);

function makeEl(tag) {
  return {
    tagName: tag, children: [], className: "", id: "", _text: "", _html: "",
    set textContent(v) { this._text = v; }, get textContent() { return this._text; },
    set innerHTML(v) { this._html = v; }, get innerHTML() { return this._html; },
    appendChild(c) { this.children.push(c); return c; },
    append(...xs) { for (const x of xs) this.children.push(typeof x === "string" ? { text: x } : x); },
    addEventListener() {}, setAttribute() {}, scrollIntoView() {},
    style: {}, classList: { add() {}, remove() {} },
  };
}

function setup() {
  const ids = ["app", "title", "byline", "src-note", "toc", "text", "foot-note", "player-link"];
  const reg = {};
  for (const id of ids) { const el = makeEl("div"); el.id = id; reg[id] = el; }
  global.document = { getElementById: (id) => reg[id] || null, createElement: (t) => makeEl(t) };
  global.location = { search: "?book=magnifica-humanitas", href: "https://x/" };
  global.fetch = async () => ({ json: async () => data });
  return reg;
}

async function run() {
  setup();
  const reg = global.document; // not used; keep setup's reg
}

test("full-text reader renders every chapter (no blank page)", async () => {
  const reg = setup();
  await import("../app/text.js?" + Math.random());
  await new Promise((r) => setTimeout(r, 20));

  // one TOC link + one chapter section per chapter
  assert.equal(reg.toc.children.length, data.chapters.length, "a TOC entry per chapter");
  assert.equal(reg.text.children.length, data.chapters.length, "a section per chapter");
  assert.ok(reg.title._text.length > 0, "title set");
  assert.ok(!/something went wrong/i.test(reg.text._html || ""), "render fallback must not fire");
});

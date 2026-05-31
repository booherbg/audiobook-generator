// Executes the REAL docs/app/guide.js against the REAL guide JSON under a minimal DOM
// shim, and asserts the companion actually renders. This is the guard that was missing
// when a render-time ReferenceError silently blanked the whole page in production.

import assert from "node:assert";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const guideJson = JSON.parse(
  readFileSync(path.join(here, "../guide/magnifica-humanitas.json"), "utf8"),
);

// ── tiny DOM shim (just enough for guide.js) ──────────────────────────────
function makeEl(tag) {
  return {
    tagName: tag, children: [], className: "", id: "", _text: "", _html: "",
    style: {}, attrs: {}, _q: {},
    set textContent(v) { this._text = v; },
    get textContent() { return this._text; },
    set innerHTML(v) {
      this._html = v; this._q = {};
      const re = /class="([^"]+)"/g; let m;
      while ((m = re.exec(v))) for (const c of m[1].split(/\s+/)) this._q["." + c] = makeEl("span");
    },
    get innerHTML() { return this._html; },
    appendChild(c) { this.children.push(c); return c; },
    append(...xs) { for (const x of xs) this.children.push(typeof x === "string" ? { text: x } : x); },
    querySelector(sel) { return this._q[sel] || null; },
    addEventListener() {},
    setAttribute(k, v) { this.attrs[k] = v; },
    classList: { add() {}, remove() {} },
  };
}

function setupDom() {
  const ids = ["app", "intro", "concepts", "commentary", "commentary-section", "glossary", "further", "title"];
  const reg = {};
  for (const id of ids) { const el = makeEl("div"); el.id = id; reg[id] = el; }
  global.document = {
    getElementById: (id) => reg[id] || null,
    createElement: (t) => makeEl(t),
  };
  global.location = { search: "?book=magnifica-humanitas", href: "https://x/" };
  global.fetch = async () => ({ json: async () => guideJson });
  return reg;  // keep the real global setTimeout — guide.js's flash timer is harmless
}

// Import guide.js fresh and wait for its async init() (fetch → render) to settle.
async function runGuide() {
  await import("../app/guide.js?" + Math.random());
  // init() awaits a microtask (fetch); a couple of macrotask turns guarantees completion.
  await new Promise((r) => setTimeout(r, 20));
}

test("companion guide renders all sections (no blank page)", async () => {
  const reg = setupDom();
  await runGuide();

  assert.equal(reg.concepts.children.length, guideJson.concepts.length,
    "every concept card must render");
  assert.ok(guideJson.concepts.length >= 12, "expected the full concept set");
  assert.equal(reg.commentary.children.length, guideJson.commentary.length,
    "every commentary aside must render");
  // glossary appends a dt AND a dd per term
  assert.equal(reg.glossary.children.length, guideJson.glossary.length * 2);
  assert.equal(reg.further.children.length, guideJson.further_reading.length);
  assert.ok(reg.intro._text.length > 0, "intro text must be set");
  // The render guard must NOT have fired — i.e. intro is the real intro, not the
  // "Something went wrong" fallback. This makes a future render throw fail loudly here.
  assert.ok(!/something went wrong/i.test(reg.intro._html || ""),
    "render fallback must not have triggered");
});

test("every concept card gets an id, and related cross-links resolve to one", async () => {
  const reg = setupDom();
  await runGuide();

  const ids = new Set(reg.concepts.children.map((el) => el.id));
  for (const id of ids) assert.ok(id.startsWith("c-"), `card id ${id} must start with c-`);

  const sl = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  for (const c of guideJson.concepts) {
    for (const r of c.related || []) {
      assert.ok(ids.has("c-" + sl(r)),
        `related link "${r}" (from "${c.title}") must point at a real card`);
    }
  }
});

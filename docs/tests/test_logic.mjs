import assert from "node:assert";
import { test } from "node:test";

import {
  buildViewModel,
  clamp,
  currentLineIndex,
  formatTime,
  lineStartSeconds,
  nextIndex,
  offsetOnVoiceSwitch,
  prevIndex,
  readJSON,
  totalDuration,
  writeJSON,
} from "../app/logic.js";

test("formatTime", () => {
  assert.equal(formatTime(0), "0:00");
  assert.equal(formatTime(754), "12:34");
  assert.equal(formatTime(3661), "1:01:01");
  assert.equal(formatTime(-5), "0:00");
  assert.equal(formatTime(NaN), "0:00");
});

test("clamp", () => {
  assert.equal(clamp(5, 0, 3), 3);
  assert.equal(clamp(-1, 0, 3), 0);
  assert.equal(clamp(2, 0, 3), 2);
});

test("chapter nav", () => {
  assert.equal(nextIndex(0, 3), 1);
  assert.equal(nextIndex(2, 3), 2);
  assert.equal(prevIndex(0), 0);
  assert.equal(prevIndex(2), 1);
});

test("offsetOnVoiceSwitch clamps to new duration", () => {
  assert.equal(offsetOnVoiceSwitch(300, 322, 314), 300);
  assert.equal(offsetOnVoiceSwitch(320, 322, 314), 314);
  assert.equal(offsetOnVoiceSwitch(-1, 322, 314), 0);
});

const MANIFEST = {
  books: [
    {
      id: "b",
      title: "T",
      subtitle: "S",
      author: "A",
      cover: "c.svg",
      has_guide: false,
      voices: [{ id: "female" }, { id: "male" }],
      chapters: [
        { index: 1, title: "Intro", files: { female: "f1.mp3", male: "m1.mp3" }, duration: { female: 10, male: 11 } },
        { index: 2, title: "Two", files: { female: "f2.mp3", male: "m2.mp3" }, duration: { female: 20, male: 22 } },
      ],
    },
  ],
};

test("buildViewModel", () => {
  const vm = buildViewModel(MANIFEST, "b");
  assert.equal(vm.title, "T");
  assert.equal(vm.chapters.length, 2);
  assert.equal(vm.chapters[0].file.female, "f1.mp3");
  assert.equal(vm.chapters[1].duration.male, 22);
  assert.equal(buildViewModel(MANIFEST, "nope"), null);
});

test("buildViewModel exposes source_url + rights (attribution must reach the player)", () => {
  const m = { books: [{ id: "b", title: "T", voices: [], chapters: [],
    source_url: "https://www.vatican.va/x", rights: "© Libreria Editrice Vaticana" }] };
  const vm = buildViewModel(m, "b");
  assert.equal(vm.rights, "© Libreria Editrice Vaticana");
  assert.equal(vm.source_url, "https://www.vatican.va/x");
  // absent fields default to empty string, never undefined (so render code is safe)
  const bare = buildViewModel({ books: [{ id: "b", title: "T", voices: [], chapters: [] }] }, "b");
  assert.equal(bare.rights, "");
  assert.equal(bare.source_url, "");
});

test("totalDuration", () => {
  const vm = buildViewModel(MANIFEST, "b");
  assert.equal(totalDuration(vm, "female"), 30);
  assert.equal(totalDuration(vm, "male"), 33);
});

test("json store round-trip + fallback", () => {
  const map = new Map();
  const store = { getItem: (k) => (map.has(k) ? map.get(k) : null), setItem: (k, v) => map.set(k, v) };
  writeJSON(store, "k", { a: 1 });
  assert.deepEqual(readJSON(store, "k", null), { a: 1 });
  assert.equal(readJSON(store, "missing", "def"), "def");
});

test("currentLineIndex (read-along highlight)", () => {
  const starts = [0, 0.25, 0.5, 0.75];
  assert.equal(currentLineIndex(starts, 0), 0);
  assert.equal(currentLineIndex(starts, 0.1), 0);
  assert.equal(currentLineIndex(starts, 0.25), 1);
  assert.equal(currentLineIndex(starts, 0.6), 2);
  assert.equal(currentLineIndex(starts, 0.99), 3);
  assert.equal(currentLineIndex(starts, -0.1), -1); // before first line
});

test("lineStartSeconds (tap-to-seek)", () => {
  const starts = [0, 0.5, 0.75];
  assert.equal(lineStartSeconds(starts, 1, 600), 300);
  assert.equal(lineStartSeconds(starts, 2, 600), 450);
  assert.equal(lineStartSeconds(starts, 0, 600), 0);
  assert.equal(lineStartSeconds(starts, 9, 600), 0); // out of range
});

// Pure, framework-free player logic — unit-tested with node:test (no build step).

export function formatTime(sec) {
  if (!isFinite(sec) || sec < 0) sec = 0;
  sec = Math.floor(sec);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const mm = h ? String(m).padStart(2, "0") : String(m);
  return h ? `${h}:${mm}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}

export function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x));
}

export function nextIndex(cur, len) {
  return Math.min(cur + 1, len - 1);
}

export function prevIndex(cur) {
  return Math.max(cur - 1, 0);
}

// Switching voice keeps the chapter and the absolute time offset (chapters are
// text-aligned across voices), clamped to the new track's duration.
export function offsetOnVoiceSwitch(t, fromDur, toDur) {
  return clamp(t, 0, toDur || 0);
}

// First 4-digit year in a date string ("1891", "2026-05-15" → "1891" / "2026"); "" if none.
export function yearOf(date) {
  const m = String(date || "").match(/\d{4}/);
  return m ? m[0] : "";
}

export function buildViewModel(manifest, bookId) {
  const book = (manifest.books || []).find((b) => b.id === bookId);
  if (!book) return null;
  return {
    id: book.id,
    title: book.title,
    subtitle: book.subtitle || "",
    author: book.author || "",
    date: book.date || "",
    cover: book.cover || "",
    description: book.description || "",
    source_url: book.source_url || "",
    rights: book.rights || "",
    hasGuide: !!book.has_guide,
    voices: book.voices || [],
    chapters: (book.chapters || []).map((c) => ({
      index: c.index,
      title: c.title,
      file: c.files || {},
      duration: c.duration || {},
    })),
  };
}

export function totalDuration(vm, voiceId) {
  return vm.chapters.reduce((sum, c) => sum + (c.duration[voiceId] || 0), 0);
}

// Read-along: `starts` is an ascending array of per-line start fractions in [0,1).
// Returns the index of the line active at `fraction` (= currentTime / duration),
// i.e. the last line whose start is <= fraction. Binary search; -1 if before the first.
export function currentLineIndex(starts, fraction) {
  let lo = 0, hi = starts.length - 1, ans = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (starts[mid] <= fraction) {
      ans = mid;
      lo = mid + 1;
    } else {
      hi = mid - 1;
    }
  }
  return ans;
}

// Seek target (seconds) for tapping line `i`: its start fraction × chapter duration.
export function lineStartSeconds(starts, i, duration) {
  if (i < 0 || i >= starts.length) return 0;
  return starts[i] * (duration || 0);
}

export function resumeKey(bookId) {
  return `audiobook:resume:${bookId}`;
}

export function prefsKey() {
  return `audiobook:prefs`;
}

export function readJSON(store, key, fallback) {
  try {
    const v = store.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch {
    return fallback;
  }
}

export function writeJSON(store, key, val) {
  try {
    store.setItem(key, JSON.stringify(val));
  } catch {
    /* storage may be unavailable (private mode) — ignore */
  }
}

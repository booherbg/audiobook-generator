import {
  buildViewModel,
  clamp,
  currentLineIndex,
  formatTime,
  lineStartSeconds,
  nextIndex,
  offsetOnVoiceSwitch,
  prefsKey,
  prevIndex,
  readJSON,
  resumeKey,
  writeJSON,
} from "./logic.js";

const $ = (id) => document.getElementById(id);
const audio = $("audio");
const BOOK_ID = new URLSearchParams(location.search).get("book");

let vm = null;
let voiceId = null;
let idx = 0;
let seeking = false;
let completed = new Set();
let saveTick = 0;

// Read-along state
let transcript = null;        // { chapters: [{index,title,lines,starts}] }
let readAlong = false;        // panel open?
let lineEls = [];             // current chapter's rendered line elements
let lastLine = -1;            // last highlighted line index (avoid redundant DOM work)
let autoScroll = true;        // follow the current line (off once the user scrolls away)
let lastAutoScrollAt = 0;     // timestamp of our own programmatic scroll (ignore those)

async function init() {
  let manifest;
  try {
    manifest = await (await fetch("manifest.json", { cache: "no-cache" })).json();
  } catch {
    return showError("Could not load the library.");
  }
  const id = BOOK_ID || (manifest.books[0] && manifest.books[0].id);
  vm = buildViewModel(manifest, id);
  if (!vm) return showError("Book not found.");

  const prefs = readJSON(localStorage, prefsKey(), { speed: 1, readAlong: false });
  const resume = readJSON(localStorage, resumeKey(vm.id), null);
  voiceId = (resume && resume.voice) || vm.voices[0].id;
  if (!vm.voices.some((v) => v.id === voiceId)) voiceId = vm.voices[0].id;
  idx = resume ? clamp(resume.chapter | 0, 0, vm.chapters.length - 1) : 0;
  completed = new Set((resume && resume.completed) || []);

  // Deep link from the companion. Preferred form is voice-independent: ?ch=<n>&f=<0..1>,
  // resolved against the CURRENT voice's chapter duration so it lands on the right passage
  // whichever voice is selected. (?t=<absolute seconds> still supported as a fallback.)
  let seekTo = resume ? resume.time : 0;
  let cameFromLink = false;
  const params = new URLSearchParams(location.search);
  const chParam = params.get("ch");
  const fParam = params.get("f");
  const tParam = params.get("t");
  if (chParam !== null && fParam !== null) {
    const ci = vm.chapters.findIndex((c) => String(c.index) === String(chParam));
    if (ci >= 0) {
      idx = ci;
      const frac = clamp(Number(fParam) || 0, 0, 0.999);
      seekTo = frac * (vm.chapters[ci].duration[voiceId] || 0);
      cameFromLink = true;
    }
  } else if (tParam !== null && !Number.isNaN(Number(tParam))) {
    let rem = Math.max(0, Number(tParam));
    for (let i = 0; i < vm.chapters.length; i++) {
      const d = vm.chapters[i].duration[voiceId] || 0;
      if (rem < d || i === vm.chapters.length - 1) { idx = i; seekTo = rem; break; }
      rem -= d;
    }
    cameFromLink = true;
  }
  // Arriving from a "listen" link: show the words so the jump is visible. Do NOT force
  // autoplay — mobile blocks it and a surprise blast on desktop is jarring; the visible
  // highlight + a ready Play button invite the tap. (Audit fix.)
  if (cameFromLink) readAlong = true;
  const autostart = false;

  renderHead();
  renderVoices();
  $("speed").value = String(prefs.speed || 1);
  audio.playbackRate = Number($("speed").value);
  if (vm.hasGuide) {
    const href = `guide.html?book=${encodeURIComponent(vm.id)}`;
    const link = $("companion-link");
    if (link) { link.style.display = ""; link.href = href; }
    const callout = $("companion-callout");
    if (callout) { callout.style.display = ""; callout.href = href; }
  }

  await loadTranscript();
  readAlong = readAlong || !!prefs.readAlong;
  applyReadAlongVisibility();

  loadChapter(idx, seekTo, autostart);
  wireControls();
  wireMediaSession();
  wireKeyboard();
}

const showError = (msg) => {
  $("app").innerHTML = `<div class="error">${msg}</div>`;
};

const chapter = () => vm.chapters[idx];
const curFile = () => chapter().file[voiceId];
const curDur = () => chapter().duration[voiceId] || 0;

function renderHead() {
  $("book-title").textContent = vm.title;
  $("book-subtitle").textContent = vm.subtitle;
  $("book-author").textContent = vm.author;
  if (vm.cover) {
    $("cover").src = vm.cover;
    $("cover").alt = vm.title;
  }
  document.title = `${vm.title} — audiobook`;
}

function renderVoices() {
  const box = $("voice-toggle");
  box.innerHTML = "";
  for (const v of vm.voices) {
    const b = document.createElement("button");
    b.textContent = v.label.split("—")[0].trim() || v.id;
    b.title = v.label;
    b.setAttribute("aria-pressed", String(v.id === voiceId));
    b.addEventListener("click", () => switchVoice(v.id));
    box.appendChild(b);
  }
}

function renderChapters() {
  const ol = $("chapter-list");
  ol.innerHTML = "";
  vm.chapters.forEach((c, i) => {
    const li = document.createElement("li");
    if (i === idx) li.classList.add("current");
    if (completed.has(c.index)) li.classList.add("done");
    const b = document.createElement("button");
    b.innerHTML =
      `<span class="num">${c.index}.</span>` +
      `<span class="ct">${c.title}</span>` +
      `<span class="dur">${formatTime(c.duration[voiceId] || 0)}</span>`;
    b.addEventListener("click", () => loadChapter(i, 0, true));
    li.appendChild(b);
    ol.appendChild(li);
  });
}

function loadChapter(i, seekTo = 0, autoplay = false) {
  idx = clamp(i, 0, vm.chapters.length - 1);
  audio.src = curFile();
  audio.load();
  const setPos = () => {
    if (seekTo) audio.currentTime = clamp(seekTo, 0, curDur() || seekTo);
    audio.removeEventListener("loadedmetadata", setPos);
    updateProgress();
  };
  audio.addEventListener("loadedmetadata", setPos);
  $("now-title").textContent = chapter().title;
  renderChapters();
  renderReadAlong();
  updateMediaMetadata();
  saveResume();
  updatePlayButton();
  if (autoplay) audio.play().catch(() => {});
}

function switchVoice(v) {
  if (v === voiceId) return;
  const t = audio.currentTime;
  const fromDur = curDur();
  const wasPlaying = !audio.paused;
  voiceId = v;
  const toDur = chapter().duration[voiceId] || 0;
  renderVoices();
  renderChapters();
  audio.src = curFile();
  const setPos = () => {
    audio.currentTime = offsetOnVoiceSwitch(t, fromDur, toDur);
    audio.removeEventListener("loadedmetadata", setPos);
    updateProgress();
  };
  audio.addEventListener("loadedmetadata", setPos);
  saveResume();
  if (wasPlaying) audio.play().catch(() => {});
}

const togglePlay = () => (audio.paused ? audio.play().catch(() => {}) : audio.pause());
const skip = (d) => (audio.currentTime = clamp(audio.currentTime + d, 0, audio.duration || 0));
const goNext = (autoplay = true) => {
  const ni = nextIndex(idx, vm.chapters.length);
  if (ni !== idx) loadChapter(ni, 0, autoplay);
};
const goPrev = () => {
  if (audio.currentTime > 3) {
    audio.currentTime = 0;
    return;
  }
  loadChapter(prevIndex(idx), 0, !audio.paused);
};

function updatePlayButton() {
  $("btn-play").textContent = audio.paused ? "▶" : "⏸";
  $("btn-play").setAttribute("aria-label", audio.paused ? "Play" : "Pause");
}

function updateProgress() {
  const d = audio.duration || curDur() || 0;
  $("seek").max = d || 0;
  if (!seeking) $("seek").value = audio.currentTime || 0;
  $("cur-time").textContent = formatTime(audio.currentTime || 0);
  $("tot-time").textContent = formatTime(d);
  updateReadAlong();
}

function saveResume() {
  writeJSON(localStorage, resumeKey(vm.id), {
    chapter: idx,
    time: audio.currentTime || 0,
    voice: voiceId,
    completed: [...completed],
  });
}

function setSpeed(value) {
  audio.playbackRate = value;
  $("speed").value = String(value);
  writeJSON(localStorage, prefsKey(), { speed: value, readAlong });
}

// ── Read-along ──────────────────────────────────────────────────────────────
async function loadTranscript() {
  try {
    transcript = await (await fetch(`transcript/${vm.id}.json`, { cache: "no-cache" })).json();
  } catch {
    transcript = null;  // feature simply absent if the file isn't there
  }
  const toggle = $("readalong-toggle");
  if (toggle && !transcript) toggle.style.display = "none";
}

function chapterLines() {
  if (!transcript) return null;
  return transcript.chapters.find((c) => c.index === chapter().index) || null;
}

function renderReadAlong() {
  const box = $("readalong-lines");
  if (!box) return;
  lineEls = [];
  lastLine = -1;
  autoScroll = true;                       // new chapter → follow again
  const jb = $("jump-current");
  if (jb) jb.style.display = "none";
  box.innerHTML = "";
  const tc = chapterLines();
  if (!tc) {
    box.innerHTML = '<p class="muted">Transcript unavailable for this chapter.</p>';
    return;
  }
  tc.lines.forEach((text, i) => {
    const p = document.createElement("p");
    p.className = "ra-line";
    p.textContent = text;
    p.addEventListener("click", () => {
      const d = audio.duration || curDur() || 0;
      audio.currentTime = lineStartSeconds(tc.starts, i, d);
      if (audio.paused) audio.play().catch(() => {});
    });
    box.appendChild(p);
    lineEls.push(p);
  });
}

// Scroll WITHIN the read-along panel (never the whole window) to centre a line.
function scrollLineIntoPanel(el) {
  const panel = $("readalong");
  if (!panel || !el) return;
  const pr = panel.getBoundingClientRect();
  const er = el.getBoundingClientRect();
  const delta = (er.top - pr.top) - (panel.clientHeight / 2 - el.clientHeight / 2);
  lastAutoScrollAt = Date.now();
  panel.scrollTop += delta;
}

function updateReadAlong() {
  if (!readAlong || !lineEls.length) return;
  const tc = chapterLines();
  if (!tc) return;
  const d = audio.duration || curDur() || 0;
  if (!d) return;
  const frac = (audio.currentTime || 0) / d;
  const li = currentLineIndex(tc.starts, frac);
  if (li === lastLine) return;
  if (lastLine >= 0 && lineEls[lastLine]) lineEls[lastLine].classList.remove("ra-current");
  if (li >= 0 && lineEls[li]) {
    lineEls[li].classList.add("ra-current");
    if (autoScroll) scrollLineIntoPanel(lineEls[li]);
  }
  lastLine = li;
}

function jumpToCurrent() {
  autoScroll = true;
  const btn = $("jump-current");
  if (btn) btn.style.display = "none";
  lastLine = -1;            // force re-highlight + re-scroll
  updateReadAlong();
}

function onPanelScroll() {
  if (Date.now() - lastAutoScrollAt < 250) return;  // our own scroll — ignore
  if (autoScroll) {
    autoScroll = false;
    const btn = $("jump-current");
    if (btn) btn.style.display = "";
  }
}

function applyReadAlongVisibility() {
  const panel = $("readalong");
  const toggle = $("readalong-toggle");
  if (panel) panel.style.display = readAlong ? "" : "none";
  if (toggle) toggle.setAttribute("aria-expanded", String(readAlong));
}

function toggleReadAlong() {
  readAlong = !readAlong;
  applyReadAlongVisibility();
  writeJSON(localStorage, prefsKey(), { speed: Number($("speed").value), readAlong });
  if (readAlong) { lastLine = -1; updateReadAlong(); }
}

function wireControls() {
  $("btn-play").addEventListener("click", togglePlay);
  $("btn-back15").addEventListener("click", () => skip(-15));
  $("btn-fwd30").addEventListener("click", () => skip(30));
  $("btn-next").addEventListener("click", () => goNext());
  $("btn-prev").addEventListener("click", goPrev);
  $("speed").addEventListener("change", () => setSpeed(Number($("speed").value)));
  const ra = $("readalong-toggle");
  if (ra) ra.addEventListener("click", toggleReadAlong);
  const panel = $("readalong");
  if (panel) panel.addEventListener("scroll", onPanelScroll, { passive: true });
  const jump = $("jump-current");
  if (jump) jump.addEventListener("click", jumpToCurrent);

  const seek = $("seek");
  seek.addEventListener("input", () => {
    seeking = true;
    $("cur-time").textContent = formatTime(Number(seek.value));
  });
  seek.addEventListener("change", () => {
    audio.currentTime = Number(seek.value);
    seeking = false;
  });

  audio.addEventListener("play", () => {
    updatePlayButton();
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
  });
  audio.addEventListener("pause", () => {
    updatePlayButton();
    saveResume();
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
  });
  audio.addEventListener("timeupdate", () => {
    updateProgress();
    if (saveTick++ % 20 === 0) saveResume();
    updatePositionState();
  });
  // Update the read-along highlight on any seek, even while paused (e.g. arriving from a
  // companion link with autoplay blocked, or tapping a line while paused).
  audio.addEventListener("seeked", () => { updateProgress(); });
  audio.addEventListener("ended", () => {
    completed.add(chapter().index);
    saveResume();
    renderChapters();
    goNext(true);
  });
}

function updateMediaMetadata() {
  if (!("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
  navigator.mediaSession.metadata = new MediaMetadata({
    title: chapter().title,
    artist: vm.author,
    album: vm.title,
    artwork: vm.cover
      ? [{ src: new URL(vm.cover, location.href).href, sizes: "600x600", type: "image/svg+xml" }]
      : [],
  });
}

function updatePositionState() {
  const ms = navigator.mediaSession;
  if (ms && ms.setPositionState && audio.duration && isFinite(audio.duration)) {
    try {
      ms.setPositionState({
        duration: audio.duration,
        position: audio.currentTime,
        playbackRate: audio.playbackRate,
      });
    } catch {
      /* ignore */
    }
  }
}

function wireMediaSession() {
  if (!("mediaSession" in navigator)) return;
  const ms = navigator.mediaSession;
  const set = (action, fn) => {
    try {
      ms.setActionHandler(action, fn);
    } catch {
      /* unsupported action */
    }
  };
  set("play", () => audio.play());
  set("pause", () => audio.pause());
  set("previoustrack", goPrev);
  set("nexttrack", () => goNext());
  set("seekbackward", (d) => skip(-(d.seekOffset || 15)));
  set("seekforward", (d) => skip(d.seekOffset || 30));
  set("seekto", (d) => {
    if (d.fastSeek && "fastSeek" in audio) audio.fastSeek(d.seekTime);
    else audio.currentTime = d.seekTime;
  });
}

function wireKeyboard() {
  document.addEventListener("keydown", (e) => {
    const tag = e.target.tagName;
    if (tag === "SELECT" || tag === "INPUT" || tag === "TEXTAREA") return;
    if (e.code === "Space") {
      e.preventDefault();
      togglePlay();
    } else if (e.code === "ArrowLeft") {
      skip(-15);
    } else if (e.code === "ArrowRight") {
      skip(30);
    } else if (e.key === "[" || e.key === "]") {
      const opts = [...$("speed").options].map((o) => Number(o.value));
      let i = opts.indexOf(Number($("speed").value));
      i = clamp(i + (e.key === "]" ? 1 : -1), 0, opts.length - 1);
      setSpeed(opts[i]);
    } else if (e.key.toLowerCase() === "r") {
      toggleReadAlong();
    }
  });
}

init();

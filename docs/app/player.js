import {
  buildViewModel,
  clamp,
  formatTime,
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

  const prefs = readJSON(localStorage, prefsKey(), { speed: 1 });
  const resume = readJSON(localStorage, resumeKey(vm.id), null);
  voiceId = (resume && resume.voice) || vm.voices[0].id;
  if (!vm.voices.some((v) => v.id === voiceId)) voiceId = vm.voices[0].id;
  idx = resume ? clamp(resume.chapter | 0, 0, vm.chapters.length - 1) : 0;
  completed = new Set((resume && resume.completed) || []);

  // Deep link from the companion guide: ?t=<absolute seconds> → find the chapter
  // containing that time (using the current voice's durations) and seek within it.
  let seekTo = resume ? resume.time : 0;
  const tParam = new URLSearchParams(location.search).get("t");
  if (tParam !== null && !Number.isNaN(Number(tParam))) {
    let rem = Math.max(0, Number(tParam));
    for (let i = 0; i < vm.chapters.length; i++) {
      const d = vm.chapters[i].duration[voiceId] || 0;
      if (rem < d || i === vm.chapters.length - 1) { idx = i; seekTo = rem; break; }
      rem -= d;
    }
  }

  renderHead();
  renderVoices();
  $("speed").value = String(prefs.speed || 1);
  audio.playbackRate = Number($("speed").value);
  if (vm.hasGuide) {
    const link = document.getElementById("companion-link");
    if (link) { link.style.display = ""; link.href = `guide.html?book=${vm.id}`; }
  }

  loadChapter(idx, seekTo, false);
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
  writeJSON(localStorage, prefsKey(), { speed: value });
}

function wireControls() {
  $("btn-play").addEventListener("click", togglePlay);
  $("btn-back15").addEventListener("click", () => skip(-15));
  $("btn-fwd30").addEventListener("click", () => skip(30));
  $("btn-next").addEventListener("click", () => goNext());
  $("btn-prev").addEventListener("click", goPrev);
  $("speed").addEventListener("change", () => setSpeed(Number($("speed").value)));

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
    }
  });
}

init();

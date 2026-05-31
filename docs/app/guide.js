// Companion guide: renders grounded concept cards, director's commentary, glossary,
// and further reading from docs/guide/<book>.json. Every "▶ listen" jumps into the
// player at the passage's timestamp. No runtime LLM — pure static data.

import { formatTime } from "./logic.js";

const $ = (id) => document.getElementById(id);
const BOOK = new URLSearchParams(location.search).get("book") || "magnifica-humanitas";

function listenHref(ts) {
  return `player.html?book=${encodeURIComponent(BOOK)}&t=${Math.floor(ts)}`;
}

function conceptCard(c) {
  const el = document.createElement("details");
  el.className = "concept";
  const sum = document.createElement("summary");
  sum.textContent = c.title;
  el.appendChild(sum);

  const body = document.createElement("div");
  body.className = "concept-body";
  body.innerHTML =
    `<p class="blurb"></p>` +
    `<blockquote class="quote"></blockquote>` +
    `<div class="cite">` +
      `<span class="ch"></span>` +
      `<a class="listen" href="${listenHref(c.timestamp)}">▶ listen (${formatTime(c.timestamp)})</a>` +
    `</div>`;
  body.querySelector(".blurb").textContent = c.blurb;
  body.querySelector(".quote").textContent = `“${c.quote}”`;
  body.querySelector(".ch").textContent = `Chapter ${c.chapter} — ${c.chapter_title}`;
  el.appendChild(body);
  return el;
}

function commentaryItem(c) {
  const el = document.createElement("details");
  el.className = "aside";
  const sum = document.createElement("summary");
  sum.innerHTML = `<span class="aside-label"></span> <a class="listen" href="${listenHref(c.timestamp)}">▶ ${formatTime(c.timestamp)}</a>`;
  sum.querySelector(".aside-label").textContent = c.label;
  el.appendChild(sum);
  const p = document.createElement("p");
  p.className = "aside-text";
  p.textContent = c.text;
  el.appendChild(p);
  return el;
}

async function init() {
  let g;
  try {
    g = await (await fetch(`guide/${BOOK}.json`, { cache: "no-cache" })).json();
  } catch {
    $("app").innerHTML = '<div class="error">Companion not available for this book.</div>';
    return;
  }
  $("intro").textContent = g.intro || "";

  const cont = $("concepts");
  for (const c of g.concepts || []) cont.appendChild(conceptCard(c));

  const com = $("commentary");
  if (g.commentary && g.commentary.length) {
    for (const c of g.commentary) com.appendChild(commentaryItem(c));
  } else {
    $("commentary-section").style.display = "none";
  }

  const gl = $("glossary");
  for (const t of g.glossary || []) {
    const dt = document.createElement("dt");
    dt.textContent = t.term;
    const dd = document.createElement("dd");
    dd.textContent = t.def;
    gl.appendChild(dt);
    gl.appendChild(dd);
  }

  const fr = $("further");
  for (const r of g.further_reading || []) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = r.url;
    a.textContent = r.title;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    li.appendChild(a);
    if (r.note) {
      const span = document.createElement("span");
      span.className = "fr-note";
      span.textContent = ` — ${r.note}`;
      li.appendChild(span);
    }
    fr.appendChild(li);
  }
}

init();

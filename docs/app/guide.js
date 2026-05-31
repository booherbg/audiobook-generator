// Companion guide: renders grounded concept cards, director's commentary, glossary,
// and further reading from docs/guide/<book>.json. Every "▶ listen" jumps into the
// player at the passage's timestamp. No runtime LLM — pure static data.

const $ = (id) => document.getElementById(id);
const BOOK = new URLSearchParams(location.search).get("book") || "magnifica-humanitas";

// Voice-independent deep link: chapter + fraction-within-chapter. The player resolves
// the fraction against whichever voice the listener has selected, so the jump lands on
// the right passage regardless of voice (the voices differ in length by ~10%).
function listenHref(c) {
  return `player.html?book=${encodeURIComponent(BOOK)}&ch=${c.chapter}&f=${c.fraction}`;
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
      `<a class="listen" href="${listenHref(c)}">▶ listen from here</a>` +
    `</div>`;
  body.querySelector(".blurb").textContent = c.blurb;
  body.querySelector(".quote").textContent = `“${c.quote}”`;
  body.querySelector(".ch").textContent = `Chapter ${c.chapter} — ${c.chapter_title}`;

  if (c.related && c.related.length) {
    const rel = document.createElement("div");
    rel.className = "related";
    rel.append("see also: ");
    c.related.forEach((title, i) => {
      const a = document.createElement("a");
      a.className = "related-link";
      a.href = "#c-" + slug(title);
      a.textContent = title;
      a.addEventListener("click", (e) => { e.preventDefault(); openConcept(slug(title)); });
      rel.appendChild(a);
      if (i < c.related.length - 1) rel.append(" · ");
    });
    body.appendChild(rel);
  }
  el.appendChild(body);
  return el;
}

// Open a concept card by slug and bring it into view (related-link target may be collapsed).
function openConcept(s) {
  const target = document.getElementById("c-" + s);
  if (!target) return;
  target.open = true;
  target.scrollIntoView({ behavior: "smooth", block: "center" });
  target.classList.add("flash");
  setTimeout(() => target.classList.remove("flash"), 1200);
}

function commentaryItem(c) {
  const el = document.createElement("details");
  el.className = "aside";
  const sum = document.createElement("summary");
  sum.innerHTML = `<span class="aside-label"></span> <a class="listen" href="${listenHref(c)}">▶ listen</a>`;
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

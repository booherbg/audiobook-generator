// Full-text reader: renders docs/text/<book>.json as a calm, mobile-friendly long read
// with a chapter jump-list. The text is the same source the audio was rendered from.
// Optional ?ch=<n> opens scrolled to that chapter (so the player/companion can deep-link here).

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const BOOK = params.get("book") || "magnifica-humanitas";

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function render(d) {
  document.title = `Full text — ${d.title || BOOK}`;
  $("title").textContent = d.title || "Full text";
  $("byline").textContent = [d.subtitle, d.author].filter(Boolean).join(" · ");
  const playerLink = $("player-link");
  if (playerLink) playerLink.href = `player.html?book=${encodeURIComponent(BOOK)}`;

  if (d.source_url) {
    const note = $("src-note");
    note.innerHTML =
      "The complete text, for reading along or checking a passage. " +
      'The authoritative original is published by the Holy See at ';
    const a = document.createElement("a");
    a.href = d.source_url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = "vatican.va";
    note.appendChild(a);
    note.append(".");
  }

  const toc = $("toc");
  const text = $("text");
  for (const ch of d.chapters || []) {
    const id = "ch-" + ch.index;

    const link = document.createElement("a");
    link.className = "toc-link";
    link.href = "#" + id;
    link.textContent = `${ch.index}. ${ch.title}`;
    toc.appendChild(link);

    const sec = document.createElement("section");
    sec.className = "reader-chapter";
    sec.id = id;
    const h = document.createElement("h2");
    h.className = "reader-ch-title";
    h.textContent = `${ch.index}. ${ch.title}`;
    sec.appendChild(h);
    for (const p of ch.paragraphs || []) {
      const para = document.createElement("p");
      para.textContent = p;
      sec.appendChild(para);
    }
    // quiet "listen to this chapter" affordance — back into the player at this chapter
    const listen = document.createElement("a");
    listen.className = "reader-listen";
    listen.href = `player.html?book=${encodeURIComponent(BOOK)}&ch=${ch.index}&f=0`;
    listen.textContent = "▶ listen to this chapter";
    sec.appendChild(listen);

    text.appendChild(sec);
  }

  $("foot-note").textContent =
    "Reproduced for accessible reading and study; the original is always the authority.";

  // deep-link to a chapter if asked
  const chParam = params.get("ch");
  if (chParam) {
    const target = document.getElementById("ch-" + chParam);
    if (target) target.scrollIntoView();
  }
}

async function init() {
  let d;
  try {
    d = await (await fetch(`text/${BOOK}.json`, { cache: "no-cache" })).json();
  } catch {
    $("app").innerHTML = '<div class="error">Full text not available for this book.</div>';
    return;
  }
  try {
    render(d);
  } catch (err) {
    $("title").textContent = "Full text";
    $("text").innerHTML =
      '<p class="error">Something went wrong rendering the text. ' +
      '<a href="player.html?book=' + encodeURIComponent(BOOK) + '">Back to the player.</a></p>';
    console.error("reader render failed:", err);
  }
}

init();

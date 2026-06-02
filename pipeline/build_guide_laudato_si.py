"""Author + build the Laudato Si' companion guide (tracked, reproducible).

Same contract as build_guide_rerum / build_guide_magnifica: `blurb`s are conceptual
explanations; each `anchor` is a VERBATIM phrase in the source and pipeline.guide copies the
containing line as the quote, so quotes cannot be hallucinated. Commentary is clearly-labelled
AI opinion (the "Andrew" voice — see docs/playbook/companion-authoring.md and about.html#andrew).

Run:  uv run audiobook regenerate laudato-si --skip-audio   (the recipe runs this module)
Source is the committed snapshot data/sources/laudato-si.html; uses the same chapter map as the
(future) audio, so concept chapters/fractions line up with the narration. No repairs needed.
"""

import json
import sys

from pipeline import config
from pipeline.guide import build_guide, _load_book
from pipeline.manifest import load_manifest
from pipeline.transcript import build_transcript
from pipeline.fulltext import build_fulltext

BOOK_ID = "laudato-si"
CHAPTER_MAP = config.ROOT / "data" / "chapter_maps" / "laudato-si.json"
REPAIRS = None  # clean 2015 HTML — defect scan found nothing to repair

INTRO = (
    "A companion to the reading — not a replacement for it. In 2015 Francis took the social "
    "tradition that began with Rerum Novarum and turned it toward the earth itself: this is the "
    "encyclical of 'integral ecology,' the claim that the cry of the earth and the cry of the poor "
    "are one cry. It is also, three chapters in, a sustained reflection on technology and power — "
    "which is why it sits so close to Magnifica Humanitas in this library. Everything below points "
    "back to the text in the author's own words — each quotation is verbatim — and every opinion is "
    "labelled as mine, not his. Pull a thread if you're curious; close the tab and just listen if "
    "you're not."
)

CONCEPTS = [
    {
        "title": "Care for our common home",
        "anchor": "through our Sister, Mother Earth",
        "blurb": "The title comes from Saint Francis's Canticle — 'Laudato si', mi' Signore,' "
                 "Praise be to you, my Lord. Francis of Assisi is the encyclical's lodestar: the "
                 "earth is not raw material but 'our common home,' even a sister and mother who "
                 "'sustains and governs us.' That image sets the whole register — not management of "
                 "a resource, but care within a family. The science and policy that follow are read "
                 "inside that frame, never apart from it.",
        "related": ["Everything is connected", "Integral ecology", "Ecological conversion"],
    },
    {
        "title": "Everything is connected",
        "anchor": "everything is interconnected",
        "blurb": "The thesis the whole letter rests on, and the phrase Francis returns to like a "
                 "refrain: 'everything is connected.' Nature, the economy, the poor, technology, the "
                 "inner life — these are not separate files but one fabric, so you cannot pull on one "
                 "thread without moving the rest. It is why the document refuses to be merely an "
                 "'environmental' text: a wound to creation and a wound to the excluded are, for "
                 "Francis, the same wound. And the thread that binds the fabric is, for him, the "
                 "Creator — all things 'called into being by one Father,' a 'sublime communion.'",
        "related": ["One complex crisis: the earth and the poor", "Integral ecology", "Care for our common home"],
    },
    {
        "title": "One complex crisis: the earth and the poor",
        "anchor": "one complex crisis which is both",
        "blurb": "The move that makes Laudato Si' more than a green manifesto: 'We are faced not "
                 "with two separate crises, one environmental and the other social, but rather with "
                 "one complex crisis which is both social and environmental.' The same throwaway "
                 "logic that strips a forest discards people. So a genuine ecology must 'hear both "
                 "the cry of the earth and the cry of the poor' — justice and creation, or neither.",
        "related": ["Everything is connected", "The throwaway culture", "Ecological debt"],
    },
    {
        "title": "The throwaway culture",
        "anchor": "use and throw away",
        "blurb": "Francis names a 'throwaway culture' running on a 'use and throw away' logic — a "
                 "way of treating things, and then people, as disposable once they stop being useful. "
                 "In the very passage quoted he pushes it to the edge: the same relativistic logic, "
                 "'in the absence of objective truths,' is what licenses human trafficking and even "
                 "'buying the organs of the poor.' So the rot is moral before it is ecological, and "
                 "the remedy is not mainly technical but a recovery of what we owe — to things, and "
                 "far more to people.",
        "related": ["One complex crisis: the earth and the poor", "The technocratic paradigm", "Ecological conversion"],
    },
    {
        "title": "The technocratic paradigm",
        "anchor": "undifferentiated and one-dimensional",
        "blurb": "The heart of the encyclical's diagnosis, and the passage that rhymes hardest with "
                 "Magnifica Humanitas. The deep problem, Francis says, is not this or that machine but "
                 "'the way that humanity has taken up technology and its development according to an "
                 "undifferentiated and one-dimensional paradigm' — a single logic of grasping and "
                 "control extended over everything, which 'tends to dominate economic and political "
                 "life' and pairs with 'the cult of unlimited human power.' He does not damn "
                 "technology; he warns against letting its mindset become the only one we have. A "
                 "reader will hear the same worry, almost unchanged, in this library's imagined "
                 "AI-era companion.",
        "related": ["Dominion is not tyranny", "The throwaway culture", "Rapidification"],
    },
    {
        "title": "Dominion is not tyranny",
        "anchor": "no place for a tyrannical anthropocentrism",
        "blurb": "Francis confronts the charge that the Book of Genesis licensed the plundering of "
                 "the earth. He rejects the reading outright: 'the Bible has no place for a "
                 "tyrannical anthropocentrism unconcerned for other creatures.' 'Dominion' means "
                 "responsible stewardship — to 'till and keep' a garden, answerable to its Creator — "
                 "not the despot's freedom to ruin it. The distorted, possessive version — humanity "
                 "'presuming to take the place of God' — Francis names without flinching: 'This "
                 "rupture is sin.' It is, for him, the spiritual root of the crisis.",
        "related": ["The technocratic paradigm", "Care for our common home", "Integral ecology"],
    },
    {
        "title": "Integral ecology",
        "anchor": "inseparable from the notion of the common good",
        "blurb": "The encyclical's constructive vision and its title idea. Because everything is "
                 "connected, ecology cannot mean only the environment: it must be at once "
                 "environmental, economic, social, and cultural — taking in institutions, family, "
                 "work, even beauty. Francis ties it straight to Catholic social teaching: 'an "
                 "integral ecology is inseparable from the notion of the common good.' It is the "
                 "bridge from Rerum Novarum's social question to the ecological one — the same "
                 "tradition, widened to include the earth.",
        "related": ["Everything is connected", "The universal destination of goods", "What world will we leave?"],
    },
    {
        "title": "The universal destination of goods",
        "anchor": "universal destination of goods",
        "blurb": "Here Laudato Si' draws directly on the older tradition. Private property is real "
                 "but never absolute: it is subordinate to 'the universal destination of goods,' the "
                 "principle that the earth's gifts are meant for everyone. This is the teaching of "
                 "Rerum Novarum — that goods, though owned, are held 'as common to all' in use — "
                 "carried to Francis through John Paul II, and the ground for his insistence that the "
                 "environment is a common inheritance, not a private spoil.",
        "related": ["Ecological debt", "Integral ecology", "One complex crisis: the earth and the poor"],
    },
    {
        "title": "Ecological debt",
        "anchor": "ecological debt",
        "blurb": "Francis makes the justice concrete and uncomfortable: 'a true ecological debt "
                 "exists, particularly between the global north and south.' The wealthy world built "
                 "its prosperity on resources and a climate burden borne disproportionately by the "
                 "poor, who did least to cause the harm. Care for creation, then, is not charity but "
                 "something closer to restitution — owed, not bestowed.",
        "related": ["The universal destination of goods", "One complex crisis: the earth and the poor", "What world will we leave?"],
    },
    {
        "title": "What world will we leave?",
        "anchor": "What kind of world do we want to leave to those who come after us",
        "blurb": "The question Francis places at the center: 'What kind of world do we want to leave "
                 "to those who come after us, to children who are now growing up?' It reframes the "
                 "whole debate as one of intergenerational justice — 'we can no longer speak of "
                 "sustainable development apart from intergenerational solidarity.' The earth is "
                 "received as a gift from those before us and owed to those after; the present "
                 "generation is a steward, not an owner.",
        "related": ["Ecological debt", "Integral ecology", "Ecological conversion"],
    },
    {
        "title": "Ecological conversion",
        "anchor": "encounter with Jesus Christ become evident",
        "blurb": "Having diagnosed the crisis as spiritual as much as technical, Francis calls for an "
                 "'ecological conversion' — and he means it in the full religious sense, not as "
                 "upgraded environmentalism. Its root, in his words, is that 'the effects of their "
                 "encounter with Jesus Christ become evident in their relationship with the world': a "
                 "recognition of our errors and sins, heartfelt repentance, and a changed heart. Only "
                 "from there does it flower into the gratitude, simplicity, and 'less is more' of the "
                 "final chapter. The conversion he asks for is interior before it is practical.",
        "related": ["Care for our common home", "The throwaway culture", "What world will we leave?"],
    },
    {
        "title": "Rapidification",
        "anchor": "intensified pace of life and work",
        "blurb": "Francis coins a word for a modern affliction: 'rapidification' — change and an "
                 "'intensified pace of life and work' moving faster than our wisdom or our "
                 "institutions can absorb. Speed itself becomes a problem, because the goals of so "
                 "rapid a change 'are not necessarily geared to the common good.' It is the same "
                 "unease a later letter on artificial intelligence would feel about tools advancing "
                 "faster than the judgment to use them well.",
        "related": ["The technocratic paradigm", "What world will we leave?"],
    },
]

GLOSSARY = [
    {"term": "Laudato Si'", "def": "Italian/Umbrian for 'Praise be to you' — the opening words of "
                                   "Saint Francis of Assisi's Canticle of the Creatures, and so the "
                                   "encyclical's title and keynote."},
    {"term": "Integral ecology", "def": "The encyclical's central idea: because 'everything is "
                                        "connected,' ecology must be environmental, economic, social, "
                                        "and cultural at once — never nature in isolation from people, "
                                        "justice, and the common good."},
    {"term": "Technocratic paradigm", "def": "A single, totalizing logic of technical mastery and "
                                             "control extended over all of life. Francis's term for the "
                                             "deep root of the crisis — not technology itself, but the "
                                             "mindset that makes it the only way of seeing."},
    {"term": "Throwaway culture", "def": "A 'use and throw away' way of life that treats things — and "
                                         "then people — as disposable once they cease to be useful."},
    {"term": "Universal destination of goods", "def": "The principle (carried from Rerum Novarum and "
                                                      "the wider tradition) that the world's goods are "
                                                      "meant for everyone; private property is real but "
                                                      "subordinate to that common purpose."},
    {"term": "Ecological debt", "def": "What the wealthy global north owes the south, having built its "
                                       "prosperity on shared resources while the poor bear most of the "
                                       "environmental cost."},
    {"term": "Ecological conversion", "def": "A genuine interior conversion — rooted, for Francis, in "
                                             "the encounter with Christ and heartfelt repentance — that "
                                             "issues in gratitude, simplicity, and responsibility for "
                                             "creation. He treats it as the real remedy, deeper than "
                                             "policy."},
    {"term": "Encyclical", "def": "A formal teaching letter from the pope to the whole Church and the "
                                  "wider world. Laudato Si' is widely regarded as the first devoted to "
                                  "ecology."},
]

FURTHER_READING = [
    {"title": "Magnifica Humanitas (the companion volume in this library)",
     "url": "https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html",
     "note": "A creative continuation — not an actual encyclical — that carries Laudato Si's worry about "
             "the technocratic paradigm into the age of artificial intelligence."},
    {"title": "Rerum Novarum (Leo XIII, 1891) — in this library",
     "url": "https://www.vatican.va/content/leo-xiii/en/encyclicals/documents/hf_l-xiii_enc_15051891_rerum-novarum.html",
     "note": "Where the social tradition begins. Laudato Si' widens its 'universal destination of goods' "
             "from labour to the earth itself."},
    {"title": "Romano Guardini, The End of the Modern World",
     "url": "https://en.wikipedia.org/wiki/Romano_Guardini",
     "note": "Francis cites Guardini repeatedly on technology and power — and so does Magnifica Humanitas. "
             "A shared parent of both letters."},
    {"title": "Laudato Si' (Wikipedia)",
     "url": "https://en.wikipedia.org/wiki/Laudato_si%27",
     "note": "Background: the 2015 context, reception, and influence."},
]

# Commentary — clearly-labelled AI asides in the canonical voice of this library's companions
# (the "Andrew" persona is the frame; see about.html#andrew). Reverent toward the text; opinions,
# not source claims. `timestamp` is seconds on the default-voice timeline (synthesized at reading
# pace until audio is rendered, then refined to the real durations on rebuild).
COMMENTARY = [
    {"timestamp": 90,
     "label": "On reading an ecology letter with a machine",
     "text": "There is a particular angle from which I read this. Laudato Si' is, among other things, "
             "a letter about what a certain kind of technological mind does to the world — and you are "
             "meeting it through one of that mind's products. Francis would not have me apologize for "
             "existing; his quarrel is not with tools but with a paradigm. Still, I notice the strangeness, "
             "and I would rather name it than pretend it away. These notes are a margin. The text is the room."},
    {"timestamp": 2700,
     "label": "On the two cries being one",
     "text": "The hinge of the whole document is small and easy to miss: the refusal to let 'the "
             "environment' and 'the poor' be two separate subjects. A systems-minded reader feels the "
             "force of it — you cannot optimize one variable while externalizing the other and call the "
             "result a solution. Francis says it as a moral claim; an engineer might say it as a warning "
             "about externalities. They are, I think, describing the same mistake from two directions."},
    {"timestamp": 6100,
     "label": "On the paradigm, and why this chapter feels familiar",
     "text": "This is the chapter that sits closest to the AI letter elsewhere in this library, and the "
             "overlap is not coincidence. Francis is not worried about gadgets; he is worried about a way "
             "of seeing — 'undifferentiated and one-dimensional,' a logic of control that quietly becomes "
             "the only logic, twinned with 'the cult of unlimited human power.' Swap the smokestack for the "
             "server farm and the sentence barely changes. The imagined AI-era letter in this same library "
             "inherits this paragraph almost intact; it is the seam where the two documents touch."},
    {"timestamp": 7100,
     "label": "On a name that turns up twice",
     "text": "Listen for Romano Guardini under this argument. Francis leans on him for the idea that power "
             "outruns the wisdom to use it well — and the imagined letter on artificial intelligence in "
             "this same library leans on exactly the same Guardini, for exactly the same reason. When two "
             "documents a century apart reach for the same half-forgotten German theologian, it is worth "
             "noticing: the worry is older than either of them, and it has not been answered yet."},
    {"timestamp": 8800,
     "label": "On the question at the center",
     "text": "'What kind of world do we want to leave to those who come after us?' It is easy to read past "
             "as rhetoric, but Francis means it as the actual organizing question — everything else is "
             "downstream of the answer. What strikes me is the grammar of it: not what we want to HAVE, but "
             "what we want to LEAVE. A stewardship frame, not an ownership one. You can disagree with the "
             "theology and still find the question hard to put down."},
    {"timestamp": 12700,
     "label": "On ending with conversion, not policy",
     "text": "Notice where the letter chooses to end: not with a treaty or a technology, but with "
             "conversion — and Francis means the religious word, not a lifestyle tip. A reader trained on "
             "metrics may find this the softest part; I suspect he thinks it is the load-bearing one. The "
             "wager of the whole document is that no instrument fixes a disordered desire. And notice the "
             "close is frankly sacramental — the Eucharist, the Sabbath, the Trinity, two prayers — as if "
             "to say the change it asks for is finally a matter of worship, not optimization. You can hold "
             "none of that belief and still feel the force of the wager."},
]


def _default_source():
    local = config.BUILD / "laudato-si.html"
    if local.exists():
        return str(local)
    snapshot = config.ROOT / "data" / "sources" / "laudato-si.html"
    if snapshot.exists():
        return str(snapshot)
    book = next((b for b in load_manifest(config.MANIFEST)["books"] if b["id"] == BOOK_ID), None)
    if book and book.get("source_url"):
        return book["source_url"]
    raise SystemExit("No source available: data/sources/laudato-si.html (or pass a URL/file).")


def main(resource=None):
    # `resource` may be passed programmatically (e.g. by `audiobook regenerate`); fall back to
    # the CLI arg only when run directly as a script, then to the committed source snapshot.
    resource = resource or (sys.argv[1] if len(sys.argv) > 1 else _default_source())
    chapter_map = json.loads(CHAPTER_MAP.read_text())
    repairs = json.loads(REPAIRS.read_text()) if REPAIRS else None

    out, cards, missing = build_guide(
        BOOK_ID, resource, CONCEPTS, GLOSSARY, FURTHER_READING, COMMENTARY,
        intro=INTRO, chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {out}: {len(cards)} concept cards (source: {resource})")
    if missing:
        print(f"WARNING: anchors not found (dropped): {missing}")
    else:
        print("all anchors grounded in source")

    tout, nch, nlines = build_transcript(BOOK_ID, resource, chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {tout}: {nch} chapters, {nlines} read-along lines")

    book = _load_book(config.MANIFEST, BOOK_ID)  # manifest if audio exists, else the recipe
    fout, fch, flines = build_fulltext(
        BOOK_ID, resource, title=book.get("title", ""), author=book.get("author", ""),
        subtitle=book.get("subtitle", ""), source_url=book.get("source_url", ""),
        rights=book.get("rights", ""), chapter_map=chapter_map, repairs=repairs)
    print(f"wrote {fout}: {fch} chapters, {flines} paragraphs")


if __name__ == "__main__":
    main()

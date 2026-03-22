"""
update_shloka.py
Fetches a shloka from the free Bhagavad Gita API (no key needed)
and rewrites the SHLOKA_START...SHLOKA_END block in README.md.

API: https://bhagavadgitaapi.in
  GET /slok/{chapter}/{verse}/
  Returns JSON with .slok (Sanskrit), .tej (Hindi), .siva (translation)

Covers all 700 verses across 18 chapters.
Rotates day-of-year % 700 so every visitor sees the same verse today,
different one tomorrow.
"""

import re, pathlib, datetime, requests, sys

# verse counts per chapter  (ch 1..18)
CHAPTER_VERSES = [47,72,43,42,29,47,30,28,34,42,55,20,35,27,20,24,28,78]

def all_refs():
    """Return list of (chapter, verse) for all ~700 shlokas."""
    refs = []
    for ch, total in enumerate(CHAPTER_VERSES, start=1):
        for v in range(1, total + 1):
            refs.append((ch, v))
    return refs

def pick_today(refs):
    day = datetime.date.today().timetuple().tm_yday
    year = datetime.date.today().year
    # mix year in so we don't repeat exact same sequence every year
    idx = (day + year * 365) % len(refs)
    return refs[idx]

def fetch_shloka(chapter, verse):
    url = f"https://bhagavadgitaapi.in/slok/{chapter}/{verse}/"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        sanskrit = data.get("slok", "").strip()
        # prefer English translation; fall back to Hindi
        translation = (
            data.get("siva", {}).get("et", "")
            or data.get("tej", {}).get("ht", "")
            or data.get("purohit", {}).get("et", "")
            or data.get("san", {}).get("et", "")
        ).strip()
        return sanskrit, translation
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        return None, None

# fallback shlokas if API is down
FALLBACKS = {
    (2, 47): (
        "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।\n"
        "मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि॥",
        "You have the right to perform your prescribed duties,\n"
        "but you are not entitled to the fruits of your actions.\n"
        "Never consider yourself the cause of results,\n"
        "and never be attached to not doing your duty."
    ),
    (2, 20): (
        "न जायते म्रियते वा कदाचिन्नायं भूत्वा भविता वा न भूयः।\n"
        "अजो नित्यः शाश्वतोऽयं पुराणो न हन्यते हन्यमाने शरीरे॥",
        "The soul is never born nor dies at any time.\n"
        "It has not come into being, does not come into being,\n"
        "and will not come into being. It is unborn, eternal,\n"
        "ever-existing, and primeval.\n"
        "It is not slain when the body is slain."
    ),
    (2, 23): (
        "नैनं छिद्रन्ति शस्त्राणि नैनं दहति पावकः।\n"
        "न चैनं क्लेदयन्त्यापो न शोषयति मारुतः॥",
        "The soul can never be cut by any weapon,\n"
        "nor burned by fire, nor moistened by water,\n"
        "nor withered by the wind."
    ),
    (4,  7): (
        "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत।\n"
        "अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्॥",
        "Whenever there is a decline in righteousness\n"
        "and a rise in unrighteousness, O Arjuna,\n"
        "at that time I manifest myself on earth."
    ),
    (6,  5): (
        "उद्धरेदात्मनात्मानं नात्मानमवसादयेत्।\n"
        "आत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः॥",
        "Elevate yourself through the power of your mind,\n"
        "and do not degrade yourself.\n"
        "The mind is the friend of the conditioned soul,\n"
        "and his enemy as well."
    ),
    (18, 66): (
        "सर्वधर्मान्परित्यज्य मामेकं शरणं व्रज।\n"
        "अहं त्वां सर्वपापेभ्यो मोक्षयिष्यामि मा शुचः॥",
        "Abandon all varieties of dharma and\n"
        "just surrender unto me alone.\n"
        "I shall deliver you from all sinful reactions.\n"
        "Do not fear."
    ),
    (10, 20): (
        "अहमात्मा गुडाकेश सर्वभूताशयस्थितः।\n"
        "अहमादिश्च मध्यं च भूतानामन्त एव च॥",
        "I am the self seated in the hearts of all creatures.\n"
        "I am the beginning, the middle,\n"
        "and the end of all beings."
    ),
}

def build_block(chapter, verse, sanskrit, translation):
    lines = [
        f"> 🪷 **Bhagavad Gita · Chapter {chapter}, Verse {verse}**",
        ">",
    ]
    for line in (sanskrit or "").split("\n"):
        if line.strip():
            lines.append(f"> *{line.strip()}*")
    lines.append(">")
    for line in (translation or "").split("\n"):
        if line.strip():
            lines.append(f"> {line.strip()}")
    return "\n".join(lines)

def main():
    refs   = all_refs()
    ch, v  = pick_today(refs)
    print(f"Today: Chapter {ch}, Verse {v}  ({len(refs)} total)")

    sanskrit, translation = fetch_shloka(ch, v)

    # fallback: try neighbour verse, then hardcoded
    if not sanskrit:
        print("Primary fetch failed, trying fallback verse...")
        fb = FALLBACKS.get((ch, v))
        if fb:
            sanskrit, translation = fb
        else:
            # try any hardcoded fallback
            (ch, v), (sanskrit, translation) = list(FALLBACKS.items())[
                datetime.date.today().timetuple().tm_yday % len(FALLBACKS)
            ]
            print(f"Using hardcoded fallback: {ch}.{v}")

    block   = build_block(ch, v, sanskrit, translation)
    readme  = pathlib.Path("README.md").read_text(encoding="utf-8")
    updated = re.sub(
        r"<!-- SHLOKA_START -->.*?<!-- SHLOKA_END -->",
        f"<!-- SHLOKA_START -->\n{block}\n<!-- SHLOKA_END -->",
        readme,
        flags=re.DOTALL,
    )
    pathlib.Path("README.md").write_text(updated, encoding="utf-8")
    print(f"✅ README updated — Gita {ch}.{v}")

if __name__ == "__main__":
    main()

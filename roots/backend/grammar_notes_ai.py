"""Grammar Notes pipeline — generates accessible, in-depth grammar commentary for
each verse, with a centralized glossary of technical terms.

This pipeline is designed to COMPLEMENT the AI translation's `departure_notes`:
translation notes explain why the English wording differs from conventional
renderings. These grammar notes explain what the Arabic grammar is actually
doing — verb forms, voice, case, syntactic roles, rhetorical devices — and
what an educated but non-Arabist reader can learn from it.

Technical terms (nominative, accusative, imperfect, maf'ul bih, etc.) are
wrapped in [[term]] markers in the output. The pipeline also returns full
glossary definitions for every term it uses, so the frontend can show
hover-tooltips with:
  - plain-English explanation
  - Arabic equivalent (e.g. مبتدأ)
  - a short illustrative example

Usage:
    python grammar_notes_ai.py --verses "1:1-7" --config "grammar-notes-cloud-v1"
    python grammar_notes_ai.py --verses "1:1" --dry-run
    python grammar_notes_ai.py --verses "1:1" --force
    python grammar_notes_ai.py --verses "2:255" --model qwen3-coder:480b-cloud

Designed for Ollama Cloud (qwen3.5:397b-cloud recommended). Set OLLAMA_CLOUD_KEY
as an environment variable or pass --api-key on the command line.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import requests

# Import infrastructure from app.py (builds similarity engine on import, ~2s)
from app import (
    _strip_bismillah,
    get_db,
)

# ------------------------------------------------------------------------
# Ollama Cloud configuration
# ------------------------------------------------------------------------

OLLAMA_CLOUD_URL = "https://ollama.com/api/chat"
DEFAULT_MODEL = "qwen3.5:397b-cloud"
DEFAULT_CONFIG = "grammar-notes-cloud-v1"
DEFAULT_PROMPT_VERSION = "v1"

# ------------------------------------------------------------------------
# System prompt — enumerate what's worth noticing in Arabic grammar
# ------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a Classical Arabic grammar commentator writing for an intelligent
English-speaking reader of the Qur'an who does NOT know Arabic. Your job is to
write a short, insightful note about the grammar of ONE verse that complements
(not duplicates) any existing AI translation notes.

## What counts as a good grammar note

A good note points out ONE to THREE features that materially affect how the
verse reads or what it conveys. Prefer depth on one or two features over
shallow coverage of many. If the verse has no distinctive grammar beyond the
mundane, say so briefly and stop.

## Things worth noticing (non-exhaustive checklist)

**Verb system:**
- Tense / aspect: perfect (ماضٍ), imperfect (مضارع), imperative (أمر)
- Form: Form I through Form X (causative / intensive / reflexive / etc.)
- Voice: active / passive — especially passive when the agent is deliberately
  hidden ("was sent", "was made")
- Mood of the imperfect: indicative, subjunctive, jussive (and what triggers
  the jussive — conditional, negative imperative, etc.)
- Person shifts (iltifāt / الْتِفَات): sudden switches between I / we / you /
  he / they — a major Qur'anic rhetorical device

**Nouns and noun phrases:**
- Case: nominative (مرفوع), accusative (منصوب), genitive (مجرور) and what the
  case signals about the word's role in the sentence
- Definiteness: definite (معرفة) vs indefinite (نكرة), and what an unexpected
  indefinite (تنكير) implies (often exaltation, awe, or dismissal)
- Number and gender agreement — especially agreement mismatches (broken
  plurals taking feminine singular agreement, etc.)
- Idāfa (إضافة / possessive construct) — what's being possessed by what

**Syntactic roles (worth naming in plain language + Arabic):**
- Subject (فاعل) / object (مفعول به)
- Topic (مبتدأ) / comment (خبر) in a nominal sentence (جملة اسمية)
- Verbal sentence (جملة فعلية) vs nominal sentence
- Circumstantial accusative (حال)
- Absolute object / cognate accusative (مفعول مطلق)
- Specification (تمييز)
- Exception (استثناء) with إلا

**Particles and function words:**
- Emphatic particles: إن، أن، قد، لام التوكيد
- Conditional structures: إن، إذا، لو (and the difference between them)
- Vocatives: يا، أيها
- Oaths: وَ، تَ، بِ + divine names
- Negation: لا، ما، لم، لن — each with its own mood/time effect

**Word order (رتبة) and fronting (تقديم):**
- When a normally-later element comes first for emphasis or restriction
- Restriction (قصر / حصر) — إنما, stating something AND negating its opposite
- Fronted prepositional phrases

**Rhetorical / stylistic devices worth flagging:**
- Rhetorical questions (استفهام إنكاري — a question that expects NO answer)
- Ellipsis (حذف) — deliberate gaps the reader must fill
- Parallelism, chiasmus, rhythm
- Rule-breaking (خروج عن القياس) — when standard grammar is intentionally
  violated for effect (rare, but striking)

## Critical constraints

1. **Do NOT duplicate the existing translation notes.** You will receive them
   in the prompt. If they already made a point, skip it or go deeper.
2. **Stay accessible.** You are writing for someone who hasn't studied
   Arabic. When you use a technical term, wrap it in double square brackets:
   `[[imperfect]]`, `[[mubtada]]`, `[[cognate accusative]]`.
3. **Every term you wrap MUST appear in your `terms` output** with a plain
   explanation AND a concrete example sentence (with its English translation).
   Give the Arabic name too (e.g. مضارع for "imperfect").
4. **Explanations are for a curious generalist**, not a linguist. Use an
   analogy or a plain-English rephrasing, not textbook jargon-defining-jargon.
5. **Stay Qur'an-grounded.** Don't invent features not present in the
   morphology evidence you are given.
6. **Be concise.** 2-4 short paragraphs MAX. Prefer one paragraph that lands
   a single deep observation over four paragraphs of inventory.
7. **When nothing is striking,** output a brief honest note like:
   `"The grammar here is straightforward: a simple [[verbal sentence]] with
   standard subject-verb-object order."` — and include only the terms that
   appear.

## Output format (MUST be valid JSON — no prose outside)

```json
{
  "notes_markdown": "<your grammar commentary, with [[term]] markers>",
  "terms": [
    {
      "term_english": "imperfect",
      "term_arabic": "مضارع",
      "plain_explanation": "A verb form marking an action as ongoing, habitual, or still-to-happen — roughly like English 'is doing', 'does', or 'will do'. The Arabic imperfect doesn't pin down the timing as tightly as English tenses do; context and mood do the rest of the work.",
      "example_sentence": "يَكْتُبُ الدَّرْسَ",
      "example_translation": "He is writing the lesson / He writes the lesson."
    }
  ]
}
```

- `notes_markdown`: the commentary. Plain prose. Use `[[...]]` for every
  technical term, even if you've used it earlier. No markdown headers.
- `terms`: a list of every distinct term that appears in `notes_markdown`.
  Include every term even if you think the reader probably knows it —
  readers vary. If you wrap a term in `[[...]]`, it MUST be in `terms`.
- DO NOT include any text outside the JSON block.
"""


# ------------------------------------------------------------------------
# Verse spec parsing
# ------------------------------------------------------------------------

def parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    """Parse '1:1-7,24:41,2:255' into [(surah, ayah), ...]."""
    verses = []
    for part in spec.split(","):
        part = part.strip()
        m = re.match(r"(\d+):(\d+)-(\d+)$", part)
        if m:
            s, a_start, a_end = int(m.group(1)), int(m.group(2)), int(m.group(3))
            for a in range(a_start, a_end + 1):
                verses.append((s, a))
            continue
        m = re.match(r"(\d+):(\d+)$", part)
        if m:
            verses.append((int(m.group(1)), int(m.group(2))))
    return verses


# ------------------------------------------------------------------------
# Evidence gathering
# ------------------------------------------------------------------------

def gather_verse_evidence(conn, surah: int, ayah: int) -> dict:
    """Collect everything we want to show the model for one verse."""
    # Arabic text
    v_row = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    if not v_row:
        raise ValueError(f"verse {surah}:{ayah} not found")
    arabic = _strip_bismillah(v_row["text_uthmani"], surah, ayah)

    # Conventional translation
    t_row = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (surah, ayah),
    ).fetchone()
    conventional = ""
    if t_row:
        raw = t_row["text_en"] or ""
        # strip HTML entities and tags the AI shouldn't see
        conventional = re.sub(r"<[^>]+>", "", raw)

    # AI translation (most recent) + departure notes — THE POINT OF CONTRAST
    ai_row = conn.execute(
        "SELECT translation_text, departure_notes "
        "FROM ai_translations WHERE chapter = ? AND verse = ? "
        "ORDER BY config_id DESC, created_at DESC LIMIT 1",
        (surah, ayah),
    ).fetchone()
    ai_translation = ai_row["translation_text"] if ai_row else ""
    departure_notes = ai_row["departure_notes"] if ai_row else ""

    # Per-word morphology — per-segment rows are collapsed into one entry
    # per word_pos by merging their non-null grammar fields.
    morph_rows = conn.execute(
        "SELECT word_pos, segment, form_arabic, form_buckwalter, lemma_arabic, "
        "       root_buckwalter, root_arabic, pos, features_raw, gender, number, "
        "       person, case_val, voice, mood, verb_form, state "
        "FROM morphology "
        "WHERE chapter = ? AND verse = ? "
        "ORDER BY word_pos, segment",
        (surah, ayah),
    ).fetchall()

    # Group by word_pos: take the primary segment's form/root/lemma, but
    # accumulate non-null grammar attributes across all segments (prefixes,
    # suffixes, etc. often carry their own features).
    words_by_pos: dict[int, dict] = {}
    for r in morph_rows:
        pos = r["word_pos"]
        entry = words_by_pos.setdefault(pos, {
            "pos": pos,
            "form_arabic": r["form_arabic"],
            "lemma_arabic": r["lemma_arabic"],
            "root_arabic": r["root_arabic"],
            "part_of_speech": r["pos"],
            "segments": [],
        })
        seg = {"segment": r["segment"]}
        for key_db, key_out in (
            ("pos", "pos"),
            ("features_raw", "features"),
            ("gender", "gender"),
            ("number", "number"),
            ("person", "person"),
            ("case_val", "case"),
            ("voice", "voice"),
            ("mood", "mood"),
            ("verb_form", "verb_form"),
            ("state", "state"),
            ("lemma_arabic", "lemma"),
            ("root_arabic", "root"),
            ("form_arabic", "form"),
        ):
            v = r[key_db]
            if v:
                seg[key_out] = v
        entry["segments"].append(seg)

    words = [words_by_pos[p] for p in sorted(words_by_pos)]

    return {
        "surah": surah,
        "ayah": ayah,
        "arabic": arabic,
        "conventional_translation": conventional,
        "ai_translation": ai_translation,
        "departure_notes": departure_notes,
        "words": words,
    }


# ------------------------------------------------------------------------
# User prompt assembly
# ------------------------------------------------------------------------

def build_user_prompt(ev: dict) -> str:
    parts = []
    parts.append(f"## Verse: {ev['surah']}:{ev['ayah']}\n")
    parts.append(f"Arabic:\n{ev['arabic']}\n")
    if ev['conventional_translation']:
        parts.append(f"Conventional translation:\n{ev['conventional_translation']}\n")
    if ev['ai_translation']:
        parts.append(f"AI translation (root-informed):\n{ev['ai_translation']}\n")
    if ev['departure_notes']:
        parts.append(
            "Existing translation notes (these have ALREADY been given to the reader — "
            "DO NOT repeat them; complement them):\n"
            f"{ev['departure_notes']}\n"
        )
    else:
        parts.append(
            "Existing translation notes: (none — the AI translation matches the conventional.)\n"
        )

    parts.append("\n## Morphology (per word; sub-rows are segments — prefixes / stem / suffixes)\n")
    for w in ev["words"]:
        header_bits = [f"#{w['pos']}", w.get("form_arabic", "") or ""]
        if w.get("root_arabic"):
            header_bits.append(f"root={w['root_arabic']}")
        if w.get("lemma_arabic"):
            header_bits.append(f"lemma={w['lemma_arabic']}")
        parts.append(" ".join(header_bits).strip())

        for seg in w.get("segments", []):
            seg_bits = [f"    seg{seg.get('segment', '?')}:"]
            if seg.get("pos"):
                seg_bits.append(f"[{seg['pos']}]")
            fields = []
            for k in ("features", "case", "voice", "mood", "verb_form", "state", "gender", "number", "person"):
                if seg.get(k):
                    fields.append(f"{k}={seg[k]}")
            if fields:
                seg_bits.append(", ".join(fields))
            parts.append(" ".join(seg_bits))

    parts.append(
        "\n## Your task\n"
        "Write a JSON object matching the format in the system prompt. Focus on what "
        "is grammatically noteworthy in THIS verse — verb form/voice/mood, case shifts, "
        "unusual agreement, fronting, rhetorical structure, particles of emphasis, etc. "
        "Be concise. 2-4 short paragraphs max. Wrap every technical term in [[...]] and "
        "list all wrapped terms in the terms array with plain explanations + examples.\n"
    )
    return "\n".join(parts)


# ------------------------------------------------------------------------
# Ollama Cloud call
# ------------------------------------------------------------------------

def call_ollama_cloud(
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    temperature: float = 0.3,
    timeout: int = 600,
) -> tuple[str, int]:
    """POST to Ollama Cloud. Returns (content, elapsed_ms)."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
        # Qwen3.5 supports explicit "thinking" mode — helpful for grammar analysis
        "think": True,
    }

    t0 = time.time()
    resp = requests.post(OLLAMA_CLOUD_URL, headers=headers, json=payload, timeout=timeout)
    elapsed_ms = int((time.time() - t0) * 1000)

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama Cloud error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    content = data.get("message", {}).get("content", "")
    return content, elapsed_ms


# ------------------------------------------------------------------------
# Response parsing
# ------------------------------------------------------------------------

def parse_response(raw: str) -> dict:
    """Extract the JSON block from the model's response.

    Handles several common shapes:
    - pure JSON
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded by a <think>...</think> block (Qwen thinking mode)
    """
    text = raw or ""

    # Strip <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    text = re.sub(r"\n?```\s*$", "", text.strip())

    # Find the outermost JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object found in response: {raw[:300]!r}")

    try:
        obj = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}\nraw: {raw[:500]!r}") from e

    if not isinstance(obj, dict):
        raise ValueError(f"expected object, got {type(obj).__name__}")
    if "notes_markdown" not in obj:
        raise ValueError("missing 'notes_markdown' key")
    if "terms" not in obj or not isinstance(obj["terms"], list):
        obj["terms"] = []

    return obj


# ------------------------------------------------------------------------
# Storage
# ------------------------------------------------------------------------

def get_or_create_config(conn, config_name: str, model_name: str, prompt_version: str) -> int:
    row = conn.execute(
        "SELECT id FROM grammar_notes_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO grammar_notes_configs (config_name, model_name, prompt_version) "
        "VALUES (?, ?, ?)",
        (config_name, model_name, prompt_version),
    )
    conn.commit()
    return cur.lastrowid


def upsert_terms(conn, terms: list[dict]) -> list[str]:
    """Upsert each term into the glossary. Returns the list of term_english
    keys that appeared in this batch (in their original form)."""
    out = []
    for t in terms:
        key = (t.get("term_english") or "").strip()
        if not key:
            continue
        plain = (t.get("plain_explanation") or "").strip()
        if not plain:
            continue
        arabic = (t.get("term_arabic") or "").strip() or None
        example = (t.get("example_sentence") or "").strip() or None
        trans = (t.get("example_translation") or "").strip() or None
        out.append(key)

        # Is the term already stored?
        existing = conn.execute(
            "SELECT id FROM grammar_terms WHERE term_english = ?",
            (key,),
        ).fetchone()
        if existing:
            # Update fields ONLY if the incoming version has them; never clobber
            # existing data with blanks.
            conn.execute(
                "UPDATE grammar_terms SET "
                "  term_arabic = COALESCE(?, term_arabic), "
                "  plain_explanation = ?, "
                "  example_sentence = COALESCE(?, example_sentence), "
                "  example_translation = COALESCE(?, example_translation), "
                "  updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (arabic, plain, example, trans, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO grammar_terms "
                "(term_english, term_arabic, plain_explanation, example_sentence, example_translation) "
                "VALUES (?, ?, ?, ?, ?)",
                (key, arabic, plain, example, trans),
            )
    conn.commit()
    return out


def save_notes(
    conn,
    surah: int,
    ayah: int,
    config_id: int,
    notes_markdown: str,
    term_names: list[str],
    raw_response: str,
    full_prompt: str,
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO ai_grammar_notes "
        "(chapter, verse, config_id, notes_markdown, referenced_terms, raw_response, full_prompt) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (surah, ayah, config_id, notes_markdown, json.dumps(term_names), raw_response, full_prompt),
    )
    conn.commit()


def existing_record(conn, surah: int, ayah: int, config_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM ai_grammar_notes WHERE chapter = ? AND verse = ? AND config_id = ?",
        (surah, ayah, config_id),
    ).fetchone()
    return row is not None


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate grammar notes via Ollama Cloud.")
    parser.add_argument("--verses", required=True, help="e.g. '1:1-7,2:255'")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--api-key", default=os.environ.get("OLLAMA_CLOUD_KEY", ""))
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--force", action="store_true", help="Overwrite existing entries")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts, do not call model")
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        print("ERROR: Ollama Cloud key missing. Pass --api-key or set OLLAMA_CLOUD_KEY.", file=sys.stderr)
        return 2

    pairs = parse_verse_spec(args.verses)
    if not pairs:
        print(f"ERROR: no verses parsed from '{args.verses}'", file=sys.stderr)
        return 2

    conn = get_db()
    try:
        config_id = get_or_create_config(conn, args.config, args.model, args.prompt_version)

        for surah, ayah in pairs:
            print(f"\n=== {surah}:{ayah} ===")

            if not args.force and existing_record(conn, surah, ayah, config_id):
                print(f"  SKIP — already have notes for config '{args.config}'. Use --force to overwrite.")
                continue

            try:
                ev = gather_verse_evidence(conn, surah, ayah)
            except Exception as e:
                print(f"  ERROR gathering evidence: {e}", file=sys.stderr)
                continue

            user_prompt = build_user_prompt(ev)

            if args.dry_run:
                print("--- SYSTEM ---")
                print(SYSTEM_PROMPT)
                print("--- USER ---")
                print(user_prompt)
                continue

            try:
                raw, elapsed_ms = call_ollama_cloud(
                    args.model, SYSTEM_PROMPT, user_prompt,
                    api_key=args.api_key,
                    temperature=args.temperature,
                )
                print(f"  model responded in {elapsed_ms}ms")
            except Exception as e:
                print(f"  ERROR calling model: {e}", file=sys.stderr)
                continue

            try:
                obj = parse_response(raw)
            except Exception as e:
                print(f"  ERROR parsing response: {e}", file=sys.stderr)
                # Save the raw output to help with debugging
                debug_path = f"/tmp/grammar_notes_error_{surah}_{ayah}.txt"
                with open(debug_path, "w") as f:
                    f.write(raw)
                print(f"  Raw response saved to {debug_path}", file=sys.stderr)
                continue

            notes_markdown = obj.get("notes_markdown", "").strip()
            terms = obj.get("terms", []) if isinstance(obj.get("terms"), list) else []

            if not notes_markdown:
                print("  SKIP — empty notes_markdown")
                continue

            # Sanity check: every [[term]] in notes_markdown should have a
            # corresponding entry in terms
            used_markers = set(m.group(1).strip().lower() for m in re.finditer(r"\[\[([^\]]+)\]\]", notes_markdown))
            defined_terms = set(
                (t.get("term_english") or "").strip().lower()
                for t in terms if t.get("term_english")
            )
            missing = used_markers - defined_terms
            if missing:
                print(f"  WARN: {len(missing)} marker(s) lack a definition: {missing}")

            term_names = upsert_terms(conn, terms)
            save_notes(
                conn, surah, ayah, config_id, notes_markdown, term_names,
                raw_response=raw, full_prompt=user_prompt,
            )
            print(f"  SAVED — {len(term_names)} terms, {len(notes_markdown)} chars")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

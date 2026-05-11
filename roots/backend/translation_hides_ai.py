"""Offline AI judge for the 'What Translation Hides' educational video series.

For each verse with a substantive `ai_translations.departure_notes`, this
script asks an LLM to:
  1. Score the verse 0-10 on "translation-hides worthiness" — how much
     real meaning the conventional English translation actually flattens.
     Long departure notes don't automatically mean video-worthy; the
     judge filters out cases where the AI translation is just stylistic.
  2. Produce a tight operator headline (≤80 chars) in the form
     "<conventional> / <actual>" so the candidate page can show one-line
     summaries instead of 220-char prose excerpts.
  3. Identify the primary 'lens' word that carries the hidden meaning
     (word_pos + Arabic + conventional vs actual gloss) when one exists.
  4. Name the evidence kind — morphology, lexical, grammar, context, or
     cognate — so videos can pick the right slide framing.

Output is written to `translation_hides_signals`, keyed on
(chapter, verse, config_id). The candidate sampler in
`educational_pipeline._translation_hides_candidates` reads judged scores
when present and falls back to the SQL composite when not, so the judge
can run incrementally without blocking the existing pipeline.

CLI mirrors `grammar_insights_ai.py`:

    python translation_hides_ai.py --limit 10 --dry-run
    python translation_hides_ai.py --verses "2:174,3:12"
    python translation_hides_ai.py --limit 1500 --model minimax-m2.5:cloud

The pipeline is resumable: rows already judged for the same
(config_name, chapter, verse) are skipped unless --force is set.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Any

from app import get_db
from translate_ai import call_model


DEFAULT_MODEL = "minimax-m2.5:cloud"
DEFAULT_CONFIG = "translation-hides-judge-v1"
DEFAULT_PROMPT_VERSION = "v1"

# Floor on departure-note length to consider a verse at all. Mirrors
# educational_pipeline.MIN_DEPARTURE_NOTE_CHARS so we don't judge
# verses the candidate sampler would never surface anyway.
MIN_DEPARTURE_NOTE_CHARS = 80

# Cap on how much per-call data we hand the LLM. The departure note is
# the gold but can run 4000+ chars; trim so the prompt stays compact.
MAX_DEPARTURE_CHARS = 3000
MAX_WORD_DETAIL_CHARS = 240
MAX_WORDS_IN_PROMPT = 8


SYSTEM_PROMPT = """\
You are a Qur'an-translation reviewer scoring whether a verse's
conventional English translation hides meaningful nuance that the
underlying Arabic actually conveys.

You evaluate ONE verse at a time. You receive:
  - The verse's Arabic text
  - The conventional English translation
  - The AI's revised translation
  - The AI's departure notes (prose explaining what was hidden)
  - Per-word AI-preferred meanings, when the per-word judge picked the
    AI gloss over the conventional one (each is a candidate 'lens' word)
  - The V7 grammar insight, when one exists

You produce a numeric video-worthiness score (0-10), a one-line
headline, the identity of the primary 'lens' word (when one exists),
the conventional vs actual gloss for that word/phrase, and the
evidence kind.

Hard constraints:
  1) Output valid JSON only. No prose before or after.
  2) Use ONLY the evidence provided. Do not invent claims.
  3) Stay Quran-only. No tafsir, hadith, schools-of-thought references.
  4) The headline must NEVER quote the departure note verbatim — it's
     a tight reframe in YOUR words.
"""


SCORE_RUBRIC = """\
Score scale (be calibrated, not generous):
  0-2  trivial — the AI translation is barely different from conventional;
       the departure note is stylistic or a clarification, not a reveal.
  3-4  minor — a real but subtle nuance; viewer would shrug.
  5-6  substantial — a meaningful shift in interpretation that changes
       how a careful reader hears the verse.
  7-8  major — the conventional translation actively flattens or
       misleads; the AI reading materially changes the verse's force.
  9-10 foundational — the conventional reading conceals something
       central to the verse's argument; the AI reading is a reveal.

Most verses score 4-7. Reserve 8+ for cases where you'd genuinely want
to make a 60-second video on it.
"""


def _truncate(text: str, n: int) -> str:
    s = (text or "").strip()
    if len(s) <= n:
        return s
    return s[:n - 1].rstrip() + "…"


def _ensure_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translation_hides_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            config_id INTEGER NOT NULL,
            score REAL,                    -- 0-10 video-worthiness
            headline TEXT,                 -- ≤80 chars, "<conv> / <actual>"
            primary_word_pos INTEGER,      -- 1-based, null if phrase-level
            primary_arabic TEXT,           -- Arabic surface for the lens word
            conventional_gloss TEXT,       -- the conventional rendering
            hidden_gloss TEXT,             -- the AI / actual rendering
            evidence_kind TEXT,            -- morphology|lexical|grammar|context|cognate
            reasoning TEXT,                -- the LLM's reasoning (audit trail)
            raw_response TEXT,             -- raw LLM JSON for replay
            model_response_time_ms INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (config_id) REFERENCES translation_hides_configs(id),
            UNIQUE (chapter, verse, config_id)
        )
        """,
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS translation_hides_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name TEXT NOT NULL UNIQUE,
            model_name TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            methodology_notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """,
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_th_signals_verse "
        "ON translation_hides_signals (chapter, verse, score DESC)"
    )
    conn.commit()


def _get_or_create_config(conn, config_name: str, model_name: str, prompt_version: str) -> int:
    row = conn.execute(
        "SELECT id FROM translation_hides_configs WHERE config_name = ?",
        (config_name,),
    ).fetchone()
    if row:
        return row["id"]
    conn.execute(
        "INSERT INTO translation_hides_configs "
        "(config_name, model_name, prompt_version, methodology_notes) "
        "VALUES (?, ?, ?, ?)",
        (
            config_name,
            model_name,
            prompt_version,
            "AI judge for the 'What Translation Hides' candidate pool.",
        ),
    )
    conn.commit()
    return _get_or_create_config(conn, config_name, model_name, prompt_version)


def _fetch_verse_context(conn, chapter: int, verse: int) -> dict | None:
    """Pull everything the judge needs in one shot. Returns None if the
    verse has no substantive departure note (the judge has nothing to
    score)."""
    t = conn.execute(
        """
        SELECT translation_text, revised_text, departure_notes
        FROM ai_translations
        WHERE chapter = ? AND verse = ?
        ORDER BY id DESC LIMIT 1
        """,
        (chapter, verse),
    ).fetchone()
    if not t:
        return None
    departure = (t["departure_notes"] or "").strip()
    if len(departure) < MIN_DEPARTURE_NOTE_CHARS:
        return None

    v = conn.execute(
        "SELECT text_uthmani FROM verses WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()
    conv = conn.execute(
        "SELECT text_en FROM translations WHERE chapter = ? AND verse = ?",
        (chapter, verse),
    ).fetchone()

    # Per-word AI-preferred meanings.
    words: list[dict] = []
    for r in conn.execute(
        """
        SELECT word_pos, meaning_short, meaning_detailed, preferred_source
        FROM ai_word_meanings
        WHERE chapter = ? AND verse = ?
          AND preferred_source IN ('ai', 'judge')
          AND TRIM(COALESCE(meaning_short, '')) != ''
        ORDER BY word_pos
        """,
        (chapter, verse),
    ).fetchall():
        # Arabic surface from morphology
        segs = conn.execute(
            "SELECT form_arabic FROM morphology "
            "WHERE chapter = ? AND verse = ? AND word_pos = ? "
            "ORDER BY segment",
            (chapter, verse, r["word_pos"]),
        ).fetchall()
        arabic = "".join((s["form_arabic"] or "") for s in segs)
        # Conventional gloss from word_glosses
        wg = conn.execute(
            "SELECT translation_en AS gloss FROM word_glosses "
            "WHERE chapter = ? AND verse = ? AND word_pos = ?",
            (chapter, verse, r["word_pos"]),
        ).fetchone()
        words.append({
            "word_pos": int(r["word_pos"]),
            "arabic": arabic,
            "conventional_gloss": (wg["gloss"] if wg else "") or "",
            "ai_meaning_short": (r["meaning_short"] or "").strip(),
            "ai_meaning_detailed": (r["meaning_detailed"] or "").strip(),
        })

    # V7 grammar insight (best eligible one).
    grammar = None
    gi_row = conn.execute(
        """
        SELECT gi.insights_v7_json
        FROM verse_grammar_insights gi
        JOIN grammar_insight_configs c ON gi.config_id = c.id
        WHERE gi.chapter = ? AND gi.verse = ?
          AND c.config_name = 'grammar-insights-quran-only-v7-unified'
          AND gi.insights_v7_json IS NOT NULL
        ORDER BY gi.created_at DESC LIMIT 1
        """,
        (chapter, verse),
    ).fetchone()
    if gi_row:
        try:
            insights = json.loads(gi_row["insights_v7_json"]) or []
        except Exception:
            insights = []
        best, best_conf = None, -1.0
        for ins in insights:
            if not isinstance(ins, dict):
                continue
            if not (ins.get("display") or {}).get("eligible"):
                continue
            conf = float((ins.get("quality") or {}).get("overall_confidence") or 0.0)
            if conf > best_conf:
                best, best_conf = ins, conf
        if best:
            grammar = {
                "observation": (best.get("claim") or {}).get("observation") or "",
                "payoff": (best.get("meaning_payoff") or {}).get("text") or "",
                "category": best.get("category") or "",
                "confidence": best_conf,
            }

    return {
        "chapter": chapter,
        "verse": verse,
        "arabic": v["text_uthmani"] if v else "",
        "conventional_translation": conv["text_en"] if conv else "",
        "ai_translation": (t["revised_text"] or t["translation_text"] or "").strip(),
        "departure_notes": departure,
        "words": words[:MAX_WORDS_IN_PROMPT],
        "grammar_insight": grammar,
    }


def _build_user_prompt(ctx: dict) -> str:
    """Assemble the LLM payload."""
    chapter = ctx["chapter"]
    verse = ctx["verse"]
    parts = [
        f"Verse: Quran {chapter}:{verse}",
        f"Arabic: {ctx['arabic']}",
        f"Conventional translation: {ctx['conventional_translation']}",
        f"AI translation: {ctx['ai_translation']}",
        "",
        "Departure notes (the AI's explanation of what differs from conventional):",
        f'"""\n{_truncate(ctx["departure_notes"], MAX_DEPARTURE_CHARS)}\n"""',
        "",
    ]
    if ctx["words"]:
        parts.append("Per-word AI-preferred meanings (candidate 'lens' words):")
        for w in ctx["words"]:
            line = (
                f"  - word {w['word_pos']} ({w['arabic']}): "
                f"conventional='{w['conventional_gloss']}' → AI='{w['ai_meaning_short']}'"
            )
            if w["ai_meaning_detailed"]:
                line += f"\n      detail: {_truncate(w['ai_meaning_detailed'], MAX_WORD_DETAIL_CHARS)}"
            parts.append(line)
        parts.append("")
    if ctx["grammar_insight"]:
        gi = ctx["grammar_insight"]
        parts.append(
            f"Grammar move at play (V7 insight, confidence {gi['confidence']:.2f}, category {gi['category']!r}):"
        )
        parts.append(f"  observation: {_truncate(gi['observation'], 400)}")
        if gi["payoff"]:
            parts.append(f"  payoff: {_truncate(gi['payoff'], 400)}")
        parts.append("")

    parts.append(SCORE_RUBRIC)
    parts.append("")
    parts.append(
        "Output a single JSON object with EXACTLY these keys:\n"
        '  "score": integer 0-10 from the rubric above\n'
        '  "headline": string ≤80 chars in the form "<conventional> / <actual>" — '
        "a tight reframe in YOUR words, not a quote from the departure note\n"
        '  "primary_word_pos": integer 1-based position of the lens word in the '
        "Arabic (whitespace-split), or null if the nuance is phrase-level "
        "or purely grammatical\n"
        '  "primary_arabic": string Arabic surface of the lens word, or "" '
        "when no single word is the focus\n"
        '  "conventional_gloss": ≤60 chars — the conventional rendering of the '
        "lens word/phrase\n"
        '  "hidden_gloss": ≤60 chars — the actual meaning the conventional '
        "rendering flattens\n"
        '  "evidence_kind": one of "morphology", "lexical", "grammar", '
        '"context", "cognate" — names WHY the AI reading is preferred\n'
        '  "reasoning": ≤200 chars — one or two sentences explaining your '
        "score, for the operator's audit trail\n"
    )
    parts.append(
        "Examples of strong headlines (format and tone):\n"
        '  - "forbidden / declared forbidden — passive removes the agent"\n'
        '  - "disbelievers / concealers of truth — root sense across Semitic"\n'
        '  - "patience / patience that is beautiful by being"\n'
        '  - "His Lord, in mercy / His Lord, whose mercy IS Him"\n'
    )

    return "\n".join(parts)


def _extract_json(text: str) -> dict:
    """Tolerate markdown wrappers around the JSON."""
    s = (text or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if s.lower().startswith("json\n"):
        s = s.split("\n", 1)[-1]
    # Some models add reasoning before the JSON; extract the first {...} block.
    if not s.startswith("{"):
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            s = m.group(0)
    return json.loads(s)


def _validate_judgment(j: dict) -> tuple[dict, list[str]]:
    """Coerce types + clamp to schema. Returns (sanitized, errors)."""
    errors: list[str] = []
    out: dict[str, Any] = {}

    # score
    try:
        score = float(j.get("score"))
    except (TypeError, ValueError):
        score = 0.0
        errors.append(f"score not numeric: {j.get('score')!r}")
    out["score"] = max(0.0, min(10.0, score))

    # headline
    headline = (j.get("headline") or "").strip()
    if not headline:
        errors.append("headline empty")
    elif len(headline) > 80:
        headline = headline[:79].rstrip() + "…"
    out["headline"] = headline

    # primary_word_pos
    pwp = j.get("primary_word_pos")
    if pwp in (None, 0, "", "null"):
        out["primary_word_pos"] = None
    else:
        try:
            out["primary_word_pos"] = int(pwp)
        except (TypeError, ValueError):
            out["primary_word_pos"] = None
            errors.append(f"primary_word_pos not int: {pwp!r}")

    # primary_arabic
    out["primary_arabic"] = (j.get("primary_arabic") or "").strip() or None

    # gloss fields
    for fld in ("conventional_gloss", "hidden_gloss"):
        v = (j.get(fld) or "").strip()
        if len(v) > 60:
            v = v[:59].rstrip() + "…"
        out[fld] = v or None

    # evidence_kind
    allowed = {"morphology", "lexical", "grammar", "context", "cognate"}
    ek = (j.get("evidence_kind") or "").strip().lower()
    if ek not in allowed:
        # Soft fallback — pick the most common kind without errroring out.
        out["evidence_kind"] = "lexical"
        if ek:
            errors.append(f"evidence_kind {ek!r} not in {allowed}; defaulted to lexical")
        else:
            errors.append("evidence_kind missing; defaulted to lexical")
    else:
        out["evidence_kind"] = ek

    # reasoning
    reasoning = (j.get("reasoning") or "").strip()
    if len(reasoning) > 250:
        reasoning = reasoning[:249].rstrip() + "…"
    out["reasoning"] = reasoning or None

    return out, errors


def _upsert(conn, chapter: int, verse: int, cfg_id: int, j: dict, raw: str, elapsed_ms: int) -> None:
    """Insert-or-replace a judgment row. UNIQUE on (chapter, verse, config_id)."""
    conn.execute(
        """
        INSERT INTO translation_hides_signals
            (chapter, verse, config_id, score, headline,
             primary_word_pos, primary_arabic,
             conventional_gloss, hidden_gloss,
             evidence_kind, reasoning, raw_response,
             model_response_time_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (chapter, verse, config_id)
        DO UPDATE SET
            score = excluded.score,
            headline = excluded.headline,
            primary_word_pos = excluded.primary_word_pos,
            primary_arabic = excluded.primary_arabic,
            conventional_gloss = excluded.conventional_gloss,
            hidden_gloss = excluded.hidden_gloss,
            evidence_kind = excluded.evidence_kind,
            reasoning = excluded.reasoning,
            raw_response = excluded.raw_response,
            model_response_time_ms = excluded.model_response_time_ms,
            created_at = datetime('now')
        """,
        (
            chapter, verse, cfg_id,
            j["score"], j["headline"],
            j["primary_word_pos"], j["primary_arabic"],
            j["conventional_gloss"], j["hidden_gloss"],
            j["evidence_kind"], j["reasoning"], raw,
            elapsed_ms,
        ),
    )
    conn.commit()


def _parse_verse_spec(spec: str) -> list[tuple[int, int]]:
    """Same shape as grammar_insights_ai.parse_verse_spec —
    accepts comma-separated 'c:v' or 'c:v1-v2' tokens."""
    out: list[tuple[int, int]] = []
    for token in (spec or "").split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise ValueError(f"bad verse spec: {token!r}")
        c, vs = token.split(":", 1)
        c = int(c)
        if "-" in vs:
            a, b = vs.split("-", 1)
            for v in range(int(a), int(b) + 1):
                out.append((c, v))
        else:
            out.append((c, int(vs)))
    return out


def _pool_for_judging(conn, limit: int | None) -> list[tuple[int, int]]:
    """Default pool: all verses with a substantive departure note,
    ordered by the same composite score the educational pipeline uses
    so the highest-signal candidates get judged first. Useful when
    --limit caps the run — the top-N gets the judgment, the rest can
    fall back to the SQL composite indefinitely."""
    rows = conn.execute(
        """
        SELECT t.chapter, t.verse,
               MIN(LENGTH(t.departure_notes), 1000) * 0.4
                 + COALESCE(awm_counts.ai_word_count, 0) * 1.5
                 + CASE WHEN gi_eligible.has_eligible IS NOT NULL THEN 8.0 ELSE 0.0 END
                 AS score
        FROM ai_translations t
        LEFT JOIN (
            SELECT chapter, verse, COUNT(*) AS ai_word_count
            FROM ai_word_meanings
            WHERE preferred_source IN ('ai', 'judge')
              AND TRIM(COALESCE(meaning_short, '')) != ''
            GROUP BY chapter, verse
        ) awm_counts ON awm_counts.chapter = t.chapter AND awm_counts.verse = t.verse
        LEFT JOIN (
            SELECT DISTINCT gi.chapter, gi.verse, 1 AS has_eligible
            FROM verse_grammar_insights gi
            JOIN grammar_insight_configs c ON gi.config_id = c.id
            WHERE c.config_name = 'grammar-insights-quran-only-v7-unified'
              AND gi.insights_v7_json IS NOT NULL
              AND gi.insights_v7_json != ''
              AND gi.signal_score >= 0.5
        ) gi_eligible ON gi_eligible.chapter = t.chapter AND gi_eligible.verse = t.verse
        WHERE t.departure_notes IS NOT NULL
          AND LENGTH(TRIM(t.departure_notes)) >= ?
        ORDER BY score DESC
        """,
        (MIN_DEPARTURE_NOTE_CHARS,),
    ).fetchall()
    pairs = [(r["chapter"], r["verse"]) for r in rows]
    return pairs[: limit] if limit else pairs


def run(args: argparse.Namespace) -> int:
    conn = get_db()
    try:
        _ensure_table(conn)
        cfg_id = _get_or_create_config(
            conn, args.config, args.model, args.prompt_version,
        )

        if args.verses:
            pool = _parse_verse_spec(args.verses)
        else:
            pool = _pool_for_judging(conn, args.limit)

        print(
            f"Translation-hides judge: {len(pool)} verse(s) to evaluate "
            f"with model '{args.model}' (config '{args.config}')",
            flush=True,
        )
        if args.dry_run:
            print("(--dry-run: no DB writes, no LLM calls)", flush=True)

        n_done = 0
        n_skip = 0
        n_err = 0
        # Track CONSECUTIVE errors (reset on each success). When the cloud
        # session expires / quota is hit, every call starts failing — we
        # don't want to burn through the whole remaining pool spamming
        # failed requests. Instead, back off exponentially and eventually
        # bail with a non-zero exit code so the outer resume wrapper can
        # wait longer (minutes-to-hours) before retrying.
        consecutive_err = 0
        max_consecutive = int(getattr(args, "max_consecutive_errors", 20))
        backoff_cap_s = 300  # never sleep more than 5 min inside the script

        for i, (s, a) in enumerate(pool, start=1):
            if not args.force:
                existing = conn.execute(
                    "SELECT 1 FROM translation_hides_signals "
                    "WHERE chapter = ? AND verse = ? AND config_id = ?",
                    (s, a, cfg_id),
                ).fetchone()
                if existing:
                    print(f"[{i}/{len(pool)}] {s}:{a} SKIP (already judged)", flush=True)
                    n_skip += 1
                    continue

            ctx = _fetch_verse_context(conn, s, a)
            if not ctx:
                print(f"[{i}/{len(pool)}] {s}:{a} SKIP (no usable context)", flush=True)
                n_skip += 1
                continue

            prompt = _build_user_prompt(ctx)
            if args.dry_run:
                print(f"[{i}/{len(pool)}] {s}:{a} DRY (prompt {len(prompt)} chars)", flush=True)
                n_done += 1
                continue

            try:
                t0 = time.time()
                raw, elapsed = call_model(
                    args.model, SYSTEM_PROMPT, prompt, temperature=args.temperature,
                )
                try:
                    j_raw = _extract_json(raw)
                except Exception:
                    # One strict retry for malformed JSON.
                    repair = prompt + (
                        "\n\nIMPORTANT: Return valid JSON only. No prose before or after."
                    )
                    raw2, elapsed2 = call_model(
                        args.model, SYSTEM_PROMPT, repair, temperature=0.0,
                    )
                    j_raw = _extract_json(raw2)
                    raw = raw2
                    elapsed += elapsed2

                j, errs = _validate_judgment(j_raw)
                if errs:
                    print(f"  validation: {'; '.join(errs)}", flush=True)

                _upsert(conn, s, a, cfg_id, j, raw, elapsed)
                n_done += 1
                consecutive_err = 0  # reset on each successful save

                # Operator-visible save line — single line, structured so a
                # tail -f | grep can extract score + headline.
                headline = (j["headline"] or "").replace("|", "/")
                ev = j["evidence_kind"] or "?"
                pw = j["primary_word_pos"] or 0
                par = (j["primary_arabic"] or "").strip()
                wall = int((time.time() - t0) * 1000)
                conv = (j["conventional_gloss"] or "").replace("|", "/")
                hid = (j["hidden_gloss"] or "").replace("|", "/")
                print(
                    f"[{i}/{len(pool)}] {s}:{a} SAVED "
                    f"| score={j['score']:.1f} | kind={ev} "
                    f"| word={pw}{(' ' + par) if par else ''} "
                    f"| conv={conv!r} → hidden={hid!r} "
                    f"| headline={headline!r} "
                    f"| {wall}ms",
                    flush=True,
                )
            except KeyboardInterrupt:
                print("\nInterrupted by user.", flush=True)
                break
            except Exception as e:
                n_err += 1
                consecutive_err += 1
                msg = str(e)[:200]
                # Exponential backoff inside the script: 2s, 4s, 8s, ...
                # capped at backoff_cap_s. Cheap calls (under a minute)
                # don't accumulate much; sustained outages reach the cap
                # within ~10 consecutive errors. This gives quick errors
                # a quick retry while not hammering on a dead endpoint.
                sleep_s = min(backoff_cap_s, 2 ** min(consecutive_err, 8))
                print(
                    f"[{i}/{len(pool)}] {s}:{a} ERROR: {msg} "
                    f"(consecutive={consecutive_err}/{max_consecutive}, "
                    f"sleeping {sleep_s}s)",
                    flush=True,
                )
                # Hard bail when consecutive errors hit the cap. The
                # outer resume wrapper sees the non-zero exit and can
                # wait minutes-to-hours before relaunching — at which
                # point the cloud session may be restored. The script
                # is fully idempotent (already-judged verses skip), so
                # the relaunch picks up exactly where we left off.
                if consecutive_err >= max_consecutive:
                    print(
                        f"\nBAILING: {consecutive_err} consecutive errors. "
                        f"The cloud endpoint appears to be persistently failing. "
                        f"Run state: judged={n_done}, skipped={n_skip}, errors={n_err}. "
                        f"Restart this script to resume — it skips already-judged verses.",
                        flush=True,
                    )
                    return 2  # distinct exit code for the wrapper
                time.sleep(sleep_s)

        print(f"\nDone. judged={n_done}, skipped={n_skip}, errors={n_err}", flush=True)
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AI judge for the 'What Translation Hides' series")
    p.add_argument("--verses", default=None,
                   help='Explicit verse spec like "21:1-28,1:1". Default: all eligible verses ranked by composite score.')
    p.add_argument("--limit", type=int, default=None,
                   help="Cap on number of verses to judge (top-N by composite SQL score).")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--prompt-version", default=DEFAULT_PROMPT_VERSION)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--force", action="store_true",
                   help="Re-judge verses that already have a row for this config.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-consecutive-errors", type=int, default=20,
                   help="Bail with exit code 2 after this many consecutive errors. "
                        "The outer wrapper (scripts/resume-judge.sh) catches the "
                        "non-zero exit and retries after a longer wait. Default 20.")
    return p


if __name__ == "__main__":
    sys.exit(run(build_parser().parse_args()))

#!/usr/bin/env bash
# Generate AI word meanings for every word in the Quran.
#
# Features:
#   - Auto-resumes from where it left off (queries DB for progress)
#   - Ctrl+C pauses gracefully; just re-run to continue
#   - Shows live progress stats (done/total words, ETA)
#   - Zipf hybrid: high-frequency lemmas translated once and reused
#
# Usage:
#   ./run_all_words.sh                                  # run/resume entire Quran
#   ./run_all_words.sh --status                         # show progress without running
#   MODEL=gpt-5.1 CONFIG=word-v2-gpt5.1 ./run_all_words.sh   # use GPT-5.1

set -e
cd "$(dirname "$0")"

MODEL="${MODEL:-gpt-5.1}"
CONFIG="${CONFIG:-word-v2-gpt5.1}"
FREQ_THRESHOLD="${FREQ_THRESHOLD:-5}"
INTERRUPTED=0

# Graceful Ctrl+C: let current word finish, then exit
trap 'INTERRUPTED=1; echo ""; echo "Pausing after current word finishes... (re-run to resume)"; ' INT

# ── Helper: query progress from DB ──
get_progress() {
  python3 << 'PYEOF'
import os
config_name = os.environ.get("CONFIG", "word-v2-gpt5.1")

from app import get_db
conn = get_db()

total = conn.execute("""
    SELECT COUNT(*) FROM (
        SELECT DISTINCT chapter, verse, word_pos
        FROM morphology
        WHERE (root_buckwalter IS NOT NULL AND root_buckwalter != '')
           OR (lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '')
    )
""").fetchone()[0]

# Count done for this config
config_row = conn.execute(
    "SELECT id FROM ai_translation_configs WHERE config_name = ?",
    (config_name,)
).fetchone()

done = 0
if config_row:
    done = conn.execute(
        "SELECT COUNT(*) FROM ai_word_meanings WHERE config_id = ?",
        (config_row["id"],)
    ).fetchone()[0]

# Find resume point: first verse with content words not yet processed
all_verses = conn.execute("""
    SELECT DISTINCT chapter, verse FROM morphology
    WHERE (root_buckwalter IS NOT NULL AND root_buckwalter != '')
       OR (lemma_buckwalter IS NOT NULL AND lemma_buckwalter != '')
    ORDER BY chapter, verse
""").fetchall()

done_verses = set()
if config_row:
    for row in conn.execute(
        "SELECT DISTINCT chapter, verse FROM ai_word_meanings WHERE config_id = ?",
        (config_row["id"],)
    ):
        done_verses.add((row[0], row[1]))

resume_surah = 0
resume_ayah = 0
for row in all_verses:
    if (row[0], row[1]) not in done_verses:
        resume_surah = row[0]
        resume_ayah = row[1]
        break

# Verse counts per surah
for r in conn.execute("SELECT chapter, MAX(verse) FROM verses GROUP BY chapter ORDER BY chapter"):
    print(f"VC {r[0]} {r[1]}")

conn.close()
print(f"TOTAL {total}")
print(f"DONE {done}")
print(f"RESUME {resume_surah} {resume_ayah}")
PYEOF
}

# ── Load progress into simple variables ──
TOTAL=0
DONE=0
RESUME_SURAH=0
RESUME_AYAH=0

# Store verse counts in a temp file (avoids associative arrays — macOS bash 3.2)
TMPVC=$(mktemp)
trap 'rm -f "$TMPVC"' EXIT

while read -r tag a b; do
  case "$tag" in
    TOTAL)  TOTAL=$a ;;
    DONE)   DONE=$a ;;
    RESUME) RESUME_SURAH=$a; RESUME_AYAH=$b ;;
    VC)     echo "$a $b" >> "$TMPVC" ;;
  esac
done < <(get_progress)

get_vc() {
  awk -v s="$1" '$1==s {print $2}' "$TMPVC"
}

REMAINING=$((TOTAL - DONE))
PCT=0
if [ "$TOTAL" -gt 0 ]; then
  PCT=$((DONE * 100 / TOTAL))
fi

# ── Status mode ──
if [ "${1:-}" = "--status" ]; then
  echo "=== AI Word Meanings Progress ==="
  echo "Total content words:  $TOTAL"
  echo "Processed:            $DONE ($PCT%)"
  echo "Remaining:            $REMAINING"
  if [ "$RESUME_SURAH" -gt 0 ]; then
    echo "Resume point:         Surah $RESUME_SURAH, Ayah $RESUME_AYAH"
  else
    echo "Status:               COMPLETE"
  fi
  echo "Model:                $MODEL"
  echo "Config:               $CONFIG"
  echo "Freq threshold:       $FREQ_THRESHOLD"
  exit 0
fi

# ── Main run ──
if [ "$RESUME_SURAH" -eq 0 ]; then
  echo "All words already processed! ($DONE/$TOTAL)"
  exit 0
fi

echo "========================================================"
echo "  AI Word Meanings Pipeline"
echo "========================================================"
echo "  Model:          $MODEL"
echo "  Config:         $CONFIG"
echo "  Freq threshold: $FREQ_THRESHOLD (lemmas >= this reused)"
echo "  Progress:       $DONE / $TOTAL ($PCT%)"
echo "  Remaining:      ~$REMAINING words"
echo "  Resuming:       Surah $RESUME_SURAH, Ayah $RESUME_AYAH"
echo "  Ctrl+C:         Pause (re-run to resume)"
echo "========================================================"
echo ""

STARTED_AT=$(date +%s)

for surah in $(seq "$RESUME_SURAH" 114); do
  if [ "$INTERRUPTED" -eq 1 ]; then break; fi

  vc=$(get_vc "$surah")
  if [ -z "$vc" ] || [ "$vc" -eq 0 ]; then continue; fi

  # For the resume surah, start from the resume ayah; otherwise from 1
  start_ayah=1
  if [ "$surah" -eq "$RESUME_SURAH" ]; then
    start_ayah=$RESUME_AYAH
  fi

  echo "--- Surah $surah (ayah $start_ayah-$vc) ---"
  python3 word_meanings_ai.py \
    --verses "$surah:$start_ayah-$vc" \
    --config "$CONFIG" \
    --model "$MODEL" \
    --freq-threshold "$FREQ_THRESHOLD"

  # Show progress
  NEW_DONE=$(python3 -c "
import os
config_name = os.environ.get('CONFIG', 'word-v2-gpt5.1')
from app import get_db
conn = get_db()
config_row = conn.execute('SELECT id FROM ai_translation_configs WHERE config_name = ?', (config_name,)).fetchone()
if config_row:
    print(conn.execute('SELECT COUNT(*) FROM ai_word_meanings WHERE config_id = ?', (config_row['id'],)).fetchone()[0])
else:
    print(0)
conn.close()
" 2>/dev/null)
  WORDS_THIS_SESSION=$((NEW_DONE - DONE))

  NOW=$(date +%s)
  ELAPSED=$((NOW - STARTED_AT))
  if [ "$WORDS_THIS_SESSION" -gt 0 ] && [ "$ELAPSED" -gt 5 ]; then
    RATE=$(python3 -c "print(f'{$WORDS_THIS_SESSION / ($ELAPSED / 3600.0):.0f}')" 2>/dev/null || echo "?")
    NEW_REMAINING=$((TOTAL - NEW_DONE))
    NEW_PCT=$((NEW_DONE * 100 / TOTAL))
    if [ "$RATE" != "?" ] && [ "$RATE" != "0" ]; then
      ETA_HRS=$(python3 -c "print(f'{$NEW_REMAINING / float($RATE):.1f}')" 2>/dev/null || echo "?")
    else
      ETA_HRS="?"
    fi
    echo ""
    echo "  >> $NEW_DONE/$TOTAL ($NEW_PCT%) | Session: +$WORDS_THIS_SESSION | ${RATE}/hr | ETA: ${ETA_HRS}h"
  fi

  echo ""
done

if [ "$INTERRUPTED" -eq 1 ]; then
  echo ""
  echo "Paused. Run ./run_all_words.sh to resume."
else
  echo "=== Complete! All $TOTAL words processed. ==="
fi

#!/usr/bin/env bash
# Generate AI translations for every verse in the Quran.
#
# Features:
#   - Auto-resumes from where it left off (queries DB for progress)
#   - Ctrl+C pauses gracefully; just re-run to continue
#   - Shows live progress stats (done/total, ETA)
#
# Usage:
#   ./run_all_verses.sh                    # run/resume entire Quran
#   ./run_all_verses.sh --status           # show progress without running
#   MODEL=qwen3:14b ./run_all_verses.sh    # use a specific model

set -e
cd "$(dirname "$0")"

MODEL="${MODEL:-qwen3.5:35b}"
CONFIG="${CONFIG:-quran-only-v2}"
INTERRUPTED=0

trap 'INTERRUPTED=1; echo ""; echo "Pausing after current verse finishes... (re-run to resume)"; ' INT

# ── Query progress from DB ──
get_progress() {
  python3 << 'PYEOF'
from app import get_db
conn = get_db()

total = conn.execute("SELECT COUNT(*) FROM verses").fetchone()[0]

# Count done for this config
config_row = conn.execute(
    "SELECT id FROM ai_translation_configs WHERE config_name = ?",
    ("quran-only-v2",)
).fetchone()

done = 0
if config_row:
    done = conn.execute(
        "SELECT COUNT(*) FROM ai_translations WHERE config_id = ?",
        (config_row["id"],)
    ).fetchone()[0]

# Find resume point
all_verses = conn.execute(
    "SELECT chapter, verse FROM verses ORDER BY chapter, verse"
).fetchall()

done_verses = set()
if config_row:
    for row in conn.execute(
        "SELECT chapter, verse FROM ai_translations WHERE config_id = ?",
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

# ── Load progress ──
TOTAL=0
DONE=0
RESUME_SURAH=0
RESUME_AYAH=0

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
  echo "=== AI Verse Translation Progress ==="
  echo "Total verses:   $TOTAL"
  echo "Translated:     $DONE ($PCT%)"
  echo "Remaining:      $REMAINING"
  if [ "$RESUME_SURAH" -gt 0 ]; then
    echo "Resume point:   Surah $RESUME_SURAH, Ayah $RESUME_AYAH"
  else
    echo "Status:         COMPLETE"
  fi
  echo "Model:          $MODEL"
  echo "Config:         $CONFIG"
  exit 0
fi

# ── Main run ──
if [ "$RESUME_SURAH" -eq 0 ]; then
  echo "All verses already translated! ($DONE/$TOTAL)"
  exit 0
fi

echo "========================================================"
echo "  AI Verse Translation Pipeline"
echo "========================================================"
echo "  Model:     $MODEL"
echo "  Config:    $CONFIG"
echo "  Progress:  $DONE / $TOTAL ($PCT%)"
echo "  Remaining: $REMAINING verses"
echo "  Resuming:  Surah $RESUME_SURAH, Ayah $RESUME_AYAH"
echo "  Ctrl+C:    Pause (re-run to resume)"
echo "========================================================"
echo ""

STARTED_AT=$(date +%s)

for surah in $(seq "$RESUME_SURAH" 114); do
  if [ "$INTERRUPTED" -eq 1 ]; then break; fi

  vc=$(get_vc "$surah")
  if [ -z "$vc" ] || [ "$vc" -eq 0 ]; then continue; fi

  start_ayah=1
  if [ "$surah" -eq "$RESUME_SURAH" ]; then
    start_ayah=$RESUME_AYAH
  fi

  echo "--- Surah $surah (ayah $start_ayah-$vc) ---"
  python3 translate_ai.py \
    --verses "$surah:$start_ayah-$vc" \
    --config "$CONFIG" \
    --model "$MODEL"

  # Show progress
  NEW_DONE=$(python3 -c "
from app import get_db
conn = get_db()
config_row = conn.execute(\"SELECT id FROM ai_translation_configs WHERE config_name = 'quran-only-v2'\").fetchone()
if config_row:
    print(conn.execute('SELECT COUNT(*) FROM ai_translations WHERE config_id = ?', (config_row[\"id\"],)).fetchone()[0])
else:
    print(0)
conn.close()
" 2>/dev/null)
  VERSES_THIS_SESSION=$((NEW_DONE - DONE))

  NOW=$(date +%s)
  ELAPSED=$((NOW - STARTED_AT))
  if [ "$VERSES_THIS_SESSION" -gt 0 ] && [ "$ELAPSED" -gt 5 ]; then
    RATE=$(python3 -c "print(f'{$VERSES_THIS_SESSION / ($ELAPSED / 3600.0):.0f}')" 2>/dev/null || echo "?")
    NEW_REMAINING=$((TOTAL - NEW_DONE))
    NEW_PCT=$((NEW_DONE * 100 / TOTAL))
    if [ "$RATE" != "?" ] && [ "$RATE" != "0" ]; then
      ETA_HRS=$(python3 -c "print(f'{$NEW_REMAINING / float($RATE):.1f}')" 2>/dev/null || echo "?")
    else
      ETA_HRS="?"
    fi
    echo ""
    echo "  >> $NEW_DONE/$TOTAL ($NEW_PCT%) | Session: +$VERSES_THIS_SESSION | ${RATE}/hr | ETA: ${ETA_HRS}h"
  fi

  echo ""
done

if [ "$INTERRUPTED" -eq 1 ]; then
  echo ""
  echo "Paused. Run ./run_all_verses.sh to resume."
else
  echo "=== Complete! All $TOTAL verses translated. ==="
fi

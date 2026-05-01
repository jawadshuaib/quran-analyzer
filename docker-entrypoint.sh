#!/bin/sh
set -e

# ============================================================================
# Pre-deploy snapshot — defense in depth
# ----------------------------------------------------------------------------
# Take a point-in-time copy of the live DB BEFORE any destructive step.
# Keeps the 3 most recent snapshots in /app/data/snapshots/ so the volume
# never balloons. Uses sqlite3.Connection.backup() (online-safe; doesn't
# require the app to be stopped). If the per-table restore logic below
# ever has a bug or misses a new column, this snapshot is the recovery
# path: stop the container, `cp` the snapshot back over quran.db, restart.
# ============================================================================
if [ -f /app/data/quran.db ]; then
  echo "Snapshotting live DB before deploy..."
  python3 -c "
import sqlite3, os, datetime, glob
snap_dir = '/app/data/snapshots'
os.makedirs(snap_dir, exist_ok=True)
ts = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
dst_path = os.path.join(snap_dir, f'quran-{ts}.db')
try:
    src = sqlite3.connect('/app/data/quran.db')
    bak = sqlite3.connect(dst_path)
    src.backup(bak)
    bak.close()
    src.close()
    # Compress the snapshot in place — SQLite DBs gzip ~5-10x and the
    # uncompressed snapshot is ~600MB. Recovery is one gunzip away.
    import gzip, shutil
    gz_path = dst_path + '.gz'
    with open(dst_path, 'rb') as f_in, gzip.open(gz_path, 'wb', compresslevel=6) as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(dst_path)
    size_mb = os.path.getsize(gz_path) / 1024 / 1024
    print(f'  Snapshot: {gz_path} ({size_mb:.1f} MB)')
    # Rotate: keep only the 2 most recent snapshots. Was 3 — the
    # per-table backup logic below is the primary recovery path; 2
    # snapshots is enough redundancy and saves ~600MB on the volume.
    # Match both legacy uncompressed (.db) and new compressed (.db.gz)
    # so the rotation cleans up both during the transition.
    snaps = sorted(
        glob.glob(os.path.join(snap_dir, 'quran-*.db')) +
        glob.glob(os.path.join(snap_dir, 'quran-*.db.gz'))
    )
    KEEP = 2
    for old in snaps[:-KEEP]:
        try:
            os.remove(old)
            print(f'  Pruned old snapshot: {os.path.basename(old)}')
        except Exception as e:
            print(f'  Prune warning: {e}')
except Exception as e:
    # Don't block deploy if snapshot fails — the per-table backups are
    # still in place. But shout loudly so the operator notices.
    print(f'  ERROR: snapshot failed: {e}')
" 2>&1
fi

# Preserve user-generated data (assistant Q&A) across deploys
if [ -f /app/data/quran.db ]; then
  echo "Backing up assistant conversations..."
  python3 -c "
import sqlite3, os
src = '/app/data/quran.db'
bak = '/tmp/assistant_backup.db'
try:
    conn = sqlite3.connect(src)
    rows = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='assistant_conversations'\").fetchall()
    if rows:
        count = conn.execute('SELECT COUNT(*) FROM assistant_conversations').fetchone()[0]
        if count > 0:
            bak_conn = sqlite3.connect(bak)
            bak_conn.execute('''CREATE TABLE IF NOT EXISTS assistant_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                page_type TEXT NOT NULL,
                page_key TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                context_summary TEXT,
                model_used TEXT,
                response_time_ms INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            )''')
            all_rows = conn.execute('SELECT session_id, page_type, page_key, question, answer, context_summary, model_used, response_time_ms, created_at FROM assistant_conversations').fetchall()
            bak_conn.executemany('INSERT INTO assistant_conversations (session_id, page_type, page_key, question, answer, context_summary, model_used, response_time_ms, created_at) VALUES (?,?,?,?,?,?,?,?,?)', all_rows)
            bak_conn.commit()
            bak_conn.close()
            print(f'  Backed up {count} conversations')
        else:
            print('  No conversations to back up')
    else:
        print('  No assistant_conversations table found')
    conn.close()
except Exception as e:
    print(f'  Backup warning: {e}')
" 2>&1
fi

# Back up insight evolution log
if [ -f /app/data/quran.db ]; then
  echo "Backing up insight evolution log..."
  python3 -c "
import sqlite3
src = '/app/data/quran.db'
bak = '/tmp/insight_evo_backup.db'
try:
    conn = sqlite3.connect(src)
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='insight_evolution_log'\").fetchall()
    if tables:
        count = conn.execute('SELECT COUNT(*) FROM insight_evolution_log').fetchone()[0]
        if count > 0:
            cols = 'conversation_id, chapter, verse, word_pos, status, target_table, target_column, target_row_id, old_value, new_value, evaluation_model, evaluation_reasoning, confidence_score, qa_question, qa_answer, reverted_at, reverted_by, created_at'
            bak_conn = sqlite3.connect(bak)
            bak_conn.execute('''CREATE TABLE IF NOT EXISTS insight_evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL, chapter INTEGER NOT NULL,
                verse INTEGER NOT NULL, word_pos INTEGER, status TEXT NOT NULL,
                target_table TEXT, target_column TEXT, target_row_id INTEGER,
                old_value TEXT, new_value TEXT, evaluation_model TEXT NOT NULL,
                evaluation_reasoning TEXT NOT NULL, confidence_score REAL,
                qa_question TEXT NOT NULL, qa_answer TEXT NOT NULL,
                reverted_at TEXT, reverted_by TEXT,
                created_at TEXT DEFAULT (datetime(\"now\")))''')
            all_rows = conn.execute(f'SELECT {cols} FROM insight_evolution_log').fetchall()
            bak_conn.executemany(f'INSERT INTO insight_evolution_log ({cols}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', all_rows)
            bak_conn.commit()
            bak_conn.close()
            print(f'  Backed up {count} insight evolution entries')
        else:
            print('  No insight evolution entries to back up')
    else:
        print('  No insight_evolution_log table found')
    conn.close()
except Exception as e:
    print(f'  Insight backup warning: {e}')
" 2>&1
fi

# Back up verse themes
if [ -f /app/data/quran.db ]; then
  echo "Backing up verse themes..."
  python3 -c "
import sqlite3
src = '/app/data/quran.db'
bak = '/tmp/verse_themes_backup.db'
try:
    conn = sqlite3.connect(src)
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='verse_themes'\").fetchall()
    if tables:
        count = conn.execute('SELECT COUNT(*) FROM verse_themes').fetchone()[0]
        if count > 0:
            cols = 'chapter, verse, theme, confidence, config_id, model_used, created_at'
            bak_conn = sqlite3.connect(bak)
            bak_conn.execute('''CREATE TABLE IF NOT EXISTS verse_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter INTEGER NOT NULL, verse INTEGER NOT NULL,
                theme TEXT NOT NULL, confidence REAL, config_id INTEGER,
                model_used TEXT, created_at TEXT DEFAULT (datetime(\"now\")),
                UNIQUE(chapter, verse, theme))''')
            all_rows = conn.execute(f'SELECT {cols} FROM verse_themes').fetchall()
            bak_conn.executemany(f'INSERT OR IGNORE INTO verse_themes ({cols}) VALUES (?,?,?,?,?,?,?)', all_rows)
            bak_conn.commit()
            bak_conn.close()
            print(f'  Backed up {count} verse theme entries')
        else:
            print('  No verse themes to back up')
    else:
        print('  No verse_themes table found')
    conn.close()
except Exception as e:
    print(f'  Verse themes backup warning: {e}')
" 2>&1
fi

# Back up all runtime-state tables. These are tables populated by the
# running app (preferences, schedules, upload runs, pipeline video rows,
# etc.) as opposed to the seed corpus (verses, roots, ai_* generated
# content). Matching prefixes:
#   admin_%    — admin_preferences, admin_pipeline_videos, admin_voices, ...
#   pipeline_% — pipeline_schedules, pipeline_schedule_runs
#   youtube_%  — youtube_upload_schedule, youtube_upload_runs
#   tiktok_%   — reserved for upcoming TikTok integration tables
#
# IMPORTANT: when you add a new user-facing table, either (a) give it
# one of these prefixes, or (b) add its prefix here. Otherwise it will
# silently get wiped on every deploy.
if [ -f /app/data/quran.db ]; then
  echo "Backing up runtime-state tables..."
  python3 -c "
import sqlite3, os
src = '/app/data/quran.db'
bak = '/tmp/admin_backup.db'
try:
    conn = sqlite3.connect(src)
    tables = [r[0] for r in conn.execute(
        \"SELECT name FROM sqlite_master WHERE type='table' AND (\"
        \"name LIKE 'admin_%' OR name LIKE 'pipeline_%' OR \"
        \"name LIKE 'youtube_%' OR name LIKE 'tiktok_%')\"
    ).fetchall()]
    if tables:
        bak_conn = sqlite3.connect(bak)
        for tbl in tables:
            schema = conn.execute(f\"SELECT sql FROM sqlite_master WHERE type='table' AND name='{tbl}'\").fetchone()
            if schema and schema[0]:
                bak_conn.execute(schema[0])
                rows = conn.execute(f'SELECT * FROM {tbl}').fetchall()
                if rows:
                    placeholders = ','.join(['?'] * len(rows[0]))
                    bak_conn.executemany(f'INSERT INTO {tbl} VALUES ({placeholders})', rows)
                    print(f'  Backed up {len(rows)} rows from {tbl}')
        # Also grab indexes (e.g. the UNIQUE idx on youtube_upload_runs.scheduled_time)
        # so that the restored table keeps its uniqueness guarantees.
        for tbl in tables:
            idx_rows = conn.execute(
                \"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL\",
                (tbl,),
            ).fetchall()
            for (idx_sql,) in idx_rows:
                try:
                    bak_conn.execute(idx_sql)
                except Exception:
                    pass  # skip if already created
        bak_conn.commit()
        bak_conn.close()
    else:
        print('  No runtime-state tables found')
    conn.close()
except Exception as e:
    print(f'  Runtime-state backup warning: {e}')
" 2>&1
fi

# ============================================================================
# Vocabulary Studio backup — preserve admin-curated semantic data
# ----------------------------------------------------------------------------
# These tables don't match the admin_/pipeline_/youtube_/tiktok_ prefixes
# but are mutated by /admin/vocabulary/* (term surveys, hard-case
# transliterations, word-meaning revisions, grammar-note revisions).
# Pattern differs by table:
#   term_surveys      — full table backup; restore via INSERT OR REPLACE
#                       so the user's surveyed roots win over the seed.
#   ai_word_meanings  — sparse: only rows where meaning_short_original IS
#                       NOT NULL (the user-revised ones). Restore = UPDATE
#                       matched-by-(chapter,verse,word_pos), so the seed's
#                       ~6000 baseline rows stay intact.
#   ai_grammar_notes  — sparse: rows where notes_markdown_original IS NOT
#                       NULL. Restore = UPDATE matched-by-(chapter,verse).
#   ai_translations   — sparse: rows where revised_text IS NOT NULL.
#                       Restore = UPDATE matched-by-(chapter,verse).
# ============================================================================
if [ -f /app/data/quran.db ]; then
  echo "Backing up vocabulary studio tables..."
  python3 -c "
import sqlite3
src = '/app/data/quran.db'
bak = '/tmp/vocab_backup.db'
try:
    conn = sqlite3.connect(src)
    bak_conn = sqlite3.connect(bak)

    def has_table(c, name):
        return bool(c.execute(
            \"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?\",
            (name,),
        ).fetchone())

    def has_column(c, table, col):
        return any(
            r[1] == col for r in c.execute(f'PRAGMA table_info(\"{table}\")')
        )

    # 1. term_surveys (full table) -----------------------------------------
    if has_table(conn, 'term_surveys'):
        cols = [r[1] for r in conn.execute('PRAGMA table_info(term_surveys)')]
        col_list = ','.join(f'\"{c}\"' for c in cols)
        # Recreate same schema in backup
        schema = conn.execute(
            \"SELECT sql FROM sqlite_master WHERE type='table' AND name='term_surveys'\"
        ).fetchone()[0]
        bak_conn.execute(schema)
        rows = conn.execute(f'SELECT {col_list} FROM term_surveys').fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(cols))
            bak_conn.executemany(
                f'INSERT INTO term_surveys ({col_list}) VALUES ({placeholders})',
                rows,
            )
            print(f'  Backed up {len(rows)} term_surveys rows')

    # 1b. proper_noun_candidates (full table — admin-curated review queue) -
    if has_table(conn, 'proper_noun_candidates'):
        cols = [r[1] for r in conn.execute('PRAGMA table_info(proper_noun_candidates)')]
        col_list = ','.join(f'\"{c}\"' for c in cols)
        schema = conn.execute(
            \"SELECT sql FROM sqlite_master WHERE type='table' AND name='proper_noun_candidates'\"
        ).fetchone()[0]
        bak_conn.execute(schema)
        rows = conn.execute(f'SELECT {col_list} FROM proper_noun_candidates').fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(cols))
            bak_conn.executemany(
                f'INSERT INTO proper_noun_candidates ({col_list}) VALUES ({placeholders})',
                rows,
            )
            print(f'  Backed up {len(rows)} proper_noun_candidates rows')

    # 2. ai_word_meanings (sparse — only revised) --------------------------
    if has_table(conn, 'ai_word_meanings') and has_column(conn, 'ai_word_meanings', 'meaning_short_original'):
        # We need the columns we'll restore + the natural key
        keep_cols = [
            'chapter', 'verse', 'word_pos',
            'meaning_short', 'meaning_detailed', 'preferred_translation',
            'meaning_short_original', 'meaning_detailed_original',
            'preferred_translation_original',
        ]
        keep_cols = [c for c in keep_cols if has_column(conn, 'ai_word_meanings', c)]
        col_list = ','.join(f'\"{c}\"' for c in keep_cols)
        bak_conn.execute(f'CREATE TABLE _wm_modified ({col_list})')
        rows = conn.execute(
            f'SELECT {col_list} FROM ai_word_meanings '
            'WHERE meaning_short_original IS NOT NULL'
        ).fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(keep_cols))
            bak_conn.executemany(
                f'INSERT INTO _wm_modified ({col_list}) VALUES ({placeholders})',
                rows,
            )
            print(f'  Backed up {len(rows)} ai_word_meanings revisions')

    # 3. ai_grammar_notes (sparse — only revised) --------------------------
    if has_table(conn, 'ai_grammar_notes') and has_column(conn, 'ai_grammar_notes', 'notes_markdown_original'):
        keep_cols = ['chapter', 'verse', 'notes_markdown', 'notes_markdown_original']
        keep_cols = [c for c in keep_cols if has_column(conn, 'ai_grammar_notes', c)]
        col_list = ','.join(f'\"{c}\"' for c in keep_cols)
        bak_conn.execute(f'CREATE TABLE _gn_modified ({col_list})')
        rows = conn.execute(
            f'SELECT {col_list} FROM ai_grammar_notes '
            \"WHERE notes_markdown_original IS NOT NULL AND notes_markdown_original != ''\"
        ).fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(keep_cols))
            bak_conn.executemany(
                f'INSERT INTO _gn_modified ({col_list}) VALUES ({placeholders})',
                rows,
            )
            print(f'  Backed up {len(rows)} ai_grammar_notes revisions')

    # 4. ai_translations (sparse — only rows where revised_text or
    #    departure_notes_original is set). Both pipelines write here:
    #    - apply_hard_case_transliterations -> revised_text
    #    - revise_verse_translations -> revised_text + departure_notes +
    #      departure_notes_original
    if has_table(conn, 'ai_translations') and has_column(conn, 'ai_translations', 'revised_text'):
        keep_cols = ['chapter', 'verse', 'revised_text']
        # Optional Phase-2 columns — only include if they exist on this DB.
        if has_column(conn, 'ai_translations', 'departure_notes'):
            keep_cols.append('departure_notes')
        if has_column(conn, 'ai_translations', 'departure_notes_original'):
            keep_cols.append('departure_notes_original')
        col_list = ','.join(f'\"{c}\"' for c in keep_cols)
        bak_conn.execute(f'CREATE TABLE _tr_modified ({col_list})')
        # Build WHERE clause matching either pipeline's marker.
        where = \"WHERE (revised_text IS NOT NULL AND revised_text != '')\"
        if 'departure_notes_original' in keep_cols:
            where += \" OR (departure_notes_original IS NOT NULL AND departure_notes_original != '')\"
        rows = conn.execute(f'SELECT {col_list} FROM ai_translations {where}').fetchall()
        if rows:
            placeholders = ','.join(['?'] * len(keep_cols))
            bak_conn.executemany(
                f'INSERT INTO _tr_modified ({col_list}) VALUES ({placeholders})',
                rows,
            )
            print(f'  Backed up {len(rows)} ai_translations revisions')

    bak_conn.commit()
    bak_conn.close()
    conn.close()
except Exception as e:
    print(f'  Vocabulary backup warning: {e}')
" 2>&1
fi

# ============================================================================
# Generic non-seed-table backup — fail-safe catch-all
# ----------------------------------------------------------------------------
# The prefix-based backups above (admin_/pipeline_/youtube_/tiktok_) only
# protect tables that match those prefixes. Any user-facing table without one
# of those prefixes — e.g. educational_videos — got silently wiped on every
# deploy along with the seed-DB copy.
#
# This step backs up EVERY table that exists in live but NOT in the seed,
# which by definition is user/runtime data created by the app after the
# image was built. It runs in addition to the prefix backups, not instead
# of them, so anything they catch (e.g. admin_pipeline_videos which IS in
# the seed as an empty table) keeps working as before.
#
# Adding a new user-facing table from now on is fail-safe by default —
# nothing about this script needs to change.
# ============================================================================
if [ -f /app/data/quran.db ]; then
  echo "Backing up non-seed (user-only) tables..."
  python3 -c "
import sqlite3, os
LIVE = '/app/data/quran.db'
SEED = '/app/seed-quran.db'
BAK = '/tmp/non_seed_backup.db'
try:
    live = sqlite3.connect(LIVE)
    seed = sqlite3.connect(SEED)
    live_tables = {r[0] for r in live.execute(
        \"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\"
    ).fetchall()}
    seed_tables = {r[0] for r in seed.execute(
        \"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\"
    ).fetchall()}
    seed.close()
    extra_tables = sorted(live_tables - seed_tables)
    if not extra_tables:
        print('  (no non-seed tables — nothing to back up)')
    else:
        if os.path.exists(BAK):
            os.remove(BAK)
        bak = sqlite3.connect(BAK)
        for tbl in extra_tables:
            schema_row = live.execute(
                \"SELECT sql FROM sqlite_master WHERE type='table' AND name = ?\",
                (tbl,),
            ).fetchone()
            if not schema_row or not schema_row[0]:
                continue
            try:
                bak.execute(schema_row[0])
            except Exception:
                pass
            bak_cols = [r[1] for r in bak.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall()]
            col_list = ','.join(f'\"{c}\"' for c in bak_cols)
            rows = live.execute(f'SELECT {col_list} FROM \"{tbl}\"').fetchall()
            if rows:
                placeholders = ','.join(['?'] * len(bak_cols))
                bak.executemany(
                    f'INSERT INTO \"{tbl}\" ({col_list}) VALUES ({placeholders})',
                    rows,
                )
                print(f'  Backed up {len(rows)} rows from {tbl}')
            # Keep the indexes too — many user-facing tables rely on
            # UNIQUE indexes (e.g. educational_videos's anchor uniqueness).
            for (idx_sql,) in live.execute(
                \"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = ? AND sql IS NOT NULL\",
                (tbl,),
            ).fetchall():
                try:
                    bak.execute(idx_sql)
                except Exception:
                    pass
        bak.commit()
        bak.close()
    live.close()
except Exception as e:
    print(f'  Non-seed backup warning: {e}')
" 2>&1
fi

# Always deploy the latest database from the image
echo "Deploying latest database..."
cp /app/seed-quran.db /app/data/quran.db

# Restore runtime-state tables into the fresh database. Matches the
# prefix list in the backup step above — keep these in sync.
#
# Robustness notes (lessons learned):
#   1. The seed DB already has empty copies of the admin_%, pipeline_%,
#      youtube_%, tiktok_% tables (the python _ensure_* functions create
#      them and the seed-baking script DELETEs rows but does not DROP).
#      So every CREATE TABLE raised "table already exists" and the outer
#      try/except bailed out BEFORE any INSERT — silently wiping all
#      admin settings on every deploy.
#   2. Fix: use CREATE TABLE IF NOT EXISTS, clear the seed's stale rows
#      first, then do column-explicit INSERTs against the intersection of
#      backup columns and destination columns. This survives schema
#      drift (e.g. if a new ALTER-added column exists in one side only).
#   3. Each table is wrapped in its own try/except so one problematic
#      table cannot take down the rest.
if [ -f /tmp/admin_backup.db ]; then
  echo "Restoring runtime-state tables..."
  python3 -c "
import sqlite3, os, re
bak = '/tmp/admin_backup.db'
dst = '/app/data/quran.db'
try:
    bak_conn = sqlite3.connect(bak)
    dst_conn = sqlite3.connect(dst)
    tables = [r[0] for r in bak_conn.execute(
        \"SELECT name FROM sqlite_master WHERE type='table' AND (\"
        \"name LIKE 'admin_%' OR name LIKE 'pipeline_%' OR \"
        \"name LIKE 'youtube_%' OR name LIKE 'tiktok_%')\"
    ).fetchall()]

    for tbl in tables:
        try:
            schema = bak_conn.execute(
                \"SELECT sql FROM sqlite_master WHERE type='table' AND name=?\",
                (tbl,),
            ).fetchone()
            if not schema or not schema[0]:
                continue

            # Make the CREATE idempotent so we don't blow up when the
            # seed already has an empty version of this table.
            create_sql = re.sub(
                r'^CREATE TABLE(?!\s+IF\s+NOT\s+EXISTS)',
                'CREATE TABLE IF NOT EXISTS',
                schema[0].strip(), count=1,
            )
            dst_conn.execute(create_sql)

            # Clear stale seed rows (empty by design, but be defensive).
            dst_conn.execute(f'DELETE FROM \"{tbl}\"')

            # Column-intersection INSERT — safe against schema drift.
            bak_cols = [r[1] for r in bak_conn.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall()]
            dst_cols = [r[1] for r in dst_conn.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall()]
            dst_set = set(dst_cols)
            common_cols = [c for c in bak_cols if c in dst_set]
            if not common_cols:
                print(f'  [{tbl}] no common columns between backup and dst, skipping')
                continue

            col_list = ','.join(f'\"{c}\"' for c in common_cols)
            placeholders = ','.join(['?'] * len(common_cols))
            rows = bak_conn.execute(f'SELECT {col_list} FROM \"{tbl}\"').fetchall()
            if rows:
                dst_conn.executemany(
                    f'INSERT INTO \"{tbl}\" ({col_list}) VALUES ({placeholders})',
                    rows,
                )
                print(f'  Restored {len(rows)} rows to {tbl}')
        except Exception as e:
            print(f'  [{tbl}] restore error: {e}')

    # Restore indexes too (e.g. UNIQUE on youtube_upload_runs.scheduled_time).
    for tbl in tables:
        try:
            idx_rows = bak_conn.execute(
                \"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL\",
                (tbl,),
            ).fetchall()
            for (idx_sql,) in idx_rows:
                idx_sql = re.sub(
                    r'^CREATE(?:\s+UNIQUE)?\s+INDEX(?!\s+IF\s+NOT\s+EXISTS)',
                    lambda m: m.group(0).replace('INDEX', 'INDEX IF NOT EXISTS'),
                    idx_sql.strip(), count=1,
                )
                try:
                    dst_conn.execute(idx_sql)
                except Exception:
                    pass
        except Exception as e:
            print(f'  [{tbl}] index restore error: {e}')

    dst_conn.commit()
    dst_conn.close()
    bak_conn.close()
    os.remove(bak)
except Exception as e:
    print(f'  Runtime-state restore warning: {e}')
" 2>&1
fi

# Restore assistant conversations into the fresh database
if [ -f /tmp/assistant_backup.db ]; then
  echo "Restoring assistant conversations..."
  python3 -c "
import sqlite3
bak = '/tmp/assistant_backup.db'
dst = '/app/data/quran.db'
try:
    bak_conn = sqlite3.connect(bak)
    rows = bak_conn.execute('SELECT session_id, page_type, page_key, question, answer, context_summary, model_used, response_time_ms, created_at FROM assistant_conversations').fetchall()
    bak_conn.close()
    if rows:
        conn = sqlite3.connect(dst)
        conn.execute('''CREATE TABLE IF NOT EXISTS assistant_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            page_type TEXT NOT NULL,
            page_key TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            context_summary TEXT,
            model_used TEXT,
            response_time_ms INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )''')
        conn.executemany('INSERT INTO assistant_conversations (session_id, page_type, page_key, question, answer, context_summary, model_used, response_time_ms, created_at) VALUES (?,?,?,?,?,?,?,?,?)', rows)
        conn.commit()
        conn.close()
        print(f'  Restored {len(rows)} conversations')
    import os
    os.remove(bak)
except Exception as e:
    print(f'  Restore warning: {e}')
" 2>&1
fi

# Restore insight evolution log into the fresh database
if [ -f /tmp/insight_evo_backup.db ]; then
  echo "Restoring insight evolution log..."
  python3 -c "
import sqlite3
bak = '/tmp/insight_evo_backup.db'
dst = '/app/data/quran.db'
try:
    bak_conn = sqlite3.connect(bak)
    cols = 'conversation_id, chapter, verse, word_pos, status, target_table, target_column, target_row_id, old_value, new_value, evaluation_model, evaluation_reasoning, confidence_score, qa_question, qa_answer, reverted_at, reverted_by, created_at'
    rows = bak_conn.execute(f'SELECT {cols} FROM insight_evolution_log').fetchall()
    bak_conn.close()
    if rows:
        conn = sqlite3.connect(dst)
        conn.execute('''CREATE TABLE IF NOT EXISTS insight_evolution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL, chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL, word_pos INTEGER, status TEXT NOT NULL,
            target_table TEXT, target_column TEXT, target_row_id INTEGER,
            old_value TEXT, new_value TEXT, evaluation_model TEXT NOT NULL,
            evaluation_reasoning TEXT NOT NULL, confidence_score REAL,
            qa_question TEXT NOT NULL, qa_answer TEXT NOT NULL,
            reverted_at TEXT, reverted_by TEXT,
            created_at TEXT DEFAULT (datetime('now')))''')
        conn.executemany(f'INSERT INTO insight_evolution_log ({cols}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
        conn.commit()
        conn.close()
        print(f'  Restored {len(rows)} insight evolution entries')
    import os
    os.remove(bak)
except Exception as e:
    print(f'  Insight restore warning: {e}')
" 2>&1
fi

# Restore verse themes into the fresh database
if [ -f /tmp/verse_themes_backup.db ]; then
  echo "Restoring verse themes..."
  python3 -c "
import sqlite3
bak = '/tmp/verse_themes_backup.db'
dst = '/app/data/quran.db'
try:
    bak_conn = sqlite3.connect(bak)
    cols = 'chapter, verse, theme, confidence, config_id, model_used, created_at'
    rows = bak_conn.execute(f'SELECT {cols} FROM verse_themes').fetchall()
    bak_conn.close()
    if rows:
        conn = sqlite3.connect(dst)
        conn.execute('''CREATE TABLE IF NOT EXISTS verse_themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER NOT NULL, verse INTEGER NOT NULL,
            theme TEXT NOT NULL, confidence REAL, config_id INTEGER,
            model_used TEXT, created_at TEXT DEFAULT (datetime(\"now\")),
            UNIQUE(chapter, verse, theme))''')
        conn.executemany(f'INSERT OR IGNORE INTO verse_themes ({cols}) VALUES (?,?,?,?,?,?,?)', rows)
        conn.commit()
        conn.close()
        print(f'  Restored {len(rows)} verse theme entries')
    import os
    os.remove(bak)
except Exception as e:
    print(f'  Verse themes restore warning: {e}')
" 2>&1
fi

# ============================================================================
# Vocabulary Studio restore — re-apply admin-curated semantic data
# ----------------------------------------------------------------------------
# Pairs with the backup step above. Each table is wrapped in its own
# try/except so one bad table can't take down the rest.
# ============================================================================
if [ -f /tmp/vocab_backup.db ]; then
  echo "Restoring vocabulary studio tables..."
  python3 -c "
import sqlite3, os
bak = '/tmp/vocab_backup.db'
dst = '/app/data/quran.db'
bak_conn = sqlite3.connect(bak)
dst_conn = sqlite3.connect(dst)

def has_table(c, name):
    return bool(c.execute(
        \"SELECT 1 FROM sqlite_master WHERE type='table' AND name=?\",
        (name,),
    ).fetchone())

def has_column(c, table, col):
    return any(
        r[1] == col for r in c.execute(f'PRAGMA table_info(\"{table}\")')
    )

def common_cols(a_conn, a_table, b_conn, b_table):
    a = [r[1] for r in a_conn.execute(f'PRAGMA table_info(\"{a_table}\")')]
    b = set(r[1] for r in b_conn.execute(f'PRAGMA table_info(\"{b_table}\")'))
    return [c for c in a if c in b]

# 1. term_surveys — INSERT OR REPLACE (user wins over seed) ----------------
try:
    if has_table(bak_conn, 'term_surveys') and has_table(dst_conn, 'term_surveys'):
        cols = common_cols(bak_conn, 'term_surveys', dst_conn, 'term_surveys')
        if cols:
            col_list = ','.join(f'\"{c}\"' for c in cols)
            placeholders = ','.join(['?'] * len(cols))
            rows = bak_conn.execute(f'SELECT {col_list} FROM term_surveys').fetchall()
            count = 0
            for row in rows:
                # Use root_buckwalter as the natural key (it has UNIQUE).
                if 'root_buckwalter' not in cols:
                    continue
                rb_idx = cols.index('root_buckwalter')
                root_bw = row[rb_idx]
                # Delete the seed row for this root if any, then insert backup row.
                dst_conn.execute(
                    'DELETE FROM term_surveys WHERE root_buckwalter = ?', (root_bw,)
                )
                dst_conn.execute(
                    f'INSERT INTO term_surveys ({col_list}) VALUES ({placeholders})',
                    row,
                )
                count += 1
            if count:
                print(f'  Restored {count} term_surveys rows')
except Exception as e:
    print(f'  [term_surveys] restore error: {e}')

# 1b. proper_noun_candidates — full-table replace (no seed data exists) -----
try:
    if has_table(bak_conn, 'proper_noun_candidates') and has_table(dst_conn, 'proper_noun_candidates'):
        cols = common_cols(bak_conn, 'proper_noun_candidates', dst_conn, 'proper_noun_candidates')
        if cols:
            col_list = ','.join(f'\"{c}\"' for c in cols)
            placeholders = ','.join(['?'] * len(cols))
            rows = bak_conn.execute(f'SELECT {col_list} FROM proper_noun_candidates').fetchall()
            count = 0
            # Wipe the (probably-empty) seed copy first, then bulk-insert.
            dst_conn.execute('DELETE FROM proper_noun_candidates')
            for row in rows:
                dst_conn.execute(
                    f'INSERT INTO proper_noun_candidates ({col_list}) VALUES ({placeholders})',
                    row,
                )
                count += 1
            if count:
                print(f'  Restored {count} proper_noun_candidates rows')
except Exception as e:
    print(f'  [proper_noun_candidates] restore error: {e}')

# 2. ai_word_meanings — UPDATE matching rows -------------------------------
try:
    if has_table(bak_conn, '_wm_modified') and has_table(dst_conn, 'ai_word_meanings'):
        # Make sure backup columns exist on destination (they may not if seed
        # is older than the bias-revision pipeline). Idempotent ALTERs.
        for col in ('meaning_short_original', 'meaning_detailed_original', 'preferred_translation_original'):
            if not has_column(dst_conn, 'ai_word_meanings', col):
                try:
                    dst_conn.execute(f'ALTER TABLE ai_word_meanings ADD COLUMN {col} TEXT')
                except Exception:
                    pass
        rows = bak_conn.execute(
            'SELECT chapter, verse, word_pos, '
            '       meaning_short, meaning_detailed, preferred_translation, '
            '       meaning_short_original, meaning_detailed_original, '
            '       preferred_translation_original '
            'FROM _wm_modified'
        ).fetchall()
        count = 0
        for r in rows:
            res = dst_conn.execute(
                'UPDATE ai_word_meanings SET '
                '  meaning_short = ?, meaning_detailed = ?, preferred_translation = ?, '
                '  meaning_short_original = ?, meaning_detailed_original = ?, '
                '  preferred_translation_original = ? '
                'WHERE chapter = ? AND verse = ? AND word_pos = ?',
                (r[3], r[4], r[5], r[6], r[7], r[8], r[0], r[1], r[2]),
            )
            if res.rowcount:
                count += 1
        if count:
            print(f'  Restored {count} ai_word_meanings revisions')
except Exception as e:
    print(f'  [ai_word_meanings] restore error: {e}')

# 3. ai_grammar_notes — UPDATE matching rows -------------------------------
try:
    if has_table(bak_conn, '_gn_modified') and has_table(dst_conn, 'ai_grammar_notes'):
        if not has_column(dst_conn, 'ai_grammar_notes', 'notes_markdown_original'):
            try:
                dst_conn.execute('ALTER TABLE ai_grammar_notes ADD COLUMN notes_markdown_original TEXT')
            except Exception:
                pass
        rows = bak_conn.execute(
            'SELECT chapter, verse, notes_markdown, notes_markdown_original FROM _gn_modified'
        ).fetchall()
        count = 0
        for r in rows:
            res = dst_conn.execute(
                'UPDATE ai_grammar_notes SET '
                '  notes_markdown = ?, notes_markdown_original = ? '
                'WHERE chapter = ? AND verse = ?',
                (r[2], r[3], r[0], r[1]),
            )
            if res.rowcount:
                count += 1
        if count:
            print(f'  Restored {count} ai_grammar_notes revisions')
except Exception as e:
    print(f'  [ai_grammar_notes] restore error: {e}')

# 4. ai_translations — UPDATE matching rows --------------------------------
try:
    if has_table(bak_conn, '_tr_modified') and has_table(dst_conn, 'ai_translations'):
        # Make sure the Phase-2 backup column exists on dest. The seed may
        # predate the revise_verse_translations migration.
        if not has_column(dst_conn, 'ai_translations', 'departure_notes_original'):
            try:
                dst_conn.execute('ALTER TABLE ai_translations ADD COLUMN departure_notes_original TEXT')
            except Exception:
                pass
        # Discover what columns this backup actually carries (the layout
        # depends on which Phase-2 columns existed at backup time).
        bak_cols = [r[1] for r in bak_conn.execute('PRAGMA table_info(_tr_modified)')]
        dst_cols = set(r[1] for r in dst_conn.execute('PRAGMA table_info(ai_translations)'))
        # We always have chapter, verse, revised_text. Optionally:
        # departure_notes, departure_notes_original.
        col_list = ','.join(f'\"{c}\"' for c in bak_cols)
        rows = bak_conn.execute(f'SELECT {col_list} FROM _tr_modified').fetchall()
        # Build the SET clause from intersect(bak_cols, dst_cols) excluding the keys.
        set_cols = [c for c in bak_cols if c in dst_cols and c not in ('chapter', 'verse')]
        if set_cols:
            set_sql = ', '.join(f'\"{c}\" = ?' for c in set_cols)
            count = 0
            for r in rows:
                # Map row columns by name
                row_map = dict(zip(bak_cols, r))
                set_vals = [row_map[c] for c in set_cols]
                res = dst_conn.execute(
                    f'UPDATE ai_translations SET {set_sql} WHERE chapter = ? AND verse = ?',
                    (*set_vals, row_map['chapter'], row_map['verse']),
                )
                if res.rowcount:
                    count += 1
            if count:
                print(f'  Restored {count} ai_translations revisions')
except Exception as e:
    print(f'  [ai_translations] restore error: {e}')

dst_conn.commit()
dst_conn.close()
bak_conn.close()
os.remove(bak)
" 2>&1
fi

# ============================================================================
# Generic non-seed-table restore — pairs with the catch-all backup above.
# ----------------------------------------------------------------------------
# Tables that exist only in live (educational_videos, future user-facing
# tables) come back here. CREATE TABLE IF NOT EXISTS handles the case where
# the app has already created the table via its _ensure_* function during
# import; in that case we just DELETE existing rows and re-INSERT from the
# backup. Each table is wrapped in its own try/except so one bad table
# can't take down the rest.
# ============================================================================
if [ -f /tmp/non_seed_backup.db ]; then
  echo "Restoring non-seed tables..."
  python3 -c "
import sqlite3, os, re
BAK = '/tmp/non_seed_backup.db'
DST = '/app/data/quran.db'
try:
    bak = sqlite3.connect(BAK)
    dst = sqlite3.connect(DST)
    tables = [r[0] for r in bak.execute(
        \"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'\"
    ).fetchall()]
    for tbl in tables:
        try:
            schema_row = bak.execute(
                \"SELECT sql FROM sqlite_master WHERE type='table' AND name = ?\",
                (tbl,),
            ).fetchone()
            if not schema_row or not schema_row[0]:
                continue
            create_sql = re.sub(
                r'^CREATE TABLE(?!\s+IF\s+NOT\s+EXISTS)',
                'CREATE TABLE IF NOT EXISTS',
                schema_row[0].strip(), count=1,
            )
            dst.execute(create_sql)
            # Wipe whatever the seed brought (almost always nothing —
            # these tables aren't in the seed) before restoring.
            dst.execute(f'DELETE FROM \"{tbl}\"')
            bak_cols = [r[1] for r in bak.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall()]
            dst_cols = {r[1] for r in dst.execute(f'PRAGMA table_info(\"{tbl}\")').fetchall()}
            common = [c for c in bak_cols if c in dst_cols]
            if not common:
                print(f'  [{tbl}] no common columns, skipping')
                continue
            col_list = ','.join(f'\"{c}\"' for c in common)
            placeholders = ','.join(['?'] * len(common))
            rows = bak.execute(f'SELECT {col_list} FROM \"{tbl}\"').fetchall()
            if rows:
                dst.executemany(
                    f'INSERT INTO \"{tbl}\" ({col_list}) VALUES ({placeholders})',
                    rows,
                )
                print(f'  Restored {len(rows)} rows to {tbl}')
            # Restore indexes (UNIQUE constraints etc.)
            for (idx_sql,) in bak.execute(
                \"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name = ? AND sql IS NOT NULL\",
                (tbl,),
            ).fetchall():
                idx_sql = re.sub(
                    r'^CREATE(?:\s+UNIQUE)?\s+INDEX(?!\s+IF\s+NOT\s+EXISTS)',
                    lambda m: m.group(0).replace('INDEX', 'INDEX IF NOT EXISTS'),
                    idx_sql.strip(), count=1,
                )
                try:
                    dst.execute(idx_sql)
                except Exception:
                    pass
        except Exception as e:
            print(f'  [{tbl}] restore error: {e}')
    dst.commit()
    dst.close()
    bak.close()
    os.remove(BAK)
except Exception as e:
    print(f'  Non-seed restore warning: {e}')
" 2>&1
fi

# Deploy mnemonic images to the data volume
mkdir -p /app/data/mnemonic_images
if [ -d /app/seed-mnemonic-images ] && [ "$(ls -A /app/seed-mnemonic-images 2>/dev/null)" ]; then
  echo "Deploying mnemonic images..."
  cp /app/seed-mnemonic-images/* /app/data/mnemonic_images/
fi

# Run cognate languages migration (idempotent — skips if already applied).
# `|| true` so a migration failure doesn't block the deploy: the app
# already has the defensive crash guard from 52c1bff for the symptom,
# and we'd rather serve traffic with stale cognate_languages than fail
# to come up at all. The set -e at the top of this script would
# otherwise abort here on any non-zero exit.
if [ -f /app/normalize_cognate_languages.py ]; then
  echo "Running cognate languages migration..."
  python3 /app/normalize_cognate_languages.py 2>&1 || \
    echo "  WARNING: migration failed — see traceback above; continuing deploy"
fi

exec "$@"

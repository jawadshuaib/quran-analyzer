#!/bin/sh
set -e

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

# Deploy mnemonic images to the data volume
mkdir -p /app/data/mnemonic_images
if [ -d /app/seed-mnemonic-images ] && [ "$(ls -A /app/seed-mnemonic-images 2>/dev/null)" ]; then
  echo "Deploying mnemonic images..."
  cp /app/seed-mnemonic-images/* /app/data/mnemonic_images/
fi

exec "$@"

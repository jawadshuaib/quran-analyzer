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

# Always deploy the latest database from the image
echo "Deploying latest database..."
cp /app/seed-quran.db /app/data/quran.db

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

# Deploy mnemonic images to the data volume
mkdir -p /app/data/mnemonic_images
if [ -d /app/seed-mnemonic-images ] && [ "$(ls -A /app/seed-mnemonic-images 2>/dev/null)" ]; then
  echo "Deploying mnemonic images..."
  cp /app/seed-mnemonic-images/* /app/data/mnemonic_images/
fi

exec "$@"

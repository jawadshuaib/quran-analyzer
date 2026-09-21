#!/usr/bin/env python3
"""Schema + worklist for root core meanings.

A NEW TABLE, not a column on ai_root_meanings. sync_tables_to_prod.sh ships
CREATE TABLE IF NOT EXISTS + INSERT OR REPLACE, which auto-creates a new table
on prod but CANNOT add a column -- a column design aborts the whole sync until
a redeploy lands an ALTER.

KEYED BY SENSE, NOT BY ROOT. A reader hovers a word. For 87% of roots one
explanation serves every word of it, but 213 roots carry genuinely different
words in the same radicals -- tarf is a glance and taraf is an edge -- and one
passage cannot serve both. So the key is (root, sense_key), where sense_key is
'' for a whole-root explanation and otherwise names the lemma group. The
lemma map turns the word a reader is actually looking at into the right row.
"""
import json
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'quran.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS root_core_meanings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_buckwalter TEXT NOT NULL,
    sense_key TEXT NOT NULL DEFAULT '',   -- '' = the whole root
    lemmas_json TEXT,                     -- the lemma group this explains
    passage TEXT,
    physical_origin TEXT,
    stations_json TEXT,                   -- which evidence stations were used
    verses_json TEXT,
    confidence TEXT,
    verdict TEXT,                         -- 'ok' | 'no_insight'
    model_used TEXT,
    prompt_version TEXT,
    gates_json TEXT,                      -- flags at generation time
    review_status TEXT DEFAULT 'pending', -- nothing public until approved
    hidden INTEGER DEFAULT 1,
    raw_response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    edited_at TEXT,
    UNIQUE(root_buckwalter, sense_key)
);
CREATE INDEX IF NOT EXISTS idx_rcm_root ON root_core_meanings(root_buckwalter);

-- word -> which explanation. Built once from the sense clustering so the API
-- never has to recompute it per request.
CREATE TABLE IF NOT EXISTS root_core_lemma_map (
    root_buckwalter TEXT NOT NULL,
    lemma_arabic TEXT NOT NULL,
    sense_key TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (root_buckwalter, lemma_arabic)
);

-- Resumable worklist: 1,911 units across many quota windows.
CREATE TABLE IF NOT EXISTS root_core_worklist (
    root_buckwalter TEXT NOT NULL,
    sense_key TEXT NOT NULL DEFAULT '',
    lemmas_json TEXT,
    n_verses INTEGER,
    status TEXT DEFAULT 'todo',           -- todo | done | failed
    attempts INTEGER DEFAULT 0,
    last_error TEXT,
    at TEXT,
    PRIMARY KEY (root_buckwalter, sense_key)
);
"""


def connect():
    c = sqlite3.connect(DB, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA busy_timeout=30000')
    c.executescript(SCHEMA)
    c.commit()
    return c


def seed(c=None):
    """Populate the worklist and the lemma map from the sense clustering."""
    import _root_lemma_split as S
    c = c or connect()
    splits = S.analyse(c)
    roots = [r[0] for r in c.execute(
        "SELECT DISTINCT root_buckwalter FROM morphology "
        "WHERE root_buckwalter NOT IN ('','-') AND root_buckwalter IS NOT NULL")]
    units = maps = 0
    for bw in roots:
        if bw in splits:
            for g in splits[bw]['groups']:
                key = '+'.join(g['lemmas'])
                c.execute("INSERT OR IGNORE INTO root_core_worklist "
                          "(root_buckwalter, sense_key, lemmas_json, n_verses) VALUES (?,?,?,?)",
                          (bw, key, json.dumps(g['lemmas'], ensure_ascii=False), g['verses']))
                units += c.total_changes and 1 or 0
                for lem in g['lemmas']:
                    c.execute("INSERT OR REPLACE INTO root_core_lemma_map "
                              "(root_buckwalter, lemma_arabic, sense_key) VALUES (?,?,?)",
                              (bw, lem, key))
                    maps += 1
            # Lemmas too small to earn their own explanation fall back to the
            # LARGEST sense group rather than to nothing -- a rare form is far
            # more likely to belong to the root's main sense than to be its own.
            main = '+'.join(splits[bw]['groups'][0]['lemmas'])
            for r in c.execute("SELECT DISTINCT lemma_arabic FROM morphology "
                               "WHERE root_buckwalter=? AND lemma_arabic!=''", (bw,)):
                c.execute("INSERT OR IGNORE INTO root_core_lemma_map "
                          "(root_buckwalter, lemma_arabic, sense_key) VALUES (?,?,?)",
                          (bw, r['lemma_arabic'], main))
        else:
            c.execute("INSERT OR IGNORE INTO root_core_worklist "
                      "(root_buckwalter, sense_key, n_verses) VALUES (?,'',?)",
                      (bw, c.execute("SELECT COUNT(DISTINCT chapter||':'||verse) FROM morphology "
                                     "WHERE root_buckwalter=?", (bw,)).fetchone()[0]))
    c.commit()
    return {
        "units": c.execute("SELECT COUNT(*) FROM root_core_worklist").fetchone()[0],
        "split_roots": len(splits),
        "lemma_map_rows": c.execute("SELECT COUNT(*) FROM root_core_lemma_map").fetchone()[0],
    }


if __name__ == '__main__':
    c = connect()
    print(json.dumps(seed(c), indent=1))
    print("worklist by size:")
    for r in c.execute("SELECT status, COUNT(*) n FROM root_core_worklist GROUP BY 1"):
        print("   %-6s %d" % (r['status'], r['n']))
    print("sample split root (Trf):")
    for r in c.execute("SELECT * FROM root_core_worklist WHERE root_buckwalter='Trf'"):
        print("   sense_key=%-12s verses=%s" % (r['sense_key'], r['n_verses']))
    for r in c.execute("SELECT * FROM root_core_lemma_map WHERE root_buckwalter='Trf'"):
        print("   lemma %-10s -> %s" % (r['lemma_arabic'], r['sense_key']))

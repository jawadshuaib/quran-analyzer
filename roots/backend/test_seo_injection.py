#!/usr/bin/env python3
"""Regression tests for the server-side SEO injection in serve_spa.

Run:  AL_NUQTA_NO_SCHEDULER=1 python3 test_seo_injection.py

Renders roots/frontend/index.html through app._render_spa_html for each main
route type and checks the head carries exactly one <title>, description and
canonical, all for that path. This silently broke once when index.html lost
its SEO marker (every page shipped the homepage title with canonical → "/").
Needs the local quran.db.
"""

import os
import re
import sys

os.environ.setdefault("AL_NUQTA_NO_SCHEDULER", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import app  # noqa: E402

INDEX_HTML = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "index.html")
SITE = app.SITE_URL

# (path, HTTP status, canonical — None means the page must carry none,
#  a fragment the <title> must contain)
CASES = [
    ("/", 200, SITE + "/", "A Root Based Translation"),
    ("/verse/2:255", 200, SITE + "/verse/2:255", "(2:255)"),
    ("/root/ktb", 200, SITE + "/root/ktb", "Root "),
    ("/word/1:1/1", 200, SITE + "/word/1:1/1", "Word 1"),
    ("/read/36", 200, SITE + "/read/36", "Read Surah"),
    ("/dictionary", 200, SITE + "/dictionary", "Dictionary"),
    ("/classical-dictionaries", 200, SITE + "/classical-dictionaries", "Classical"),
    ("/meters", 200, SITE + "/meters", "metres"),
    ("/meter/tawil", 200, SITE + "/meter/tawil", "metre"),
    ("/poems", 200, SITE + "/poems", "Poetry"),
    ("/poem/1", 200, SITE + "/poem/1", "pre-Islamic poem"),
    ("/settings", 200, SITE + "/settings", "Settings"),
    ("/meter/not-a-metre", 404, None, "404"),
    ("/no-such-page", 404, None, "404"),
]
if app._DICT_GUIDES:
    slug = app._DICT_GUIDES[0]["slug"]
    CASES.append((f"/classical-dictionaries/{slug}", 200,
                  f"{SITE}/classical-dictionaries/{slug}", "Classical Dictionary"))


def _count(pattern, doc):
    return len(re.findall(pattern, doc))


def check(template, path, status, canonical, title_part):
    doc, got_status = app._render_spa_html(template, path)
    head = doc.split("</head>", 1)[0]
    errs = []
    if got_status != status:
        errs.append(f"status {got_status}, expected {status}")
    titles = re.findall(r"<title>([^<]*)</title>", head)
    if len(titles) != 1:
        errs.append(f"{len(titles)} <title> tags")
    elif title_part not in titles[0]:
        errs.append(f"title {titles[0]!r} lacks {title_part!r}")
    if _count(r'<meta name="description"', head) != 1:
        errs.append(f'{_count(r"<meta name=.description.", head)} descriptions')
    canonicals = re.findall(r'<link rel="canonical" href="([^"]*)"', head)
    if canonical is None:
        if canonicals:
            errs.append(f"unexpected canonical {canonicals}")
    elif canonicals != [canonical]:
        errs.append(f"canonical {canonicals}, expected [{canonical!r}]")
    for tag in ("og:title", "twitter:title", "og:url"):
        n = _count(rf'"{tag}"', head)
        if n > 1:
            errs.append(f"{n} {tag} tags")
    if "SEO_META_" in doc:
        errs.append("SEO marker left in the page")
    return [f"{path}: {e}" for e in errs]


def main():
    with open(INDEX_HTML, encoding="utf-8") as f:
        template = f.read()
    fails = []
    if len(app._SEO_BLOCK_RE.findall(template)) != 1:
        fails.append("index.html must hold exactly one SEO_META_START … SEO_META_END block")
    for case in CASES:
        fails += check(template, *case)
    if fails:
        print(f"FAIL ({len(fails)})")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"ok — {len(CASES)} paths")


if __name__ == "__main__":
    main()

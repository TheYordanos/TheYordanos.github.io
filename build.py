#!/usr/bin/env python3
"""Build articles/*.html from articles_md/*.md with Pandoc and refresh the
article list in index.html.

Front matter per article:
    ---
    title: Chess in Odin
    description: Short summary for the meta tag.
    date: 2026-09-12        (YYYY-MM-DD, newest first)
    draft: true             (optional, skips the article)
    ---

Usage:
    python build.py           # incremental: only rebuilds changed articles
    python build.py --force   # rebuild everything
"""
import html
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "articles_md"
OUT_DIR = ROOT / "articles"
TEMPLATE = OUT_DIR / "template.txt"
INDEX = ROOT / "index.html"

START_MARK = "<!-- ARTICLES:START -->"
END_MARK = "<!-- ARTICLES:END -->"
ITEM_INDENT = "\t\t\t\t"

PANDOC_EXTRA = [
    # "--highlight-style=pygments",
]


def fail(msg):
    print(f"error: {msg}")
    sys.exit(1)


def read_front_matter(path):
    """Tiny `key: value` parser for the --- block at the top of a file."""
    text = path.read_text(encoding="utf-8-sig")
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", text, re.S)
    meta = {}
    if not m:
        return meta
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if kv:
            value = kv.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            meta[kv.group(1).lower()] = value
    return meta


def is_up_to_date(src, out, newest_dep):
    if not out.exists():
        return False
    return out.stat().st_mtime >= max(src.stat().st_mtime, newest_dep)


def build(job):
    src, out, force, template_mtime = job
    if not force and is_up_to_date(src, out, template_mtime):
        return src, "ok", ""
    result = subprocess.run(
        ["pandoc", str(src), "--from", "markdown", "--to", "html5",
         "--template", str(TEMPLATE), "-o", str(out), *PANDOC_EXTRA],
        capture_output=True,
    )
    if result.returncode != 0:
        return src, "failed", result.stderr.decode("utf-8", "replace")
    return src, "built", ""


def splice_index(items):
    data = INDEX.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in data else "\n"

    s = data.find(START_MARK)
    e = data.find(END_MARK)
    if s < 0 or e < 0 or e < s:
        fail(f"index.html needs these two lines inside the articles list:\n"
             f"  {START_MARK}\n  {END_MARK}")

    # keep the END marker's indentation
    line_start = data.rfind("\n", 0, e) + 1
    indent = data[line_start:e] if line_start > s else ""
    if indent.strip():
        indent = ""

    lines = [
        f'{ITEM_INDENT}<li><a href="articles/{slug}.html">{html.escape(title)}</a></li>'
        for _, slug, title in items
    ]
    body = nl.join(lines) + nl if lines else ""
    new = data[: s + len(START_MARK)] + nl + body + indent + data[e:]

    if new != data:
        INDEX.write_bytes(new.encode("utf-8"))  # UTF-8, no BOM, newlines preserved
    return len(lines)


def main():
    force = "--force" in sys.argv or "-f" in sys.argv

    if not shutil.which("pandoc"):
        fail("pandoc not found. Install it, then open a NEW terminal window.")
    if not TEMPLATE.exists():
        fail(f"missing {TEMPLATE}")
    if not INDEX.exists():
        fail("missing index.html")
    if not CONTENT_DIR.is_dir():
        fail(f"missing {CONTENT_DIR}")

    OUT_DIR.mkdir(exist_ok=True)
    template_mtime = TEMPLATE.stat().st_mtime

    jobs, items, keep = [], [], set()
    for src in sorted(CONTENT_DIR.glob("*.md")):
        meta = read_front_matter(src)
        slug = src.stem
        if meta.get("draft", "").lower() in ("true", "yes", "1"):
            print(f"skip   {slug} [draft]")
            continue

        date = meta.get("date", "")
        title = meta.get("title", "")
        if not date:
            print(f"warning: {slug} has no date; it will sort last")
            date = "0000-00-00"
        if not title:
            print(f"warning: {slug} has no title; using filename")
            title = slug

        items.append((date, slug, title))
        keep.add(slug)
        jobs.append((src, OUT_DIR / f"{slug}.html", force, template_mtime))

    # remove html for deleted/draft articles (template.txt is untouched)
    for old in OUT_DIR.glob("*.html"):
        if old.stem not in keep:
            old.unlink()
            print(f"remove {old.name}")

    errors = 0
    built = 0
    with ThreadPoolExecutor() as pool:
        for src, status, err in pool.map(build, jobs):
            if status == "built":
                built += 1
                print(f"built  {src.stem}.html")
            elif status == "failed":
                errors += 1
                print(f"error: pandoc failed on {src.name}\n{err}")
    if errors:
        sys.exit(1)

    # newest first, then title A-Z
    items.sort(key=lambda r: r[2])
    items.sort(key=lambda r: r[0], reverse=True)
    count = splice_index(items)

    print(f"done: {count} article(s), {built} rebuilt, index.html updated")


if __name__ == "__main__":
    main()

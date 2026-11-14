#!/usr/bin/env python3
"""Build articles/*.html from articles_md/*.md with Pandoc, then refresh the
article lists in index.html (latest few) and archive.html (everything).

Front matter per article:
    ---
    title: Chess in Odin
    description: Short summary for the meta tag.
    date: 2026-09-12        (YYYY-MM-DD, newest first)
    draft: true             (optional, skips the article)
    toc: true               (optional, adds a table of contents)
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
FILTERS = ROOT / "filters.lua"
INDEX = ROOT / "index.html"
ARCHIVE = ROOT / "archive.html"

INDEX_LIMIT = 20  # how many articles to show on the index page

# RSS/Atom feed (feed.xml).
SITE_URL = "https://theyordanos.github.io"
SITE_TITLE = "Yordanos"
SITE_AUTHOR = "Yordanos Z."
FEED = ROOT / "feed.xml"
FEED_LIMIT = 20  # newest articles in the feed

OG_IMAGE = "res/og.png"

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
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", text, re.DOTALL)
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


def page_vars(slug, title, description):
    """Template variables for link previews, as pandoc -V arguments.
    Values are pre-escaped for use inside HTML attributes, so the template
    can write content="$og_title$" directly."""
    values = {
        "og_title": title,
        "og_description": description,
        "og_url": f"{SITE_URL}/articles/{slug}.html",
        "og_image": f"{SITE_URL}/{OG_IMAGE}",
        "og_site": SITE_TITLE,
    }
    args = []
    for key, value in values.items():
        if value:
            args += ["-V", f"{key}={html.escape(value, quote=True)}"]
    return args


def build(job):
    src, out, force, template_mtime, extra_args = job
    if not force and is_up_to_date(src, out, template_mtime):
        return src, "ok", ""
    # no check=True on purpose: we report failures ourselves below
    result = subprocess.run(
        ["pandoc", str(src), "--from", "markdown", "--to", "html5",
         "--template", str(TEMPLATE),
         "--lua-filter", str(FILTERS),
         *extra_args, "-o", str(out), *PANDOC_EXTRA],
        capture_output=True,
    )
    if result.returncode != 0:
        return src, "failed", result.stderr.decode("utf-8", "replace")
    return src, "built", ""


def render_items(items, year_headings=False):
    """items: (date, slug, title) tuples, already sorted. Returns <li> lines."""
    lines, last_year = [], None
    for date, slug, title in items:
        year = date[:4]
        dated = year != "0000"
        if year_headings and dated and year != last_year:
            lines.append(f'{ITEM_INDENT}<li class="year">{year}</li>')
            last_year = year
        lines.append(
            f'{ITEM_INDENT}<li><time>{date if dated else ""}</time>'
            f'<a href="articles/{slug}.html">{html.escape(title)}</a></li>'
        )
    return lines


def splice(path, lines):
    """Replace everything between the ARTICLES markers in `path`."""
    data = path.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in data else "\n"

    s = data.find(START_MARK)
    e = data.find(END_MARK)
    if s < 0 or e < 0 or e < s:
        fail(f"{path.name} needs these two lines inside the articles list:\n"
             f"  {START_MARK}\n  {END_MARK}")

    # keep the END marker's indentation
    line_start = data.rfind("\n", 0, e) + 1
    indent = data[line_start:e] if line_start > s else ""
    if indent.strip():
        indent = ""

    body = nl.join(lines) + nl if lines else ""
    new = data[: s + len(START_MARK)] + nl + body + indent + data[e:]

    if new != data:
        path.write_bytes(new.encode("utf-8"))  # UTF-8, no BOM, newlines preserved


def write_feed(items, descriptions):
    """Atom feed of the newest articles. items: sorted (date, slug, title)."""
    esc = html.escape
    entries = []
    for date, slug, title in items:
        if date == "0000-00-00":
            continue  # undated articles stay out of the feed
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            entries.append((date, slug, title))
        else:
            print(f"warning: {slug} date '{date}' is not YYYY-MM-DD; left out of feed.xml")
    entries = entries[:FEED_LIMIT]

    updated = f"{entries[0][0]}T00:00:00Z" if entries else "1970-01-01T00:00:00Z"
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml-stylesheet type="text/css" href="styles/feed.css"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{esc(SITE_TITLE)}</title>",
        f'<link href="{SITE_URL}/"/>',
        f'<link rel="self" href="{SITE_URL}/feed.xml"/>',
        f"<id>{SITE_URL}/</id>",
        f"<updated>{updated}</updated>",
        f"<author><name>{esc(SITE_AUTHOR)}</name></author>",
    ]
    for date, slug, title in entries:
        url = f"{SITE_URL}/articles/{slug}.html"
        out += [
            "<entry>",
            f"<title>{esc(title)}</title>",
            f'<link href="{url}"/>',
            f"<id>{url}</id>",
            f"<updated>{date}T00:00:00Z</updated>",
        ]
        if descriptions.get(slug):
            out.append(f"<summary>{esc(descriptions[slug])}</summary>")
        out.append("</entry>")
    out.append("</feed>")

    text = "\n".join(out) + "\n"
    old = FEED.read_bytes().decode("utf-8") if FEED.exists() else ""
    if text != old:
        FEED.write_bytes(text.encode("utf-8"))
    return len(entries)


def main():
    force = "--force" in sys.argv or "-f" in sys.argv

    if not shutil.which("pandoc"):
        fail("pandoc not found. Install it, then open a NEW terminal window.")
    if not TEMPLATE.exists():
        fail(f"missing {TEMPLATE}")
    if not FILTERS.exists():
        fail(f"missing {FILTERS}")
    if not INDEX.exists():
        fail("missing index.html")
    if not CONTENT_DIR.is_dir():
        fail(f"missing {CONTENT_DIR}")

    OUT_DIR.mkdir(exist_ok=True)
    # editing the template, a filter or this script rebuilds every article
    template_mtime = max(TEMPLATE.stat().st_mtime,
                         FILTERS.stat().st_mtime,
                         Path(__file__).stat().st_mtime)

    jobs, items, keep, descriptions = [], [], set(), {}
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
        descriptions[slug] = meta.get("description", "")
        keep.add(slug)
        extra = page_vars(slug, title, descriptions[slug])
        if meta.get("toc", "").lower() in ("true", "yes", "1"):
            # the template needs the flag, "toc: true" alone gives an empty box
            extra.append("--toc")
        jobs.append((src, OUT_DIR / f"{slug}.html", force, template_mtime, extra))

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

    splice(INDEX, render_items(items[:INDEX_LIMIT]))

    if ARCHIVE.exists():
        splice(ARCHIVE, render_items(items, year_headings=True))
        archive_note = "archive.html updated"
    else:
        archive_note = "archive.html not found, skipped"

    feed_count = write_feed(items, descriptions)
    if "example.com" in SITE_URL:
        print("warning: SITE_URL in build.py is still the placeholder; "
              "feed links will be wrong until you set it")

    print(f"done: {len(items)} article(s), {built} rebuilt, "
          f"index.html shows {min(len(items), INDEX_LIMIT)}, {archive_note}, "
          f"feed.xml has {feed_count}")


if __name__ == "__main__":
    main()

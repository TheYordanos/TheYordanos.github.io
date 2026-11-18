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
    series: Chess in Odin   (optional, lists the parts at the top of each one)
    part: 2                 (optional, order inside a series; default is by date)
    image: ../res/cover.png (optional, link preview image; default is the
                             first image in the article, then OG_IMAGE)
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
from urllib.parse import urljoin

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

OG_IMAGE = "res/article_og.png"  # used when an article has no image
NOT_PREVIEW = (".mp4", ".webm", ".mov", ".mp3", ".ogg", ".wav", ".m4a", ".svg")

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


def first_image(text):
    """Path or URL of the first ![](image) in the Markdown, or ''.
    Images inside code fences and inline code are examples, so they are skipped."""
    text = re.sub(r"^(`{3,}|~{3,}).*?^\1", "", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"`[^`\n]*`", "", text)
    for m in re.finditer(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)", text):
        path = m.group(1)
        if not path.lower().split("?")[0].endswith(NOT_PREVIEW):
            return path
    return ""


def page_vars(slug, title, description, image=""):
    """Template variables for link previews, as pandoc -V arguments.
    Values are pre-escaped for use inside HTML attributes, so the template
    can write content="$og_title$" directly."""
    values = {
        "og_title": title,
        "og_description": description,
        "og_url": f"{SITE_URL}/articles/{slug}.html",
        # paths are relative to the built page, like in the article itself
        "og_image": urljoin(f"{SITE_URL}/articles/{slug}.html", image)
                    if image else f"{SITE_URL}/{OG_IMAGE}",
        "og_site": SITE_TITLE,
    }
    args = []
    for key, value in values.items():
        if value:
            args += ["-V", f"{key}={html.escape(value, quote=True)}"]
    return args


def series_html(name, parts, current):
    """Box listing every article of a series. parts: [(slug, title)] in order."""
    lis = []
    for slug, title in parts:
        t = html.escape(title)
        if slug == current:
            lis.append(f'<li aria-current="page">{t}</li>')
        else:
            lis.append(f'<li><a href="{slug}.html">{t}</a></li>')
    return (f'<nav class="series" aria-label="Series">'
            f'<p class="series-title">Series: {html.escape(name)}</p>'
            f'<ol>{"".join(lis)}</ol></nav>')


def series_pager(parts, current):
    """Previous/next boxes for an article in a series. parts: [(slug, title)] in order."""
    slugs = [s for s, _ in parts]
    i = slugs.index(current)
    boxes = []
    if i > 0:
        slug, title = parts[i - 1]
        boxes.append(f'<a class="prev" rel="prev" href="{slug}.html">'
                     f'<span class="pager-label">Previous</span>'
                     f'<span class="pager-title">{html.escape(title)}</span></a>')
    if i < len(parts) - 1:
        slug, title = parts[i + 1]
        boxes.append(f'<a class="next" rel="next" href="{slug}.html">'
                     f'<span class="pager-label">Next</span>'
                     f'<span class="pager-title">{html.escape(title)}</span></a>')
    return ('<nav class="series-pager" aria-label="Series navigation">'
            + "".join(boxes) + '</nav>')


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


def render_items(items, group_of=None, badges=None):
    """items: (date, slug, title) tuples, already sorted. Returns <li> lines.
    group_of(item) gives the heading an item belongs under, or None."""
    lines, last = [], None
    for item in items:
        date, slug, title = item
        label = group_of(item) if group_of else None
        if label and label != last:
            lines.append(f'{ITEM_INDENT}<li class="year">{html.escape(label)}</li>')
            last = label
        shown = date if date[:4] != "0000" else ""
        text = html.escape(title)
        if badges and slug in badges:
            text += f" [{badges[slug]}]"  # e.g. "Chess in Odin [Part 1/4]"
        lines.append(
            f'{ITEM_INDENT}<li><time>{shown}</time>'
            f'<a href="articles/{slug}.html">{text}</a></li>'
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
    pending = []                  # (src, slug, series key, extra pandoc args)
    members, names, newest = {}, {}, {}  # series: parts, display name, newest file
    for src in sorted(CONTENT_DIR.glob("*.md")):
        meta = read_front_matter(src)
        slug = src.stem
        skey = meta.get("series", "").strip().lower()
        if skey:  # drafts count too: marking a part as draft changes its siblings
            newest[skey] = max(newest.get(skey, 0), src.stat().st_mtime)
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
        image = meta.get("image") or first_image(src.read_text(encoding="utf-8-sig"))
        extra = page_vars(slug, title, descriptions[slug], image)
        if meta.get("toc", "").lower() in ("true", "yes", "1"):
            # the template needs the flag, "toc: true" alone gives an empty box
            extra.append("--toc")
        if skey:
            names.setdefault(skey, meta["series"].strip())
            members.setdefault(skey, []).append(
                (meta.get("part", "").strip(), date, slug, title))
        pending.append((src, slug, skey, extra))

    # order each series by "part:" if every part has one, otherwise by date
    ordered, badges = {}, {}
    series_of, part_pos = {}, {}
    for skey, rows in members.items():
        if len(rows) < 2:
            continue
        by_part = all(r[0].isdigit() for r in rows)
        rows = sorted(rows, key=lambda r: (int(r[0]) if by_part else 0, r[1], r[2]))
        ordered[skey] = [(r[2], r[3]) for r in rows]
        for n, (part_slug, _) in enumerate(ordered[skey], 1):
            badges[part_slug] = f"Part {n}/{len(rows)}"
            series_of[part_slug] = skey
            part_pos[part_slug] = n

    for src, slug, skey, extra in pending:
        dep = template_mtime
        if skey in ordered:
            # this page lists its siblings, so it must rebuild when they change
            parts = ordered[skey]
            extra = extra + ["-V", "series_nav=" + series_html(names[skey], parts, slug),
                             "-V", "series_pager=" + series_pager(parts, slug)]
            dep = max(dep, newest[skey])
        jobs.append((src, OUT_DIR / f"{slug}.html", force, dep, extra))

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

    # newest first. Within a day: A-Z by title (or series name), with the
    # parts of a series kept together and listed last part first.
    def day_order(item):
        _, slug, title = item
        skey = series_of.get(slug)
        if skey:
            return (names[skey].lower(), -part_pos[slug])
        return (title.lower(), 0)

    items.sort(key=day_order)
    items.sort(key=lambda r: r[0], reverse=True)

    splice(INDEX, render_items(items[:INDEX_LIMIT], badges=badges))

    if ARCHIVE.exists():
        year_of = lambda it: it[0][:4] if it[0][:4] != "0000" else None
        splice(ARCHIVE, render_items(items, year_of, badges))
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

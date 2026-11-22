"""Build articles/*.html from articles_md/*.md and docs/*.html from docs_md/*.md
with Pandoc, then refresh the lists in index.html (latest INDEX_LIMIT articles),
archive.html (everything) and feed.xml (articles and docs).

Front matter per article:
    ---
    title: Chess in Odin
    description: Short summary for the meta tag.
    date: 2026-09-12        (YYYY-MM-DD, newest first)
    draft: true             (optional, skips the article)
    toc: true               (optional, adds a table of contents)
    series: Chess in Odin   (optional, lists the parts at the top of each one)
    part: 2                 (optional, order inside a series; default is by date)
    source: link            (optional, link to source code)
    image: ../res/cover.png (optional, link preview image; default is the
                             first image in the article, then OG_IMAGE)
    ---

Front matter per doc:
    ---
    title: Getting started
    description: Short summary for the meta tag.
    project: Mazes          (optional, groups docs; the pages of a project list each other)
    order: 1                (optional, position inside the project; default is by title)
    version: v0.1           (optional, shown under the title)
    updated: 2026-11-22     (optional, shown under the title; also the date in
                             feed.xml, docs without it stay out of the feed)
    source: link            (optional, link to source code)
    toc: false              (optional, the table of contents is on by default)
    draft: true             (optional, skips the doc)
    ---

Usage:
    python build.py
    python build.py --force
"""
import html
import re
import shutil
import subprocess
import sys
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

# --- Settings -------------------------------------------------------------

SITE_URL = "https://theyordanos.github.io"
SITE_TITLE = "Yordanos"
SITE_AUTHOR = "Yordanos Z."

INDEX_LIMIT = 50
FEED_LIMIT = 50

ARTICLE_OG_IMAGE = "res/article_og.png"
DOCS_OG_IMAGE = "res/docs_og.png"
NOT_PREVIEW = (".mp4", ".webm", ".mov", ".mp3", ".ogg", ".wav", ".m4a", ".svg")

PANDOC_EXTRA = [
    # "--highlight-style=pygments",
]

# --- Paths ----------------------------------------------------------------

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent

ARTICLES_SRC = ROOT / "articles_md"
ARTICLES_OUT = ROOT / "articles"
ARTICLES_TEMPLATE = ARTICLES_OUT / "template.txt"

DOCS_SRC = ROOT / "docs_md"
DOCS_OUT = ROOT / "docs"
DOCS_TEMPLATE = DOCS_OUT / "template.txt"

FILTERS = ROOT / "filters.lua"
INDEX = ROOT / "index.html"
ARCHIVE = ROOT / "archive.html"
FEED = ROOT / "feed.xml"

# --- Markers in index.html / archive.html ---------------------------------

ARTICLES_START = "<!-- ARTICLES:START -->"
ARTICLES_END = "<!-- ARTICLES:END -->"
DOCS_START = "<!-- DOCS:START -->"
DOCS_END = "<!-- DOCS:END -->"
LIST_INDENT = "\t\t\t\t"

UNDATED = "0000-00-00"
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


# --- Data -----------------------------------------------------------------

@dataclass(eq=False)
class Article:
    src: Path
    slug: str
    title: str
    date: str
    description: str
    meta: dict
    series_key: str = ""
    series_name: str = ""
    part: str = ""
    series: Optional["Series"] = None


@dataclass(eq=False)
class Series:
    key: str
    name: str
    parts: list
    numbers: dict
    newest: float

    def links(self):
        return [(a.slug, a.title) for a in self.parts]


@dataclass(eq=False)
class Doc:
    src: Path
    slug: str
    title: str
    description: str
    meta: dict
    project: str
    order: int
    updated: str

    @property
    def project_key(self):
        return self.project.lower()

    @property
    def project_name(self):
        return self.project or "General"


@dataclass(eq=False)
class DocProject:
    key: str
    name: str
    pages: list
    newest: float


Entry = namedtuple("Entry", "date article series")

Job = namedtuple("Job", "src out template args stale_after")

FeedEntry = namedtuple("FeedEntry", "date url title summary")


# --- Small helpers --------------------------------------------------------

def fail(msg):
    print(f"error: {msg}")
    sys.exit(1)


def newest_mtime(*paths):
    return max(p.stat().st_mtime for p in paths)


def is_draft(meta):
    return meta.get("draft", "").lower() in ("true", "yes", "1")


def write_if_changed(path, text):
    old = path.read_bytes().decode("utf-8") if path.exists() else None
    if text != old:
        path.write_bytes(text.encode("utf-8"))


def remove_stale_pages(out_dir, keep, label):
    for old in out_dir.glob("*.html"):
        if old.stem not in keep:
            old.unlink()
            print(f"remove {label}/{old.name}")


def read_front_matter(path):
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


def first_image(text):
    text = re.sub(r"^(`{3,}|~{3,}).*?^\1", "", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"`[^`\n]*`", "", text)
    for m in re.finditer(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)", text):
        path = m.group(1)
        if not path.lower().split("?")[0].endswith(NOT_PREVIEW):
            return path
    return ""


# --- Pandoc arguments and small HTML pieces -------------------------------

def preview_args(folder, slug, title, description, image="", fallback=ARTICLE_OG_IMAGE):
    page_url = f"{SITE_URL}/{folder}/{slug}.html"
    values = {
        "og_title": title,
        "og_description": description,
        "og_url": page_url,
        "og_image": urljoin(page_url, image) if image else f"{SITE_URL}/{fallback}",
        "og_site": SITE_TITLE,
    }
    args = []
    for key, value in values.items():
        if value:
            args += ["-V", f"{key}={html.escape(value, quote=True)}"]
    return args


def source_html(url):
    shown = re.sub(r"^https?://", "", url).rstrip("/")
    return (f'<p class="source"><span class="source-label">Source</span>'
            f'<a href="{html.escape(url, quote=True)}" rel="noopener">'
            f'{html.escape(shown)}</a></p>')


def page_args(folder, slug, title, description, meta, markdown, fallback=ARTICLE_OG_IMAGE):
    image = meta.get("image") or first_image(markdown)
    args = preview_args(folder, slug, title, description, image, fallback)
    source = meta.get("source", "").strip()
    if source:
        if not re.match(r"https?://", source):
            print(f"warning: {folder}/{slug} source '{source}' is not an http(s) URL")
        args += ["-V", "source_link=" + source_html(source)]
    return args


def series_nav_html(series, current):
    items = []
    for a in series.parts:
        title = html.escape(a.title)
        value = f' value="{series.numbers[a.slug]}"'
        if a is current:
            items.append(f'<li{value} aria-current="page">{title}</li>')
        else:
            items.append(f'<li{value}><a href="{a.slug}.html">{title}</a></li>')
    return (f'<nav class="series" aria-label="Series">'
            f'<p class="series-title">Series: {html.escape(series.name)}</p>'
            f'<ol>{"".join(items)}</ol></nav>')


def pager_html(links, current_slug):
    slugs = [slug for slug, _ in links]
    i = slugs.index(current_slug)
    boxes = []
    if i > 0:
        slug, title = links[i - 1]
        boxes.append(f'<a class="prev" rel="prev" href="{slug}.html">'
                     f'<span class="pager-label">Previous</span>'
                     f'<span class="pager-title">{html.escape(title)}</span></a>')
    if i < len(links) - 1:
        slug, title = links[i + 1]
        boxes.append(f'<a class="next" rel="next" href="{slug}.html">'
                     f'<span class="pager-label">Next</span>'
                     f'<span class="pager-title">{html.escape(title)}</span></a>')
    return ('<nav class="series-pager" aria-label="Series navigation">'
            + "".join(boxes) + '</nav>')


def docs_nav_html(project, current):
    items = []
    for doc in project.pages:
        title = html.escape(doc.title)
        mark = ' aria-current="page"' if doc is current else ""
        items.append(f'<li><a href="{doc.slug}.html"{mark}>{title}</a></li>')
    name = html.escape(project.name)
    return (f'<nav class="docs-pages" aria-label="{name} documentation">'
            f'<p class="side-label">{name}</p><ul>{"".join(items)}</ul></nav>')


# --- Pandoc ---------------------------------------------------------------

def is_up_to_date(job):
    if not job.out.exists():
        return False
    return job.out.stat().st_mtime >= max(job.src.stat().st_mtime, job.stale_after)


def convert(job, force):
    if not force and is_up_to_date(job):
        return job.src, "ok", ""
    result = subprocess.run(
        ["pandoc", str(job.src), "--from", "markdown", "--to", "html5",
         "--template", str(job.template),
         "--lua-filter", str(FILTERS),
         *job.args, "-o", str(job.out), *PANDOC_EXTRA],
        capture_output=True,
    )
    if result.returncode != 0:
        return job.src, "failed", result.stderr.decode("utf-8", "replace")
    return job.src, "built", ""


def run_jobs(jobs, force, label):
    built = errors = 0
    with ThreadPoolExecutor() as pool:
        for src, status, err in pool.map(lambda job: convert(job, force), jobs):
            if status == "built":
                built += 1
                print(f"built  {label}/{src.stem}.html")
            elif status == "failed":
                errors += 1
                print(f"error: pandoc failed on {src.name}\n{err}")
    return built, errors


# --- Articles -------------------------------------------------------------

def collect_articles():
    articles, series_newest = [], {}
    for src in sorted(ARTICLES_SRC.glob("*.md")):
        meta = read_front_matter(src)
        slug = src.stem
        key = meta.get("series", "").strip().lower()
        if key:
            series_newest[key] = max(series_newest.get(key, 0), src.stat().st_mtime)
        if is_draft(meta):
            print(f"skip   articles/{slug} [draft]")
            continue

        date = meta.get("date", "")
        if not date:
            print(f"warning: articles/{slug} has no date; it will sort last")
            date = UNDATED
        title = meta.get("title", "")
        if not title:
            print(f"warning: articles/{slug} has no title; using filename")
            title = slug

        articles.append(Article(
            src=src, slug=slug, title=title, date=date, meta=meta,
            description=meta.get("description", ""),
            series_key=key, series_name=meta.get("series", "").strip(),
            part=meta.get("part", "").strip(),
        ))
    return articles, series_newest


def link_series(articles, series_newest):
    groups = {}
    for a in articles:
        if a.series_key:
            groups.setdefault(a.series_key, []).append(a)

    for key, parts in groups.items():
        if len(parts) < 2:
            continue
        name = parts[0].series_name
        by_part = all(a.part.isdigit() for a in parts)
        parts.sort(key=lambda a: (int(a.part) if by_part else 0, a.date, a.slug))
        numbers = {a.slug: int(a.part) if by_part else n
                   for n, a in enumerate(parts, 1)}
        series = Series(key, name, parts, numbers, series_newest[key])
        for a in parts:
            a.series = series


def build_articles(articles, force):
    ARTICLES_OUT.mkdir(exist_ok=True)
    shared_mtime = newest_mtime(ARTICLES_TEMPLATE, FILTERS, SCRIPT)

    jobs = []
    for a in articles:
        args = page_args("articles", a.slug, a.title, a.description, a.meta,
                         a.src.read_text(encoding="utf-8-sig"))
        if a.meta.get("toc", "").lower() in ("true", "yes", "1"):
            # the template needs the flag, "toc: true" alone gives an empty box
            args.append("--toc")
        stale_after = shared_mtime
        if a.series:
            # this page lists its siblings, so it must rebuild when they change
            args += ["-V", "series_nav=" + series_nav_html(a.series, a),
                     "-V", "series_pager=" + pager_html(a.series.links(), a.slug)]
            stale_after = max(stale_after, a.series.newest)
        jobs.append(Job(a.src, ARTICLES_OUT / f"{a.slug}.html",
                        ARTICLES_TEMPLATE, args, stale_after))

    remove_stale_pages(ARTICLES_OUT, {a.slug for a in articles}, "articles")
    return run_jobs(jobs, force, "articles")


def sort_newest_first(articles):
    def within_day(a):
        if a.series:
            return (a.series.name.lower(), -a.series.parts.index(a))
        return (a.title.lower(), 0)

    articles.sort(key=within_day)
    articles.sort(key=lambda a: a.date, reverse=True)


def collapse_series(articles):
    # articles must be sorted newest first: a series appears once, at its latest part
    entries, seen = [], set()
    for a in articles:
        if a.series is None:
            entries.append(Entry(a.date, a, None))
        elif a.series.key not in seen:
            seen.add(a.series.key)
            entries.append(Entry(a.date, None, a.series))
    return entries


# --- Docs -----------------------------------------------------------------

def collect_docs():
    docs, project_newest = [], {}
    for src in sorted(DOCS_SRC.glob("*.md")):
        meta = read_front_matter(src)
        slug = src.stem
        project = meta.get("project", "").strip()
        key = project.lower()
        project_newest[key] = max(project_newest.get(key, 0), src.stat().st_mtime)
        if is_draft(meta):
            print(f"skip   docs/{slug} [draft]")
            continue

        title = meta.get("title", "")
        if not title:
            print(f"warning: docs/{slug} has no title; using filename")
            title = slug
        order = meta.get("order", "").strip()
        docs.append(Doc(
            src=src, slug=slug, title=title, meta=meta, project=project,
            description=meta.get("description", ""),
            order=int(order) if re.fullmatch(r"-?\d+", order) else 10**6,
            updated=meta.get("updated", ""),
        ))
    return docs, project_newest


def group_docs(docs, project_newest):
    projects = {}
    for d in docs:
        p = projects.setdefault(
            d.project_key,
            DocProject(d.project_key, d.project_name, [], project_newest[d.project_key]))
        p.pages.append(d)
    for p in projects.values():
        p.pages.sort(key=lambda d: (d.order, d.title.lower()))
    return sorted(projects.values(), key=lambda p: p.name.lower())


def build_docs(projects, force):
    DOCS_OUT.mkdir(exist_ok=True)
    shared_mtime = newest_mtime(DOCS_TEMPLATE, FILTERS, SCRIPT)

    jobs, slugs = [], set()
    for project in projects:
        links = [(d.slug, d.title) for d in project.pages]
        # pages of a project list each other, so they rebuild together
        stale_after = max(shared_mtime, project.newest)
        for d in project.pages:
            args = page_args("docs", d.slug, d.title, d.description, d.meta,
                             d.src.read_text(encoding="utf-8-sig"), DOCS_OG_IMAGE)
            if d.meta.get("toc", "true").lower() not in ("false", "no", "0"):
                args += ["--toc", "--toc-depth=3"]
            args += ["-V", "docs_nav=" + docs_nav_html(project, d)]
            if len(links) > 1:
                args += ["-V", "docs_pager=" + pager_html(links, d.slug)]
            jobs.append(Job(d.src, DOCS_OUT / f"{d.slug}.html",
                            DOCS_TEMPLATE, args, stale_after))
            slugs.add(d.slug)

    remove_stale_pages(DOCS_OUT, slugs, "docs")
    return run_jobs(jobs, force, "docs")


# --- index.html / archive.html lists --------------------------------------

def render_entries(entries, year_heading=None):
    lines, last_heading = [], None
    for entry in entries:
        heading = year_heading(entry.date) if year_heading else None
        if heading and heading != last_heading:
            lines.append(f'{LIST_INDENT}<li class="year">{html.escape(heading)}</li>')
            last_heading = heading
        shown = "" if entry.date[:4] == "0000" else entry.date
        if entry.series:
            lines += render_series(entry.series, shown)
        else:
            a = entry.article
            lines.append(f'{LIST_INDENT}<li><time>{shown}</time>'
                         f'<a href="articles/{a.slug}.html">{html.escape(a.title)}</a></li>')
    return lines


def render_series(series, shown_date):
    i = LIST_INDENT
    lines = [
        f'{i}<li class="series-group"><time>{shown_date}</time>',
        f'{i}\t<div class="series-block">',
        f'{i}\t\t<span class="series-name">{html.escape(series.name)}</span>'
        f'<span class="series-count">{len(series.parts)} parts</span>',
        f'{i}\t\t<ul class="parts">',
    ]
    for a in series.parts:
        lines.append(f'{i}\t\t\t<li><span class="part-no">Part {series.numbers[a.slug]}</span>'
                     f'<a href="articles/{a.slug}.html">{html.escape(a.title)}</a></li>')
    lines += [f'{i}\t\t</ul>', f'{i}\t</div>', f'{i}</li>']
    return lines


def render_docs(projects, show_dates=False):
    i = LIST_INDENT
    if not projects:
        return [f'{i}<li class="doc-empty">No docs yet.</li>']
    lines = []
    for p in projects:
        count = f'{len(p.pages)} page{"" if len(p.pages) == 1 else "s"}'
        lines.append(f'{i}<li class="doc-project">')
        lines.append(f'{i}\t<a class="doc-project-name" href="docs/{p.pages[0].slug}.html">'
                     f'{html.escape(p.name)}</a><span class="doc-count">{count}</span>')
        lines.append(f'{i}\t<ul class="doc-pages">')
        for d in p.pages:
            when = f'<time>{html.escape(d.updated)}</time>' if show_dates and d.updated else ""
            lines.append(f'{i}\t\t<li><a href="docs/{d.slug}.html">'
                         f'{html.escape(d.title)}</a>{when}</li>')
        lines.append(f'{i}\t</ul>')
        lines.append(f'{i}</li>')
    return lines


def year_heading(date):
    return None if date[:4] == "0000" else date[:4]


def splice(path, lines, start=ARTICLES_START, end=ARTICLES_END, required=True):
    data = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in data else "\n"

    start_at = data.find(start)
    end_at = data.find(end)
    if start_at < 0 or end_at < 0 or end_at < start_at:
        if not required:
            print(f"note: {path.name} has no {start} / {end} lines; list not updated")
            return
        fail(f"{path.name} needs these two lines inside the list:\n"
             f"  {start}\n  {end}")

    line_start = data.rfind("\n", 0, end_at) + 1
    indent = data[line_start:end_at] if line_start > start_at else ""
    if indent.strip():
        indent = ""

    body = newline.join(lines) + newline if lines else ""
    new = data[: start_at + len(start)] + newline + body + indent + data[end_at:]
    write_if_changed(path, new)


# --- feed.xml -------------------------------------------------------------

def collect_feed_entries(articles, docs):
    entries = []
    for a in articles:
        if a.date == UNDATED:
            continue
        if DATE_RE.fullmatch(a.date):
            entries.append(FeedEntry(a.date, f"{SITE_URL}/articles/{a.slug}.html",
                                     a.title, a.description))
        else:
            print(f"warning: articles/{a.slug} date '{a.date}' is not YYYY-MM-DD; "
                  f"left out of feed.xml")

    undated_docs = []
    for d in docs:
        if not d.updated:
            undated_docs.append(f"docs/{d.slug}")
        elif DATE_RE.fullmatch(d.updated):
            title = f"{d.project}: {d.title}" if d.project else d.title
            entries.append(FeedEntry(d.updated, f"{SITE_URL}/docs/{d.slug}.html",
                                     title, d.description))
        else:
            print(f"warning: docs/{d.slug} updated '{d.updated}' is not YYYY-MM-DD; "
                  f"left out of feed.xml")
    if undated_docs:
        print(f"note: {len(undated_docs)} doc(s) have no 'updated:' date and are left "
              f"out of feed.xml: {', '.join(undated_docs)}")

    entries.sort(key=lambda e: e.date, reverse=True)
    return entries[:FEED_LIMIT]


def write_feed(entries):
    esc = html.escape
    updated = f"{entries[0].date}T00:00:00Z" if entries else "1970-01-01T00:00:00Z"
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
    for e in entries:
        out += [
            "<entry>",
            f"<title>{esc(e.title)}</title>",
            f'<link href="{e.url}"/>',
            f"<id>{e.url}</id>",
            f"<updated>{e.date}T00:00:00Z</updated>",
        ]
        if e.summary:
            out.append(f"<summary>{esc(e.summary)}</summary>")
        out.append("</entry>")
    out.append("</feed>")

    write_if_changed(FEED, "\n".join(out) + "\n")
    return len(entries)


# --- Main -----------------------------------------------------------------

def check_requirements():
    if not shutil.which("pandoc"):
        fail("pandoc not found. Install it, then open a NEW terminal window.")
    for path in (ARTICLES_TEMPLATE, FILTERS, INDEX):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")
    if not ARTICLES_SRC.is_dir():
        fail(f"missing {ARTICLES_SRC.relative_to(ROOT)}")


def main():
    force = "--force" in sys.argv or "-f" in sys.argv
    check_requirements()

    articles, series_newest = collect_articles()
    link_series(articles, series_newest)
    built, errors = build_articles(articles, force)
    if errors:
        sys.exit(1)

    docs, projects, docs_built = [], [], 0
    docs_on = DOCS_SRC.is_dir()
    if docs_on:
        if not DOCS_TEMPLATE.exists():
            fail(f"missing {DOCS_TEMPLATE.relative_to(ROOT)}")
        docs, project_newest = collect_docs()
        projects = group_docs(docs, project_newest)
        docs_built, doc_errors = build_docs(projects, force)
        if doc_errors:
            sys.exit(1)

    sort_newest_first(articles)
    entries = collapse_series(articles)

    splice(INDEX, render_entries(entries[:INDEX_LIMIT]))
    if ARCHIVE.exists():
        splice(ARCHIVE, render_entries(entries, year_heading))
        archive_note = "archive.html updated"
    else:
        archive_note = "archive.html not found, skipped"

    if docs_on:
        splice(INDEX, render_docs(projects), DOCS_START, DOCS_END, required=False)
        if ARCHIVE.exists():
            splice(ARCHIVE, render_docs(projects, show_dates=True),
                   DOCS_START, DOCS_END, required=False)

    feed_count = write_feed(collect_feed_entries(articles, docs))
    if "example.com" in SITE_URL:
        print("warning: SITE_URL in build.py is still the placeholder; "
              "feed links will be wrong until you set it")

    docs_note = (f"docs: {len(docs)} page(s), {docs_built} rebuilt"
                 if docs_on else "no docs_md/")
    print(f"done: {len(articles)} article(s), {built} rebuilt, "
          f"index.html shows {min(len(entries), INDEX_LIMIT)} entries, {archive_note}, "
          f"feed.xml has {feed_count}, {docs_note}")


if __name__ == "__main__":
    main()

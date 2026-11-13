#!/usr/bin/env bash
# Builds articles/*.html from articles_md/*.md with Pandoc, then regenerates
# the article list inside index.html (between the ARTICLES markers).
#
# Front matter per article:
#   ---
#   title: Chess in Odin
#   description: Short summary for the meta tag.
#   date: 2026-09-12        # YYYY-MM-DD, used for sorting (newest first)
#   draft: true             # optional, skips the article entirely
#   ---

[ -n "${BASH_VERSION:-}" ] || { echo "error: run this with bash (./build.sh or bash build.sh), not sh/zsh" >&2; exit 1; }

set -euo pipefail
cd "$(dirname "$0")"

CONTENT_DIR="articles_md"
OUT_DIR="articles"
TEMPLATE="articles/template.txt"
INDEX="index.html"
START_MARK="<!-- ARTICLES:START -->"
END_MARK="<!-- ARTICLES:END -->"

# ---- checks ---------------------------------------------------------------
command -v pandoc >/dev/null || { echo "error: pandoc not found" >&2; exit 1; }
[ -f "$TEMPLATE" ] || { echo "error: missing $TEMPLATE" >&2; exit 1; }
[ -f "$INDEX" ]    || { echo "error: missing $INDEX" >&2; exit 1; }
grep -qF "$START_MARK" "$INDEX" && grep -qF "$END_MARK" "$INDEX" || {
	echo "error: $INDEX needs these two lines inside the <ul> of the articles section:" >&2
	echo "  $START_MARK" >&2
	echo "  $END_MARK" >&2
	exit 1
}

mkdir -p "$OUT_DIR"

# Everything in $OUT_DIR is generated, so start clean (removes stale articles)
rm -f "$OUT_DIR"/*.html

# ---- temp files -----------------------------------------------------------
META_TPL="$(mktemp)"
ITEMS="$(mktemp)"
LIST="$(mktemp)"
NEW_INDEX="$(mktemp)"
trap 'rm -f "$META_TPL" "$ITEMS" "$LIST" "$NEW_INDEX"' EXIT

# Tiny Pandoc template that prints: status|date|title (title is HTML-escaped)
printf '%s' '$if(draft)$draft$else$ok$endif$|$date$|$title$' > "$META_TPL"

# ---- build each article ---------------------------------------------------
count=0
for f in "$CONTENT_DIR"/*.md; do
	[ -e "$f" ] || continue   # no .md files yet: the glob stays literal
	slug="$(basename "${f%.md}")"

	# The metadata template has no trailing newline, so feed it through a
	# here-string (which adds one). Reading it straight from pandoc made `read`
	# return non-zero at EOF and `set -e` ended the script silently.
	meta="$(pandoc "$f" -t html --template="$META_TPL" | tr -d '\r')"
	IFS='|' read -r status date title <<< "$meta"

	if [ "$status" = "draft" ]; then
		echo "skip   $slug (draft)"
		continue
	fi
	if [ -z "$title" ]; then
		echo "warn:  $f has no title, using filename" >&2
		title="$slug"
	fi
	if [ -z "$date" ]; then
		echo "warn:  $f has no date, it will sort last" >&2
		date="0000-00-00"
	fi

	pandoc "$f" \
		--from markdown \
		--to html5 \
		--template="$TEMPLATE" \
		-o "$OUT_DIR/$slug.html"

	printf '%s|%s|%s\n' "$date" "$slug" "$title" >> "$ITEMS"
	echo "built  $OUT_DIR/$slug.html"
	count=$((count + 1))
done

# ---- generate the list (newest first) -------------------------------------
sort -r "$ITEMS" | while IFS='|' read -r date slug title; do
	printf '\t\t\t\t<li><a href="%s/%s.html">%s</a></li>\n' "$OUT_DIR" "$slug" "$title"
done > "$LIST"

# ---- splice the list into index.html between the markers ------------------
awk -v start="$START_MARK" -v end="$END_MARK" -v listfile="$LIST" '
	index($0, start) {
		print
		while ((getline line < listfile) > 0) print line
		skipping = 1
		next
	}
	index($0, end) { skipping = 0 }
	!skipping { print }
' "$INDEX" > "$NEW_INDEX"

cat "$NEW_INDEX" > "$INDEX"

echo "done: $count article(s), $INDEX updated"

-- Footnotes to Sidenotes
local n = 0

function Note(note)
  n = n + 1
  local id = "sn-" .. n

  local out = {
    pandoc.RawInline("html",
      '<label for="' .. id .. '" class="sidenote-number"></label>' ..
      '<input type="checkbox" id="' .. id .. '" class="margin-toggle">' ..
      '<span class="sidenote">')
  }
  for _, inline in ipairs(pandoc.utils.blocks_to_inlines(note.content)) do
    table.insert(out, inline)
  end
  table.insert(out, pandoc.RawInline("html", "</span>"))

  return out
end

-- Adds a small "#" link after every heading from level 2 down.
function Header(h)
	if h.level >= 2 and h.identifier ~= "" then
		h.content:insert(pandoc.Space())
		h.content:insert(pandoc.Link(
			{pandoc.Span({pandoc.Str("#")}, pandoc.Attr("", {"anchor-mark"}))},
			"#" .. h.identifier, "",
			{class = "anchor", ["aria-label"] = "Link to this section"}))
	end
	return h
end

local function escape(text)
	return (text:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function file_id(name)
	local id = name:lower():gsub("[^%w]+", "-")
	id = id:gsub("^%-+", ""):gsub("%-+$", "")
	return "file-" .. id
end

local function url_encode(text)
	return (text:gsub("[^%w%-%._~/]", function(c)
		return string.format("%%%02X", c:byte())
	end))
end

local gist_slug, gist_language = "", ""

local function read_meta(doc)
	local function text(key)
		return doc.meta[key] and pandoc.utils.stringify(doc.meta[key]) or ""
	end
	gist_slug = text("gist_slug")
	gist_language = text("language")
end

function CodeBlock(block)
	local name = block.attributes["file"]
	if not name or name == "" then return nil end

	local _, breaks = block.text:gsub("\n", "")
	local count = breaks + 1
	local numbers = {}
	for i = 1, count do numbers[i] = tostring(i) end

	local label = block.attributes["label"] or gist_language
	local info = count .. (count == 1 and " line" or " lines")
	if label ~= "" then
		info = escape(label) .. " \u{00B7} " .. info
	end

	local raw = ""
	if gist_slug ~= "" then
		local base = name:gsub("\\", "/"):match("[^/]+$") or name
		local href = "raw/" .. url_encode(gist_slug) .. "/" .. url_encode(base)
		raw = '<a class="gist-btn" href="' .. href .. '">Raw</a>'
	end

	local open = '<figure class="gist-file" id="' .. file_id(name) .. '">'
		.. '<figcaption><span class="gist-name">' .. escape(name) .. '</span>'
		.. '<span class="gist-info">' .. info .. '</span>' .. raw .. '</figcaption>'
		.. '<div class="gist-code"><pre class="gist-gutter" aria-hidden="true">'
		.. table.concat(numbers, "\n") .. '</pre>'

	return {
		pandoc.RawBlock("html", open),
		pandoc.CodeBlock(block.text, pandoc.Attr("", block.classes)),
		pandoc.RawBlock("html", "</div></figure>"),
	}
end

return {
	{ Pandoc = read_meta },
	{ Note = Note, Header = Header, CodeBlock = CodeBlock },
}

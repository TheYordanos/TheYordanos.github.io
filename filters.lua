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

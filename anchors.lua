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

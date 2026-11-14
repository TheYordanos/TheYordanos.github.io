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

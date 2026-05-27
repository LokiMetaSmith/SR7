-- multcols.lua
-- Wraps the document in \begin{multicols}{2} ... \end{multicols}
-- Breaks out of multicols around tables.

function Pandoc(doc)
    local blocks = doc.blocks
    local new_blocks = {}
    local in_multicols = false

    local begin_multicols = pandoc.RawBlock('latex', '\\begin{multicols}{2}')
    local end_multicols = pandoc.RawBlock('latex', '\\end{multicols}')

    -- Start with multicols
    table.insert(new_blocks, begin_multicols)
    in_multicols = true

    for _, block in ipairs(blocks) do
        if block.t == 'Table' then
            if in_multicols then
                table.insert(new_blocks, end_multicols)
                in_multicols = false
            end
            table.insert(new_blocks, block)
        else
            if not in_multicols then
                table.insert(new_blocks, begin_multicols)
                in_multicols = true
            end
            table.insert(new_blocks, block)
        end
    end

    if in_multicols then
        table.insert(new_blocks, end_multicols)
    end

    return pandoc.Pandoc(new_blocks, doc.meta)
end

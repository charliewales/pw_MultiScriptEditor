def apply_multiline_highlighting(
    highlighter,
    text,
    delimiter,
    in_state,
    style,
):
    """Apply a multiline format and return whether the block remains open."""
    if highlighter.previousBlockState() == in_state:
        start = 0
        delimiter_length = 0
    else:
        match = delimiter.search(text)
        start = match.start() if match else -1
        delimiter_length = match.end() - match.start() if match else 0

    while start >= 0:
        match = delimiter.search(text, start + delimiter_length)
        end = match.start() if match else -1
        match_length = match.end() - match.start() if match else 0

        if end >= 0:
            length = end - start + match_length
            highlighter.setCurrentBlockState(0)
        else:
            highlighter.setCurrentBlockState(in_state)
            length = len(text) - start

        highlighter.setFormat(start, length, style)

        match = delimiter.search(text, start + length)
        start = match.start() if match else -1
        delimiter_length = match.end() - match.start() if match else 0

    return highlighter.currentBlockState() == in_state

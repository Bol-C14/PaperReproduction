"""Versioned metadata-only EDIF text screen; never an equivalence checker."""
import re

# Exact known top-level header shape only. No comments/properties/names removed.
HEADER = re.compile(
    rb"(?m)^\(status[ \t]*\r?\n[ \t]+\(written[ \t]*\r?\n"
    rb"[ \t]+(?P<timestamp>\(timeStamp [0-9]{4} [0-9]{1,2} [0-9]{1,2} "
    rb"[0-9]{1,2} [0-9]{1,2} [0-9]{1,2}\))(?=[ \t]*\r?\n)"
)


def canonicalize_timestamp_v1(text):
    if not text.startswith(b"(edif "):
        raise ValueError("Require decoded EDIF text")
    matches = list(HEADER.finditer(text))
    if len(matches) != 1:
        raise ValueError("Require exactly one known status/written header")
    match = matches[0]
    start, end = match.span("timestamp")
    # Status must precede library and design content; ambiguous/unknown shape fails closed.
    body_starts = [p for token in (b"(library ", b"(external ", b"(design ")
                   if (p := text.find(token)) >= 0]
    if not body_starts or end >= min(body_starts):
        raise ValueError("Header not before netlist body")
    return text[:start] + b"(timeStamp REMOVED_METADATA_V1)" + text[end:]

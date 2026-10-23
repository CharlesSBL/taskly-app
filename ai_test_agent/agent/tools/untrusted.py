"""Wrap repository content so the model cannot mistake it for instructions.

The system prompt tells the model that everything inside
`<untrusted_source_data>` is data. A file could try to close that tag early,
so any occurrence of the closing tag is escaped before wrapping.
"""

from __future__ import annotations

OPEN_TAG = "<untrusted_source_data>"
CLOSE_TAG = "</untrusted_source_data>"
ESCAPED_CLOSE_TAG = "&lt;/untrusted_source_data&gt;"


def escape_untrusted(text: str) -> str:
    return text.replace(CLOSE_TAG, ESCAPED_CLOSE_TAG)


def wrap_untrusted(text: str, source: str) -> str:
    safe_source = escape_untrusted(source).replace('"', "&quot;")
    return f'<untrusted_source_data source="{safe_source}">\n{escape_untrusted(text)}\n{CLOSE_TAG}'

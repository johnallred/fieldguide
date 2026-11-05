"""Give the `summary` front-matter field three readers instead of none.

Every page in this guide carries a one-line `summary`. Before this hook it was
read by nothing:

* It is front matter, so the search plugin never saw it. Measured: 83 pages
  whose summary text could not be found in the site's own search index.
* It is not in the page body, so no reader ever saw it either.
* Material falls back to `site_description` for the meta description unless a
  page sets `description`, so search engines did not see it.

A field written on 121 pages and consumed by nobody is the defect the
`metadata` and `taxonomy` pages are about, sitting in this repository while
those pages described it. This hook makes the one field feed all three: the
rendered page, the search index, and the meta description.

`on_page_markdown` rather than a later event, because the summary has to be in
the Markdown for the search plugin to index it.
"""

from __future__ import annotations

import re

# The generated placeholder pages open with their own admonition and already
# say what they are, so a lead paragraph there would be noise.
PLACEHOLDER = "placeholder"

# A concept page opens with "# Title" then a metadata line such as
# "`core` · difficulty 3 · 5h". The lead belongs after the title.
TITLE = re.compile(r"^(#\s+.+?\n)", re.M)


def on_page_markdown(markdown: str, page, config, files) -> str:
    summary = page.meta.get("summary")
    if not summary or page.meta.get("diataxis") == PLACEHOLDER:
        return markdown
    if page.meta.get("generated"):
        return markdown

    match = TITLE.search(markdown)
    if not match:
        return markdown

    # Italic, so it reads as a standfirst rather than as body prose.
    lead = f"\n*{summary.strip()}*\n"
    at = match.end()
    if markdown[at : at + len(lead)] == lead:
        return markdown
    return markdown[:at] + lead + markdown[at:]


def on_page_context(context, page, config, nav):
    """Also use the summary as the meta description, which Material will not."""
    summary = page.meta.get("summary")
    if summary and not page.meta.get("description"):
        page.meta["description"] = summary
    return context

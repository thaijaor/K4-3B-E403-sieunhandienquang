"""Load locally authored Markdown with explicit, stable citation anchors.

Supported demo format: one H1 title, H2 headings with {#anchor}, paragraphs
and unordered lists. Raw HTML is displayed as text by the client.
"""
import json
import re
from pathlib import Path


def load_lessons(manifest_path):
    manifest_path = Path(manifest_path)
    lessons = json.loads(manifest_path.read_text(encoding="utf-8"))
    for lesson in lessons:
        path = (manifest_path.parent / lesson["markdown"]).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()) or path.suffix != ".md":
            raise ValueError("Markdown must be inside the manifest directory")
        text = path.read_text(encoding="utf-8")
        headings = list(re.finditer(r"^## (.+?) \{#([a-z0-9-]+)\}\s*$", text, re.M))
        if not headings:
            raise ValueError("Markdown needs explicit H2 citation anchors")
        lesson["sources"] = []
        for index, match in enumerate(headings):
            title, anchor = match.groups()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            body = text[match.end():end].strip()
            lesson["sources"].append({"id": f"{lesson['id']}--{anchor}", "kind": "markdown",
                                      "locator": f"{lesson['markdown']}#{anchor}", "anchor": anchor,
                                      "label": title, "title": title, "text": body})
    return lessons

"""Đọc manifest bài học. Quy ước source phải giữ khớp codebase/app/lessons.py:
id = lesson_id + "--" + anchor, locator = markdown + "#" + anchor, mỗi H2 `## Tên {#anchor}` là một đoạn."""
import json
import re
from pathlib import Path

HEADING = re.compile(r"^## (.+?)(?:\s+\{#([a-z0-9-]+)\})?\s*$", re.M)


def load_lessons(manifest_path):
    manifest_path = Path(manifest_path)
    lessons = json.loads(manifest_path.read_text(encoding="utf-8"))
    for lesson in lessons:
        path = (manifest_path.parent / lesson["markdown"]).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()) or path.suffix != ".md":
            raise ValueError("Markdown must be inside the manifest directory")
        text = path.read_text(encoding="utf-8")
        headings = list(HEADING.finditer(text))
        lesson["sources"] = []
        for index, match in enumerate(headings):
            title = match.group(1).strip()
            explicit_anchor = match.group(2)
            if explicit_anchor:
                anchor = explicit_anchor
            else:
                slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
                anchor = slug if slug else f"section-{index+1}"
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            lesson["sources"].append({"id": f"{lesson['id']}--{anchor}", "locator": f"{lesson['markdown']}#{anchor}",
                                      "title": title, "text": text[match.end():end].strip()})
    return lessons

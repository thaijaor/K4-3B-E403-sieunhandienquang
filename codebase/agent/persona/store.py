"""Lưu Persona theo học viên (SQLite). Không có version: lần ghi sau thắng.

Persona chỉ chứa điều được nhớ. Tutor tự ghi nhớ / quên bằng tool; mỗi lần đổi ghi một bản
`updates` để học viên hoàn tác đúng dòng đó. Không lưu câu phủ định kiểu "đừng nhớ X"."""
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

MAX_CHARS = 2000
MAX_LINE = 200
TUTOR_SECTIONS = ("Tính cách Tutor", "Tutor nhớ về bạn")
MEMORY_SECTION = "Tutor nhớ về bạn"
DEFAULT_TEXT = """# PERSONA — Tutor của tôi

## Tính cách Tutor
- Xưng hô: mình – bạn

## Tutor nhớ về bạn
"""


class PersonaError(ValueError):
    pass


def _section_span(text, section):
    """(start, end) của phần thân dưới heading `## section`, hoặc None."""
    match = re.search(rf"^## {re.escape(section)}[ \t]*$", text, re.M)
    if not match:
        return None
    following = re.search(r"^## ", text[match.end():], re.M)
    return match.end(), match.end() + following.start() if following else len(text)


def section_items(text, section):
    span = _section_span(text, section)
    if not span:
        return []
    return [line[2:].strip() for line in text[span[0]:span[1]].splitlines() if line.startswith("- ")]


def _key(item):
    return item.split(":", 1)[0].strip().lower() if ":" in item else None


def _rewrite(text, span, lines):
    body = "\n" + "\n".join(line for line in lines if line.strip()) + "\n\n"
    return (text[:span[0]] + body + text[span[1]:].lstrip("\n")).rstrip("\n") + "\n"


def add_item(text, section, item):
    """Thêm `- item` vào cuối mục. Dòng dạng `Khoá: giá trị` thay dòng cùng khoá thay vì thêm trùng."""
    return add_item_replacing(text, section, item)[0]


def add_item_replacing(text, section, item):
    """Như add_item, trả thêm dòng cũ bị thay (hoặc None) để hoàn tác được."""
    item = " ".join(item.split())
    span = _section_span(text, section)
    if not span:
        return text.rstrip("\n") + f"\n\n## {section}\n- {item}\n", None
    lines = text[span[0]:span[1]].strip("\n").splitlines()
    key, replaced = _key(item), None
    for index, line in enumerate(lines):
        if not line.startswith("- "):
            continue
        existing = line[2:].strip()
        if existing.lower() == item.lower():
            return text, None
        if key and _key(existing) == key:
            replaced, lines[index] = existing, f"- {item}"
            break
    else:
        lines.append(f"- {item}")
    return _rewrite(text, span, lines), replaced


def find_item(text, item):
    """(section, dòng) khớp `item`: trùng nguyên dòng, trùng khoá, hoặc chứa nhau — chỉ khi khớp duy nhất."""
    needle = " ".join(item.split()).lower()
    if not needle:
        return None
    for match in (lambda line: line.lower() == needle,
                  lambda line: _key(needle) is not None and _key(line) == _key(needle),
                  lambda line: needle in line.lower() or line.lower() in needle):
        found = [(section, line) for section in TUTOR_SECTIONS for line in section_items(text, section) if match(line)]
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            return None
    return None


def remove_item(text, section, item):
    span = _section_span(text, section)
    if not span:
        return text
    lines = text[span[0]:span[1]].strip("\n").splitlines()
    kept = [line for line in lines if not (line.startswith("- ") and line[2:].strip().lower() == item.lower())]
    return text if kept == lines else _rewrite(text, span, kept)


def clear_section(text, section):
    span = _section_span(text, section)
    if not span:
        return text
    return (text[:span[0]] + "\n\n" + text[span[1]:].lstrip("\n")).rstrip("\n") + "\n"


class PersonaStore:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS personas (learner TEXT PRIMARY KEY, text TEXT NOT NULL, updated_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS updates (
                id TEXT PRIMARY KEY, learner TEXT NOT NULL, action TEXT NOT NULL, section TEXT NOT NULL,
                item TEXT NOT NULL, replaced TEXT, status TEXT NOT NULL DEFAULT 'applied');
            """)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _view(text, updated_at):
        return {"text": text, "updated_at": time.strftime("%H:%M %d/%m/%Y", time.localtime(updated_at))}

    def _current(self, db, learner):
        row = db.execute("SELECT text, updated_at FROM personas WHERE learner=?", (learner,)).fetchone()
        return (row["text"], row["updated_at"]) if row else (DEFAULT_TEXT, time.time())

    def _write(self, db, learner, text):
        if len(text) > MAX_CHARS:
            raise PersonaError(f"Persona tối đa {MAX_CHARS} ký tự.")
        now = time.time()
        db.execute("INSERT INTO personas VALUES (?,?,?) ON CONFLICT(learner) DO UPDATE SET text=excluded.text, updated_at=excluded.updated_at",
                   (learner, text, now))
        return self._view(text, now)

    def get(self, learner):
        with self._db() as db:
            return self._view(*self._current(db, learner))

    def save(self, learner, text):
        with self._db() as db:
            return self._write(db, learner, text)

    def clear_memory(self, learner):
        with self._db() as db:
            return self._write(db, learner, clear_section(self._current(db, learner)[0], MEMORY_SECTION))

    def _record(self, db, learner, action, section, item, replaced, before, after):
        update = {"id": str(uuid.uuid4()), "action": action, "line": item, "before": before, "after": after}
        db.execute("INSERT INTO updates (id, learner, action, section, item, replaced) VALUES (?,?,?,?,?,?)",
                   (update["id"], learner, action, section, item, replaced))
        return update

    def remember(self, learner, section, item):
        """Ghi ngay một dòng. Trả bản update, hoặc None nếu không có gì đổi."""
        item = " ".join(str(item).split())
        if section not in TUTOR_SECTIONS:
            raise PersonaError(f"section phải là một trong {TUTOR_SECTIONS}.")
        if not item or len(item) > MAX_LINE:
            raise PersonaError(f"item phải là một dòng 1–{MAX_LINE} ký tự.")
        with self._db() as db:
            before = self._current(db, learner)[0]
            after, replaced = add_item_replacing(before, section, item)
            if after == before:
                return None
            self._write(db, learner, after)
            return self._record(db, learner, "remember", section, item, replaced, before, after)

    def forget(self, learner, item):
        """Xoá dòng khớp `item` (duy nhất). Trả bản update, hoặc None nếu không tìm thấy."""
        with self._db() as db:
            before = self._current(db, learner)[0]
            found = find_item(before, str(item))
            if not found:
                return None
            section, line = found
            after = remove_item(before, section, line)
            self._write(db, learner, after)
            return self._record(db, learner, "forget", section, line, None, before, after)

    def undo(self, learner, update_id):
        """Hoàn tác đúng dòng của bản update trên Persona HIỆN TẠI. Gọi lần hai trả Persona hiện tại."""
        with self._db() as db:
            row = db.execute("SELECT * FROM updates WHERE id=? AND learner=?", (update_id, learner)).fetchone()
            if not row:
                raise KeyError(update_id)
            current = self._current(db, learner)[0]
            if row["status"] != "applied":
                return self._view(*self._current(db, learner))
            if row["action"] == "remember":
                text = (add_item(current, row["section"], row["replaced"]) if row["replaced"]
                        else remove_item(current, row["section"], row["item"]))
            else:
                text = add_item(current, row["section"], row["item"])
            result = self._write(db, learner, text)
            db.execute("UPDATE updates SET status='undone' WHERE id=?", (update_id,))
            return result

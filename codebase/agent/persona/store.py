"""Lưu Persona theo học viên (SQLite). Không có version: lần ghi sau thắng."""
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

MAX_CHARS = 2000
TUTOR_SECTIONS = ("Tính cách Tutor", "Tutor nhớ về bạn")  # "Không được nhớ" chỉ học viên sửa
MEMORY_SECTION = "Tutor nhớ về bạn"
FORBIDDEN_SECTION = "Không được nhớ"
DEFAULT_TEXT = """# PERSONA — Tutor của tôi

## Tính cách Tutor
- Xưng hô: mình – bạn

## Tutor nhớ về bạn

## Không được nhớ
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


def add_item(text, section, item):
    """Thêm `- item` vào cuối mục. Dòng dạng `Khoá: giá trị` thay dòng cùng khoá thay vì thêm trùng."""
    item = " ".join(item.split())
    span = _section_span(text, section)
    if not span:
        return text.rstrip("\n") + f"\n\n## {section}\n- {item}\n"
    lines = text[span[0]:span[1]].strip("\n").splitlines()
    key = item.split(":", 1)[0].strip().lower() if ":" in item else None
    for index, line in enumerate(lines):
        if not line.startswith("- "):
            continue
        existing = line[2:].strip()
        if existing.lower() == item.lower():
            return text
        if key and ":" in existing and existing.split(":", 1)[0].strip().lower() == key:
            lines[index] = f"- {item}"
            break
    else:
        lines.append(f"- {item}")
    body = "\n" + "\n".join(line for line in lines if line.strip()) + "\n\n"
    return (text[:span[0]] + body + text[span[1]:].lstrip("\n")).rstrip("\n") + "\n"


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
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY, learner TEXT NOT NULL, section TEXT NOT NULL, item TEXT NOT NULL,
                before TEXT NOT NULL, after TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending');
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

    def propose(self, learner, section, item):
        """Tạo đề xuất pending. Trả None nếu không có gì để đổi hoặc học viên đã cấm nhớ điều này."""
        item = " ".join(str(item).split())
        if section not in TUTOR_SECTIONS or not item:
            raise PersonaError(f"section phải là một trong {TUTOR_SECTIONS}.")
        with self._db() as db:
            before = self._current(db, learner)[0]
            if any(rule and rule.lower() in item.lower() for rule in section_items(before, FORBIDDEN_SECTION)):
                return None
            after = add_item(before, section, item)
            if after == before or len(after) > MAX_CHARS:
                return None
            proposal = {"id": str(uuid.uuid4()), "before": before, "after": after}
            db.execute("INSERT INTO proposals (id, learner, section, item, before, after) VALUES (?,?,?,?,?,?)",
                       (proposal["id"], learner, section, item, before, after))
            return proposal

    def _proposal(self, db, learner, proposal_id):
        row = db.execute("SELECT * FROM proposals WHERE id=? AND learner=?", (proposal_id, learner)).fetchone()
        if not row:
            raise KeyError(proposal_id)
        return row

    def accept(self, learner, proposal_id, edited_text=None):
        """Áp đề xuất vào Persona HIỆN TẠI (không ghi đè bằng bản `after` cũ). Gọi lại lần hai trả Persona hiện tại."""
        with self._db() as db:
            row = self._proposal(db, learner, proposal_id)
            if row["status"] != "pending":
                return self._view(*self._current(db, learner))
            current = self._current(db, learner)[0]
            text = edited_text if edited_text is not None else add_item(current, row["section"], row["item"])
            result = self._write(db, learner, text)
            db.execute("UPDATE proposals SET status='accepted' WHERE id=?", (proposal_id,))
            return result

    def reject(self, learner, proposal_id):
        with self._db() as db:
            row = self._proposal(db, learner, proposal_id)
            if row["status"] == "pending":
                db.execute("UPDATE proposals SET status='rejected' WHERE id=?", (proposal_id,))
            return {"status": "rejected" if row["status"] == "pending" else row["status"]}

"""Single-instance application backend. AI and Persona remain external services."""
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from integrations import Services, ContractError
from lessons import load_lessons
from models import AIReply, NewChat, Persona, PersonaWrite, Question

HERE = Path(__file__).parent
LOG = logging.getLogger("tutor")


def create_app(db_path=None, services=None, lessons_path=None):
    db_path = Path(db_path or os.getenv("TUTOR_DB", HERE / "data" / "tutor.sqlite"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    services = services or Services(os.getenv("AI_API_URL", ""), os.getenv("PERSONA_API_URL", ""), os.getenv("SERVICE_API_KEY", ""))
    lessons = load_lessons(lessons_path or os.getenv("LESSONS_FILE", HERE / "lessons.sample.json"))
    failed_updates = {}
    recovery_lock = threading.Lock()
    lesson_map = {lesson["id"]: lesson for lesson in lessons}
    sources = {source["id"]: (lesson["id"], source) for lesson in lessons for source in lesson["sources"]}
    if len(lesson_map) != len(lessons) or len(sources) != sum(len(x["sources"]) for x in lessons):
        raise ValueError("Lesson and source IDs must be unique")

    @contextmanager
    def connect():
        db = sqlite3.connect(db_path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                with recovery_lock:
                    for turn_id, (detail, rotate) in list(failed_updates.items()):
                        db.execute("UPDATE turns SET status='failed',error=? WHERE id=? AND status='pending'", (detail, turn_id))
                        if rotate:
                            db.execute("UPDATE ai_keys SET key=? WHERE turn_id=?", (str(uuid.uuid4()), turn_id))
                    db.commit()
                    failed_updates.clear()
                yield db
        finally:
            db.close()

    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (owner TEXT PRIMARY KEY, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, lesson_id TEXT NOT NULL, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS turns (
            id TEXT PRIMARY KEY, chat_id TEXT NOT NULL REFERENCES chats(id),
            request_id TEXT NOT NULL, input TEXT NOT NULL, status TEXT NOT NULL,
            result TEXT, error TEXT, created_at REAL NOT NULL,
            UNIQUE(chat_id, request_id));
        CREATE UNIQUE INDEX IF NOT EXISTS one_pending_turn ON turns(chat_id) WHERE status='pending';
        CREATE TABLE IF NOT EXISTS ai_keys (turn_id TEXT PRIMARY KEY REFERENCES turns(id), key TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS persona_updates (
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, chat_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied');
        """)
        # Database cũ còn cột snapshot Persona; Persona giờ đọc trực tiếp từ agent mỗi lượt.
        if any(column["name"] == "persona" for column in db.execute("PRAGMA table_info(chats)")):
            db.execute("ALTER TABLE chats DROP COLUMN persona")
        # One server process only: interrupted requests are retryable after restart.
        db.execute("UPDATE turns SET status='failed', error='Máy chủ vừa khởi động lại. Vui lòng thử lại.' WHERE status='pending'")

    app = FastAPI(title="VLearn Tutor application", docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv("TUTOR_HOSTS", "127.0.0.1,localhost,testserver").split(","))

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request_id = str(uuid.uuid4())
        started = time.monotonic()
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("X-Tutor-Request") != "1":
            return JSONResponse({"detail": "Thiếu header xác nhận request."}, status_code=403)
        if len(await request.body()) > 65536:
            return JSONResponse({"detail": "Request quá lớn."}, status_code=413)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers["Cache-Control"] = "no-store"
        LOG.info("request=%s method=%s status=%s duration_ms=%.0f", request_id, request.method, response.status_code, (time.monotonic() - started) * 1000)
        return response

    def owner(request: Request):
        token = request.cookies.get("tutor_session", "")
        key = hashlib.sha256(token.encode()).hexdigest()
        with connect() as db:
            row = db.execute("SELECT owner FROM sessions WHERE owner=? AND expires>?", (key, time.time())).fetchone()
        if not row:
            raise HTTPException(401, "Phiên làm việc hết hạn. Tải lại trang để bắt đầu phiên mới.")
        return key

    def chat_for(chat_id, user):
        with connect() as db:
            row = db.execute("SELECT * FROM chats WHERE id=? AND owner=?", (chat_id, user)).fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy hội thoại.")
        return dict(row)

    def persona_call(method, path, user, payload=None):
        result = services.request("persona", method, path, user, payload)
        try:
            return Persona.model_validate(result).model_dump()
        except ValidationError:
            raise HTTPException(502, "API Persona trả dữ liệu không đúng contract.")

    @app.post("/api/session")
    def session(request: Request, response: Response):
        try:
            user = owner(request)
        except HTTPException:
            token = secrets.token_urlsafe(32)
            user = hashlib.sha256(token.encode()).hexdigest()
            with connect() as db:
                db.execute("INSERT INTO sessions VALUES (?,?)", (user, time.time() + 7 * 86400))
            response.set_cookie("tutor_session", token, httponly=True, samesite="strict", secure=os.getenv("COOKIE_SECURE") == "1", max_age=7 * 86400)
        return {"ai_connected": bool(services.ai_url), "persona_connected": bool(services.persona_url), "sample_lessons": any(x.get("sample") for x in lessons), "fixture_mode": bool(getattr(services, "is_fixture", False))}

    @app.get("/api/lessons")
    def list_lessons(user=Depends(owner)):
        return [{k: v for k, v in x.items() if k != "sources"} for x in lessons]

    @app.get("/api/lessons/{lesson_id}")
    def get_lesson(lesson_id: str, user=Depends(owner)):
        if lesson_id not in lesson_map:
            raise HTTPException(404, "Không tìm thấy bài.")
        return lesson_map[lesson_id]

    @app.get("/api/sources/{source_id}")
    def get_source(source_id: str, chat_id: str, user=Depends(owner)):
        chat = chat_for(chat_id, user)
        if source_id not in sources or sources[source_id][0] != chat["lesson_id"]:
            raise HTTPException(404, "Nguồn không thuộc bài của hội thoại.")
        return sources[source_id][1]

    @app.post("/api/chats")
    def new_chat(body: NewChat, user=Depends(owner)):
        if body.lesson_id not in lesson_map:
            raise HTTPException(404, "Không tìm thấy bài.")
        chat_id = str(uuid.uuid4())
        with connect() as db:
            db.execute("INSERT INTO chats VALUES (?,?,?,?)", (chat_id, user, body.lesson_id, time.time()))
        return {"id": chat_id, "lesson_id": body.lesson_id, "messages": []}

    @app.get("/api/chats")
    def list_chats(user=Depends(owner)):
        with connect() as db:
            rows = db.execute("SELECT id,lesson_id,created_at FROM chats WHERE owner=? ORDER BY created_at DESC,id DESC", (user,)).fetchall()
        return [{**dict(row), "title": lesson_map.get(row["lesson_id"], {}).get("title", "Bài học không còn tồn tại")} for row in rows]

    @app.get("/api/chats/{chat_id}")
    def get_chat(chat_id: str, user=Depends(owner)):
        chat = chat_for(chat_id, user)
        with connect() as db:
            turns = db.execute("SELECT * FROM turns WHERE chat_id=? ORDER BY created_at,id", (chat_id,)).fetchall()
            update_states = {r["id"]: r["status"] for r in db.execute("SELECT id,status FROM persona_updates WHERE chat_id=?", (chat_id,))}
        messages = []
        for turn in turns:
            question = json.loads(turn["input"])
            messages.append({"role": "user", "text": question["text"], "status": turn["status"], "request": question, "error": turn["error"], "retryable": turn["status"] == "failed" and turn["id"] == turns[-1]["id"]})
            if turn["result"]:
                reply = json.loads(turn["result"])
                for update in reply.get("persona_updates", []):
                    update["status"] = update_states.get(update["id"], "applied")
                messages.append({"role": "assistant", **reply})
        return {"id": chat_id, "lesson_id": chat["lesson_id"], "messages": messages}

    @app.post("/api/chats/{chat_id}/messages")
    def message(chat_id: str, body: Question, user=Depends(owner)):
        chat = chat_for(chat_id, user)
        for source_id in body.selected_source_ids:
            if source_id not in sources or sources[source_id][0] != chat["lesson_id"]:
                raise HTTPException(422, "Đoạn được chọn không thuộc bài.")
        encoded = json.dumps(body.model_dump(), sort_keys=True, ensure_ascii=False)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM turns WHERE chat_id=? AND request_id=?", (chat_id, body.client_request_id)).fetchone()
            if old and old["input"] != encoded:
                raise HTTPException(409, "Mã request đã dùng cho câu hỏi khác.")
            if old and old["status"] == "complete":
                return json.loads(old["result"])
            if db.execute("SELECT 1 FROM turns WHERE chat_id=? AND status='pending'", (chat_id,)).fetchone():
                raise HTTPException(409, "Hội thoại đang xử lý một câu hỏi.")
            if old:
                latest = db.execute("SELECT id FROM turns WHERE chat_id=? ORDER BY created_at DESC,id DESC LIMIT 1", (chat_id,)).fetchone()
                if latest["id"] != old["id"]:
                    raise HTTPException(409, "Chỉ có thể thử lại câu hỏi cuối. Hãy gửi lại thành câu hỏi mới.")
            turn_id = old["id"] if old else str(uuid.uuid4())
            if old:
                db.execute("UPDATE turns SET status='pending',error=NULL WHERE id=?", (turn_id,))
            else:
                db.execute("INSERT INTO turns VALUES (?,?,?,?,?,NULL,NULL,?)", (turn_id, chat_id, body.client_request_id, encoded, "pending", time.time()))
            db.execute("INSERT OR IGNORE INTO ai_keys VALUES (?,?)", (turn_id, turn_id))
            ai_key = db.execute("SELECT key FROM ai_keys WHERE turn_id=?", (turn_id,)).fetchone()["key"]
            completed = db.execute("SELECT input,result FROM turns WHERE chat_id=? AND status='complete' ORDER BY created_at,id", (chat_id,)).fetchall()
        try:
            history = []
            for previous in completed:
                history.extend([{"role": "user", "text": json.loads(previous["input"])["text"]}, {"role": "assistant", "text": json.loads(previous["result"])["text"]}])
            result = services.request("ai", "POST", "/respond", user, {"request_id": ai_key, "chat_id": chat_id, "lesson_id": chat["lesson_id"], "text": body.text, "history": history, "selected_source_ids": body.selected_source_ids}, ai_key)
            reply = AIReply.model_validate(result)
            if reply.decision == "answer" and not reply.citations:
                raise ValueError("Answer without citation")
            for citation in reply.citations:
                if citation.source_id not in sources or sources[citation.source_id][0] != chat["lesson_id"] or sources[citation.source_id][1]["locator"] != citation.locator:
                    raise ValueError("Invalid citation")
            for action in reply.actions:
                if action.type == "open_source" and (action.value not in sources or sources[action.value][0] != chat["lesson_id"]):
                    raise ValueError("Invalid source action")
            if not services.persona_url:
                reply.persona_updates = []  # không có Persona service thì không có chỗ hoàn tác
            response = reply.model_dump()
            response["message_id"] = turn_id
            response["request_id"] = body.client_request_id
            with connect() as db:
                for update in reply.persona_updates:
                    db.execute("INSERT INTO persona_updates (id,owner,chat_id) VALUES (?,?,?)", (update.id, user, chat_id))
                db.execute("UPDATE turns SET status='complete',result=? WHERE id=?", (json.dumps(response, ensure_ascii=False), turn_id))
            return response
        except (ValidationError, ValueError, ContractError, sqlite3.IntegrityError):
            rotate = True
            failure = HTTPException(502, "AI trả dữ liệu hoặc citation không đúng contract.")
        except HTTPException as exc:
            failure = exc
            rotate = exc.status_code < 500
        except Exception:
            LOG.exception("Unexpected failure processing turn %s", turn_id)
            failure = HTTPException(500, "Lượt hỏi gặp lỗi máy chủ. Vui lòng thử lại.")
            rotate = False
        # Keep cleanup queued if SQLite is temporarily locked; the next DB access
        # reconciles it before exposing the chat or accepting another message.
        with recovery_lock:
            failed_updates[turn_id] = (failure.detail, rotate)
        try:
            with connect():
                pass
        except sqlite3.Error:
            LOG.exception("Deferred failed-turn cleanup for %s", turn_id)
        raise failure

    @app.get("/api/persona")
    def get_persona(user=Depends(owner)):
        return persona_call("GET", "/persona", user)

    @app.put("/api/persona")
    def save_persona(body: PersonaWrite, user=Depends(owner)):
        return persona_call("PUT", "/persona", user, body.model_dump())

    @app.delete("/api/persona/memory")
    def clear_memory(user=Depends(owner)):
        return persona_call("DELETE", "/persona/memory", user)

    @app.post("/api/persona/updates/{update_id}/undo")
    def undo(update_id: str, user=Depends(owner)):
        with connect() as db:
            row = db.execute("SELECT * FROM persona_updates WHERE id=? AND owner=?", (update_id, user)).fetchone()
        if not row:
            raise HTTPException(404, "Không tìm thấy thay đổi Persona.")
        result = persona_call("POST", f"/persona/updates/{update_id}/undo", user, {})
        with connect() as db:
            db.execute("UPDATE persona_updates SET status='undone' WHERE id=?", (update_id,))
        return result

    @app.get("/")
    def index():
        return FileResponse(HERE / "static" / "index.html")

    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    return app

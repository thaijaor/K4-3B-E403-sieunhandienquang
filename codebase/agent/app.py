"""Agent service: POST /respond cho BE, route Persona. Chạy một process."""
import hmac
import logging
import os
import time
from pathlib import Path

import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agent import respond
from lessons import load_lessons
from llm import LLM
from persona.routes import router as persona_router
from schemas import AIReply, RespondRequest

HERE = Path(__file__).parent
LOG = logging.getLogger("agent")


def create_app(llm=None, lessons_file=None, env_file=HERE / ".env"):
    if env_file:
        load_dotenv(env_file)
    lessons_file = lessons_file or os.getenv("LESSONS_FILE", HERE.parent / "app" / "lessons.sample.json")
    lessons = {lesson["id"]: lesson for lesson in load_lessons(lessons_file)}
    llm = llm or LLM()
    service_key = os.getenv("SERVICE_API_KEY", "")

    app = FastAPI(title="VLearn Tutor agent", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def check_service_key(request: Request, call_next):
        # BE gửi Authorization: Bearer <SERVICE_API_KEY>; không cấu hình key thì bỏ qua (chạy local).
        if service_key and request.url.path != "/health":
            given = request.headers.get("Authorization", "").encode()
            if not hmac.compare_digest(given, f"Bearer {service_key}".encode()):
                return JSONResponse({"detail": "Sai hoặc thiếu service key."}, status_code=401)
        return await call_next(request)

    @app.get("/health")
    def health():
        return {"status": "ok", "model": llm.model, "lessons": len(lessons)}

    @app.post("/respond", response_model=AIReply)
    def respond_route(body: RespondRequest):
        lesson = lessons.get(body.lesson_id)
        if not lesson:
            raise HTTPException(404, "Không tìm thấy bài.")
        started = time.monotonic()
        try:
            reply = respond(body, lesson, llm)
        except openai.APITimeoutError:
            raise HTTPException(504, "Model phản hồi quá lâu.")
        except openai.APIError:
            LOG.exception("LLM call failed for request %s", body.request_id)
            raise HTTPException(502, "Gọi model thất bại.")
        LOG.info("request=%s lesson=%s decision=%s duration_ms=%.0f", body.request_id, body.lesson_id,
                 reply.decision, (time.monotonic() - started) * 1000)
        return reply

    app.include_router(persona_router)
    return app

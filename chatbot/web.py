"""Webes felület a chatbothoz (Flask)."""

import argparse
import json
import os
import secrets
import threading
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from chatbot.bot import DEFAULT_MODEL, WEB_SYSTEM_PROMPT, Chatbot, ChatbotError

STATIC_DIR = Path(__file__).parent / "static"
SESSION_COOKIE = "chatbot_session"
MAX_SESSIONS = 500
MAX_QUESTION_LENGTH = 20000


class SessionStore:
    """Böngészőnként külön beszélgetést tart a memóriában."""

    def __init__(self, factory: Callable[[], Chatbot], limit: int = MAX_SESSIONS) -> None:
        self._factory = factory
        self._limit = limit
        self._sessions: OrderedDict[str, tuple[Chatbot, threading.Lock]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str) -> tuple[Chatbot, threading.Lock]:
        with self._lock:
            if session_id in self._sessions:
                self._sessions.move_to_end(session_id)
            else:
                self._sessions[session_id] = (self._factory(), threading.Lock())
                if len(self._sessions) > self._limit:
                    self._sessions.popitem(last=False)
            return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        """Új beszélgetést indít; egy esetleg még futó válasz a régihez tartozik."""
        with self._lock:
            self._sessions.pop(session_id, None)


def create_app(bot_factory: Callable[[], Chatbot] | None = None) -> Flask:
    if bot_factory is None:
        model = os.environ.get("CHATBOT_MODEL", DEFAULT_MODEL)
        effort = os.environ.get("CHATBOT_EFFORT", "low")

        def bot_factory() -> Chatbot:
            return Chatbot(model=model, effort=effort, system=WEB_SYSTEM_PROMPT)

    app = Flask(__name__, static_folder=None)
    store = SessionStore(bot_factory)

    def session_id() -> str:
        return request.cookies.get(SESSION_COOKIE) or secrets.token_urlsafe(24)

    def with_cookie(response: Response, sid: str) -> Response:
        response.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="Strict")
        return response

    @app.get("/")
    def index() -> Response:
        return with_cookie(send_from_directory(STATIC_DIR, "index.html"), session_id())

    @app.post("/api/chat")
    def chat() -> Response:
        sid = session_id()
        question = str((request.get_json(silent=True) or {}).get("message", "")).strip()
        if not question:
            return jsonify(error="Üres kérdés."), 400
        if len(question) > MAX_QUESTION_LENGTH:
            return jsonify(error="A kérdés túl hosszú."), 400

        bot, lock = store.get(sid)
        if not lock.acquire(blocking=False):
            return jsonify(error="Még készül az előző válasz."), 409

        released = False

        def release() -> None:
            nonlocal released
            if not released:
                released = True
                lock.release()

        def generate():
            # Soronként egy JSON-esemény: {"text": ...}, {"error": ...} vagy {"done": true}.
            try:
                for chunk in bot.ask(question):
                    yield json.dumps({"text": chunk}, ensure_ascii=False) + "\n"
                yield json.dumps({"done": True}) + "\n"
            except ChatbotError as e:
                yield json.dumps({"error": str(e)}, ensure_ascii=False) + "\n"
            finally:
                release()

        response = Response(generate(), mimetype="application/x-ndjson")
        # Akkor is felszabadul, ha a böngésző a válasz előtt bontja a kapcsolatot.
        response.call_on_close(release)
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return with_cookie(response, sid)

    @app.post("/api/reset")
    def reset() -> Response:
        sid = session_id()
        store.reset(sid)
        return with_cookie(jsonify(ok=True), sid)

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A chatbot webes felülete.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = parser.parse_args(argv)

    print(f"A chatbot fut: http://{args.host}:{args.port}")
    create_app().run(host=args.host, port=args.port, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

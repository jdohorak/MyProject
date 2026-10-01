import json

import pytest

from chatbot import ChatbotError
from chatbot.web import create_app


class FakeBot:
    def __init__(self, chunks=("Szia", "!"), error=None):
        self.chunks = chunks
        self.error = error
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        yield from self.chunks
        if self.error:
            raise ChatbotError(self.error)


def make_client(**bot_kwargs):
    bots = []

    def factory():
        bot = FakeBot(**bot_kwargs)
        bots.append(bot)
        return bot

    return create_app(factory).test_client(), bots


def events(response):
    return [json.loads(line) for line in response.get_data(as_text=True).splitlines()]


def test_index_sets_session_cookie():
    client, _ = make_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "chatbot_session" in response.headers["Set-Cookie"]
    assert b"<title>" in response.data


def test_chat_streams_events_and_keeps_session():
    client, bots = make_client()
    client.get("/")
    first = client.post("/api/chat", json={"message": "Hello"})
    assert events(first) == [{"text": "Szia"}, {"text": "!"}, {"done": True}]
    client.post("/api/chat", json={"message": "Még egy"}).get_data()
    assert len(bots) == 1
    assert bots[0].questions == ["Hello", "Még egy"]


def test_chat_reports_bot_error():
    client, _ = make_client(chunks=(), error="API-hiba")
    response = client.post("/api/chat", json={"message": "x"})
    assert events(response) == [{"error": "API-hiba"}]


@pytest.mark.parametrize("payload", [{}, {"message": "   "}, {"message": "x" * 20001}])
def test_chat_rejects_invalid_input(payload):
    client, _ = make_client()
    assert client.post("/api/chat", json=payload).status_code == 400


def test_reset_starts_new_conversation():
    client, bots = make_client()
    client.get("/")
    client.post("/api/chat", json={"message": "a"}).get_data()
    assert client.post("/api/reset").status_code == 200
    client.post("/api/chat", json={"message": "b"}).get_data()
    assert [b.questions for b in bots] == [["a"], ["b"]]

from types import SimpleNamespace

import pytest

from chatbot import Chatbot, ChatbotError


class FakeStream:
    def __init__(self, chunks, stop_reason="end_turn"):
        self.text_stream = iter(chunks)
        self._message = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text="".join(chunks))],
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._message


class FakeClient:
    def __init__(self, streams):
        self.calls = []
        self._streams = iter(streams)
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return next(self._streams)


def test_ask_streams_and_keeps_history():
    client = FakeClient([FakeStream(["Buda", "pest"]), FakeStream(["Igen."])])
    bot = Chatbot(client=client)

    assert "".join(bot.ask("Mi Magyarország fővárosa?")) == "Budapest"
    assert "".join(bot.ask("Biztos?")) == "Igen."

    second = client.calls[1]["messages"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    assert client.calls[0]["fallbacks"] == "default"
    assert len(bot.messages) == 4


def test_refusal_drops_turn():
    bot = Chatbot(client=FakeClient([FakeStream([], stop_reason="refusal")]))
    with pytest.raises(ChatbotError):
        list(bot.ask("valami"))
    assert bot.messages == []


def test_interrupted_answer_drops_turn():
    bot = Chatbot(client=FakeClient([FakeStream(["a", "b", "c"])]))
    gen = bot.ask("kérdés")
    next(gen)
    gen.close()
    assert bot.messages == []


def test_reset():
    bot = Chatbot(client=FakeClient([FakeStream(["ok"])]))
    list(bot.ask("szia"))
    bot.reset()
    assert bot.messages == []

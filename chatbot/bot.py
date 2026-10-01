"""A beszélgetést kezelő Chatbot osztály."""

from collections.abc import Iterator

import anthropic

DEFAULT_MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = (
    "Segítőkész, barátságos asszisztens vagy, aki általános kérdésekre válaszol "
    "(tudomány, történelem, technika, hétköznapi ügyek, nyelv, matematika stb.). "
    "Mindig azon a nyelven válaszolj, amelyen a felhasználó írt. "
    "Adj tömör, pontos választ, és csak akkor fejtsd ki bővebben, ha a kérdés megkívánja. "
    "Ha valamiben nem vagy biztos, mondd ki nyíltan, és ne találj ki tényeket. "
    "A válaszaid terminálban jelennek meg, ezért kerüld a bonyolult formázást."
)


class ChatbotError(Exception):
    """Felhasználónak megjeleníthető hiba."""


class Chatbot:
    """Többfordulós beszélgetés a Claude modellel, folyamatos (streaming) kimenettel."""

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = DEFAULT_MODEL,
        effort: str = "low",
        system: str = SYSTEM_PROMPT,
    ) -> None:
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.system = system
        self.messages: list[dict] = []

    def reset(self) -> None:
        """Új beszélgetést kezd (törli az előzményeket)."""
        self.messages.clear()

    def ask(self, question: str) -> Iterator[str]:
        """Elküldi a kérdést, és darabonként visszaadja a válasz szövegét."""
        self.messages.append({"role": "user", "content": question})
        completed = False
        try:
            with self.client.beta.messages.stream(
                model=self.model,
                max_tokens=64000,
                system=self.system,
                messages=self.messages,
                output_config={"effort": self.effort},
                # Ha a modell biztonsági okból elutasítaná a kérést, az API
                # automatikusan egy ajánlott tartalék modellen futtatja újra.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            ) as stream:
                yield from stream.text_stream
                response = stream.get_final_message()

            if response.stop_reason == "refusal":
                raise ChatbotError("Erre a kérdésre nem tudok válaszolni.")

            # A teljes tartalmat (gondolkodási blokkokkal együtt) változatlanul
            # visszaadjuk a következő kérésben.
            self.messages.append({"role": "assistant", "content": response.content})
            completed = True
        except anthropic.AuthenticationError as e:
            raise ChatbotError(
                "Érvénytelen vagy hiányzó API-kulcs. Állítsd be az ANTHROPIC_API_KEY "
                "környezeti változót."
            ) from e
        except anthropic.RateLimitError as e:
            raise ChatbotError("Túl sok kérés. Várj egy kicsit, majd próbáld újra.") from e
        except anthropic.APIStatusError as e:
            raise ChatbotError(f"API-hiba ({e.status_code}): {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ChatbotError("Hálózati hiba. Ellenőrizd az internetkapcsolatot.") from e
        finally:
            # Hiba, elutasítás vagy megszakítás esetén a kérdést is eldobjuk,
            # hogy az előzmények konzisztensek maradjanak.
            if not completed:
                self.messages.pop()

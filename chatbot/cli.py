"""Parancssori felület a chatbothoz."""

import argparse
import os
import sys

from chatbot.bot import DEFAULT_MODEL, Chatbot, ChatbotError

HELP = """Parancsok:
  /uj     új beszélgetés indítása
  /sugo   ez a súgó
  /kilep  kilépés (Ctrl+D is működik)"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Általános kérdésekre válaszoló chatbot.")
    parser.add_argument("--model", default=os.environ.get("CHATBOT_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--effort",
        default=os.environ.get("CHATBOT_EFFORT", "low"),
        choices=["low", "medium", "high", "xhigh", "max"],
        help="Mennyit gondolkodjon a modell válasz előtt (alapértelmezés: low).",
    )
    args = parser.parse_args(argv)

    bot = Chatbot(model=args.model, effort=args.effort)
    print("Szia! Kérdezz bármit. (/sugo a parancsokhoz)\n")

    while True:
        try:
            question = input("Te: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nViszlát!")
            return 0

        if not question:
            continue
        if question in ("/kilep", "/exit", "/quit"):
            print("Viszlát!")
            return 0
        if question in ("/sugo", "/help"):
            print(HELP + "\n")
            continue
        if question in ("/uj", "/new"):
            bot.reset()
            print("Új beszélgetés indult.\n")
            continue

        print("Bot: ", end="", flush=True)
        try:
            for chunk in bot.ask(question):
                print(chunk, end="", flush=True)
        except ChatbotError as e:
            print(f"\n[Hiba] {e}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n[Megszakítva]")
        print("\n")


if __name__ == "__main__":
    sys.exit(main())

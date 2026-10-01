# MyProject – Chatbot

Chatbot (parancssori és webes felülettel), amely általános kérdésekre válaszol a Claude API (Anthropic) segítségével.
A válasz folyamatosan, gépelésszerűen jelenik meg, és a bot emlékszik a beszélgetés korábbi részére.

## Telepítés

Python 3.10 vagy újabb kell hozzá.

```bash
pip install -e .          # csak parancssor
pip install -e ".[web]"   # parancssor + webes felület
```

## API-kulcs

Hozz létre egy kulcsot a https://console.anthropic.com oldalon, majd állítsd be:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Használat – parancssor

```bash
chatbot            # vagy: python -m chatbot
```

Parancsok a beszélgetés közben:

| Parancs  | Leírás                     |
|----------|----------------------------|
| `/uj`    | új beszélgetés indítása    |
| `/sugo`  | súgó                       |
| `/kilep` | kilépés (Ctrl+D is működik) |

Opciók:

- `--model` – a használt modell (alapértelmezés: `claude-opus-5-5`, vagy a `CHATBOT_MODEL` változó)
- `--effort` – mennyit gondolkodjon válasz előtt: `low` (alapértelmezés), `medium`, `high`, `xhigh`, `max`
  (vagy a `CHATBOT_EFFORT` változó). Magasabb érték alaposabb, de lassabb és drágább választ ad.

## Használat – webes felület

```bash
chatbot-web               # vagy: python -m chatbot.web
```

Ezután nyisd meg a böngészőben: http://127.0.0.1:8000

- Enter: küldés, Shift+Enter: új sor
- a válasz gépelés közben látszik, és a **Leállítás** gombbal megszakítható
- az **Új beszélgetés** gomb törli az előzményeket
- a válaszok formázva (listák, félkövér, kódblokkok) jelennek meg

Opciók: `--host` (alapértelmezés: `127.0.0.1`) és `--port` (alapértelmezés: `8000`, vagy a `PORT` változó).
A modellt és a gondolkodási szintet itt a `CHATBOT_MODEL` és `CHATBOT_EFFORT` változókkal lehet állítani.

A szerver a Flask beépített fejlesztői szerverét használja, és a beszélgetéseket a memóriában
tartja (újraindításkor törlődnek). Saját gépen vagy belső hálózaton való használatra készült;
nyilvános internetre ne tedd ki hitelesítés nélkül, mert bárki a te API-kulcsodat használná.

## Tesztek

```bash
pip install -e ".[dev]"
pytest
```

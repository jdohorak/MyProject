# MyProject – Chatbot

Parancssori chatbot, amely általános kérdésekre válaszol a Claude API (Anthropic) segítségével.
A válasz folyamatosan, gépelésszerűen jelenik meg, és a bot emlékszik a beszélgetés korábbi részére.

## Telepítés

Python 3.10 vagy újabb kell hozzá.

```bash
pip install -e .
```

## API-kulcs

Hozz létre egy kulcsot a https://console.anthropic.com oldalon, majd állítsd be:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Használat

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

## Tesztek

```bash
pip install -e ".[dev]"
pytest
```

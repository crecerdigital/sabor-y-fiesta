# Sabor & Fiesta — Taste-Aware Event Concierge

An agentic event concierge that plans a full night out — **dinner + music + activity + sweet finish + timeline** — from your *taste*: the food you love, the music that moves you, the vibe you want, and your city.

**The idea (Qloo-style cross-domain taste):** your taste in one domain predicts what you'll love in another. If salsa runs in your veins, a Caribbean kitchen with live music isn't a guess — it's an affinity. Sabor & Fiesta makes those connections explicit ("🔗 here's how your tastes connect") and turns them into a plan a family can actually use for birthdays, quinceañeras, anniversaries, and gatherings.

Built for the **Qloo Agentic Hackathon** (Devpost) by **Crecer Digital**.

## Two data modes (always declared in the UI)

| Mode | When | What happens |
|---|---|---|
| `local-demo` | No `QLOO_API_KEY` set | The local taste engine (`engine.py`) scores curated city data (`data/curated.json`) by cross-domain tag affinity. The UI shows a **"DEMO MODE"** badge. Nothing is faked. |
| `qloo-live` | `QLOO_API_KEY` set | Restaurant and artist picks come from the **real Qloo API** (`qloo_client.py`: `/search` for seed entities → `/v2/insights` for `urn:entity:place` and `urn:entity:artist`). Activity & dessert are completed by the local layer, and the UI shows a **"LIVE"** badge. If the API fails, it falls back to local mode. |

## Run it locally

Requires only **Python 3.10+** — no pip installs, no frameworks (standard library only).

```bash
python3 app.py
# → http://localhost:8000
```

Health check: `GET /api/health` · Plan endpoint: `POST /api/plan` (JSON).

### Enable the live Qloo API

Hackathon participants get a **free API key** from the form linked in Qloo's
official hackathon developer guide
(https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide).
The key is delivered by email and **only works against the hackathon base URL**.

```bash
export QLOO_API_KEY="your-key-here"
export QLOO_API_URL="https://hackathon.api.qloo.com"   # default, shown for clarity
python3 app.py
```

⚠️ Never commit your key. It is read from the environment only (`.gitignore` covers `.env`).

Try it from the terminal:

```bash
curl -s -X POST localhost:8000/api/plan -H 'Content-Type: application/json' \
  -d '{"name":"Maria","city":"Charlotte, NC","cuisines":["caribena"],\
"music":["salsa"],"ambiance":"fiesta","occasion":"cumpleanos","guests":20,"lang":"es"}'
```

## Project structure

```
app.py            HTTP server (stdlib only) — page + /api/plan + /api/health
engine.py         Local taste engine: cross-domain affinity scoring + plan narrative (ES/EN)
qloo_client.py    Real Qloo API integration (search → insights), key via env var
data/curated.json Curated local demo data: 6 cities + fallback, restaurants, activities, desserts
static/index.html Self-contained UI (form, plan cards, timeline, ES/EN toggle)
PENDIENTES.md     Submission checklist (Spanish) — what remains for Devpost
```

## Deploy (for the public demo)

Any host that runs a Python web process works. Example with **Render** (free tier):
build command *(none)*, start command `python3 app.py`, environment variables
`PORT` (set by the host) and `QLOO_API_KEY` (your key, kept secret).
A `Procfile` is included for Heroku-style platforms.

## License

MIT — see [LICENSE](LICENSE). © 2026 Cristhiam Acuña / Crecer Digital.

"""
qloo_client.py — Integración REAL con la API de Qloo (Taste AI) para el
Qloo Agentic Hackathon. Código separado y comentado, listo para enchufar
la clave de participante.

====================================================================
CÓMO ACTIVARLO (paso del titular de la cuenta, ver PENDIENTES.md)
====================================================================
1. El participante pide su API key GRATUITA en el formulario oficial
   enlazado desde la guía del hackathon:
   https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide
   ("API Key Request Form"). La clave llega por correo (revisar spam;
   puede tardar unos días laborables).
2. Exporta las variables de entorno ANTES de arrancar el servidor:

       export QLOO_API_KEY="pega-aqui-tu-clave"
       # Opcional (este es el valor correcto por defecto para el hackathon):
       export QLOO_API_URL="https://hackathon.api.qloo.com"

   ⚠️ La clave SOLO funciona contra https://hackathon.api.qloo.com
   (contra api.qloo.com o staging devuelve 401).
   ⚠️ NUNCA escribas la clave en el código ni la subas al repo público.

3. Reinicia app.py. Sin clave, la app corre en modo demo con datos
   locales (engine.py) y lo indica con total transparencia en la UI.

====================================================================
FLUJO DE LA API (según la guía oficial del hackathon)
====================================================================
  GET /search?query=<nombre>            → entity_id de las semillas de gusto
  GET /v2/insights?filter.type=...     → recomendaciones (Insights API)
      &signal.interests.entities=<entity_id,...>
  Cabecera obligatoria:  X-Api-Key: <clave>   (NO Bearer, NO query param)

Tipos usados: comida/lugares = urn:entity:place · música = urn:entity:artist
(/recommendations y /recs son legacy y NO se usan.)
"""

import json
import os
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("QLOO_API_URL", "https://hackathon.api.qloo.com")
API_KEY = os.environ.get("QLOO_API_KEY", "")

# Coordenadas aproximadas por ciudad para sesgar resultados por ubicación.
# (Si un parámetro no es válido para el tipo de entidad, la API lo ignora
# en silencio, así que esto es seguro como "best effort".)
CITY_GEO = {
    "Charlotte, NC": (35.2271, -80.8431),
    "Miami, FL": (25.7617, -80.1918),
    "New York, NY": (40.7128, -74.0060),
    "Ciudad de México": (19.4326, -99.1332),
    "Bogotá": (4.71099, -74.0721),
    "Madrid": (40.4168, -3.7038),
}

# Semilla de búsqueda por cada gusto musical elegido en la UI:
# nombre de un artista/entidad representativa para /search.
MUSIC_SEED_QUERY = {
    "salsa": "Marc Anthony",
    "bachata": "Romeo Santos",
    "merengue": "Juan Luis Guerra",
    "regional": "Grupo Firme",
    "jazz": "Frank Sinatra",
    "boleros": "Luis Miguel",
    "regueton": "Bad Bunny",
    "electronica": "Calvin Harris",
    "pop_latino": "Shakira",
    "rock_espanol": "Maná",
}

CUISINE_SEED_QUERY = {
    "mexicana": "Mexican food",
    "caribena": "Caribbean food",
    "italiana": "Italian food",
    "japonesa": "Japanese food",
    "americana": "American food",
    "mediterranea": "Mediterranean food",
    "peruana": "Peruvian food",
    "espanola": "Spanish food",
    "india": "Indian food",
}


def is_configured():
    """True si hay API key en el entorno."""
    return bool(API_KEY)


def _get(path, params):
    """GET autenticado contra la API de Qloo. Devuelve dict o lanza."""
    url = BASE_URL.rstrip("/") + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"X-Api-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_entity_id(query):
    """Busca una entidad por nombre y devuelve su entity_id (o None)."""
    data = _get("/search", {"query": query})
    results = data.get("results") or []
    if results:
        return results[0].get("entity_id") or results[0].get("id")
    return None


def insights(filter_type, entity_ids, city=None, take=5):
    """Llama a /v2/insights y devuelve la lista de entidades recomendadas."""
    params = {
        "filter.type": filter_type,
        "signal.interests.entities": ",".join(entity_ids),
        "take": take,
    }
    geo = CITY_GEO.get(city or "")
    if geo:
        params["filter.location.lat"] = geo[0]
        params["filter.location.lon"] = geo[1]
    data = _get("/v2/insights", params)
    return (data.get("results") or {}).get("entities") or []


def _entity_name(entity):
    return entity.get("name") or (entity.get("properties") or {}).get("name") or "—"


def get_live_picks(profile):
    """
    Devuelve {"restaurant": {...}, "music": {...}} construidos con datos
    REALES de Qloo, o None si la API no responde / no hay clave / no hay
    resultados. app.py usa engine.py como respaldo en ese caso.

    Nota: actividad y postre se completan con la capa local curada
    (engine.py), porque son experiencias de la ciudad; la UI lo declara.
    """
    if not is_configured():
        return None

    # 1) Semillas: IDs de entidades de los gustos del usuario.
    seed_ids = []
    for seed in profile.get("music", []):
        q = MUSIC_SEED_QUERY.get(seed)
        if q:
            eid = search_entity_id(q)
            if eid:
                seed_ids.append(eid)
    for cuisine in profile.get("cuisines", []):
        q = CUISINE_SEED_QUERY.get(cuisine)
        if q:
            eid = search_entity_id(q)
            if eid:
                seed_ids.append(eid)
    if not seed_ids:
        return None

    city = profile.get("city")
    picks = {}

    # 2) Lugares (restaurantes) que combinan con esos gustos.
    places = insights("urn:entity:place", seed_ids, city=city, take=5)
    if places:
        top = places[0]
        props = top.get("properties") or {}
        picks["restaurant"] = {
            "name": _entity_name(top),
            "cuisine": profile.get("cuisines", ["—"])[0],
            "neighborhood": props.get("address", {}).get("neighborhood", city or "")
            if isinstance(props.get("address"), dict) else (city or ""),
            "price": props.get("price_level", "$$") if isinstance(props.get("price_level"), str) else "$$",
            "dish": props.get("description", "") or "House specialty / Especialidad de la casa",
            "why": "Elegido por la API de Qloo a partir de tus gustos (afinidades entre dominios).",
            "alternatives": [_entity_name(e) for e in places[1:4]],
        }

    # 3) Artistas afines a las semillas musicales.
    artists = insights("urn:entity:artist", seed_ids, city=None, take=5)
    if artists:
        top = artists[0]
        picks["music"] = {
            "artist": _entity_name(top),
            "also": _entity_name(artists[1]) if len(artists) > 1 else "",
            "vibe": "Afinidad calculada por el grafo de gustos de Qloo",
            "moment": "",
            "why": "Qloo conecta tus gustos entre dominios: de tus semillas salen artistas afines como este.",
            "alternatives": [_entity_name(e) for e in artists[2:5]],
        }

    return picks or None

"""
engine.py — Motor de gustos LOCAL de Sabor & Fiesta (modo demo sin API key).

Replica, con datos curados locales (data/curated.json), la idea central de
Qloo: las afinidades cruzan dominios. Si te gusta la salsa (música), eso
dice algo de qué restaurantes y actividades vas a amar (caribeño, baile,
en vivo). El motor:

  1. Convierte las respuestas del usuario en un conjunto de "tags de gusto"
     (semillas directas + afinidades cruzadas entre dominios).
  2. Puntúa cada restaurante/actividad/postre de la ciudad por solapamiento
     de tags y elige los mejores.
  3. Arma un plan con línea de tiempo y explicaciones que conectan los
     gustos entre dominios ("porque amas X, elegimos Y").

Cuando QLOO_API_KEY está presente, app.py intenta primero qloo_client.py
(API real de Qloo) y solo usa este motor como respaldo transparente.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "curated.json")

with open(DATA_PATH, encoding="utf-8") as f:
    DATA = json.load(f)

# ----------------------------------------------------------------------------
# Afinidades cruzadas entre dominios (el "grafo de gustos" local).
# Una semilla (música, cocina, ocasión) activa tags de OTROS dominios.
# ----------------------------------------------------------------------------
CROSS_AFFINITY = {
    "salsa":      ["baile", "en-vivo"],
    "bachata":    ["baile", "intimo"],
    "merengue":   ["familiar", "fiesta"],
    "regional":   ["en-vivo", "fiesta"],
    "jazz":       ["intimo", "velas"],
    "boleros":    ["intimo", "velas"],
    "regueton":   ["nocturno", "urbano"],
    "electronica": ["rooftop", "nocturno"],
    "pop_latino": ["terraza", "familiar"],
    "rock_espanol": ["nostalgia", "en-vivo"],
}

OCCASION_TAGS = {
    "cumpleanos":  ["fiesta", "familiar", "en-vivo"],
    "aniversario": ["romantico", "intimo", "velas"],
    "quinceanera": ["familiar", "fiesta", "baile", "tradicional"],
    "familia":     ["familiar", "acogedor", "tradicional"],
    "amigos":      ["fiesta", "nocturno", "casual"],
    "negocios":    ["elegante", "moderno", "intimo"],
}

# Nombres bonitos para mostrar los tags/seeds internos (las claves son ASCII).
TAG_DISPLAY = {
    "es": {"caribena": "caribeña", "caribeno": "caribeño", "en-vivo": "en vivo",
           "romantico": "romántico", "intimo": "íntimo", "electronica": "electrónica",
           "regueton": "reguetón", "pop_latino": "pop latino", "rock_espanol": "rock en español",
           "regional": "regional mexicano"},
    "en": {"caribena": "Caribbean", "caribeno": "Caribbean", "tropical": "tropical",
           "sabroso": "flavorful", "familiar": "family-friendly", "fiesta": "party",
           "baile": "dancing", "en-vivo": "live", "romantico": "romantic", "intimo": "intimate",
           "velas": "candlelit", "elegante": "elegant", "moderno": "modern", "nocturno": "nightlife",
           "urbano": "urban", "terraza": "terrace", "acogedor": "cozy", "tradicional": "traditional",
           "picante": "spicy", "mariscos": "seafood", "ligero": "light", "saludable": "healthy",
           "especias": "spiced", "nostalgia": "nostalgic", "electronica": "electronic",
           "regueton": "reggaeton", "pop_latino": "Latin pop", "rock_espanol": "Spanish rock",
           "regional": "Regional Mexican"},
}


def _disp(tags, lang):
    m = TAG_DISPLAY.get(lang, {})
    return [m.get(t, t) for t in tags]

STRINGS = {
    "es": {
        "greeting": "¡{name}, armé tu plan con sabor en {city}!",
        "default_name": "amigo/a",
        "why_restaurant": "Porque tus gustos apuntan a {tags}: este lugar cruza tu amor por la cocina {cuisine} con el ambiente que buscabas.",
        "why_music": "Tu música manda: {artist} pone el tono ({vibe}) y también suena {alt} para variar.",
        "why_activity": "La actividad cierra el círculo de tus gustos: {tags}.",
        "dessert": "El toque dulce final, sin romper el ambiente.",
        "connection": "{seed} → {tags}",
        "timeline": [
            ("18:30", "Llegada y rompehielo", "Punto de encuentro y primeras fotos del grupo."),
            ("19:00", "La cena", None),
            ("20:45", "El postre", None),
            ("21:15", "Música y a celebrar", None),
        ],
        "dinner_detail": "{dish} en {name} ({neighborhood}).",
        "dessert_detail": "{name}.",
        "music_detail": "{artist} — {vibe}.",
        "budget_note": "Nivel de precio del plan: {price}",
        "occasion_line": "Ocasión: {occasion} · Invitados: {guests}",
    },
    "en": {
        "greeting": "{name}, here's your flavor-packed plan for {city}!",
        "default_name": "friend",
        "why_restaurant": "Your taste points to {tags}: this spot crosses your love of {cuisine} food with the vibe you asked for.",
        "why_music": "Your music leads: {artist} sets the tone ({vibe}), with {alt} in rotation.",
        "why_activity": "The activity closes the loop on your taste: {tags}.",
        "dessert": "The sweet finish, without breaking the mood.",
        "connection": "{seed} → {tags}",
        "timeline": [
            ("6:30 PM", "Arrival & icebreaker", "Meeting point and first group photos."),
            ("7:00 PM", "Dinner", None),
            ("8:45 PM", "Dessert", None),
            ("9:15 PM", "Music & celebration", None),
        ],
        "dinner_detail": "{dish} at {name} ({neighborhood}).",
        "dessert_detail": "{name}.",
        "music_detail": "{artist} — {vibe}.",
        "budget_note": "Plan price level: {price}",
        "occasion_line": "Occasion: {occasion} · Guests: {guests}",
    },
}

CUISINE_LABEL = {    "es": {"mexicana": "mexicana", "caribena": "caribeña", "italiana": "italiana",
           "japonesa": "japonesa", "americana": "americana", "mediterranea": "mediterránea",
           "peruana": "peruana", "espanola": "española", "india": "india"},
    "en": {"mexicana": "Mexican", "caribena": "Caribbean", "italiana": "Italian",
           "japonesa": "Japanese", "americana": "American", "mediterranea": "Mediterranean",
           "peruana": "Peruvian", "espanola": "Spanish", "india": "Indian"},
}


def _city_data(city):
    return DATA["cities"].get(city) or DATA["cities"]["_default"]


def _score(item_tags, taste_tags):
    return sum(1 for t in item_tags if t in taste_tags)


def _best(items, taste_tags, required_tag=None):
    """Devuelve (item, tags_que_coinciden) del mejor puntuado."""
    best, best_hits = None, []
    for item in items:
        if required_tag and required_tag not in item.get("tags", []) and required_tag != item.get("cuisine"):
            continue
        hits = [t for t in item.get("tags", []) if t in taste_tags]
        if item.get("cuisine") in taste_tags:
            hits.append(item["cuisine"])
        if best is None or len(hits) > len(best_hits):
            best, best_hits = item, hits
    return best, best_hits


def build_plan(profile):
    """
    profile: dict con claves
      name, city, cuisines [..], music [..], ambiance, occasion, guests, lang
    Devuelve el plan en el MISMO esquema que usa qloo_client.py.
    """
    lang = profile.get("lang", "es")
    T = STRINGS.get(lang, STRINGS["es"])
    city = profile.get("city") or "Charlotte, NC"
    data = _city_data(city)

    # --- 1. Tags de gusto: semillas directas + afinidades cruzadas ----------
    taste_tags = set()
    connections = []
    for cuisine in profile.get("cuisines", []):
        tags = DATA["cuisine_tags"].get(cuisine, [])
        taste_tags.update(tags)
        taste_tags.add(cuisine)
        label = CUISINE_LABEL.get(lang, {}).get(cuisine, cuisine)
        connections.append({"seed": label,
                            "tags": [t for t in tags if t != cuisine][:3]})
    for seed in profile.get("music", []):
        entry = DATA["music_seeds"].get(seed)
        if entry:
            taste_tags.update(entry["tags"])
            extra = CROSS_AFFINITY.get(seed, [])
            taste_tags.update(extra)
            connections.append({"seed": seed, "tags": (entry["tags"][:2] + extra[:1])})
    amb = DATA["ambiance_tags"].get(profile.get("ambiance", ""), [])
    taste_tags.update(amb)
    taste_tags.update(OCCASION_TAGS.get(profile.get("occasion", ""), []))

    # --- 2. Selección por puntuación ---------------------------------------
    # Restaurante: prioridad a alguna de las cocinas elegidas.
    restaurant, r_hits = None, []
    for cuisine in profile.get("cuisines", []):
        cand, hits = _best(data["restaurants"], taste_tags, required_tag=cuisine)
        if cand and (restaurant is None or len(hits) > len(r_hits)):
            restaurant, r_hits = cand, hits
    if restaurant is None:
        restaurant, r_hits = _best(data["restaurants"], taste_tags)

    activity, a_hits = _best(data["activities"], taste_tags)
    sweet, _ = _best(data["sweet"], taste_tags)

    # Música: artista principal de la primera semilla elegida.
    music_seed = (profile.get("music") or ["salsa"])[0]
    music_entry = DATA["music_seeds"].get(music_seed, DATA["music_seeds"]["salsa"])

    # --- 3. Narrativa del conserje -----------------------------------------
    name = (profile.get("name") or "").strip() or T["default_name"]
    cuisine_label = CUISINE_LABEL.get(lang, {}).get(restaurant["cuisine"], restaurant["cuisine"])
    tl = T["timeline"]
    timeline = [
        {"time": tl[0][0], "title": tl[0][1], "detail": tl[0][2]},
        {"time": tl[1][0], "title": tl[1][1],
         "detail": T["dinner_detail"].format(dish=restaurant["dish_" + lang] if "dish_" + lang in restaurant else restaurant["dish_es"],
                                             name=restaurant["name"],
                                             neighborhood=restaurant["neighborhood"])},
        {"time": tl[2][0], "title": tl[2][1],
         "detail": T["dessert_detail"].format(name=sweet["name_" + lang] if "name_" + lang in sweet else sweet["name_es"])},
        {"time": tl[3][0], "title": tl[3][1],
         "detail": T["music_detail"].format(artist=music_entry["artist"], vibe=music_entry["vibe_" + lang])},
    ]

    return {
        "mode": "local-demo",
        "greeting": T["greeting"].format(name=name, city=city),
        "city": city,
        "occasion_line": T["occasion_line"].format(occasion=profile.get("occasion", ""),
                                                   guests=profile.get("guests", "")),
        "taste_connections": [
            T["connection"].format(seed=_disp([c["seed"]], lang)[0],
                                   tags=", ".join(_disp(c["tags"], lang)))
            for c in connections
        ],
        "plan": {
            "restaurant": {
                "name": restaurant["name"],
                "cuisine": cuisine_label,
                "neighborhood": restaurant["neighborhood"],
                "price": restaurant["price"],
                "dish": restaurant["dish_" + lang] if "dish_" + lang in restaurant else restaurant["dish_es"],
                "why": T["why_restaurant"].format(tags=", ".join(_disp(r_hits[:3], lang)) or "—", cuisine=cuisine_label),
            },
            "music": {
                "artist": music_entry["artist"],
                "also": music_entry["alt"],
                "vibe": music_entry["vibe_" + lang],
                "moment": activity["name_" + lang] if "name_" + lang in activity else activity["name_es"],
                "why": T["why_music"].format(artist=music_entry["artist"],
                                             vibe=music_entry["vibe_" + lang],
                                             alt=music_entry["alt"]),
            },
            "activity": {
                "name": activity["name_" + lang] if "name_" + lang in activity else activity["name_es"],
                "why": T["why_activity"].format(tags=", ".join(_disp(a_hits[:3], lang)) or "—"),
            },
            "sweet_finish": {
                "name": sweet["name_" + lang] if "name_" + lang in sweet else sweet["name_es"],
                "why": T["dessert"],
            },
            "timeline": timeline,
            "budget_note": T["budget_note"].format(price=restaurant["price"]),
        },
    }

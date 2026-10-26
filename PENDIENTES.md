# PENDIENTES — Envío final en Devpost (Qloo Agentic Hackathon)

**Fecha límite: 30 de octubre de 2026, 11:45 PM EDT.** ⏰
Proyecto: «Sabor & Fiesta — Taste-Aware Event Concierge» (borrador 3/5 en Devpost, cuenta cristhiamacuna82).
Premios: $25,000 en total (1.º $15,000 · 2.º $6,000 · 3.º $4,000) + posible inversión extra de $25,000 de Jason Calacanis a su favorito.
⚠️ Los 3 finalistas presentan EN VIVO el 5 de noviembre (con Jason Calacanis, Cedric the Entertainer y Alex Elias) — si quedamos Top 3, Cristhiam debe aparecer en cámara/voz: decisión suya, preparar con tiempo.

---

## 1) 🔑 API key de Qloo — PASO DE CRISTHIAM, URGENTE (tarda días)

- [ ] Llenar el **formulario oficial de solicitud de API key** (gratis para participantes), enlazado en la guía oficial: https://docs.qloo.com/reference/qloo-llm-hackathon-developer-guide → «API Key Request Form» (forms.gle).
- La guía dice que la clave se entrega **por correo y puede tardar unos días laborables** → pedirla HOY (24-oct) para que llegue antes del 30-oct. Revisar la carpeta de **spam** (la guía advierte que suele caer ahí). Buzón: el de la cuenta del hackathon (cristhiamacuna82@gmail.com).
- Con la clave en mano, NO pegarla en chat público ni en el repo: se configura como variable de entorno `QLOO_API_KEY` en el servidor/hosting (ver README). La demo pasa sola a modo **qloo-live** (restaurantes y artistas reales de la API; base correcta: `https://hackathon.api.qloo.com`).
- Si la clave no llega a tiempo: el envío igual es válido con el modo local, PERO el criterio «Technological Implementation / uso de Qloo» puntúa mucho mejor en vivo → la clave es la prioridad #1.

## 2) 🐙 Repo público — NO consta cuenta de GitHub de Cristhiam

- [ ] Crear cuenta en github.com (paso de Cristhiam, con su correo cristhiamacuna82@gmail.com) — o confirmar si ya tiene una.
- [ ] Crear repo público, nombre sugerido: `sabor-y-fiesta`.
- [ ] Subir TODO el contenido de esta carpeta `qloo-demo/` (app.py, engine.py, qloo_client.py, data/, static/, README.md, LICENSE, Procfile, .gitignore). La licencia MIT ya está incluida y debe verse en el «About» del repo (requisito del hackathon).
- [ ] Verificar que NO se suba ninguna clave (`.env` está en .gitignore; la clave solo vive como variable de entorno).
- Comandos (desde esta carpeta):
  ```
  git init && git add . && git commit -m "Sabor & Fiesta — Qloo Agentic Hackathon"
  git branch -M main && git remote add origin https://github.com/<usuario>/sabor-y-fiesta.git
  git push -u origin main
  ```

## 3) 🌐 URL pública de la demo — OBLIGATORIO (lo local no califica)

Las reglas exigen demo **alojada y publicada externamente**; una demo que solo corre local NO es elegible.
Opción recomendada (gratis): **Render** (render.com)
- [ ] Crear cuenta (puede entrar con GitHub recién creado) → New → Web Service → conectar el repo `sabor-y-fiesta`.
- [ ] Start command: `python3 app.py` · Build command: *(vacío)*.
- [ ] Variable de entorno: `QLOO_API_KEY` = la clave del punto 1 (Render pone `PORT` solo).
- [ ] Abrir la URL pública resultante y probar el plan completo (formulario → plan).
Alternativas gratis con el mismo código: Railway, Fly.io, PythonAnywhere (con `Procfile` incluido sirve en plataformas tipo Heroku).

## 4) 📝 Campos del envío en Devpost (cuando lo anterior exista)

- [ ] **Fecha de inicio del desarrollo (start date): 24 de octubre de 2026** (día en que se construyó esta demo; el registro al hackathon también fue el 24-oct).
- [ ] **URL de la demo:** la pública del punto 3 (NO localhost).
- [ ] **URL del repo:** la del punto 2.
- [ ] **Descripción (debe ir en INGLÉS por reglas — texto listo para pegar):**

> **Sabor & Fiesta — Taste-Aware Event Concierge** is an agent that plans a complete night out from your taste. Tell it the food you love, the music that moves you, the vibe you want and your city, and it returns a full plan: a restaurant, the music (artists), a signature activity, a sweet finish, and a step-by-step timeline — plus an explicit map of *how your tastes connect across domains*.
>
> **How it uses Qloo:** the concierge resolves your favorite artists and cuisines into Qloo entities via `/search`, then calls the **Insights API** (`/v2/insights`) with those entities as interest signals to get cross-domain recommendations for places (`urn:entity:place`) and artists (`urn:entity:artist`) from Qloo's 250M+ entity taste graph. Your love of salsa doesn't just pick the playlist — it steers the kitchen, the venue and the energy of the night. An offline curated engine is included for transparency and resilience, and the UI always declares which data mode is active.
>
> **Why it matters:** Latino families plan birthdays, quinceañeras and anniversaries around food and music, but generic recommenders treat each category separately. Sabor & Fiesta treats taste as one connected graph — the way people actually feel it — and turns it into a plan in seconds, in English and Spanish.
>
> Built with Python (standard library only) + a self-contained web UI. MIT licensed.

- [ ] Confirmar los demás campos del borrador (track/categorías ya puestos en el registro).

## 5) Estado de la demo (verificado 2026-10-24)

- ✅ Corre local: `python3 app.py` → http://localhost:8000 (dejada corriendo y verificada en el puerto 8123 de esta máquina).
- ✅ Página carga (HTTP 200) y `/api/plan` responde planes completos en ES y EN; ciudad desconocida cae al set genérico sin romperse.
- ✅ Respaldo probado: con una clave falsa, la app cae al modo local sin error (nunca queda caída por culpa de la API).
- ⏳ Modo `qloo-live` queda activo automáticamente cuando exista `QLOO_API_KEY` válida (código en `qloo_client.py`, sin fingir respuestas).
- ❗ NO se ha tocado Devpost (esto es solo la construcción + checklist, como se pidió).

# Konfigurácia Claims AI Prototype

## Jediný zdroj pravdy: `.env.local`

Všetky nastavenia sa načítavajú z `.env.local` súboru, ktorý NIKDY neuploadujte na GitHub.

### Aktuálne nastavenia v `.env.local`:

```bash
# Google Cloud Platform - EU rezidencia
GOOGLE_APPLICATION_CREDENTIALS=claims-ai-prototype-1-abf1c40fc2d.json
GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1

# Vertex AI - EU rezidencia
USE_VERTEX_AI=1
VERTEX_AI_LOCATION=europe-west1

# Gemini AI – stabilný alias modelu pre Vertex AI
GEMINI_MODEL=gemini-2.0-flash

# Database
DATABASE_URL=sqlite:///claims_ai.db
```

## Hierarchia načítavania konfigurácie:

1. **`.env.local`** – jediný zdroj pravdy (override=True)
2. (Voliteľne) systémové environment premenné

## Dôležité súbory:

- **`.env.local`** – citlivé údaje, NIKDY na GitHub
- **`env.example`** – šablóna bez tajomstiev
- **`claims-ai-prototype-1-abf1c40fc2d.json`** – GCP service account

## Opravené problémy:

1. ✅ Zjednotená konfigurácia cez `.env.local`
2. ✅ EU rezidencia cez Vertex AI (europe-west1)
3. ✅ Stabilný model alias: `gemini-2.0-flash` (alebo `gemini-1.5-pro` / `gemini-1.5-flash`)
4. ✅ Odstránené duplicitné nastavenia
5. ✅ Jasná hierarchia načítavania

## Spustenie služieb:

```bash
# Streamlit (8501)
$env:USE_VERTEX_AI="1"; $env:VERTEX_AI_LOCATION="europe-west1"; $env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"; $env:GOOGLE_APPLICATION_CREDENTIALS="claims-ai-prototype-1-abf1c40fc2d.json"; streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0

# FastAPI (8000)
$env:USE_VERTEX_AI="1"; $env:VERTEX_AI_LOCATION="europe-west1"; $env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"; $env:GOOGLE_APPLICATION_CREDENTIALS="claims-ai-prototype-1-abf1c40fc2d.json"; uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

# Nástroj na Analýzu Poistných Udalostí

## Prehľad
Tento nástroj automatizuje spracovanie poistných dokumentov pomocou Google Cloud služieb:
- **Google Document AI** - OCR spracovanie PDF dokumentov
- **Google Cloud DLP** - anonymizácia citlivých údajov
- **Google Gemini AI** - AI analýza dokumentov
- **SQLite/MySQL** - ukladanie spracovaných dát
- **Streamlit** - webové rozhranie
- **FastAPI** - REST API s Swagger dokumentáciou

## Požiadavky

### Systémové požiadavky
- Python 3.8+
- Windows/Linux/macOS
- Minimálne 4GB RAM
- 2GB voľného miesta na disku

### Google Cloud Platform
- Aktívny GCP projekt s povolenými službami:
  - Document AI API
  - Cloud DLP API
  - Vertex AI API (pre Gemini)
- Service Account s JSON kľúčom
- Document AI processor
- DLP de-identify template
- DLP inspect template

### Python balíčky
Všetky závislosti sú v `requirements.txt`:
```
google-cloud-documentai
google-cloud-dlp
google-cloud-aiplatform
streamlit
fastapi
uvicorn
sqlalchemy
pymysql
configparser
```

## Inštalácia

### 1. Klonovanie repozitára
```bash
git clone <repository-url>
cd google-cloud
```

### 2. Inštalácia Python závislostí
```bash
pip install -r requirements.txt
```

### 3. Konfigurácia Google Cloud

#### 3.1 Service Account JSON kľúč
1. **GCP Console** → IAM & Admin → Service Accounts
2. **Vytvorte nový Service Account** alebo použite existujúci
3. **Pridajte role:**
   - Document AI API User
   - Cloud DLP User
   - Vertex AI User
4. **Vytvorte JSON kľúč** a stiahnite `service-account-key.json`
5. **Umiestnite súbor** do koreňového priečinka projektu

#### 3.2 Environment Variables
**Windows PowerShell:**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
$env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
$env:GEMINI_API_KEY="your-actual-gemini-api-key-here"
```

**Windows CMD:**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
set GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
set GEMINI_API_KEY=your-actual-gemini-api-key-here
```

**Linux/macOS:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
export GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
export GEMINI_API_KEY="your-actual-gemini-api-key-here"
```

#### 3.3 Gemini API Kľúč
1. **Google AI Studio** → https://makersuite.google.com/app/apikey
2. **Vytvorte nový API kľúč**
3. **Nastavte environment variable** `GEMINI_API_KEY`
4. **NIKDY NEUPLOADOVAŤ** API kľúč na GitHub!

#### 3.4 Použitie .env.local súboru (odporúčané)
1. **Skopírujte** `env.example` ako `.env.local`
2. **Upravte** `.env.local` s vašimi skutočnými hodnotami:
   ```bash
   # .env.local
   GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
   GEMINI_API_KEY=your-actual-gemini-api-key-here
   DATABASE_URL=sqlite:///claims_ai.db
   ```
3. **Aplikácia automaticky načíta** `.env.local` súbor
4. **NIKDY NEUPLOADOVAŤ** `.env.local` na GitHub!

### 4. Konfigurácia aplikácie

#### 4.1 config.ini (GCP nastavenia)
Upravte `config.ini` s vašimi GCP údajmi:

```ini
[gcp]
project_id = claims-ai-prototype-1

[document_ai]
location = eu
processor_id = 1e3f139679670c26
mime_type = application/pdf

[dlp]
location = europe-west3
template_id = projects/claims-ai-prototype-1/locations/europe-west3/deidentifyTemplates/de-identify-sensitive-data
inspect_template_id = projects/claims-ai-prototype-1/locations/europe-west3/inspectTemplates/find-sensitive-data

[gemini]
# api_key = YOUR_GEMINI_API_KEY  # NIKDY NEUPLOADOVAŤ!
model = gemini-1.5-flash-latest
analysis_prompt = Zhrň kľúčové body z nasledujúcich poistných dokumentov...

[database]
url = sqlite:///claims_ai.db
# Pre MySQL: mysql+pymysql://user:password@localhost/dbname
```

#### 4.2 Dôležité poznámky
- **project_id**: Použite váš GCP projekt ID
- **processor_id**: Document AI processor ID z GCP Console
- **template_id**: DLP de-identify template ID
- **inspect_template_id**: DLP inspect template ID
- **api_key**: NIKDY NEUPLOADOVAŤ - použite environment variable

#### 4.3 Environment Variables - Prehľad
```bash
# Povinné pre funkčnosť aplikácie:
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Voliteľné:
DATABASE_URL=sqlite:///claims_ai.db
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
API_HOST=0.0.0.0
API_PORT=8000
```

#### 4.4 Bezpečnostné odporúčania
- **NIKDY NEUPLOADOVAŤ** `service-account-key.json` na GitHub
- **NIKDY NEUPLOADOVAŤ** `.env.local` súbor na GitHub
- **NIKDY NEUPLOADOVAŤ** API kľúče v kóde
- **Používajte environment variables** pre všetky citlivé údaje
- **Skontrolujte .gitignore** pred každým commitom

## Používanie

### Streamlit Webová Aplikácia

#### 5.1 Spustenie aplikácie
```bash
# Nastavte environment variables
$env:GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
$env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
$env:GEMINI_API_KEY="your-actual-gemini-api-key-here"

# Spustite Streamlit
streamlit run app_streamlit.py
```

#### 5.2 Prístup k aplikácii
- **URL**: http://localhost:8501
- **Funkcie**:
  - Upload PDF dokumentov
  - Spracovanie poistných udalostí
  - Zobrazenie OCR textu vs. anonymizovaného textu
  - Prehľad databázy
  - Spracovanie citlivých a všeobecných dokumentov

### FastAPI REST API

#### 6.1 Spustenie API
```bash
# Nastavte environment variables
$env:GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
$env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
$env:GEMINI_API_KEY="your-actual-gemini-api-key-here"

# Spustite FastAPI
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

#### 6.2 Prístup k API
- **API URL**: http://localhost:8000
- **Swagger dokumentácia**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Health check**: http://localhost:8000/health

#### API Endpointy

##### Základné
- `GET /health` - Stav služby
- `GET /events/{event_id}/documents` - Zoznam spracovaných dokumentov
- `GET /events/{event_id}/pdfs` - Zoznam dostupných PDF súborov

##### Spracovanie dokumentov
- `POST /upload/{event_id}` - Upload PDF súboru
- `POST /ocr/{event_id}` - OCR spracovanie PDF
- `POST /anonymize/{event_id}` - Anonymizácia textu
- `POST /analysis/single/{event_id}` - Analýza jedného dokumentu
- `POST /analysis/batch/{event_id}` - Analýza všetkých dokumentov v udalosti
- `POST /process/{event_id}` - Kompletné spracovanie (OCR + anonymizácia + analýza)

##### Anonymizácia a identifikácia
- `POST /anonymize/{event_id}` - Anonymizácia existujúceho OCR textu
- `POST /anonymize/{event_id}` s `{"filename": "súbor.txt"}` - Anonymizácia konkrétneho súboru
- `POST /inspect/{event_id}` - Identifikácia citlivých dát v texte
- `POST /inspect/{event_id}` s `{"filename": "súbor.txt"}` - Identifikácia v konkrétnom súbore

#### Príklady použitia API

##### Upload PDF
```bash
curl -X POST "http://localhost:8000/upload/test-event" \
  -H "accept: application/json" \
  -F "file=@document.pdf"
```

##### OCR spracovanie
```bash
curl -X POST "http://localhost:8000/ocr/test-event" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.pdf"}'
```

##### Kompletné spracovanie
```bash
curl -X POST "http://localhost:8000/process/test-event" \
  -H "accept: application/json"
```

##### Anonymizácia textu
```bash
curl -X POST "http://localhost:8000/anonymize/test-event" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.txt"}'
```

##### Identifikácia citlivých dát
```bash
curl -X POST "http://localhost:8000/inspect/test-event" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"filename": "document.txt"}'
```

## Štruktúra projektu

```
google-cloud/
├── app_streamlit.py          # Streamlit webová aplikácia
├── api.py                    # FastAPI REST API
├── main.py                   # OCR a anonymizácia
├── analyza.py                # AI analýza
├── db.py                     # Databázové modely
├── config.ini                # Konfigurácia
├── requirements.txt          # Python závislosti
├── claims-ai.db             # SQLite databáza
├── poistne_udalosti/        # Vstupné PDF dokumenty
│   ├── {event_id}/
│   │   ├── citlive_dokumenty/
│   │   └── vseobecne_dokumenty/
├── raw_ocr_output/          # OCR výstup
├── anonymized_output/        # Anonymizovaný text
├── general_output/           # Všeobecné dokumenty
└── analysis_output/          # AI analýzy
```

## Databáza

### SQLite (predvolené)
- Automaticky sa vytvorí `claims_ai.db`
- Vhodné pre testovanie a malé nasadenia

### MySQL (produkčné)
1. Vytvorte MySQL databázu
2. Upravte `config.ini`:
   ```ini
   [database]
   url = mysql+pymysql://user:password@localhost/dbname
   ```
3. Inštalujte MySQL driver: `pip install pymysql`

### Databázové tabuľky
- `claim_events` - Poistné udalosti
- `document_texts` - OCR a anonymizované texty
- `analysis_results` - AI analýzy

## Testovanie aplikácie

### 7.1 Kontrola funkčnosti
1. **Spustite Streamlit**: `streamlit run app_streamlit.py`
2. **Spustite FastAPI**: `uvicorn api:app --reload`
3. **Otestujte API endpointy** cez Swagger UI
4. **Upload test PDF** a spracujte ho

### 7.2 Testovacie kroky
```bash
# 1. Kontrola health endpointu
curl http://localhost:8000/health

# 2. Upload test PDF
curl -X POST "http://localhost:8000/upload/test-event" \
  -F "file=@test-document.pdf"

# 3. OCR spracovanie
curl -X POST "http://localhost:8000/ocr/test-event" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test-document.pdf"}'

# 4. Anonymizácia
curl -X POST "http://localhost:8000/anonymize/test-event" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test-document.pdf"}'
```

## Troubleshooting

### Časté chyby

#### 403 Permission denied
- Skontrolujte service account JSON kľúč
- Overte `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Skontrolujte oprávnenia v GCP Console

#### 404 Processor not found
- Overte `processor_id` v `config.ini`
- Skontrolujte, či processor existuje v správnom regióne

#### 400 API key not valid (Gemini)
- Skontrolujte `gemini.api_key` v `config.ini`
- Overte platnosť API kľúča

#### Databázové chyby
- Skontrolujte `database.url` v `config.ini`
- Pre MySQL overte pripojenie a oprávnenia

### Logy
- Streamlit: Konzola kde ste spustili aplikáciu
- FastAPI: Konzola kde beží uvicorn
- Databáza: `claims_ai.db` (SQLite) alebo MySQL logy

## Nasadenie v produkcii

### 1. Produkčná databáza
- Použite MySQL alebo PostgreSQL
- Nastavte správne oprávnenia a backup

### 2. Environment variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export DATABASE_URL="mysql+pymysql://user:password@host/dbname"
```

### 3. Reverse proxy
- Nginx alebo Apache pre produkčné nasadenie
- SSL certifikáty
- Firewall pravidlá

### 4. Monitoring
- Logy aplikácie
- Metriky databázy
- GCP monitoring

## Docker Nasadenie

### Rýchle spustenie s Docker Compose
```bash
# Spustenie všetkých služieb
docker-compose up -d

# Kontrola stavu
docker-compose ps

# Logy
docker-compose logs -f claims_ai
```

### Docker Compose služby
- **claims_ai**: Hlavná aplikácia (Streamlit + FastAPI)
- **mysql**: MySQL databáza
- **nginx**: Reverse proxy (voliteľné)

### Porty
- **8501**: Streamlit webová aplikácia
- **8000**: FastAPI REST API
- **3306**: MySQL databáza
- **80/443**: Nginx (HTTP/HTTPS)

## Produkčné nasadenie

### Infraštruktúra
- **Minimálne**: 4 vCPU, 8GB RAM, 50GB SSD
- **Odporúčané**: 8 vCPU, 16GB RAM, 100GB SSD
- **OS**: Ubuntu 22.04 LTS

### Bezpečnosť

#### ⚠️ **KRITICKÉ: Ochrana citlivých údajov**
- **NIKDY NEUPLOADOVAŤ** `service-account-key.json` na GitHub
- **NIKDY NEUPLOADOVAŤ** `.env` súbory s API kľúčmi
- **NIKDY NEUPLOADOVAŤ** `claims-ai-prototype-1-*.json` súbory

#### Bezpečnostné opatrenia
- Všetky citlivé súbory sú v `.gitignore`
- Používajte `.env.local` pre lokálne nastavenia
- Service account kľúče majú minimálne potrebné oprávnenia
- Databázové credentials sú bezpečné

#### SSL/HTTPS
- SSL/HTTPS certifikáty
- Firewall pravidlá
- Service account s minimálnymi oprávneniami
- Databázové credentials

### Monitoring a Backup
- Health checks pre všetky služby
- Automatické backup databázy
- Log aggregation
- Performance metrik

## Podpora

Pre technickú podporu kontaktujte:
- Email: [vaša email adresa]
- Dokumentácia: [link na internú dokumentáciu]
- Issue tracker: [link na GitHub issues]

## Licencia

Interné použitie - Novis Claims Team

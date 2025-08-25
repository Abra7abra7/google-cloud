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
1. Stiahnite service account JSON kľúč z GCP Console
2. Umiestnite `service-account-key.json` do koreňového priečinka
3. Nastavte environment variable:
   ```bash
   # Windows PowerShell
   $env:GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
   
   # Windows CMD
   set GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   
   # Linux/macOS
   export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
   ```

### 4. Konfigurácia aplikácie
Upravte `config.ini` s vašimi GCP údajmi:

```ini
[google_cloud]
project_id = YOUR_PROJECT_ID
location = europe-west3

[document_ai]
processor_id = YOUR_PROCESSOR_ID
location = europe-west3

[dlp]
location = europe-west3
template_id = projects/YOUR_PROJECT_ID/locations/europe-west3/deidentifyTemplates/YOUR_TEMPLATE_ID
inspect_template_id = projects/YOUR_PROJECT_ID/locations/europe-west3/inspectTemplates/YOUR_TEMPLATE_ID

[gemini]
api_key = YOUR_GEMINI_API_KEY
model = gemini-1.5-flash

[database]
url = sqlite:///claims_ai.db
# Pre MySQL: mysql+pymysql://user:password@localhost/dbname
```

## Používanie

### Streamlit Webová Aplikácia
```bash
streamlit run app_streamlit.py
```
- URL: http://localhost:8501
- Upload PDF dokumentov
- Spracovanie poistných udalostí
- Zobrazenie OCR textu vs. anonymizovaného textu
- Prehľad databázy

### FastAPI REST API
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
- URL: http://localhost:8000
- Swagger dokumentácia: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

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

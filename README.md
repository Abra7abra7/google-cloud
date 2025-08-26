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
Všetky závislosti sú v `requirements.txt` (Streamlit, FastAPI, Vertex AI, Document AI, DLP, SQLAlchemy,...).

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

#### 3.2 Použitie `.env.local` (jediný zdroj pravdy)
1. Skopírujte `env.example` ako `.env.local`
2. Vyplňte hodnoty (Vertex AI v EU, alias modelu):
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
   USE_VERTEX_AI=1
   VERTEX_AI_LOCATION=europe-west1
   GEMINI_MODEL=gemini-2.0-flash   # alebo gemini-1.5-pro / gemini-1.5-flash
   ANALYSIS_PROMPT=Zhrň kľúčové body z nasledujúcich poistných dokumentov...
   DATABASE_URL=sqlite:///claims_ai.db
   ```
3. `.env.local` sa načíta automaticky pri štarte aplikácií
4. `.env.local` a JSON kľúč NIKDY neuploadovať na GitHub

### 4. Konfigurácia aplikácie (skrátene)
Všetky nastavenia sú v `.env.local`. Žiadny `config.ini` sa už nepoužíva.

#### 4.1 Environment Variables - Prehľad
```bash
GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT, USE_VERTEX_AI, VERTEX_AI_LOCATION,
GEMINI_MODEL (aliasy: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash),
ANALYSIS_PROMPT, DATABASE_URL, STREAMLIT_SERVER_PORT, STREAMLIT_SERVER_ADDRESS, API_HOST, API_PORT
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
# Streamlit (port 8502)
streamlit run app_streamlit.py --server.port 8502 --server.address 0.0.0.0
```

#### 5.2 Prístup k aplikácii
- **URL**: http://localhost:8502
- **Funkcie**:
  - Upload PDF dokumentov
  - Spracovanie poistných udalostí
  - Zobrazenie OCR textu vs. anonymizovaného textu
  - Prehľad databázy
  - Spracovanie citlivých a všeobecných dokumentov

### FastAPI REST API

#### 6.1 Spustenie API
```bash
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
├── KONFIGURACIA.md           # Zhrnutie konfigurácie (.env.local je zdroj pravdy)
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
2. Do `.env.local` nastavte `DATABASE_URL`, napr. `mysql+pymysql://user:password@localhost:3306/claims_ai`
3. Inštalujte MySQL driver: `pip install pymysql`

### Databázové tabuľky
- `claim_events` - Poistné udalosti
- `document_texts` - OCR a anonymizované texty
- `analysis_results` - AI analýzy

## Testovanie aplikácie

### 7.1 Kontrola funkčnosti
1. **Spustite Streamlit**: `streamlit run app_streamlit.py --server.port 8502 --server.address 0.0.0.0`
2. **Spustite FastAPI**: `uvicorn api:app --host 0.0.0.0 --port 8000 --reload`
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

## Nasadenie na rôzne servery

### Podporované operačné systémy
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 9+, RHEL 7+, Amazon Linux 2
- **Windows**: Windows Server 2016+, Windows 10/11, Windows Server Core
- **macOS**: macOS 10.15+
- **Cloud**: AWS EC2, Google Cloud, Azure, DigitalOcean, VPS

### Požiadavky na server
- **Minimálne**: 2 vCPU, 4GB RAM, 20GB disk
- **Odporúčané**: 4-8 vCPU, 8-16GB RAM, 50-100GB SSD
- **OS**: Linux (odporúčané), Windows, macOS

### Nasadenie na Linux server

#### Ubuntu/Debian
```bash
# 1. Aktualizácia systému
sudo apt update && sudo apt upgrade -y

# 2. Inštalácia Python a Git
sudo apt install -y python3 python3-pip python3-venv git curl

# 3. Vytvorenie Python virtual environment
python3 -m venv claims-ai-env
source claims-ai-env/bin/activate

# 4. Klonovanie repozitára
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud

# 5. Inštalácia závislostí
pip install -r requirements.txt

# 6. Nastavenie environment variables
export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
export GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
export GEMINI_API_KEY="your-actual-gemini-api-key-here"

# 7. Spustenie aplikácie
streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0 &
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### CentOS/RHEL
```bash
# 1. Aktualizácia systému
sudo yum update -y

# 2. Inštalácia Python a Git
sudo yum install -y python3 python3-pip git curl

# 3. Vytvorenie Python virtual environment
python3 -m venv claims-ai-env
source claims-ai-env/bin/activate

# 4. Pokračovanie rovnako ako Ubuntu
```

#### Systemd služby (Linux)
```bash
# 1. Vytvorenie systemd služby pre Streamlit
sudo tee /etc/systemd/system/claims-ai-streamlit.service << EOF
[Unit]
Description=Claims AI Streamlit Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/google-cloud
Environment=GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/google-cloud/service-account-key.json
Environment=GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
Environment=GEMINI_API_KEY=your-actual-gemini-api-key-here
ExecStart=/home/ubuntu/claims-ai-env/bin/streamlit run app_streamlit.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 2. Vytvorenie systemd služby pre FastAPI
sudo tee /etc/systemd/system/claims-ai-api.service << EOF
[Unit]
Description=Claims AI FastAPI Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/google-cloud
Environment=GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/google-cloud/service-account-key.json
Environment=GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
Environment=GEMINI_API_KEY=your-actual-gemini-api-key-here
ExecStart=/home/ubuntu/claims-ai-env/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 3. Aktivácia a spustenie služieb
sudo systemctl daemon-reload
sudo systemctl enable claims-ai-streamlit
sudo systemctl enable claims-ai-api
sudo systemctl start claims-ai-streamlit
sudo systemctl start claims-ai-api

# 4. Kontrola stavu
sudo systemctl status claims-ai-streamlit
sudo systemctl status claims-ai-api
```

### Nasadenie na Windows server

#### Windows Server 2016/2019/2022
```powershell
# 1. Inštalácia Python (stiahnite z python.org)
# 2. Inštalácia Git (stiahnite z git-scm.com)

# 3. Otvorte PowerShell ako Administrator
# 4. Vytvorenie Python virtual environment
python -m venv claims-ai-env
.\claims-ai-env\Scripts\Activate.ps1

# 5. Klonovanie repozitára
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud

# 6. Inštalácia závislostí
pip install -r requirements.txt

# 7. Nastavenie environment variables
$env:GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
$env:GOOGLE_CLOUD_PROJECT="claims-ai-prototype-1"
$env:GEMINI_API_KEY="your-actual-gemini-api-key-here"

# 8. Spustenie aplikácie
Start-Process -FilePath "streamlit" -ArgumentList "run app_streamlit.py --server.port 8501 --server.address 0.0.0.0"
Start-Process -FilePath "uvicorn" -ArgumentList "api:app --host 0.0.0.0 --port 8000"
```

#### Windows služby (NSSM)
```powershell
# 1. Stiahnite NSSM: https://nssm.cc/download
# 2. Vytvorenie Windows služby pre Streamlit
nssm install ClaimsAIStreamlit "C:\Users\Administrator\claims-ai-env\Scripts\streamlit.exe" "run app_streamlit.py --server.port 8501 --server.address 0.0.0.0"
nssm set ClaimsAIStreamlit AppDirectory "C:\Users\Administrator\google-cloud"
nssm set ClaimsAIStreamlit AppEnvironmentExtra GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
nssm set ClaimsAIStreamlit AppEnvironmentExtra GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
nssm set ClaimsAIStreamlit AppEnvironmentExtra GEMINI_API_KEY=your-actual-gemini-api-key-here

# 3. Vytvorenie Windows služby pre FastAPI
nssm install ClaimsAIAPI "C:\Users\Administrator\claims-ai-env\Scripts\uvicorn.exe" "api:app --host 0.0.0.0 --port 8000"
nssm set ClaimsAIAPI AppDirectory "C:\Users\Administrator\google-cloud"
nssm set ClaimsAIAPI AppEnvironmentExtra GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
nssm set ClaimsAIAPI AppEnvironmentExtra GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1
nssm set ClaimsAIAPI AppEnvironmentExtra GEMINI_API_KEY=your-actual-gemini-api-key-here

# 4. Spustenie služieb
Start-Service ClaimsAIStreamlit
Start-Service ClaimsAIAPI
```

### Nasadenie cez Docker (univerzálne pre všetky OS)

#### Docker Compose
```bash
# 1. Inštalácia Docker a Docker Compose
# Linux: curl -fsSL https://get.docker.com | sh
# Windows: Docker Desktop
# macOS: Docker Desktop

# 2. Klonovanie repozitára
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud

# 3. Vytvorenie .env súboru
cp env.example .env
# Upravte .env s vašimi hodnotami

# 4. Spustenie cez Docker Compose
docker-compose up -d

# 5. Kontrola stavu
docker-compose ps
docker-compose logs -f claims_ai
```

### Nasadenie na cloud platformy

#### AWS EC2
```bash
# 1. Spustenie Ubuntu 22.04 LTS instance
# 2. Pripojenie cez SSH
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Inštalácia Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# 4. Klonovanie a spustenie
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud
docker-compose up -d

# 5. Konfigurácia security groups
# - Port 8501 (Streamlit)
# - Port 8000 (FastAPI)
# - Port 22 (SSH)
```

#### Google Cloud Compute Engine
```bash
# 1. Spustenie Ubuntu 22.04 LTS instance
# 2. Pripojenie cez Cloud Shell alebo SSH
gcloud compute ssh your-instance-name --zone=your-zone

# 3. Inštalácia Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 4. Klonovanie a spustenie
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud
docker-compose up -d

# 5. Konfigurácia firewall rules
gcloud compute firewall-rules create claims-ai-streamlit --allow tcp:8501
gcloud compute firewall-rules create claims-ai-api --allow tcp:8000
```

#### Azure Virtual Machines
```bash
# 1. Spustenie Ubuntu 22.04 LTS VM
# 2. Pripojenie cez SSH
ssh azureuser@your-vm-ip

# 3. Inštalácia Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker azureuser
newgrp docker

# 4. Klonovanie a spustenie
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud
docker-compose up -d

# 5. Konfigurácia Network Security Groups
# - Port 8501 (Streamlit)
# - Port 8000 (FastAPI)
# - Port 22 (SSH)
```

#### DigitalOcean Droplet
```bash
# 1. Vytvorenie Ubuntu 22.04 LTS Droplet
# 2. Pripojenie cez SSH
ssh root@your-droplet-ip

# 3. Inštalácia Docker
curl -fsSL https://get.docker.com | sh

# 4. Klonovanie a spustenie
git clone https://github.com/Abra7abra7/google-cloud.git
cd google-cloud
docker-compose up -d

# 5. Konfigurácia firewall
ufw allow 8501
ufw allow 8000
ufw allow 22
ufw enable
```

### Reverse Proxy a SSL (produkčné nasadenie)

#### Nginx konfigurácia
```bash
# 1. Inštalácia Nginx
sudo apt install -y nginx

# 2. Vytvorenie Nginx konfigurácie
sudo tee /etc/nginx/sites-available/claims-ai << EOF
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certifikáty
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Streamlit aplikácia
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # FastAPI
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 3. Aktivácia konfigurácie
sudo ln -s /etc/nginx/sites-available/claims-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Let's Encrypt SSL certifikát
```bash
# 1. Inštalácia Certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. Získanie SSL certifikátu
sudo certbot --nginx -d your-domain.com

# 3. Automatické obnovovanie
sudo crontab -e
# Pridajte: 0 12 * * * /usr/bin/certbot renew --quiet
```

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

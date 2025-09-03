# Checklist validácie konfigurácie Claims AI

## ⚠️ KRITICKÉ: Tieto hodnoty musia byť SKUTOČNE platné, nie placeholdery!

### 1. Google Cloud Service Account
- [ ] **GOOGLE_APPLICATION_CREDENTIALS** - cesta k JSON súboru existuje a je čitateľná
- [ ] **GOOGLE_CLOUD_PROJECT** - projekt ID je skutočný a aktívny
- [ ] Service account má potrebné role:
  - [ ] Document AI API User
  - [ ] Cloud DLP User  
  - [ ] Vertex AI User (ak USE_VERTEX_AI=1)

### 2. Document AI (OCR)
- [ ] **DOCUMENT_AI_PROCESSOR_ID** - SKUTOČNÉ ID processora (nie "your-processor-id")
- [ ] **DOCUMENT_AI_LOCATION** - región processora (napr. "eu", "us", "asia")
- [ ] Processor existuje v GCP Console a je aktívny
- [ ] Processor má povolené OCR pre PDF súbory

**Kontrola:**
```bash
# V GCP Console: Document AI > Processors
# Skopírujte Processor ID (nie názov, ale ID)
```

### 3. Cloud DLP (Anonymizácia)
- [ ] **DLP_DEIDENTIFY_TEMPLATE_ID** - SKUTOČNÉ ID de-identify šablóny
- [ ] **DLP_INSPECT_TEMPLATE_ID** - SKUTOČNÉ ID inspect šablóny (voliteľné)
- [ ] **DLP_LOCATION** - región šablón (napr. "europe-west3")
- [ ] Šablóny existujú v GCP Console a sú aktívne

**Kontrola:**
```bash
# V GCP Console: Security > Sensitive Data Protection > De-identify templates
# Skopírujte plné resource meno: projects/PROJECT/locations/REGION/deidentifyTemplates/TEMPLATE_ID
```

### 4. Vertex AI (Analýza)
- [ ] **USE_VERTEX_AI=1** - ak chcete používať Vertex AI
- [ ] **VERTEX_AI_LOCATION** - región (napr. "europe-west1")
- [ ] **GEMINI_MODEL** - platný model (napr. "gemini-2.0-flash")
- [ ] Vertex AI API je povolené v projekte
- [ ] Service account má Vertex AI User rolu

**Alternatíva (Google AI Studio):**
- [ ] **USE_VERTEX_AI=0** - ak chcete používať Google AI Studio
- [ ] **GEMINI_API_KEY** - platný API kľúč z Google AI Studio

### 5. Databáza
- [ ] **DATABASE_URL** - platná URL (SQLite alebo MySQL)
- [ ] Ak MySQL: databáza existuje a je dostupná
- [ ] Ak SQLite: priečinok je zapisovateľný

## 🔍 Diagnostické kroky

### Krok 1: Overenie .env.local
```bash
# Skontrolujte, že súbor existuje a obsahuje skutočné hodnoty
cat .env.local | grep -E "(PROCESSOR_ID|TEMPLATE_ID|API_KEY)"
```

### Krok 2: Test Google Cloud pripojenia
```bash
# Test service account
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))
print('Credentials:', os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
"
```

### Krok 3: Test Document AI
```bash
# Test processora (nahraďte skutočným ID)
python -c "
from main import PROJECT_ID, DOC_AI_LOCATION, PROCESSOR_ID
print(f'Testing Document AI: {PROJECT_ID}/{DOC_AI_LOCATION}/{PROCESSOR_ID}')
"
```

### Krok 4: Test DLP
```bash
# Test DLP šablóny (nahraďte skutočným ID)
python -c "
from main import PROJECT_ID, DLP_LOCATION, DLP_TEMPLATE_ID
print(f'Testing DLP: {PROJECT_ID}/{DLP_LOCATION}/{DLP_TEMPLATE_ID}')
"
```

### Krok 5: Test Vertex AI
```bash
# Test Vertex AI inicializácie
python -c "
from analyza import USE_VERTEX_AI, GCP_PROJECT, VERTEX_LOCATION
print(f'Vertex AI: {USE_VERTEX_AI}, Project: {GCP_PROJECT}, Location: {VERTEX_LOCATION}')
"
```

## 🚨 Časté chyby

### Chyba 1: Placeholder hodnoty
```
❌ DOCUMENT_AI_PROCESSOR_ID=your-processor-id
✅ DOCUMENT_AI_PROCESSOR_ID=abc123def456
```

### Chyba 2: Nesprávny región
```
❌ DOCUMENT_AI_LOCATION=eu (ale processor je v us)
✅ DOCUMENT_AI_LOCATION=us
```

### Chyba 3: Neúplné DLP template ID
```
❌ DLP_DEIDENTIFY_TEMPLATE_ID=template-123
✅ DLP_DEIDENTIFY_TEMPLATE_ID=projects/claims-ai-prototype-1/locations/europe-west3/deidentifyTemplates/template-123
```

### Chyba 4: Vertex AI bez oprávnení
```
❌ Service account nemá Vertex AI User rolu
✅ Pridajte rolu v GCP Console: IAM & Admin > Service Accounts
```

## 📋 Kompletný príklad .env.local

```bash
# Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS=claims-ai-prototype-1-abf1c40fcb2d.json
GOOGLE_CLOUD_PROJECT=claims-ai-prototype-1

# Vertex AI (EU rezidencia)
USE_VERTEX_AI=1
VERTEX_AI_LOCATION=europe-west1
GEMINI_MODEL=gemini-2.0-flash

# Document AI
DOCUMENT_AI_LOCATION=eu
DOCUMENT_AI_PROCESSOR_ID=abc123def456789  # SKUTOČNÉ ID!
DOCUMENT_AI_MIME_TYPE=application/pdf

# Cloud DLP
DLP_LOCATION=europe-west3
DLP_DEIDENTIFY_TEMPLATE_ID=projects/claims-ai-prototype-1/locations/europe-west3/deidentifyTemplates/def456ghi789  # SKUTOČNÉ ID!
DLP_INSPECT_TEMPLATE_ID=projects/claims-ai-prototype-1/locations/europe-west3/inspectTemplates/ghi789jkl012  # SKUTOČNÉ ID!

# Databáza
DATABASE_URL=sqlite:///claims_ai.db

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000
```

## 🔧 Rýchle opravy

### Ak OCR nefunguje:
1. Skontrolujte `DOCUMENT_AI_PROCESSOR_ID` - musí byť skutočné ID
2. Skontrolujte `DOCUMENT_AI_LOCATION` - musí sedieť s regiónom processora
3. Overte, že processor je aktívny v GCP Console

### Ak anonymizácia nefunguje:
1. Skontrolujte `DLP_DEIDENTIFY_TEMPLATE_ID` - musí byť plné resource meno
2. Skontrolujte `DLP_LOCATION` - musí sedieť s regiónom šablóny
3. Overte, že šablóna existuje a je aktívna

### Ak analýza nefunguje:
1. Pre Vertex AI: skontrolujte `USE_VERTEX_AI=1` a Vertex AI oprávnenia
2. Pre Google AI Studio: skontrolujte `USE_VERTEX_AI=0` a `GEMINI_API_KEY`
3. Overte, že model je dostupný v zvolenom regióne

## 📞 Podpora

Ak problémy pretrvávajú:
1. Skontrolujte GCP Console pre aktívne služby
2. Overte IAM oprávnenia pre service account
3. Skontrolujte kvóty a limity v GCP
4. Pozrite si logy v Streamlit konzole pre konkrétne chybové hlásenia

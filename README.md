# Nástroj na spracovanie a analýzu dokumentov pomocou Google Cloud AI

Tento projekt automatizuje proces extrakcie textu (OCR), selektívnej anonymizácie citlivých dát a inteligentnej analýzy obsahu dokumentov spojených s poistnými udalosťami. Využíva na to služby Google Cloud: Document AI, Data Loss Prevention (DLP) a Vertex AI (model Gemini).

## Architektúra

Celý proces je rozdelený na dva hlavné kroky, ktoré riadia dva samostatné skripty:

1.  **`main.py` - Spracovanie a anonymizácia:**
    *   Načíta všetky dokumenty z priečinka konkrétnej poistnej udalosti.
    *   Rozlišuje medzi citlivými a všeobecnými dokumentmi.
    *   Na **citlivé dokumenty** aplikuje OCR (Document AI) a následne anonymizáciu (DLP).
    *   Na **všeobecné dokumenty** aplikuje iba OCR.
    *   Výstupy ukladá do prehľadnej štruktúry v priečinkoch `anonymized_output/` a `general_output/`.

2.  **`analyza.py` - Analýza obsahu:**
    *   Načíta všetky spracované texty (anonymizované aj všeobecné) pre danú poistnú udalosť.
    *   Spojí ich do jedného komplexného kontextu.
    *   Tento kontext pošle na analýzu modelu **Gemini** cez Vertex AI, ktorý vygeneruje súhrn alebo odpovie na zadané otázky.

## Požiadavky

*   Python 3.8+
*   Účet na Google Cloud Platform s aktivovanými API: Document AI, DLP, Vertex AI.
*   Autentifikačný súbor (service account key) pre prístup k GCP.
*   Nainštalované knižnice (pozri `requirements.txt`).

## Inštalácia

1.  **Klonovanie repozitára:**
    ```bash
    git clone <URL_repozitara>
    cd google-cloud
    ```

2.  **Inštalácia závislostí:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Nastavenie autentifikácie:**
    Nastavte environmentálnu premennú `GOOGLE_APPLICATION_CREDENTIALS` tak, aby ukazovala na váš JSON kľúč.
    ```bash
    # Pre Windows (v príkazovom riadku)
    set GOOGLE_APPLICATION_CREDENTIALS="C:\cesta\k\vasmu\klucu.json"

    # Pre PowerShell
    $env:GOOGLE_APPLICATION_CREDENTIALS="C:\cesta\k\vasmu\klucu.json"
    ```

## Konfigurácia (`config.ini`)

Všetky nastavenia projektu sa nachádzajú v súbore `config.ini`. Pred prvým spustením si ho skontrolujte a prispôsobte.

*   **[gcp]**: `project_id` - ID vášho Google Cloud projektu.
*   **[document_ai]**: `location`, `processor_id`, `mime_type` - Nastavenia pre Document AI.
*   **[dlp]**: `template_id` - ID de-identifikačnej šablóny pre DLP.
*   **[analysis]**: `location`, `model_name`, `prompt` - Nastavenia pre model Gemini (napr. `gemini-1.5-flash-001`) a zadanie pre analýzu.

## Použitie

Existujú dva spôsoby použitia nástroja: cez grafické rozhranie (odporúčané) alebo cez príkazový riadok.

### Webové rozhranie (odporúčané)

Pre najjednoduchšie a najmodernejšie použitie spustite aplikáciu pomocou Streamlit:

```bash
streamlit run app_streamlit.py
```

Aplikácia sa automaticky otvorí vo vašom webovom prehliadači.

1.  V ľavom paneli si vyberte poistnú udalosť, ktorú chcete spracovať.
2.  Kliknite na tlačidlo **"Spracovať a analyzovať udalosť"**.
3.  Sledujte priebeh v reálnom čase priamo na stránke.
4.  Po dokončení sa zobrazí výsledok analýzy a môžete si ho stiahnuť.

### Príkazový riadok (CLI)


### 1. Príprava dát

Vytvorte si hlavný priečinok (napr. `poistne_udalosti`) a v ňom pre každú udalosť samostatný podpriečinok. Názov tohto podpriečinka slúži ako **ID udalosti**.

V každom priečinku udalosti vytvorte nasledujúce dva podpriečinky:

*   `citlive_dokumenty/`: Sem vložte všetky PDF, ktoré obsahujú osobné údaje a **vyžadujú anonymizáciu**.
*   `vseobecne_dokumenty/`: Sem vložte všetky PDF, ktoré sú bezpečné a **nevyžadujú anonymizáciu**.

**Príklad štruktúry:**
```
poistne_udalosti/
└── PU_12345/                  <-- ID udalosti je 'PU_12345'
    ├── citlive_dokumenty/
    │   └── lekarska_sprava.pdf
    └── vseobecne_dokumenty/
        └── poistne_podmienky.pdf
```

### 2. Spracovanie a anonymizácia

Spustite skript `main.py` a ako argument mu odovzdajte cestu k priečinku konkrétnej poistnej udalosti.

```bash
python main.py "C:\cesta\k\poistne_udalosti\PU_12345"
```
Skript automaticky vytvorí priečinky `anonymized_output/PU_12345` a `general_output/PU_12345` s výslednými `.txt` súbormi.

### 3. Analýza

Po dokončení spracovania spustite skript `analyza.py` a ako argument mu odovzdajte **ID udalosti**.

```bash
python analyza.py PU_12345
```
Skript načíta všetky relevantné texty a výslednú analýzu od modelu Gemini uloží do súboru v priečinku `analysis_output`.

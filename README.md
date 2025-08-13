# Nástroj na Analýzu Poistných Udalostí

Tento projekt je webová aplikácia postavená na Streamlite, ktorá automatizuje spracovanie a analýzu dokumentov z poistných udalostí. Využíva služby Google Cloud (Document AI, DLP, Gemini) na extrakciu textu (OCR), selektívnu anonymizáciu citlivých dát a generovanie súhrnnej analýzy.

## Kľúčové funkcie

- **Moderné webové UI:** Jednoduché a intuitívne rozhranie vytvorené pomocou Streamlitu.
- **Vytváranie udalostí priamo v UI:** Používatelia môžu vytvárať nové poistné udalosti a nahrávať PDF dokumenty priamo v aplikácii.
- **Selektívna anonymizácia:** Rozlišuje medzi citlivými a všeobecnými dokumentmi. Citlivé prechádzajú anonymizáciou cez Google Cloud DLP.
- **AI Analýza:** Všetky texty z jednej udalosti sú spojené a odoslané na analýzu modelu Google Gemini, ktorý vygeneruje súhrnný report.
- **Human-in-the-Loop kontrola:** Aplikácia ukladá a zobrazuje všetky medzikroky (pôvodný OCR text, anonymizovaný text), čo umožňuje jednoduchú kontrolu a validáciu.
- **Prehľad vstupných dát:** Pred spustením spracovania si môžete skontrolovať zoznam všetkých nahratých súborov.
- **Perzistentné výsledky:** Aplikácia si "pamätá" už spracované udalosti a okamžite zobrazí výsledky bez nutnosti opätovného spracovania.

## Požiadavky

1.  **Google Cloud Projekt:** Vytvorený projekt na [Google Cloud Platform](https://console.cloud.google.com/).
2.  **Aktívne API:** V projekte musia byť povolené nasledujúce API:
    - Document AI API
    - Cloud Data Loss Prevention (DLP) API
    - Vertex AI API (pre prístup k Gemini)
3.  **Servisný účet:** Vytvorený servisný účet s rolami, ktoré mu umožnia prístup k vyššie uvedeným službám (napr. `Document AI Editor`, `DLP User`, `Vertex AI User`).
4.  **Kľúč k servisnému účtu:** Stiahnutý JSON kľúč pre servisný účet.
5.  **DLP Šablóna:** Vytvorená de-identifikačná šablóna v Cloud DLP, ktorá definuje, aké dáta sa majú anonymizovať.

## Inštalácia

1.  **Klonovanie repozitára:**
    ```bash
    git clone <URL_repozitara>
    cd <nazov_repozitara>
    ```

2.  **Vytvorenie virtuálneho prostredia (odporúčané):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Na Windows: venv\Scripts\activate
    ```

3.  **Inštalácia závislostí:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Nastavenie autentifikácie:** Nastavte environmentálnu premennú `GOOGLE_APPLICATION_CREDENTIALS` tak, aby ukazovala na váš stiahnutý JSON kľúč.
    ```bash
    # Príklad pre Linux/macOS
    export GOOGLE_APPLICATION_CREDENTIALS="/cesta/k/vasmu/klucu.json"

    # Príklad pre Windows (PowerShell)
    $env:GOOGLE_APPLICATION_CREDENTIALS="C:\cesta\k\vasmu\klucu.json"
    ```

## Konfigurácia

Všetky nastavenia projektu sa nachádzajú v súbore `config.ini`. Pred prvým spustením ho musíte upraviť:

```ini
[gcp]
project_id = váš-gcp-projekt-id

[document_ai]
location = eu
processor_id = váš-doc-ai-procesor-id
mime_type = application/pdf

[dlp]
template_id = projects/váš-projekt/deidentifyTemplates/váš-template-id

[gemini]
api_key = váš-gemini-api-kľúč
model = gemini-1.5-flash-latest
analysis_prompt = Tu vložte váš prompt pre analýzu...
```

## Ako spustiť aplikáciu

Po úspešnej inštalácii a konfigurácii spustite Streamlit aplikáciu príkazom:

```bash
streamlit run app_streamlit.py
```

Aplikácia sa automaticky otvorí vo vašom predvolenom prehliadači.

## Štruktúra projektu

Aplikácia očakáva, že poistné udalosti budú organizované v priečinku `poistne_udalosti`. Každá udalosť je samostatný podpriečinok, ktorý obsahuje dva ďalšie podpriečinky:

- `citlive_dokumenty/`: Sem patria PDF súbory, ktoré obsahujú citlivé dáta a vyžadujú anonymizáciu (napr. lekárske správy).
- `vseobecne_dokumenty/`: Sem patria PDF súbory bez citlivých dát (napr. faktúry, sprievodné listy).

Túto štruktúru môžete vytvoriť manuálne, alebo jednoduchšie, priamo cez používateľské rozhranie aplikácie.

### Generované priečinky

Aplikácia počas behu automaticky vytvára nasledujúce priečinky pre ukladanie výstupov:

- `raw_ocr_output/`: Obsahuje surový text z OCR pre citlivé dokumenty (pre účely kontroly).
- `anonymized_output/`: Obsahuje anonymizovaný text z citlivých dokumentov.
- `general_output/`: Obsahuje text z OCR pre všeobecné dokumenty.
- `analysis_output/`: Obsahuje finálnu textovú analýzu od modelu Gemini.

# Automatizovaná Anonymizácia a Analýza Dokumentov s Google Cloud AI

Tento projekt poskytuje sadu Python skriptov na automatizáciu procesu extrakcie textu z PDF dokumentov (pomocou Google Document AI), následnú anonymizáciu citlivých dát (pomocou Google Cloud DLP) a finálnu obsahovú analýzu pomocou generatívnych modelov Gemini.

## Architektúra a Pracovný Postup

Projekt je založený na dvojkrokovom spracovaní:

1.  **Krok 1: Spracovanie a Anonymizácia (skript `main.py`)**
    -   Načíta PDF súbor alebo všetky PDF súbory z určeného priečinka.
    -   Extrahovaný text z OCR uloží do priečinka `ocr_output`.
    -   Anonymizovaný text pomocou DLP šablóny uloží do priečinka `anonymized_output`.

2.  **Krok 2: Generatívna Analýza (skript `analyza.py`)**
    -   Načíta už anonymizované texty z `anonymized_output`.
    -   Načíta všeobecné (necitlivé) dokumenty z priečinka `vstup_vseobecne`.
    -   Spojí všetky texty a pomocou modelu Gemini vykoná obsahovú analýzu na základe promptu definovaného v `config.ini`.

## Funkcie

- **Extrakcia textu**: Spracuje PDF súbory pomocou špecifikovaného Google Document AI procesora.
- **Anonymizácia dát**: Používa pred-konfigurovanú Google Cloud DLP šablónu na nájdenie a redigovanie citlivých informácií.
- **Generatívna Analýza**: Využíva silu modelov Gemini na pokročilú analýzu a zhrnutie obsahu dokumentov.
- **Centrálna Konfigurácia**: Všetky nastavenia projektu sú spravované v jednom súbore (`config.ini`), čo umožňuje jednoduchú zmenu modelov, ID projektov a ciest.
- **Dávkové spracovanie**: Dokáže spracovať jeden PDF súbor alebo všetky PDF súbory v určenom priečinku.

## Požiadavky

Pred spustením skriptu je potrebné mať v Google Cloud nastavené:

1.  **Google Cloud Projekt**: Aktívny a nakonfigurovaný projekt.
2.  **Povolené API**: Uistite sa, že máte v projekte povolené nasledujúce API:
    -   Cloud Document AI API
    -   Cloud Data Loss Prevention (DLP) API
    -   Vertex AI API
3.  **Service Account**: Servisný účet s potrebnými IAM rolami (`Document AI Editor`, `DLP User`, `Vertex AI User`). Stiahnite si JSON kľúč pre tento účet a nastavte environmentálnu premennú `GOOGLE_APPLICATION_CREDENTIALS`.
4.  **Document AI Procesor**: Vytvorený Document AI procesor (napr. typu "Document OCR").
5.  **DLP Šablóna**: Vytvorená DLP de-identifikačná šablóna.

## Inštalácia a Nastavenie

1.  **Nainštalujte potrebné Python knižnice:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Nakonfigurujte projekt v `config.ini`**:
    Otvorte súbor `config.ini` a doplňte všetky požadované hodnoty podľa vášho nastavenia v Google Cloud. Môžete tu jednoducho meniť model pre analýzu, cesty, ID a ďalšie parametre.

    ```ini
    [gcp]
    project_id = vas-gcp-projekt-id

    [document_ai]
    location = eu
    processor_id = vas-doc-ai-procesor-id
    ...

    [analysis]
    location = global
    model_name = gemini-1.5-flash-001
    ...
    ```

## Použitie

Celý proces pozostáva z dvoch hlavných krokov:

**Krok 1: Spustenie spracovania a anonymizácie**

Presuňte všetky citlivé PDF dokumenty do jedného priečinka a spustite skript `main.py` s cestou k tomuto priečinku ako argumentom.

```bash
# Spracuje všetky PDF v zadanom priečinku
python main.py "C:\cesta\k\vasim\pdf-suborom"
```

Výstupy sa uložia do priečinkov `ocr_output` a `anonymized_output`.

**Krok 2: Spustenie analýzy**

Umiestnite všetky všeobecné, necitlivé textové súbory do priečinka `vstup_vseobecne`. Následne spustite skript `analyza.py`. Skript si automaticky načíta dáta z výstupných priečinkov predchádzajúceho kroku.

```bash
python analyza.py
```

Skript vypíše analýzu od modelu Gemini priamo do konzoly.

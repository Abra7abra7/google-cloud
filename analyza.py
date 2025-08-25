import os
import argparse
import configparser
import glob
from typing import Callable

import google.generativeai as genai
from db import get_session, AnalysisResult

# --- Konfigurácia ---
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

GEMINI_API_KEY = config.get('gemini', 'api_key')
GEMINI_MODEL = config.get('gemini', 'model')
ANALYSIS_PROMPT = config.get('gemini', 'analysis_prompt')

# --- Inicializácia klienta --- 
genai.configure(api_key=GEMINI_API_KEY)

# --- Pomocné funkcie ---
def read_all_texts_from_dir(directory: str) -> str:
    """Načíta a spojí obsah všetkých .txt súborov z daného priečinka."""
    full_text = ""
    if not os.path.isdir(directory):
        return ""
        
    for filepath in sorted(glob.glob(os.path.join(directory, '*.txt'))):
        with open(filepath, 'r', encoding='utf-8') as f:
            filename = os.path.basename(filepath)
            full_text += f"\n--- Začiatok dokumentu: {filename} ---\n"
            full_text += f.read()
            full_text += f"\n--- Koniec dokumentu: {filename} ---\n"
    return full_text

# --- Hlavná funkcia --- 
def run_analysis(event_id: str, anonymized_dir: str, general_dir: str, analysis_dir: str, status_callback: Callable):
    """Spustí analýzu všetkých textov pre danú udalosť pomocou Gemini."""
    status_callback(f"Spúšťam analýzu poistnej udalosti: {event_id}...")

    # Cesty k priečinkom s textami pre danú udalosť
    anonymized_event_dir = os.path.join(anonymized_dir, event_id)
    general_event_dir = os.path.join(general_dir, event_id)

    # Načítanie všetkých textov
    status_callback(f"Načítavam anonymizované texty z: {os.path.basename(anonymized_dir)}/{event_id}...")
    anonymized_texts = read_all_texts_from_dir(anonymized_event_dir)
    
    status_callback(f"Načítavam všeobecné texty z: {os.path.basename(general_dir)}/{event_id}...")
    general_texts = read_all_texts_from_dir(general_event_dir)

    combined_text = "Nasledujú anonymizované texty z citlivých dokumentov:\n" + anonymized_texts + \
                     "\n\nNasledujú texty zo všeobecných dokumentov:\n" + general_texts

    if not anonymized_texts and not general_texts:
        status_callback("Chyba: Pre túto udalosť neboli nájdené žiadne texty na analýzu.")
        return None

    # Príprava a volanie Gemini modelu
    try:
        status_callback(f"Inicializujem Gemini klienta...")
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        full_prompt = ANALYSIS_PROMPT + "\n\n" + combined_text
        
        status_callback(f"Posielam dáta na analýzu do modelu '{GEMINI_MODEL}'...")
        response = model.generate_content(full_prompt)
        analysis_result = response.text

        # Uloženie výsledku na disk
        os.makedirs(analysis_dir, exist_ok=True)
        result_path = os.path.join(analysis_dir, f"{event_id}_analyza.txt")
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(analysis_result)

        # Perzistencia do DB (ak je nakonfigurovaná)
        session = get_session()
        if session is not None:
            try:
                session.add(AnalysisResult(event_id=event_id, model=GEMINI_MODEL, summary_text=analysis_result))
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
        
        status_callback(f"Výsledok analýzy bol úspešne uložený do: {result_path}")
        return result_path

    except Exception as e:
        status_callback(f"Chyba pri komunikácii s Gemini API: {e}")
        raise

def analyze_text(input_text: str, prompt: str) -> str:
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt + "\n\n" + input_text)
    return response.text

def analyze_single_document(event_id: str, filename: str, anonymized_dir: str, general_dir: str, prompt: str | None) -> str:
    anon_path = os.path.join(anonymized_dir, event_id, filename)
    gen_path = os.path.join(general_dir, event_id, filename)
    text = ""
    if os.path.exists(anon_path):
        with open(anon_path, 'r', encoding='utf-8') as f:
            text = f.read()
    elif os.path.exists(gen_path):
        with open(gen_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        raise FileNotFoundError("Súbor pre analýzu neexistuje v anonymized ani general výstupoch.")

    use_prompt = prompt or ANALYSIS_PROMPT
    return analyze_text(text, use_prompt)

# --- Spustenie z príkazového riadku ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyzuj texty jednej poistnej udalosti pomocou Gemini.")
    parser.add_argument("event_id", help="ID (názov priečinka) poistnej udalosti.")
    parser.add_argument("--anonymized_dir", default="anonymized_output", help="Hlavný priečinok s anonymizovanými textami.")
    parser.add_argument("--general_dir", default="general_output", help="Hlavný priečinok so všeobecnými textami.")
    parser.add_argument("--analysis_dir", default="analysis_output", help="Priečinok pre uloženie výslednej analýzy.")
    args = parser.parse_args()

    run_analysis(args.event_id, args.anonymized_dir, args.general_dir, args.analysis_dir, print)

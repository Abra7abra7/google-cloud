import os
import argparse
import configparser
from typing import Callable
from google import genai
from google.genai import types

# --- Konfigurácia ---
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

PROJECT_ID = config.get('gcp', 'project_id')
ANALYSIS_LOCATION = config.get('analysis', 'location')
MODEL_NAME = config.get('analysis', 'model_name')
ANALYSIS_PROMPT = config.get('analysis', 'prompt')

def load_texts_from_dir(directory_path: str, status_callback: Callable = None) -> str:
    """Načíta obsah všetkých .txt súborov z daného priečinka a spojí ich."""
    all_texts = []
    if not os.path.isdir(directory_path):
        if status_callback:
            status_callback(f"Info: Priečinok '{directory_path}' neexistuje. Preskakujem.")
        return ""

    for filename in sorted(os.listdir(directory_path)):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_texts.append(f.read())
            except Exception as e:
                if status_callback:
                    status_callback(f"Chyba pri čítaní súboru {file_path}: {e}")
    
    return "\n\n--- ďalší dokument ---\n\n".join(all_texts)

def analyze_and_save(
    project_id: str, 
    location: str, 
    model_name: str, 
    prompt: str, 
    documents_text: str,
    output_path: str,
    status_callback: Callable = None
):
    """Pošle text do modelu Gemini a výsledok uloží do súboru."""
    if status_callback:
        status_callback("Inicializujem Gemini klienta...")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )

    full_prompt = f"{prompt}\n\nDokumenty na analýzu:\n---\n{documents_text}"
    contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

    if status_callback:
        status_callback(f"Posielam dáta na analýzu do modelu '{model_name}'...")
    response_stream = client.models.generate_content_stream(model=model_name, contents=contents)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in response_stream:
                f.write(chunk.text)
        if status_callback:
            status_callback(f"Výsledok analýzy bol úspešne uložený do: {output_path}")
    except Exception as e:
        if status_callback:
            status_callback(f"Nastala chyba pri ukladaní výsledku analýzy: {e}")

def run_analysis(event_id: str, anonymized_dir: str, general_dir: str, analysis_dir: str, status_callback: Callable = None):
    """Hlavná logika pre spustenie analýzy jednej poistnej udalosti."""
    if status_callback:
        status_callback(f"Spúšťam analýzu poistnej udalosti: {event_id}...")

    anonymized_path = os.path.join(anonymized_dir, event_id)
    general_path = os.path.join(general_dir, event_id)

    if status_callback:
        status_callback(f"Načítavam anonymizované texty z: {anonymized_path}...")
    anonymized_texts = load_texts_from_dir(anonymized_path, status_callback)
    
    if status_callback:
        status_callback(f"Načítavam všeobecné texty z: {general_path}...")
    general_texts = load_texts_from_dir(general_path, status_callback)
    
    combined_text = anonymized_texts + "\n\n--- všeobecné dokumenty ---\n\n" + general_texts
    
    if not combined_text.strip():
        if status_callback:
            status_callback("Nenašli sa žiadne texty na analýzu. Končím.")
        return None
        
    os.makedirs(analysis_dir, exist_ok=True)
    output_file = os.path.join(analysis_dir, f"{event_id}_analyza.txt")

    analyze_and_save(
        PROJECT_ID, ANALYSIS_LOCATION, MODEL_NAME, ANALYSIS_PROMPT, combined_text, output_file, status_callback
    )
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyzuj textové dáta jednej poistnej udalosti a ulož výsledok.")
    parser.add_argument("event_id", help="ID poistnej udalosti.")
    parser.add_argument("--anonymized_dir", default="anonymized_output")
    parser.add_argument("--general_dir", default="general_output")
    parser.add_argument("--analysis_dir", default="analysis_output")
    args = parser.parse_args()

    run_analysis(args.event_id, args.anonymized_dir, args.general_dir, args.analysis_dir, print)

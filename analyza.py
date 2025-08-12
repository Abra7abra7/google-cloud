import os
import argparse
import configparser
from google import genai
from google.genai import types

# --- Konfigurácia ---
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

PROJECT_ID = config.get('gcp', 'project_id')
ANALYSIS_LOCATION = config.get('analysis', 'location')
MODEL_NAME = config.get('analysis', 'model_name')
ANALYSIS_PROMPT = config.get('analysis', 'prompt')

def load_texts_from_dir(directory_path: str) -> str:
    """Načíta obsah všetkých .txt súborov z daného priečinka a spojí ich."""
    all_texts = []
    if not os.path.isdir(directory_path):
        print(f"Info: Priečinok '{directory_path}' neexistuje alebo je prázdny. Preskakujem.")
        return ""

    for filename in sorted(os.listdir(directory_path)):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_texts.append(f.read())
            except Exception as e:
                print(f"Chyba pri čítaní súboru {file_path}: {e}")
    
    return "\n\n--- ďalší dokument ---\n\n".join(all_texts)

def analyze_and_save(
    project_id: str, 
    location: str, 
    model_name: str, 
    prompt: str, 
    documents_text: str,
    output_path: str
):
    """Pošle text do modelu Gemini a výsledok uloží do súboru."""
    print("\nInicializujem Gemini klienta...")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )

    full_prompt = f"{prompt}\n\nDokumenty na analýzu:\n---\n{documents_text}"
    contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]

    print(f"Posielam dáta na analýzu do modelu '{model_name}'...")
    response_stream = client.models.generate_content_stream(model=model_name, contents=contents)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in response_stream:
                f.write(chunk.text)
        print(f"--- Výsledok analýzy bol úspešne uložený do: {output_path} ---")
    except Exception as e:
        print(f"Nastala chyba pri ukladaní výsledku analýzy: {e}")

def main(args):
    """Hlavná funkcia pre spustenie analýzy jednej poistnej udalosti."""
    event_id = args.event_id
    print(f"=== Spúšťam analýzu poistnej udalosti: {event_id} ===")

    # Cesty k spracovaným dátam
    anonymized_path = os.path.join(args.anonymized_dir, event_id)
    general_path = os.path.join(args.general_dir, event_id)

    # 1. Načítanie textov
    print(f"Načítavam anonymizované texty z: {anonymized_path}")
    anonymized_texts = load_texts_from_dir(anonymized_path)
    
    print(f"Načítavam všeobecné texty z: {general_path}")
    general_texts = load_texts_from_dir(general_path)
    
    # 2. Spojenie všetkých textov do jedného kontextu
    combined_text = anonymized_texts + "\n\n--- všeobecné dokumenty ---\n\n" + general_texts
    
    if not combined_text.strip():
        print("Nenašli sa žiadne texty na analýzu. Končím.")
        return
        
    # 3. Príprava výstupného súboru a spustenie analýzy
    os.makedirs(args.analysis_dir, exist_ok=True)
    output_file = os.path.join(args.analysis_dir, f"{event_id}_analyza.txt")

    analyze_and_save(
        PROJECT_ID, ANALYSIS_LOCATION, MODEL_NAME, ANALYSIS_PROMPT, combined_text, output_file
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyzuj textové dáta jednej poistnej udalosti a ulož výsledok.")
    parser.add_argument(
        "event_id", 
        help="ID (názov priečinka) poistnej udalosti, ktorá sa má analyzovať."
    )
    parser.add_argument(
        "--anonymized_dir", 
        default="anonymized_output", 
        help="Hlavný priečinok s anonymizovanými textami."
    )
    parser.add_argument(
        "--general_dir", 
        default="general_output", 
        help="Hlavný priečinok so všeobecnými textami."
    )
    parser.add_argument(
        "--analysis_dir",
        default="analysis_output",
        help="Priečinok, do ktorého sa uloží finálny výsledok analýzy."
    )
    args = parser.parse_args()
    main(args)

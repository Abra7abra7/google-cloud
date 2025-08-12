import os
import argparse
import configparser
from google import genai
from google.genai import types

# --- Konfigurácia ---
# Načítanie konfigurácie z externého súboru
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

PROJECT_ID = config.get('gcp', 'project_id')
LOCATION = config.get('analysis', 'location')
MODEL_NAME = config.get('analysis', 'model_name')
ANALYSIS_PROMPT = config.get('analysis', 'prompt')

def load_texts_from_dir(directory_path: str) -> str:
    """Načíta obsah všetkých .txt súborov z daného priečinka a spojí ich.
    Vráti jeden reťazec obsahujúci všetky texty.
    """
    all_texts = []
    if not os.path.isdir(directory_path):
        print(f"Varovanie: Priečinok '{directory_path}' neexistuje. Preskakujem.")
        return ""

    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_texts.append(f.read())
            except Exception as e:
                print(f"Chyba pri čítaní súboru {file_path}: {e}")
    
    return "\n---\n".join(all_texts)

def analyze_with_gemini(project_id: str, location: str, model_name: str, prompt: str, documents_text: str):
    """Pošle text dokumentov a prompt do modelu Gemini a vypíše jeho odpoveď.
    Používa novú knižnicu google.genai a streamuje odpoveď.
    """
    print("\nInicializujem Gemini klienta...")
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )

    # Spojenie promptu a dát do jedného celku
    full_prompt = f"{prompt}\n\nDokumenty na analýzu:\n---\n{documents_text}"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(text=full_prompt)
            ]
        )
    ]

    print(f"Posielam dáta na analýzu do modelu '{model_name}'...")
    print("--- Výsledok analýzy od Gemini ---")
    
    # Streamovanie a vypisovanie odpovede
    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=contents,
    ):
        print(chunk.text, end="")
    print() # Zalomenie riadku na konci

def main(args):
    """Hlavná funkcia pre spustenie analýzy.
    """
    print("Spúšťam pokročilú analýzu dokumentov...")
    
    # 1. Načítanie anonymizovaných textov
    print(f"Načítavam anonymizované súbory z: {args.anonymized_dir}")
    anonymized_texts = load_texts_from_dir(args.anonymized_dir)
    
    # 2. Načítanie všeobecných textov
    print(f"Načítavam všeobecné súbory z: {args.general_dir}")
    general_texts = load_texts_from_dir(args.general_dir)
    
    # 3. Spojenie všetkých textov
    combined_text = anonymized_texts + "\n" + general_texts
    
    if not combined_text.strip():
        print("Nenašli sa žiadne texty na analýzu. Končím.")
        return
        
    # 4. Spustenie analýzy pomocou Gemini
    analyze_with_gemini(PROJECT_ID, LOCATION, MODEL_NAME, ANALYSIS_PROMPT, combined_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyzuj textové dáta z poistných zmlúv pomocou Vertex AI.")
    parser.add_argument(
        "-a", "--anonymized_dir", 
        default="anonymized_output", 
        help="Priečinok s anonymizovanými textami."
    )
    parser.add_argument(
        "-g", "--general_dir", 
        default="vstup_vseobecne", 
        help="Priečinok so všeobecnými, necitlivými textami."
    )
    args = parser.parse_args()
    main(args)

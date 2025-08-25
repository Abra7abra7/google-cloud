import os
import argparse
import glob
from typing import Callable

from dotenv import load_dotenv
from db import get_session, AnalysisResult, get_active_prompt, PromptRun

# --- Konfigurácia ---
load_dotenv('.env.local', override=True)
load_dotenv(override=False)

USE_VERTEX_AI = (os.getenv('USE_VERTEX_AI') or '0').strip() in ('1', 'true', 'True')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
ANALYSIS_PROMPT = os.getenv('ANALYSIS_PROMPT', 'Zhrň kľúčové body z nasledujúcich poistných dokumentov. Zameraj sa na typ poistenia, poistné sumy, dátumy platnosti a mená zúčastnených strán. Vypíš výsledok v prehľadnej štruktúre.')
GCP_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
VERTEX_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'europe-west1')

# --- Inicializácia klientov ---
if USE_VERTEX_AI:
    # Vertex AI (EU rezidencia podľa location)
    try:
        from vertexai import init as vertex_init
        from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
    except Exception as e:
        raise RuntimeError(f"Chýba závislosť google-cloud-aiplatform alebo vertexai: {e}")

    if not GCP_PROJECT:
        raise ValueError("GOOGLE_CLOUD_PROJECT musí byť nastavený pre Vertex AI")
    vertex_init(project=GCP_PROJECT, location=VERTEX_LOCATION)
    VertexModel = VertexGenerativeModel
else:
    # Google AI Studio (API kľúč)
    import google.generativeai as genai
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY musí byť nastavený v environment variables alebo config.ini")
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
def _resolve_vertex_model_name(preferred_model_name: str | None) -> str:
    """Zmapuje preferovaný názov modelu na alias stabilnej verzie v EU.
    Používa auto-updated aliasy odporúčané v dokumentácii
    (napr. gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash) [zdroj].
    """
    name = (preferred_model_name or GEMINI_MODEL or '').strip()
    name_lower = name.lower()
    # Preferuj stabilný alias gemini-2.0-flash, ak je zadaný rad 2.*
    if name_lower.startswith('gemini-2'):
        return 'gemini-2.0-flash'
    # 1.5 vetvy – použijeme aliasy namiesto pinovanej verzie
    if 'pro' in name_lower:
        return 'gemini-1.5-pro'
    if 'flash' in name_lower or 'gemini-1.5' in name_lower:
        return 'gemini-1.5-flash'
    # neznáme → bezpečný default
    return 'gemini-2.0-flash'


def _generate_text(prompt: str, model_name_override: str | None = None) -> str:
    if USE_VERTEX_AI:
        vertex_model_name = _resolve_vertex_model_name(model_name_override)
        model = VertexModel(vertex_model_name)
        resp = model.generate_content(prompt)
        return getattr(resp, 'text', None) or ''.join(getattr(resp, 'candidates', []) or [])
    else:
        import google.generativeai as genai
        use_name = (model_name_override or GEMINI_MODEL)
        model = genai.GenerativeModel(use_name)
        resp = model.generate_content(prompt)
        return resp.text


def run_analysis(event_id: str, anonymized_dir: str, general_dir: str, analysis_dir: str, status_callback: Callable):
    """Spustí analýzu všetkých textov pre danú udalosť pomocou Gemini."""
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
    status_callback(f"Spúšťam analýzu poistnej udalosti: {event_id}...")

    # Získanie aktívneho promptu z databázy
    active_prompt = get_active_prompt()
    if not active_prompt:
        status_callback("Varovanie: Používam predvolený prompt z config.ini")
        prompt_content = ANALYSIS_PROMPT
        model_name = GEMINI_MODEL
    else:
        prompt_content = active_prompt.content
        model_name = active_prompt.model
        status_callback(f"Používam prompt: {active_prompt.name} v{active_prompt.version}")

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
        status_callback(f"Inicializujem model...")
        full_prompt = prompt_content + "\n\n" + combined_text
        effective_model = _resolve_vertex_model_name(model_name) if USE_VERTEX_AI else (model_name or GEMINI_MODEL)
        status_callback(f"Posielam dáta na analýzu do modelu '{effective_model}'...")
        analysis_result = _generate_text(full_prompt, model_name_override=model_name)

        # Uloženie výsledku na disk
        os.makedirs(analysis_dir, exist_ok=True)
        result_path = os.path.join(analysis_dir, f"{event_id}_analyza.txt")
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(analysis_result)

        # Perzistencia do DB (ak je nakonfigurovaná)
        session = get_session()
        if session is not None:
            try:
                # Uloženie výsledku analýzy
                analysis_record = AnalysisResult(event_id=event_id, model=model_name, summary_text=analysis_result)
                session.add(analysis_record)
                
                # Logovanie behu promptu
                if active_prompt:
                    prompt_run = PromptRun(
                        prompt_id=active_prompt.id,
                        event_id=event_id,
                        model=model_name
                        # tokens_in a tokens_out môžeme pridať neskôr ak bude potrebné
                    )
                    session.add(prompt_run)
                
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
    return _generate_text(prompt + "\n\n" + input_text)

def analyze_single_document(event_id: str, filename: str, anonymized_dir: str, general_dir: str, prompt: str | None) -> str:
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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

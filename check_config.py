#!/usr/bin/env python3
"""
Diagnostický skript pre kontrolu konfigurácie Claims AI
Spustite: python check_config.py
"""

import os
import sys
from dotenv import load_dotenv

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def check_env_file():
    """Kontrola .env.local súboru"""
    print_header("KONTROLA .env.local SÚBORU")
    
    if not os.path.exists('.env.local'):
        print_error(".env.local súbor neexistuje!")
        print_info("Skopírujte env.example ako .env.local a vyplňte hodnoty")
        return False
    
    print_success(".env.local súbor existuje")
    
    # Načítanie env premenných
    load_dotenv('.env.local', override=True)
    return True

def check_google_cloud():
    """Kontrola Google Cloud konfigurácie"""
    print_header("KONTROLA GOOGLE CLOUD")
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print_error("GOOGLE_CLOUD_PROJECT nie je nastavený")
        return False
    
    if not credentials_path:
        print_error("GOOGLE_APPLICATION_CREDENTIALS nie je nastavený")
        return False
    
    print_success(f"Project ID: {project_id}")
    print_success(f"Credentials: {credentials_path}")
    
    # Kontrola existencie credentials súboru
    if not os.path.exists(credentials_path):
        print_error(f"Credentials súbor neexistuje: {credentials_path}")
        return False
    
    print_success("Credentials súbor existuje")
    
    # Kontrola, či nie sú placeholder hodnoty
    if 'your-gcp-project-id' in project_id or 'your-' in project_id:
        print_error("GOOGLE_CLOUD_PROJECT obsahuje placeholder hodnotu!")
        return False
    
    return True

def check_document_ai():
    """Kontrola Document AI konfigurácie"""
    print_header("KONTROLA DOCUMENT AI")
    
    processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID')
    location = os.getenv('DOCUMENT_AI_LOCATION', 'eu')
    
    if not processor_id:
        print_error("DOCUMENT_AI_PROCESSOR_ID nie je nastavený")
        return False
    
    print_success(f"Processor ID: {processor_id}")
    print_success(f"Location: {location}")
    
    # Kontrola placeholder hodnôt
    if 'your-processor-id' in processor_id or 'your-' in processor_id:
        print_error("DOCUMENT_AI_PROCESSOR_ID obsahuje placeholder hodnotu!")
        print_info("Musíte zadať skutočné ID processora z GCP Console")
        return False
    
    return True

def check_dlp():
    """Kontrola Cloud DLP konfigurácie"""
    print_header("KONTROLA CLOUD DLP")
    
    deidentify_template = os.getenv('DLP_DEIDENTIFY_TEMPLATE_ID')
    inspect_template = os.getenv('DLP_INSPECT_TEMPLATE_ID')
    location = os.getenv('DLP_LOCATION', 'europe-west3')
    
    if not deidentify_template:
        print_error("DLP_DEIDENTIFY_TEMPLATE_ID nie je nastavený")
        return False
    
    print_success(f"De-identify Template: {deidentify_template}")
    print_success(f"Location: {location}")
    
    if inspect_template:
        print_success(f"Inspect Template: {inspect_template}")
    else:
        print_warning("DLP_INSPECT_TEMPLATE_ID nie je nastavený (voliteľné)")
    
    # Kontrola placeholder hodnôt
    if 'your-template-id' in deidentify_template or 'your-' in deidentify_template:
        print_error("DLP_DEIDENTIFY_TEMPLATE_ID obsahuje placeholder hodnotu!")
        print_info("Musíte zadať skutočné ID šablóny z GCP Console")
        return False
    
    # Kontrola formátu template ID
    if not deidentify_template.startswith('projects/'):
        print_error("DLP_DEIDENTIFY_TEMPLATE_ID musí byť plné resource meno!")
        print_info("Formát: projects/PROJECT/locations/REGION/deidentifyTemplates/TEMPLATE_ID")
        return False
    
    return True

def check_vertex_ai():
    """Kontrola Vertex AI konfigurácie"""
    print_header("KONTROLA VERTEX AI")
    
    use_vertex = os.getenv('USE_VERTEX_AI', '0').strip() in ('1', 'true', 'True')
    location = os.getenv('VERTEX_AI_LOCATION', 'europe-west1')
    model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    if use_vertex:
        print_success("Vertex AI je povolené")
        print_success(f"Location: {location}")
        print_success(f"Model: {model}")
        
        # Test importu vertexai
        try:
            from vertexai import init as vertex_init
            print_success("Vertex AI knižnica je dostupná")
        except ImportError as e:
            print_error(f"Vertex AI knižnica nie je nainštalovaná: {e}")
            return False
    else:
        print_info("Vertex AI je vypnuté, používa sa Google AI Studio")
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print_error("GEMINI_API_KEY nie je nastavený pre Google AI Studio")
            return False
        print_success("GEMINI_API_KEY je nastavený")
    
    return True

def check_database():
    """Kontrola databázovej konfigurácie"""
    print_header("KONTROLA DATABÁZY")
    
    database_url = os.getenv('DATABASE_URL', 'sqlite:///claims_ai.db')
    print_success(f"Database URL: {database_url}")
    
    if database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            print_success("SQLite databáza existuje")
        else:
            print_warning("SQLite databáza neexistuje (bude vytvorená pri prvom spustení)")
    elif database_url.startswith('mysql'):
        print_info("MySQL databáza - overte pripojenie manuálne")
    
    return True

def test_imports():
    """Test importov kľúčových modulov"""
    print_header("TEST IMPORTOV")
    
    modules_to_test = [
        ('streamlit', 'Streamlit'),
        ('fastapi', 'FastAPI'),
        ('google.cloud.documentai', 'Document AI'),
        ('google.cloud.dlp', 'Cloud DLP'),
        ('google.generativeai', 'Google Generative AI'),
        ('sqlalchemy', 'SQLAlchemy'),
    ]
    
    all_ok = True
    for module, name in modules_to_test:
        try:
            __import__(module)
            print_success(f"{name} knižnica je dostupná")
        except ImportError as e:
            print_error(f"{name} knižnica nie je dostupná: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Hlavná funkcia"""
    print("🔍 DIAGNOSTIKA KONFIGURÁCIE CLAIMS AI")
    print("=" * 60)
    
    checks = [
        ("Environment súbor", check_env_file),
        ("Google Cloud", check_google_cloud),
        ("Document AI", check_document_ai),
        ("Cloud DLP", check_dlp),
        ("Vertex AI", check_vertex_ai),
        ("Databáza", check_database),
        ("Importy", test_imports),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Chyba pri kontrole {name}: {e}")
            results.append((name, False))
    
    # Zhrnutie
    print_header("ZHRNUTIE")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: OK")
        else:
            print_error(f"{name}: CHYBA")
    
    print(f"\n📊 Výsledok: {passed}/{total} kontrol prešlo")
    
    if passed == total:
        print_success("🎉 Všetky kontroly prešli! Konfigurácia vyzerá v poriadku.")
        return 0
    else:
        print_error("❌ Niektoré kontroly zlyhali. Opravte chyby pred spustením aplikácie.")
        print_info("Pozrite si KONFIGURACIA_CHECKLIST.md pre detailné inštrukcie")
        return 1

if __name__ == "__main__":
    sys.exit(main())

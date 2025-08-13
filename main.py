import os
import argparse
import configparser
from typing import Callable

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai
from google.cloud import dlp_v2

# --- Konfigurácia ---
# Načítanie nastavení z externého súboru pre jednoduchú správu.
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

PROJECT_ID = config.get('gcp', 'project_id')
DOC_AI_LOCATION = config.get('document_ai', 'location')
PROCESSOR_ID = config.get('document_ai', 'processor_id')
DLP_TEMPLATE_ID = config.get('dlp', 'template_id')
MIME_TYPE = config.get('document_ai', 'mime_type')

# --- Funkcie pre Google Cloud služby ---
def process_document(
    project_id: str, location: str, processor_id: str, file_path: str, mime_type: str
) -> str:
    """Spracuje jeden dokument pomocou Document AI (OCR) a vráti extrahovaný text."""
    client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)
    name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as image:
        image_content = image.read()

    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    return result.document.text

def anonymize_text(
    project_id: str, text_to_anonymize: str, dlp_template_id: str
) -> str:
    """Anonymizuje text pomocou Cloud DLP de-identifikačnej šablóny."""
    dlp_client = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}/locations/global"
    request = dlp_v2.DeidentifyContentRequest(
        parent=parent,
        deidentify_template_name=dlp_template_id,
        item={"value": text_to_anonymize},
    )
    response = dlp_client.deidentify_content(request=request)
    return response.item.value

# --- Logika spracovania súborov ---
def ocr_and_anonymize(file_path: str, raw_ocr_dir: str):
    """Orchestruje OCR, uloženie surového textu a následnú anonymizáciu."""
    # 1. OCR
    text = process_document(PROJECT_ID, DOC_AI_LOCATION, PROCESSOR_ID, file_path, MIME_TYPE)
    
    # 2. Uloženie surového OCR textu pre 'human-in-the-loop' kontrolu
    raw_filename = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
    raw_output_path = os.path.join(raw_ocr_dir, raw_filename)
    os.makedirs(raw_ocr_dir, exist_ok=True)
    with open(raw_output_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 3. Anonymizácia
    return anonymize_text(PROJECT_ID, text, DLP_TEMPLATE_ID)

def process_directory(base_path: str, process_func: Callable, output_dir: str, status_callback: Callable):
    """Spracuje všetky PDF súbory v danom priečinku pomocou poskytnutej funkcie."""
    if not os.path.isdir(base_path):
        status_callback(f"Info: Priečinok '{os.path.basename(base_path)}' neexistuje. Preskakujem.")
        return

    status_callback(f"Spracovávam priečinok: {os.path.basename(base_path)}...")
    os.makedirs(output_dir, exist_ok=True)

    for filename in sorted(os.listdir(base_path)):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(base_path, filename)
            try:
                status_callback(f"Spracovávam súbor: {filename}...")
                processed_text = process_func(file_path)
                
                output_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(processed_text)
                status_callback(f"Uložené: {output_filename}")

            except Exception as e:
                status_callback(f"Chyba pri súbore {filename}: {e}")

# --- Hlavná funkcia --- 
def run_processing(event_path: str, anonymized_dir: str, general_dir: str, raw_ocr_dir: str, status_callback: Callable):
    """Hlavná logika pre spracovanie jednej poistnej udalosti (citlivé a všeobecné dokumenty)."""
    if not os.path.isdir(event_path):
        status_callback(f"Chyba: Zadaná cesta '{event_path}' nie je platný priečinok.")
        return

    event_id = os.path.basename(event_path)
    status_callback(f"Spúšťam spracovanie poistnej udalosti: {event_id}...")

    # Cesty k pod-priečinkom
    sensitive_path = os.path.join(event_path, "citlive_dokumenty")
    general_path = os.path.join(event_path, "vseobecne_dokumenty")

    # Cesty pre výstupy
    anonymized_output_dir = os.path.join(anonymized_dir, event_id)
    general_output_dir = os.path.join(general_dir, event_id)
    raw_ocr_output_dir = os.path.join(raw_ocr_dir, event_id)

    # Spracovanie citlivých dokumentov (OCR + uloženie raw + anonymizácia)
    ocr_and_anonymize_func = lambda fp: ocr_and_anonymize(fp, raw_ocr_output_dir)
    process_directory(sensitive_path, ocr_and_anonymize_func, anonymized_output_dir, status_callback)

    # Spracovanie všeobecných dokumentov (iba OCR)
    ocr_only_func = lambda fp: process_document(PROJECT_ID, DOC_AI_LOCATION, PROCESSOR_ID, fp, MIME_TYPE)
    process_directory(general_path, ocr_only_func, general_output_dir, status_callback)

    status_callback(f"Spracovanie dokumentov pre udalosť {event_id} dokončené.")

# --- Spustenie z príkazového riadku --- 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spracuj a selektívne anonymizuj dokumenty jednej poistnej udalosti.")
    parser.add_argument("event_path", help="Cesta k hlavnému priečinku poistnej udalosti.")
    parser.add_argument("--anonymized_dir", default="anonymized_output", help="Hlavný priečinok pre anonymizované texty.")
    parser.add_argument("--general_dir", default="general_output", help="Hlavný priečinok pre všeobecné texty.")
    parser.add_argument("--raw_ocr_dir", default="raw_ocr_output", help="Hlavný priečinok pre surové OCR texty.")
    args = parser.parse_args()
    
    # Pre príkazový riadok používame jednoduchý print ako callback
    run_processing(args.event_path, args.anonymized_dir, args.general_dir, args.raw_ocr_dir, print)

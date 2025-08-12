import os
import argparse
import configparser
from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai
from google.cloud import dlp_v2

# --- Konfigurácia ---
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

PROJECT_ID = config.get('gcp', 'project_id')
DOC_AI_LOCATION = config.get('document_ai', 'location')
PROCESSOR_ID = config.get('document_ai', 'processor_id')
DLP_TEMPLATE_ID = config.get('dlp', 'template_id')
MIME_TYPE = config.get('document_ai', 'mime_type')

def process_document(
    project_id: str, location: str, processor_id: str, file_path: str, mime_type: str
) -> str:
    """Spracuje dokument pomocou Document AI a vráti extrahovaný text."""
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
    """Anonymizuje text pomocou jednej, kompletnej de-identifikačnej šablóny."""
    dlp_client = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}/locations/global"
    request = dlp_v2.DeidentifyContentRequest(
        parent=parent,
        deidentify_template_name=dlp_template_id,
        item={"value": text_to_anonymize},
    )
    response = dlp_client.deidentify_content(request=request)
    return response.item.value

def process_directory(base_path: str, process_func, output_dir: str):
    """Spracuje všetky PDF súbory v danom priečinku pomocou poskytnutej funkcie."""
    if not os.path.isdir(base_path):
        print(f"Info: Priečinok '{os.path.basename(base_path)}' neexistuje. Preskakujem.")
        return

    print(f"--- Spracovávam priečinok: {os.path.basename(base_path)} ---")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(base_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(base_path, filename)
            try:
                print(f"\nSpracovávam súbor: {filename}")
                processed_text = process_func(file_path)
                
                output_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, output_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(processed_text)
                print(f"Výstup bol uložený do: {output_path}")

            except Exception as e:
                print(f"Nastala chyba pri spracovaní súboru {filename}: {e}")

def main(args):
    """Hlavná funkcia, ktorá riadi spracovanie jednej poistnej udalosti."""
    event_path = args.event_path
    if not os.path.isdir(event_path):
        print(f"Chyba: Zadaná cesta '{event_path}' nie je platný priečinok poistnej udalosti.")
        return

    event_id = os.path.basename(event_path)
    print(f"=== Spúšťam spracovanie poistnej udalosti: {event_id} ===")

    # Cesty k podpriečinkom
    sensitive_path = os.path.join(event_path, "citlive_dokumenty")
    general_path = os.path.join(event_path, "vseobecne_dokumenty")

    # Cesty k výstupným priečinkom
    anonymized_output_dir = os.path.join(args.anonymized_dir, event_id)
    general_output_dir = os.path.join(args.general_dir, event_id)

    # 1. Spracovanie citlivých dokumentov (OCR + Anonymizácia)
    def ocr_and_anonymize(file_path):
        text = process_document(PROJECT_ID, DOC_AI_LOCATION, PROCESSOR_ID, file_path, MIME_TYPE)
        return anonymize_text(PROJECT_ID, text, DLP_TEMPLATE_ID)

    process_directory(sensitive_path, ocr_and_anonymize, anonymized_output_dir)

    # 2. Spracovanie všeobecných dokumentov (iba OCR)
    def ocr_only(file_path):
        return process_document(PROJECT_ID, DOC_AI_LOCATION, PROCESSOR_ID, file_path, MIME_TYPE)

    process_directory(general_path, ocr_only, general_output_dir)

    print(f"\n=== Spracovanie poistnej udalosti {event_id} dokončené. ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spracuj a selektívne anonymizuj dokumenty jednej poistnej udalosti.")
    parser.add_argument(
        "event_path", 
        help="Cesta k hlavnému priečinku poistnej udalosti, ktorý obsahuje podpriečinky 'citlive_dokumenty' a 'vseobecne_dokumenty'."
    )
    parser.add_argument(
        "--anonymized_dir", 
        default="anonymized_output", 
        help="Hlavný priečinok, do ktorého sa uložia anonymizované texty."
    )
    parser.add_argument(
        "--general_dir", 
        default="general_output", 
        help="Hlavný priečinok, do ktorého sa uložia neanonymizované texty zo všeobecných dokumentov."
    )
    args = parser.parse_args()
    main(args)

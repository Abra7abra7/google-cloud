import os
import argparse
import configparser
from typing import List

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai
from google.cloud import dlp_v2

# --- Konfigurácia --- 
# Načítanie konfigurácie z externého súboru
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Načítanie hodnôt z konfiguračného súboru
PROJECT_ID = config.get('gcp', 'project_id')
LOCATION = config.get('document_ai', 'location')
PROCESSOR_ID = config.get('document_ai', 'processor_id')
DLP_TEMPLATE_ID = config.get('dlp', 'template_id')
MIME_TYPE = config.get('document_ai', 'mime_type')


def process_document(
    project_id: str, location: str, processor_id: str, file_path: str, mime_type: str
) -> str:
    """
    Spracuje dokument pomocou Document AI a vráti extrahovaný text.
    """
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
    """
    Anonymizuje text pomocou jednej, kompletnej de-identifikačnej šablóny.
    """
    dlp_client = dlp_v2.DlpServiceClient()

    # Rodičovský zdroj pre volanie API. Musí zodpovedať lokácii šablóny ('global').
    parent = f"projects/{project_id}/locations/global"

    # Vytvorenie požiadavky, ktorá používa už len názov jednej šablóny.
    request = dlp_v2.DeidentifyContentRequest(
        parent=parent,
        deidentify_template_name=dlp_template_id,
        item={"value": text_to_anonymize},
    )

    response = dlp_client.deidentify_content(request=request)
    return response.item.value


def main(args):
    """
    Hlavná funkcia, ktorá spája spracovanie dokumentu a anonymizáciu.
    """
    # Určenie vstupných súborov
    if os.path.isfile(args.input_path):
        files_to_process = [args.input_path]
    elif os.path.isdir(args.input_path):
        files_to_process = [
            os.path.join(args.input_path, f) 
            for f in os.listdir(args.input_path) if f.lower().endswith('.pdf')
        ]
    else:
        print(f"Chyba: Vstupná cesta '{args.input_path}' neexistuje alebo nie je súbor ani priečinok.")
        return

    # Vytvorenie výstupných priečinkov
    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Anonymizované výstupy sa budú ukladať do: {args.output_dir}")
    os.makedirs(args.ocr_dir, exist_ok=True)
    print(f"Surové OCR výstupy sa budú ukladať do: {args.ocr_dir}")

    for file_path in files_to_process:
        try:
            base_filename = os.path.basename(file_path)
            print(f"\n--- Spracovávam súbor: {base_filename} ---")

            # Krok 1: Spracovanie dokumentu cez Document AI
            extracted_text = process_document(
                PROJECT_ID, LOCATION, PROCESSOR_ID, file_path, MIME_TYPE
            )
            print("Dokument úspešne spracovaný v Document AI.")

            # Krok 1.5: Uloženie surového OCR výstupu
            ocr_filename = os.path.splitext(base_filename)[0] + "_ocr.txt"
            ocr_path = os.path.join(args.ocr_dir, ocr_filename)
            with open(ocr_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            print(f"Surový OCR text bol uložený do súboru: {ocr_path}")

            # Krok 2: Anonymizácia extrahovaného textu
            print("Spúšťam anonymizáciu textu...")
            anonymized_text = anonymize_text(
                PROJECT_ID,
                extracted_text,
                DLP_TEMPLATE_ID,
            )
            print("Text úspešne anonymizovaný.")

            # Krok 3: Uloženie anonymizovaného výstupu do súboru
            output_filename = os.path.splitext(base_filename)[0] + "_anonymized.txt"
            output_path = os.path.join(args.output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(anonymized_text)
            print(f"Anonymizovaný text bol uložený do súboru: {output_path}")

        except Exception as e:
            print(f"Nastala chyba pri spracovaní súboru {file_path}: {e}")


if __name__ == "__main__":
    # Nastavenie argumentov príkazového riadku
    parser = argparse.ArgumentParser(description="Spracuj a anonymizuj dokumenty pomocou Google Cloud AI.")
    parser.add_argument(
        "input_path", 
        help="Cesta k PDF súboru alebo k priečinku s PDF súbormi."
    )
    parser.add_argument(
        "-o", "--output_dir", 
        default="anonymized_output", 
        help="Priečinok, do ktorého sa uložia anonymizované texty."
    )
    parser.add_argument(
        "--ocr_dir", 
        default="ocr_output", 
        help="Priečinok, do ktorého sa uložia surové texty z OCR."
    )
    args = parser.parse_args()
    main(args)

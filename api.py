from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os

from main import run_processing, ocr_document, anonymize_text, PROJECT_ID, DLP_TEMPLATE_ID
from analyza import run_analysis, analyze_single_document, analyze_text

EVENTS_BASE_DIR = "poistne_udalosti"
ANONYMIZED_DIR = "anonymized_output"
GENERAL_DIR = "general_output"
ANALYSIS_DIR = "analysis_output"
RAW_OCR_DIR = "raw_ocr_output"


class ProcessResponse(BaseModel):
    message: str
class OCRRequest(BaseModel):
    filename: str

class AnonymizeRequest(BaseModel):
    filename: str | None = None
    text: str | None = None

class SingleAnalysisRequest(BaseModel):
    filename: str
    prompt: str | None = None

class BatchAnalysisRequest(BaseModel):
    prompt: str | None = None


app = FastAPI(title="Claims AI API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload/{event_id}")
async def upload_pdf(event_id: str, file: UploadFile = File(...), category: str = Form("citlive_dokumenty")):
    """Nahraje PDF do štruktúry udalosti. category: citlive_dokumenty | vseobecne_dokumenty"""
    if category not in ("citlive_dokumenty", "vseobecne_dokumenty"):
        raise HTTPException(status_code=400, detail="category musí byť 'citlive_dokumenty' alebo 'vseobecne_dokumenty'")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Podporované sú len PDF súbory")
    base = os.path.join(EVENTS_BASE_DIR, event_id, category)
    os.makedirs(base, exist_ok=True)
    dest_path = os.path.join(base, file.filename)
    try:
        content = await file.read()
        with open(dest_path, 'wb') as out:
            out.write(content)
        return {"message": "Súbor nahraný", "path": dest_path.replace('\\','/')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/{event_id}", response_model=ProcessResponse)
def process_event(event_id: str):
    event_path = os.path.join(EVENTS_BASE_DIR, event_id)
    messages = []

    def cb(msg: str):
        messages.append(msg)

    try:
        run_processing(event_path, ANONYMIZED_DIR, GENERAL_DIR, RAW_OCR_DIR, cb)
        return {"message": f"Spracovanie spustené/dokončené pre {event_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/{event_id}")
def ocr_event_file(event_id: str, req: OCRRequest):
    event_dir = os.path.join(EVENTS_BASE_DIR, event_id)
    file_path = os.path.join(event_dir, "vseobecne_dokumenty", req.filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(event_dir, "citlive_dokumenty", req.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Súbor sa nenašiel v udalosti.")
    try:
        text = ocr_document(file_path)
        return {"text_preview": text[:1000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/anonymize/{event_id}")
def anonymize_event_text(event_id: str, req: AnonymizeRequest):
    if not req.text and not req.filename:
        raise HTTPException(status_code=400, detail="Poskytnite filename alebo text na anonymizáciu.")
    text = req.text
    if text is None and req.filename:
        # načítaj text zo súboru v raw_ocr_output
        path = os.path.join(RAW_OCR_DIR, event_id, os.path.splitext(req.filename)[0] + ".txt")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="RAW OCR text neexistuje. Spustite OCR najprv.")
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    try:
        anon = anonymize_text(PROJECT_ID, text, DLP_TEMPLATE_ID)
        return {"anonymized_preview": anon[:1000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/{event_id}", response_model=ProcessResponse)
def analyze_event(event_id: str):
    messages = []

    def cb(msg: str):
        messages.append(msg)

    try:
        run_analysis(event_id, ANONYMIZED_DIR, GENERAL_DIR, ANALYSIS_DIR, cb)
        return {"message": f"Analýza spustená/dokončená pre {event_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/single/{event_id}")
def analyze_single(event_id: str, req: SingleAnalysisRequest):
    try:
        result = analyze_single_document(event_id, req.filename, ANONYMIZED_DIR, GENERAL_DIR, req.prompt)
        return {"result_preview": result[:2000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/batch/{event_id}")
def analyze_batch(event_id: str, req: BatchAnalysisRequest):
    # využijeme existujúci run_analysis s override promptu cez environment (dočasne)
    try:
        if req.prompt:
            # dočasný override – analyza.py číta z configu, takže pre rýchlosť použijeme priamu funkciu analyze_text
            # načítaj všetky texty ako v run_analysis
            anon_dir = os.path.join(ANONYMIZED_DIR, event_id)
            gen_dir = os.path.join(GENERAL_DIR, event_id)
            texts = []
            for base in [anon_dir, gen_dir]:
                try:
                    for f in sorted(os.listdir(base)):
                        if f.lower().endswith('.txt'):
                            with open(os.path.join(base, f), 'r', encoding='utf-8') as fh:
                                texts.append(f"\n--- {f} ---\n" + fh.read())
                except Exception:
                    pass
            combined = "\n\n".join(texts)
            res = analyze_text(combined, req.prompt)
            return {"result_preview": res[:2000]}
        else:
            # fallback na existujúcu batch analýzu
            msgs = []
            def cb(m: str):
                msgs.append(m)
            run_analysis(event_id, ANONYMIZED_DIR, GENERAL_DIR, ANALYSIS_DIR, cb)
            return {"message": "Batch analýza spustená/dokončená"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}/documents")
def list_event_documents(event_id: str):
    anon_dir = os.path.join(ANONYMIZED_DIR, event_id)
    gen_dir = os.path.join(GENERAL_DIR, event_id)
    raw_dir = os.path.join(RAW_OCR_DIR, event_id)

    def ls_txt(path: str):
        try:
            return sorted([f for f in os.listdir(path) if f.lower().endswith('.txt')])
        except Exception:
            return []

    return {
        "event_id": event_id,
        "anonymized_texts": ls_txt(anon_dir),
        "general_texts": ls_txt(gen_dir),
        "raw_ocr_texts": ls_txt(raw_dir),
    }


@app.get("/events/{event_id}/pdfs")
def list_event_pdfs(event_id: str):
    sens_dir = os.path.join(EVENTS_BASE_DIR, event_id, "citlive_dokumenty")
    gen_dir = os.path.join(EVENTS_BASE_DIR, event_id, "vseobecne_dokumenty")

    def ls_pdf(path: str):
        try:
            return sorted([f for f in os.listdir(path) if f.lower().endswith('.pdf')])
        except Exception:
            return []

    return {
        "event_id": event_id,
        "citlive_dokumenty": ls_pdf(sens_dir),
        "vseobecne_dokumenty": ls_pdf(gen_dir),
    }



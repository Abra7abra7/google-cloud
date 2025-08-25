from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os

from main import run_processing, ocr_document, anonymize_text, PROJECT_ID, DLP_TEMPLATE_ID
from analyza import run_analysis, analyze_single_document, analyze_text
from db import get_session, Prompt, PromptRun

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


class PromptCreate(BaseModel):
    name: str
    version: str = "1.0"
    model: str
    content: str
    is_active: bool = False


class PromptUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    model: str | None = None
    content: str | None = None
    is_active: bool | None = None


class PromptResponse(BaseModel):
    id: int
    name: str
    version: str
    model: str
    content: str
    is_active: bool
    created_at: str
    updated_at: str


app = FastAPI(title="Claims AI API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload/{event_id}")
async def upload_pdf(event_id: str, file: UploadFile = File(...), category: str = Form("citlive_dokumenty")):
    """Nahraje PDF do štruktúry udalosti. category: citlive_dokumenty | vseobecne_dokumenty"""
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
    try:
        result = analyze_single_document(event_id, req.filename, ANONYMIZED_DIR, GENERAL_DIR, req.prompt)
        return {"result_preview": result[:2000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/batch/{event_id}")
def analyze_batch(event_id: str, req: BatchAnalysisRequest):
    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
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


# --- API endpointy pre správu promptov ---

@app.get("/prompts", response_model=list[PromptResponse])
def list_prompts():
    """Získa zoznam všetkých promptov."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        prompts = session.query(Prompt).all()
        return [
            PromptResponse(
                id=p.id,
                name=p.name,
                version=p.version,
                model=p.model,
                content=p.content,
                is_active=p.is_active,
                created_at=str(p.created_at),
                updated_at=str(p.updated_at)
            ) for p in prompts
        ]
    finally:
        session.close()


@app.get("/prompts/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: int):
    """Získa konkrétny prompt podľa ID."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        prompt = session.query(Prompt).filter_by(id=prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt nebol nájdený")
        
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            version=prompt.version,
            model=prompt.model,
            content=prompt.content,
            is_active=prompt.is_active,
            created_at=str(prompt.created_at),
            updated_at=str(prompt.updated_at)
        )
    finally:
        session.close()


@app.post("/prompts", response_model=PromptResponse)
def create_prompt(prompt_data: PromptCreate):
    """Vytvorí nový prompt."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        # Ak sa má aktivovať nový prompt, deaktivujeme ostatné
        if prompt_data.is_active:
            session.query(Prompt).update({"is_active": False})
        
        prompt = Prompt(
            name=prompt_data.name,
            version=prompt_data.version,
            model=prompt_data.model,
            content=prompt_data.content,
            is_active=prompt_data.is_active
        )
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            version=prompt.version,
            model=prompt.model,
            content=prompt.content,
            is_active=prompt.is_active,
            created_at=str(prompt.created_at),
            updated_at=str(prompt.updated_at)
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Chyba pri vytváraní promptu: {str(e)}")
    finally:
        session.close()


@app.put("/prompts/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: int, prompt_data: PromptUpdate):
    """Aktualizuje existujúci prompt."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        prompt = session.query(Prompt).filter_by(id=prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt nebol nájdený")
        
        # Aktualizácia polí
        if prompt_data.name is not None:
            prompt.name = prompt_data.name
        if prompt_data.version is not None:
            prompt.version = prompt_data.version
        if prompt_data.model is not None:
            prompt.model = prompt_data.model
        if prompt_data.content is not None:
            prompt.content = prompt_data.content
        if prompt_data.is_active is not None:
            prompt.is_active = prompt_data.is_active
            # Ak sa má aktivovať, deaktivujeme ostatné
            if prompt_data.is_active:
                session.query(Prompt).filter(Prompt.id != prompt_id).update({"is_active": False})
        
        session.commit()
        session.refresh(prompt)
        
        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            version=prompt.version,
            model=prompt.model,
            content=prompt.content,
            is_active=prompt.is_active,
            created_at=str(prompt.created_at),
            updated_at=str(prompt.updated_at)
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Chyba pri aktualizácii promptu: {str(e)}")
    finally:
        session.close()


@app.delete("/prompts/{prompt_id}")
def delete_prompt(prompt_id: int):
    """Vymaže prompt."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        prompt = session.query(Prompt).filter_by(id=prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt nebol nájdený")
        
        if prompt.is_active:
            raise HTTPException(status_code=400, detail="Nie je možné vymazať aktívny prompt")
        
        session.delete(prompt)
        session.commit()
        return {"message": "Prompt bol úspešne vymazaný"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Chyba pri mazaní promptu: {str(e)}")
    finally:
        session.close()


@app.post("/prompts/{prompt_id}/activate")
def activate_prompt(prompt_id: int):
    """Aktivuje prompt (deaktivuje ostatné)."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        prompt = session.query(Prompt).filter_by(id=prompt_id).first()
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt nebol nájdený")
        
        # Deaktivujeme všetky prompty
        session.query(Prompt).update({"is_active": False})
        
        # Aktivujeme vybraný
        prompt.is_active = True
        session.commit()
        
        return {"message": f"Prompt '{prompt.name}' bol aktivovaný"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Chyba pri aktivácii promptu: {str(e)}")
    finally:
        session.close()


@app.get("/prompts/{prompt_id}/runs")
def get_prompt_runs(prompt_id: int):
    """Získa históriu behov pre prompt."""
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Databáza nie je dostupná")
    
    try:
        runs = session.query(PromptRun).filter_by(prompt_id=prompt_id).order_by(PromptRun.created_at.desc()).all()
        return [
            {
                "id": run.id,
                "event_id": run.event_id,
                "model": run.model,
                "tokens_in": run.tokens_in,
                "tokens_out": run.tokens_out,
                "created_at": str(run.created_at)
            } for run in runs
        ]
    finally:
        session.close()



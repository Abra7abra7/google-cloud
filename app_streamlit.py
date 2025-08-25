import os
import streamlit as st
import datetime
import glob
import difflib

# Importujeme refaktorované funkcie z našich skriptov
from main import run_processing
from analyza import run_analysis
from db import get_session, DocumentText, AnalysisResult, ClaimEvent

# --- Konfigurácia Streamlit aplikácie ---
st.set_page_config(page_title="Analýza Poistných Udalostí", layout="wide")

st.title("Nástroj na analýzu poistných udalostí")
st.markdown("Táto aplikácia automatizuje spracovanie a analýzu dokumentov z poistných udalostí.")

# --- Globálne premenné a cesty ---
EVENTS_BASE_DIR = "poistne_udalosti"
ANONYMIZED_DIR = "anonymized_output"
GENERAL_DIR = "general_output"
ANALYSIS_DIR = "analysis_output"
RAW_OCR_DIR = "raw_ocr_output"

# --- Pomocné funkcie ---
def get_available_events(base_dir: str):
    """Načíta zoznam dostupných poistných udalostí (priečinkov)."""
    if not os.path.isdir(base_dir):
        st.error(f"Hlavný priečinok pre udalosti '{base_dir}' nebol nájdený!")
        return []
    return sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

def read_file_content(file_path: str) -> str:
    """Bezpečne načíta obsah textového súboru."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Súbor nebol nájdený."
    except Exception as e:
        return f"Chyba pri čítaní súboru: {e}"

def display_input_files(event_id: str):
    """Zobrazí zoznam vstupných PDF súborov pre danú udalosť."""
    with st.expander("Zobraziť vstupné dokumenty"):
        sensitive_path = os.path.join(EVENTS_BASE_DIR, event_id, "citlive_dokumenty")
        general_path = os.path.join(EVENTS_BASE_DIR, event_id, "vseobecne_dokumenty")

        st.markdown("**Citlivé dokumenty:**")
        try:
            sensitive_files = [f for f in os.listdir(sensitive_path) if f.lower().endswith('.pdf')]
            if sensitive_files:
                for f in sensitive_files: st.markdown(f"- `{f}`")
            else:
                st.info("Nenájdené žiadne citlivé dokumenty.")
        except FileNotFoundError:
            st.warning("Priečinok pre citlivé dokumenty neexistuje.")

        st.markdown("**Všeobecné dokumenty:**")
        try:
            general_files = [f for f in os.listdir(general_path) if f.lower().endswith('.pdf')]
            if general_files:
                for f in general_files: st.markdown(f"- `{f}`")
            else:
                st.info("Nenájdené žiadne všeobecné dokumenty.")
        except FileNotFoundError:
            st.warning("Priečinok pre všeobecné dokumenty neexistuje.")

# --- Komponenty UI ---
def create_new_event_section():
    """Zobrazí sekciu na vytvorenie novej poistnej udalosti."""
    st.header("Vytvoriť novú poistnú udalosť")
    with st.expander("Kliknite sem pre vytvorenie novej udalosti"):
        with st.form("new_event_form", clear_on_submit=True):
            new_event_id = st.text_input("Zadajte názov (ID) novej poistnej udalosti", placeholder="napr. PU_2024_015")
            sensitive_files = st.file_uploader("Nahrajte citlivé dokumenty", type=['pdf'], accept_multiple_files=True, key="sensitive")
            general_files = st.file_uploader("Nahrajte všeobecné dokumenty", type=['pdf'], accept_multiple_files=True, key="general")
            submitted = st.form_submit_button("Vytvoriť udalosť")

            if submitted:
                handle_new_event_submission(new_event_id, sensitive_files, general_files)

def handle_new_event_submission(event_id, sensitive_files, general_files):
    """Spracuje logiku pre vytvorenie novej udalosti po odoslaní formulára."""
    if not event_id:
        st.error("Musíte zadať názov (ID) poistnej udalosti.")
        return
    if not sensitive_files and not general_files:
        st.error("Musíte nahrať aspoň jeden dokument.")
        return

    try:
        event_dir = os.path.join(EVENTS_BASE_DIR, event_id)
        if os.path.exists(event_dir):
            st.error(f"Udalosť s názvom '{event_id}' už existuje!")
            return

        # Vytvorenie priečinkov a uloženie súborov
        for file_list, subfolder in [(sensitive_files, "citlive_dokumenty"), (general_files, "vseobecne_dokumenty")]:
            if file_list:
                target_dir = os.path.join(event_dir, subfolder)
                os.makedirs(target_dir, exist_ok=True)
                for f in file_list:
                    with open(os.path.join(target_dir, f.name), "wb") as out_file:
                        out_file.write(f.getvalue())
        
        st.success(f"Poistná udalosť '{event_id}' bola úspešne vytvorená!")
        st.info("Zoznam udalostí sa aktualizuje...")
        st.rerun()

    except Exception as e:
        st.error(f"Nepodarilo sa vytvoriť udalosť: {e}")

def display_results(event_id):
    """Zobrazí výsledky spracovania a analýzy pre vybranú udalosť."""
    st.subheader(f"Výsledky pre udalosť: {event_id}")
    display_input_files(event_id)

    result_path = os.path.join(ANALYSIS_DIR, f"{event_id}_analyza.txt")
    process_button_text = "Spracovať a analyzovať"

    if os.path.exists(result_path):
        display_analysis_tabs(event_id, result_path)
        process_button_text = "Spracovať znova"
    
    if st.button(process_button_text):
        run_full_process(event_id)

def display_analysis_tabs(event_id, result_path):
    """Zobrazí výsledky v záložkách (Finálna analýza, Detailné výstupy, DB prehľad)."""
    tab1, tab2, tab3 = st.tabs(["Finálna Analýza", "Detailné výstupy (Human-in-the-loop)", "DB prehľad"])

    with tab1:
        st.subheader("Súhrnná analýza (Gemini)")
        analysis_content = read_file_content(result_path)
        st.text_area("Analyzovaný text", analysis_content, height=400)
        st.download_button("Stiahnuť analýzu", analysis_content, os.path.basename(result_path), 'text/plain')

    with tab2:
        display_detailed_outputs(event_id)

    with tab3:
        display_db_status(event_id)

def display_detailed_outputs(event_id):
    """Zobrazí detailné porovnanie OCR vs. anonymizovaného textu."""
    st.subheader("Kontrola medzikrokov spracovania")

    # Citlivé dokumenty
    st.markdown("#### Citlivé dokumenty")
    raw_ocr_event_dir = os.path.join(RAW_OCR_DIR, event_id)
    anonymized_event_dir = os.path.join(ANONYMIZED_DIR, event_id)
    sensitive_docs = glob.glob(os.path.join(raw_ocr_event_dir, '*.txt'))
    if not sensitive_docs:
        st.info("Nenájdené žiadne spracované citlivé dokumenty.")
    else:
        for doc_path in sensitive_docs:
            doc_name = os.path.basename(doc_path)
            with st.expander(f"Dokument: {doc_name}"):
                col_raw, col_anon = st.columns(2)
                raw_content = read_file_content(doc_path)
                anonymized_content = read_file_content(os.path.join(anonymized_event_dir, doc_name))
                with col_raw: st.text_area("Pôvodný text (OCR)", raw_content, height=300, key=f"raw_{doc_name}")
                with col_anon: st.text_area("Anonymizovaný text", anonymized_content, height=300, key=f"anon_{doc_name}")

                diff = difflib.unified_diff(
                    (raw_content or "").splitlines(),
                    (anonymized_content or "").splitlines(),
                    fromfile='OCR', tofile='ANON', lineterm=''
                )
                diff_text = '\n'.join(diff)
                if diff_text:
                    st.markdown("**Zvýraznené rozdiely (diff):**")
                    st.code(diff_text, language='diff')

    # Všeobecné dokumenty
    st.markdown("#### Všeobecné dokumenty")
    general_event_dir = os.path.join(GENERAL_DIR, event_id)
    general_docs = glob.glob(os.path.join(general_event_dir, '*.txt'))
    if not general_docs:
        st.info("Nenájdené žiadne spracované všeobecné dokumenty.")
    else:
        for doc_path in general_docs:
            doc_name = os.path.basename(doc_path)
            with st.expander(f"Dokument: {doc_name}"):
                st.text_area("OCR Text", read_file_content(doc_path), height=300, key=f"gen_{doc_name}")

def display_db_status(event_id: str):
    """Zobrazí prehľad záznamov uložených v databáze pre vybranú udalosť."""
    st.subheader("Databázové záznamy (SQLite/MySQL)")
    session = get_session()
    if session is None:
        st.info("Databáza nie je nakonfigurovaná alebo je vypnutá v config.ini.")
        return
    try:
        total_events = session.query(ClaimEvent).count()
        total_docs = session.query(DocumentText).count()
        total_analysis = session.query(AnalysisResult).count()
        st.markdown(f"- Počet udalostí v DB: **{total_events}**")
        st.markdown(f"- Počet dokumentov v DB: **{total_docs}**")
        st.markdown(f"- Počet analýz v DB: **{total_analysis}**")

        st.markdown("\nZáznamy pre vybranú udalosť:")
        docs = session.query(DocumentText).filter_by(event_id=event_id).all()
        if docs:
            for d in docs:
                with st.expander(f"Dokument v DB: {d.filename}"):
                    st.write({
                        "event_id": d.event_id,
                        "filename": d.filename,
                        "ocr_text_len": len(d.ocr_text or ''),
                        "anonymized_text_len": len(d.anonymized_text or ''),
                        "created_at": str(getattr(d, 'created_at', '')),
                    })
        else:
            st.info("Pre túto udalosť zatiaľ nie sú uložené žiadne dokumenty v DB.")

        analyses = session.query(AnalysisResult).filter_by(event_id=event_id).all()
        if analyses:
            for a in analyses:
                with st.expander("Výsledok analýzy v DB"):
                    st.write({
                        "model": a.model,
                        "created_at": str(getattr(a, 'created_at', '')),
                        "summary_preview": (a.summary_text or '')[:400] + ("..." if a.summary_text and len(a.summary_text) > 400 else ""),
                    })
        else:
            st.info("Pre túto udalosť zatiaľ nie je uložená žiadna analýza v DB.")
    finally:
        session.close()

def run_full_process(event_id):
    """Spustí celý proces spracovania a analýzy a zobrazí priebeh."""
    event_path = os.path.join(EVENTS_BASE_DIR, event_id)
    status_placeholder = st.empty()
    log_messages = []

    def status_callback(message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_messages.append(f"`{timestamp}` - {message}")
        status_placeholder.info('\n'.join(log_messages[-15:]))

    try:
        with st.spinner("Proces prebieha, prosím počkajte..."):
            status_callback("Spúšťam spracovanie dokumentov...")
            run_processing(event_path, ANONYMIZED_DIR, GENERAL_DIR, RAW_OCR_DIR, status_callback)
            
            status_callback("Spracovanie dokumentov dokončené. Spúšťam analýzu...")
            run_analysis(event_id, ANONYMIZED_DIR, GENERAL_DIR, ANALYSIS_DIR, status_callback)
        
        st.success(f"Proces pre udalosť '{event_id}' bol úspešne dokončený!")
        st.rerun()

    except Exception as e:
        st.error(f"Nastala neočakávaná chyba: {e}")

# --- Hlavná logika aplikácie ---
def main():
    """Hlavný beh Streamlit aplikácie."""
    create_new_event_section()
    st.divider()

    st.header("Dostupné poistné udalosti")
    events = get_available_events(EVENTS_BASE_DIR)

    if not events:
        st.warning(f"V priečinku `{EVENTS_BASE_DIR}` sa nenašli žiadne poistné udalosti. Vytvorte novú udalosť vyššie.")
    else:
        col1, col2 = st.columns([1, 3])

        with col1:
            st.subheader("Zoznam udalostí")
            selected_event = st.radio("Vyberte udalosť:", events, label_visibility="collapsed")

        with col2:
            if selected_event:
                display_results(selected_event)

if __name__ == "__main__":
    main()

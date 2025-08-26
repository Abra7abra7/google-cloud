import os
import html
from dotenv import load_dotenv
import streamlit as st
import datetime
import glob
import difflib

# Načítanie .env.local ako jediného zdroja pravdy pre konfiguráciu
load_dotenv('.env.local', override=True)
load_dotenv(override=False)

# Importujeme refaktorované funkcie z našich skriptov
from main import run_processing
from analyza import run_analysis
from db import get_session, DocumentText, AnalysisResult, ClaimEvent, Prompt, PromptRun

# --- Konfigurácia Streamlit aplikácie ---
st.set_page_config(page_title="Analýza Poistných Udalostí", layout="wide")

# Jemné vizuálne vylepšenia
st.markdown(
    """
    <style>
      /* Zmenšenie vertikálnych medzier */
      .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
      /* Zvýraznenie metrík */
      div[data-testid="stMetricValue"] { font-weight: 700; }
      /* Krajšie expander hlavičky */
      details > summary { font-size: 0.98rem; }
      /* Odstupy medzi sekciami */
      hr { margin: 0.8rem 0 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

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

def get_global_metrics():
    """Vráti počty udalostí, dokumentov a analýz pre prehľadové metriky."""
    try:
        session = get_session()
        if session is None:
            return 0, 0, 0
        try:
            total_events = session.query(ClaimEvent).count()
            total_docs = session.query(DocumentText).count()
            total_analysis = session.query(AnalysisResult).count()
            return total_events, total_docs, total_analysis
        finally:
            session.close()
    except Exception:
        return 0, 0, 0

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
            new_event_id = st.text_input("Zadajte názov (ID) novej poistnej udalosti", placeholder="napr. PU_2024_015", help="Názov sa automaticky vyčistí od medzier")
            sensitive_files = st.file_uploader("Nahrajte citlivé dokumenty", type=['pdf'], accept_multiple_files=True, key="sensitive")
            general_files = st.file_uploader("Nahrajte všeobecné dokumenty", type=['pdf'], accept_multiple_files=True, key="general")
            submitted = st.form_submit_button("Vytvoriť udalosť")

            if submitted:
                handle_new_event_submission(new_event_id, sensitive_files, general_files)

    st.markdown("---")

def handle_new_event_submission(event_id, sensitive_files, general_files):
    """Spracuje logiku pre vytvorenie novej udalosti po odoslaní formulára."""
    if not event_id:
        st.error("Musíte zadať názov (ID) poistnej udalosti.")
        return
    if not sensitive_files and not general_files:
        st.error("Musíte nahrať aspoň jeden dokument.")
        return

    # Vyčistenie názvu udalosti od medzier
    event_id = event_id.strip()
    if not event_id:
        st.error("Názov udalosti nemôže byť prázdny.")
        return

    try:
        # Návrh jedinečného názvu, ak priečinok už existuje
        base_event_id = event_id
        event_dir = os.path.join(EVENTS_BASE_DIR, base_event_id)
        if os.path.exists(event_dir):
            suffix = 2
            while os.path.exists(os.path.join(EVENTS_BASE_DIR, f"{base_event_id}-{suffix}")):
                suffix += 1
            event_id = f"{base_event_id}-{suffix}"
            event_dir = os.path.join(EVENTS_BASE_DIR, event_id)
            st.warning(f"Udalosť s názvom '{base_event_id}' už existuje. Ukladám ako '{event_id}'.")

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

    # Pomocná funkcia na zvýraznenie rozdielov medzi OCR a anonymizovaným textom
    def highlight_differences(original_text: str, anonymized_text: str) -> tuple[str, str, int]:
        """Vytvorí HTML s vyznačením rozdielov. Vracia (html_raw, html_anon, diff_count)."""
        sm = difflib.SequenceMatcher(a=original_text, b=anonymized_text)
        parts_raw: list[str] = []
        parts_anon: list[str] = []
        diff_count = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            a_seg = original_text[i1:i2]
            b_seg = anonymized_text[j1:j2]
            if tag == 'equal':
                parts_raw.append(a_seg)
                parts_anon.append(b_seg)
            elif tag in ('replace', 'delete', 'insert'):
                # zvýrazníme rozdiely; počítame ako diff položky
                diff_count += 1
                if a_seg:
                    parts_raw.append(f"<mark style='background:#ffe8e8'>{html.escape(a_seg)}</mark>")
                if b_seg:
                    parts_anon.append(f"<mark style='background:#e8ffe8'>{html.escape(b_seg)}</mark>")
        # HTML výstup
        html_raw = "<div style='white-space:pre-wrap; font-family:monospace'>" + ''.join(parts_raw) + "</div>"
        html_anon = "<div style='white-space:pre-wrap; font-family:monospace'>" + ''.join(parts_anon) + "</div>"
        return html_raw, html_anon, diff_count

    # Citlivé dokumenty
    st.markdown("#### Citlivé dokumenty")
    raw_ocr_event_dir = os.path.join(RAW_OCR_DIR, event_id)
    anonymized_event_dir = os.path.join(ANONYMIZED_DIR, event_id)
    sensitive_docs = glob.glob(os.path.join(raw_ocr_event_dir, '*.txt'))
    if not sensitive_docs:
        st.info("Nenájdené žiadne spracované citlivé dokumenty. Nahrajte PDF do priečinka citlivé dokumenty a spustite spracovanie.")
    else:
        for doc_path in sensitive_docs:
            doc_name = os.path.basename(doc_path)
            with st.expander(f"Dokument: {doc_name}"):
                col_raw, col_anon = st.columns(2)
                raw_content = read_file_content(doc_path) or ""
                anonymized_content = read_file_content(os.path.join(anonymized_event_dir, doc_name)) or ""
                # zvýraznenie rozdielov (inline highlighting)
                html_raw, html_anon, diff_count = highlight_differences(raw_content, anonymized_content)
                with col_raw:
                    st.markdown("**Pôvodný text (OCR)**", help="Text extrahovaný Document AI")
                    st.markdown(html_raw, unsafe_allow_html=True)
                with col_anon:
                    st.markdown("**Anonymizovaný text**", help="Text po Cloud DLP de-identifikácii")
                    st.markdown(html_anon, unsafe_allow_html=True)
                st.caption(f"Počet odlišných úsekov: {diff_count}")

    # Všeobecné dokumenty
    st.markdown("#### Všeobecné dokumenty")
    general_event_dir = os.path.join(GENERAL_DIR, event_id)
    general_docs = glob.glob(os.path.join(general_event_dir, '*.txt'))
    if not general_docs:
        st.info("Nenájdené žiadne spracované všeobecné dokumenty. Nahrajte PDF do priečinka všeobecné dokumenty a spustite spracovanie.")
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
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Udalosti", total_events)
        col_b.metric("Dokumenty", total_docs)
        col_c.metric("Analýzy", total_analysis)

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


def manage_prompts_section():
    """Zobrazí sekciu na správu promptov."""
    st.header("Správa promptov")
    
    session = get_session()
    if session is None:
        st.error("Databáza nie je dostupná!")
        return
    
    try:
        # Zoznam existujúcich promptov
        prompts = session.query(Prompt).all()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Existujúce prompty")
            if prompts:
                for prompt in prompts:
                    with st.expander(f"{prompt.name} v{prompt.version} {'✅' if prompt.is_active else '❌'}"):
                        st.write(f"**Model:** {prompt.model}")
                        st.write(f"**Aktívny:** {'Áno' if prompt.is_active else 'Nie'}")
                        st.write(f"**Vytvorený:** {prompt.created_at.strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Aktualizovaný:** {prompt.updated_at.strftime('%Y-%m-%d %H:%M')}")
                        
                        st.text_area("Obsah promptu", prompt.content, height=150, key=f"view_{prompt.id}")
                        
                        col_edit, col_activate, col_delete = st.columns(3)
                        with col_edit:
                            if st.button("Upraviť", key=f"edit_{prompt.id}"):
                                st.session_state[f"editing_prompt_{prompt.id}"] = True
                        
                        with col_activate:
                            if not prompt.is_active:
                                if st.button("Aktivovať", key=f"activate_{prompt.id}"):
                                    try:
                                        # Deaktivujeme všetky prompty
                                        session.query(Prompt).update({"is_active": False})
                                        # Aktivujeme vybraný
                                        prompt.is_active = True
                                        session.commit()
                                        st.success(f"Prompt '{prompt.name}' bol aktivovaný!")
                                        st.rerun()
                                    except Exception as e:
                                        session.rollback()
                                        st.error(f"Chyba pri aktivácii: {e}")
                        
                        with col_delete:
                            if not prompt.is_active:
                                if st.button("Vymazať", key=f"delete_{prompt.id}"):
                                    try:
                                        session.delete(prompt)
                                        session.commit()
                                        st.success(f"Prompt '{prompt.name}' bol vymazaný!")
                                        st.rerun()
                                    except Exception as e:
                                        session.rollback()
                                        st.error(f"Chyba pri mazaní: {e}")
                        
                        # Editácia promptu
                        if st.session_state.get(f"editing_prompt_{prompt.id}", False):
                            with st.form(f"edit_form_{prompt.id}"):
                                new_name = st.text_input("Názov", value=prompt.name, key=f"edit_name_{prompt.id}")
                                new_version = st.text_input("Verzia", value=prompt.version, key=f"edit_version_{prompt.id}")
                                new_model = st.text_input("Model", value=prompt.model, key=f"edit_model_{prompt.id}")
                                new_content = st.text_area("Obsah", value=prompt.content, height=200, key=f"edit_content_{prompt.id}")
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("Uložiť"):
                                        try:
                                            prompt.name = new_name
                                            prompt.version = new_version
                                            prompt.model = new_model
                                            prompt.content = new_content
                                            prompt.updated_at = datetime.datetime.utcnow()
                                            session.commit()
                                            st.success("Prompt bol úspešne upravený!")
                                            st.session_state[f"editing_prompt_{prompt.id}"] = False
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"Chyba pri ukladaní: {e}")
                                
                                with col_cancel:
                                    if st.form_submit_button("Zrušiť"):
                                        st.session_state[f"editing_prompt_{prompt.id}"] = False
                                        st.rerun()
            else:
                st.info("Zatiaľ nie sú vytvorené žiadne prompty.")
        
        with col2:
            st.subheader("Vytvoriť nový prompt")
            with st.form("new_prompt_form"):
                name = st.text_input("Názov promptu", placeholder="napr. Poistné udalosti - základný")
                version = st.text_input("Verzia", value="1.0")
                model = st.text_input("Model", value="gemini-1.5-flash-002")
                content = st.text_area("Obsah promptu", 
                                     value="Zhrň kľúčové body z nasledujúcich poistných dokumentov. Zameraj sa na typ poistenia, poistné sumy, dátumy platnosti a mená zúčastnených strán. Vypíš výsledok v prehľadnej štruktúre.",
                                     height=200)
                is_active = st.checkbox("Aktivovať po vytvorení")
                
                if st.form_submit_button("Vytvoriť prompt"):
                    if not name or not content:
                        st.error("Názov a obsah promptu sú povinné!")
                    else:
                        try:
                            # Ak sa má aktivovať nový prompt, deaktivujeme ostatné
                            if is_active:
                                session.query(Prompt).update({"is_active": False})
                            
                            new_prompt = Prompt(
                                name=name,
                                version=version,
                                model=model,
                                content=content,
                                is_active=is_active
                            )
                            session.add(new_prompt)
                            session.commit()
                            st.success(f"Prompt '{name}' bol úspešne vytvorený!")
                            st.rerun()
                        except Exception as e:
                            session.rollback()
                            st.error(f"Chyba pri vytváraní promptu: {e}")
    
    finally:
        session.close()

# --- Hlavná logika aplikácie ---
def main():
    """Hlavný beh Streamlit aplikácie."""
    # Sidebar pre navigáciu
    st.sidebar.title("Navigácia")
    page = st.sidebar.radio("Vyberte stránku:", ["Poistné udalosti", "Správa promptov"])
    
    if page == "Poistné udalosti":
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
    
    elif page == "Správa promptov":
        manage_prompts_section()

if __name__ == "__main__":
    main()

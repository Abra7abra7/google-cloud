import os
import streamlit as st
import datetime
import glob

# Importujeme refaktorované funkcie z našich skriptov
from main import run_processing
from analyza import run_analysis

# --- Konfigurácia Streamlit aplikácie ---
st.set_page_config(page_title="Analýza Poistných Udalostí", layout="wide")

st.title("Nástroj na analýzu poistných udalostí")
st.markdown("Táto aplikácia automatizuje spracovanie a analýzu dokumentov z poistných udalostí.")

# --- Globálne premenné a cesty ---
EVENTS_BASE_DIR = "poistne_udalosti"
ANONYMIZED_DIR = "anonymized_output"
GENERAL_DIR = "general_output"
ANALYSIS_DIR = "analysis_output"
RAW_OCR_DIR = "raw_ocr_output" # Nový priečinok pre medzivýsledky

# --- Funkcie pre aplikáciu ---
def get_available_events(base_dir: str):
    """Načíta zoznam dostupných poistných udalostí (priečinkov)."""
    if not os.path.isdir(base_dir):
        return []
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

def read_file_content(file_path):
    """Bezpečne načíta obsah súboru."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Súbor nebol nájdený."
    except Exception as e:
        return f"Chyba pri čítaní súboru: {e}"

# --- Sekcia na vytvorenie novej udalosti ---
st.header("Vytvoriť novú poistnú udalosť")
with st.expander("Kliknite sem pre vytvorenie novej udalosti"):
    with st.form("new_event_form", clear_on_submit=True):
        new_event_id = st.text_input("Zadajte názov (ID) novej poistnej udalosti", placeholder="napr. PU_2024_015")
        sensitive_files = st.file_uploader("Nahrajte citlivé dokumenty (budú anonymizované)", type=['pdf'], accept_multiple_files=True, key="sensitive")
        general_files = st.file_uploader("Nahrajte všeobecné dokumenty (nebudú anonymizované)", type=['pdf'], accept_multiple_files=True, key="general")
        submitted = st.form_submit_button("Vytvoriť udalosť")

        if submitted:
            if not new_event_id:
                st.error("Musíte zadať názov (ID) poistnej udalosti.")
            elif not sensitive_files and not general_files:
                st.error("Musíte nahrať aspoň jeden dokument.")
            else:
                try:
                    event_dir = os.path.join(EVENTS_BASE_DIR, new_event_id)
                    if os.path.exists(event_dir):
                        st.error(f"Udalosť s názvom '{new_event_id}' už existuje!")
                    else:
                        sensitive_dir = os.path.join(event_dir, "citlive_dokumenty")
                        general_dir = os.path.join(event_dir, "vseobecne_dokumenty")
                        os.makedirs(sensitive_dir, exist_ok=True)
                        os.makedirs(general_dir, exist_ok=True)

                        for f in sensitive_files:
                            with open(os.path.join(sensitive_dir, f.name), "wb") as out_file:
                                out_file.write(f.getvalue())
                        for f in general_files:
                            with open(os.path.join(general_dir, f.name), "wb") as out_file:
                                out_file.write(f.getvalue())
                        
                        st.success(f"Poistná udalosť '{new_event_id}' bola úspešne vytvorená!")
                        st.info("Zoznam udalostí sa aktualizuje.")
                except Exception as e:
                    st.error(f"Nepodarilo sa vytvoriť udalosť: {e}")

st.divider()
st.header("Dostupné poistné udalosti")

events = get_available_events(EVENTS_BASE_DIR)

if not events:
    st.warning(f"V priečinku `{EVENTS_BASE_DIR}` sa nenašli žiadne poistné udalosti.")
else:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Zoznam udalostí")
        selected_event = st.radio("Vyberte udalosť na spracovanie:", events)

    with col2:
        st.subheader(f"Výsledky pre udalosť: {selected_event}")

        # --- Sekcia na zobrazenie vstupných súborov ---
        with st.expander("Zobraziť vstupné dokumenty"):
            sensitive_path = os.path.join(EVENTS_BASE_DIR, selected_event, "citlive_dokumenty")
            general_path = os.path.join(EVENTS_BASE_DIR, selected_event, "vseobecne_dokumenty")

            st.markdown("**Citlivé dokumenty:**")
            try:
                sensitive_files = [f for f in os.listdir(sensitive_path) if f.lower().endswith('.pdf')]
                if sensitive_files:
                    for f in sensitive_files:
                        st.markdown(f"- `{f}`")
                else:
                    st.info("Nenájdené žiadne citlivé dokumenty.")
            except FileNotFoundError:
                st.warning("Priečinok pre citlivé dokumenty neexistuje.")

            st.markdown("**Všeobecné dokumenty:**")
            try:
                general_files = [f for f in os.listdir(general_path) if f.lower().endswith('.pdf')]
                if general_files:
                    for f in general_files:
                        st.markdown(f"- `{f}`")
                else:
                    st.info("Nenájdené žiadne všeobecné dokumenty.")
            except FileNotFoundError:
                st.warning("Priečinok pre všeobecné dokumenty neexistuje.")

        
        result_path = os.path.join(ANALYSIS_DIR, f"{selected_event}_analyza.txt")
        process_button_text = "Spracovať a analyzovať"

        # Skontrolujeme, či už existuje výsledok analýzy
        if os.path.exists(result_path):
            # --- Zobrazenie výsledkov v záložkách ---
            tab1, tab2 = st.tabs(["Finálna Analýza", "Detailné výstupy (Human-in-the-loop)"])

            with tab1:
                st.subheader("Súhrnná analýza (Gemini)")
                analysis_content = read_file_content(result_path)
                st.text_area("Analyzovaný text", analysis_content, height=400)
                st.download_button("Stiahnuť výsledok analýzy", analysis_content, os.path.basename(result_path), 'text/plain')

            with tab2:
                st.subheader("Kontrola medzikrokov spracovania")

                # Cesty k výstupným priečinkom pre danú udalosť
                raw_ocr_event_dir = os.path.join(RAW_OCR_DIR, selected_event)
                anonymized_event_dir = os.path.join(ANONYMIZED_DIR, selected_event)
                general_event_dir = os.path.join(GENERAL_DIR, selected_event)

                st.markdown("#### Citlivé dokumenty")
                sensitive_docs = glob.glob(os.path.join(raw_ocr_event_dir, '*.txt'))
                if not sensitive_docs:
                    st.info("Pre túto udalosť neboli spracované žiadne citlivé dokumenty.")
                else:
                    for doc_path in sensitive_docs:
                        doc_name = os.path.basename(doc_path)
                        with st.expander(f"Dokument: {doc_name}"):
                            col_raw, col_anon = st.columns(2)
                            
                            raw_content = read_file_content(doc_path)
                            anonymized_path = os.path.join(anonymized_event_dir, doc_name)
                            anonymized_content = read_file_content(anonymized_path)

                            with col_raw:
                                st.markdown("**Pôvodný text (OCR)**")
                                st.text_area("Raw OCR", raw_content, height=300, key=f"raw_{doc_name}")
                            with col_anon:
                                st.markdown("**Anonymizovaný text**")
                                st.text_area("Anonymized", anonymized_content, height=300, key=f"anon_{doc_name}")

                st.markdown("#### Všeobecné dokumenty")
                general_docs = glob.glob(os.path.join(general_event_dir, '*.txt'))
                if not general_docs:
                    st.info("Pre túto udalosť neboli spracované žiadne všeobecné dokumenty.")
                else:
                    for doc_path in general_docs:
                        doc_name = os.path.basename(doc_path)
                        with st.expander(f"Dokument: {doc_name}"):
                            content = read_file_content(doc_path)
                            st.text_area("OCR Text", content, height=300, key=f"gen_{doc_name}")

            process_button_text = "Spracovať znova"
        
        # Tlačidlo na spracovanie sa zobrazí vždy, ale text sa mení
        if st.button(process_button_text):
            event_path = os.path.join(EVENTS_BASE_DIR, selected_event)
            status_placeholder = st.empty()
            log_messages = []

            def status_callback(message):
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                log_messages.append(f"`{timestamp}` - {message}")
                status_placeholder.info('\n'.join(log_messages[-15:]))

            try:
                with st.spinner("Proces prebieha, prosím počkajte..."):
                    status_callback("Spúšťam spracovanie dokumentov...")
                    # Odovzdávame aj novú cestu RAW_OCR_DIR
                    run_processing(event_path, ANONYMIZED_DIR, GENERAL_DIR, RAW_OCR_DIR, status_callback)
                    
                    status_callback("Spracovanie dokumentov dokončené. Spúšťam analýzu...")
                    run_analysis(selected_event, ANONYMIZED_DIR, GENERAL_DIR, ANALYSIS_DIR, status_callback)
                
                st.success(f"Proces pre udalosť '{selected_event}' bol úspešne dokončený!")
                st.rerun()

            except Exception as e:
                st.error(f"Nastala neočakávaná chyba: {e}")

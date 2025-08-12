import os
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog

# Importujeme refaktorované funkcie z našich skriptov
from main import run_processing
from analyza import run_analysis

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nástroj na analýzu poistných udalostí")
        self.geometry("700x550")
        self._set_appearance_mode("dark")

        self.event_path = ""
        self.result_path = ""

        # --- UI Elementy ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Frame pre hornú časť (výber súboru)
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.select_button = ctk.CTkButton(self.top_frame, text="Vybrať priečinok poistnej udalosti", command=self.select_event_folder)
        self.select_button.grid(row=0, column=0, padx=10, pady=10)

        self.path_label = ctk.CTkLabel(self.top_frame, text="Nie je vybraný žiadny priečinok", anchor="w")
        self.path_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Frame pre hlavné tlačidlo
        self.run_button_frame = ctk.CTkFrame(self)
        self.run_button_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.run_button_frame.grid_columnconfigure(0, weight=1)

        self.run_button = ctk.CTkButton(self.run_button_frame, text="Spracovať a analyzovať", command=self.start_processing_thread, state="disabled")
        self.run_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Textové pole pre status
        self.status_textbox = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.status_textbox.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Frame pre spodné tlačidlo (zobrazenie výsledku)
        self.result_button_frame = ctk.CTkFrame(self)
        self.result_button_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.result_button_frame.grid_columnconfigure(0, weight=1)

        self.result_button = ctk.CTkButton(self.result_button_frame, text="Zobraziť výsledok", command=self.show_result, state="disabled")
        self.result_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    def select_event_folder(self):
        path = filedialog.askdirectory(title="Vyberte priečinok poistnej udalosti")
        if not path:
            return

        # Validácia: Skontrolujeme, či priečinok obsahuje požadované podpriečinky
        has_sensitive = os.path.isdir(os.path.join(path, "citlive_dokumenty"))
        has_general = os.path.isdir(os.path.join(path, "vseobecne_dokumenty"))

        if not has_sensitive and not has_general:
            self.event_path = ""
            self.path_label.configure(text="Neplatný priečinok! Musí obsahovať 'citlive_dokumenty' alebo 'vseobecne_dokumenty'.")
            self.run_button.configure(state="disabled")
            self.update_status("Chyba: Vybraný priečinok nemá správnu štruktúru.", clear=True)
            return

        self.event_path = path
        self.path_label.configure(text=os.path.basename(path))
        self.run_button.configure(state="normal")
        self.result_button.configure(state="disabled")
        self.update_status("Priečinok pripravený. Stlačte 'Spracovať a analyzovať'.", clear=True)

    def update_status(self, message, clear=False):
        self.status_textbox.configure(state="normal")
        if clear:
            self.status_textbox.delete("1.0", "end")
        self.status_textbox.insert("end", message + "\n")
        self.status_textbox.see("end")
        self.status_textbox.configure(state="disabled")
        self.update_idletasks() # Okamžité prekreslenie UI

    def start_processing_thread(self):
        self.run_button.configure(state="disabled")
        self.result_button.configure(state="disabled")
        self.update_status("Spúšťam proces...", clear=True)
        
        # Spustenie v samostatnom vlákne, aby UI nezamrzlo
        thread = threading.Thread(target=self.process_event)
        thread.start()

    def process_event(self):
        try:
            event_id = os.path.basename(self.event_path)

            # 1. Spracovanie (main.py)
            run_processing(self.event_path, "anonymized_output", "general_output", self.update_status)
            
            # 2. Analýza (analyza.py)
            self.result_path = run_analysis(event_id, "anonymized_output", "general_output", "analysis_output", self.update_status)

            self.update_status("\nPROCES DOKONČENÝ.")
            if self.result_path and os.path.exists(self.result_path):
                self.result_button.configure(state="normal")

        except Exception as e:
            self.update_status(f"\nNASTALA KRITICKÁ CHYBA: {e}")
        finally:
            self.run_button.configure(state="normal")

    def show_result(self):
        if self.result_path and os.path.exists(self.result_path):
            # Použijeme os.startfile pre Windows na otvorenie súboru v predvolenom programe
            if os.name == 'nt':
                os.startfile(self.result_path)
            # Pre macOS
            elif os.name == 'posix':
                subprocess.call(('open', self.result_path))

if __name__ == "__main__":
    app = App()
    app.mainloop()

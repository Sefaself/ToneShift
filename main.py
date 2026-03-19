import tkinter as tk
from tkinter import messagebox
import pyperclip
from google import genai
import threading


# ── CONFIG ──────────────────────────────────────────────────────────────────
DEFAULT_API_KEY = ""   # ← inserisci qui la tua chiave di default


TONI = ["Correggi", "Formale", "Informale", "Amichevole", "Persuasivo", "Assertivo", "Semplifica"]


TONE_PROMPTS = {
    "Correggi":     "Correggi tutti gli errori grammaticali, ortografici e di punteggiatura nel testo seguente. Preserva esattamente il significato e il tono originale. Restituisci solo il testo corretto, e magari migliora il testo rendendolo più fluido e naturale, ma senza cambiare il suo stile o registro.",
    "Formale":      "Riscrivi il testo seguente in un tono formale e professionale, adatto a un contesto lavorativo o accademico. Restituisci solo il testo riscritto, nient'altro.",
    "Informale":    "Riscrivi il testo seguente in un tono rilassato e colloquiale, come in una conversazione quotidiana. Restituisci solo il testo riscritto, nient'altro.",
    "Amichevole":   "Riscrivi il testo seguente in un tono caldo, amichevole e accogliente. Restituisci solo il testo riscritto, nient'altro.",
    "Persuasivo":   "Riscrivi il testo seguente in modo convincente e persuasivo, spingendo il lettore ad essere d'accordo o ad agire. Restituisci solo il testo riscritto, nient'altro.",
    "Assertivo":    "Riscrivi il testo seguente in un tono sicuro, diretto e assertivo. Restituisci solo il testo riscritto, nient'altro.",
    "Semplifica":   "Riscrivi il testo seguente in modo che anche un bambino di 5 anni possa capirlo. Usa parole semplici e frasi brevi. Restituisci solo il testo riscritto, nient'altro.",
}


# ── COLORI & FONT ────────────────────────────────────────────────────────────
BG       = "#0f0f13"
PANEL    = "#1a1a24"
ACCENT   = "#7c6af7"
ACCENT2  = "#a78bfa"
TEXT_FG  = "#e8e6f0"
MUTED    = "#6b6880"
SUCCESS  = "#4ade80"
BORDER   = "#2a2a3a"
DANGER   = "#f87171"


FONT_TITLE = ("Georgia", 22, "bold")
FONT_LABEL = ("Helvetica", 10, "bold")
FONT_BODY  = ("Helvetica", 11)
FONT_BTN   = ("Helvetica", 10, "bold")
FONT_SMALL = ("Helvetica", 9)
FONT_MONO  = ("Courier", 10)


# ── HELPERS ──────────────────────────────────────────────────────────────────
def conta_parole(testo): return len(testo.split()) if testo.strip() else 0
def tempo_lettura(testo):
    secs = int((conta_parole(testo) / 200) * 60)
    if secs < 60: return f"{secs}s di lettura"
    return f"{secs//60}m {secs%60}s di lettura"


# ── APP PRINCIPALE ────────────────────────────────────────────────────────────
class ToneShift(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ToneShift — Editor di Testo Intelligente")
        self.geometry("1100x780")
        self.minsize(900, 650)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._api_key_visible = False
        self._build_ui()
        self._incolla_automatico()


    # ── COSTRUZIONE UI ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Intestazione
        header = tk.Frame(self, bg=BG, pady=16)
        header.pack(fill="x", padx=30)
        tk.Label(header, text="ToneShift", font=FONT_TITLE, bg=BG, fg=ACCENT2).pack(side="left")
        tk.Label(header, text="  correggi · riscrivi · trasforma", font=("Helvetica", 11),
                 bg=BG, fg=MUTED).pack(side="left", pady=6)


        # ── Pannello API Key
        api_frame = tk.Frame(self, bg=PANEL, pady=10, padx=16)
        api_frame.pack(fill="x", padx=30, pady=(0, 12))


        tk.Label(api_frame, text="🔑  CHIAVE API", font=FONT_LABEL,
                 bg=PANEL, fg=MUTED).pack(side="left", padx=(0, 10))


        self._api_key_var = tk.StringVar(value=DEFAULT_API_KEY)
        self._api_entry = tk.Entry(
            api_frame, textvariable=self._api_key_var,
            font=FONT_MONO, bg=BG, fg=TEXT_FG,
            insertbackground=ACCENT2, relief="flat",
            show="•", width=52,
            selectbackground=ACCENT, selectforeground="#fff"
        )
        self._api_entry.pack(side="left", padx=(0, 8), ipady=5)


        self._toggle_btn = tk.Button(
            api_frame, text="👁  Mostra", font=FONT_BTN,
            bg=BG, fg=MUTED, relief="flat", padx=10, pady=4,
            cursor="hand2", bd=0, command=self._toggle_api_visibility
        )
        self._toggle_btn.pack(side="left", padx=(0, 6))


        tk.Button(
            api_frame, text="✓  Salva", font=FONT_BTN,
            bg=ACCENT, fg="#fff", relief="flat", padx=10, pady=4,
            cursor="hand2", bd=0, command=self._salva_api_key
        ).pack(side="left")


        self._api_status = tk.Label(api_frame, text="", font=FONT_SMALL, bg=PANEL, fg=SUCCESS)
        self._api_status.pack(side="left", padx=(10, 0))


        # ── Pulsanti tono
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=30, pady=(0, 14))
        tk.Label(btn_frame, text="MODALITÀ", font=FONT_LABEL, bg=BG, fg=MUTED).pack(side="left", padx=(0, 12))


        self.tono_selezionato = tk.StringVar(value=TONI[0])
        self._tono_buttons = {}
        for tono in TONI:
            btn = tk.Button(
                btn_frame, text=tono, font=FONT_BTN,
                bg=PANEL, fg=MUTED, relief="flat",
                padx=12, pady=6, cursor="hand2",
                bd=0, highlightthickness=1, highlightbackground=BORDER,
                command=lambda t=tono: self._seleziona_tono(t)
            )
            btn.pack(side="left", padx=4)
            self._tono_buttons[tono] = btn
        self._seleziona_tono(TONI[0])


        # ── Pannelli testo
        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(1, weight=1)
        panels.rowconfigure(1, weight=1)


        tk.Label(panels, text="TESTO ORIGINALE", font=FONT_LABEL, bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w", pady=(0,6))
        tk.Label(panels, text="TESTO ELABORATO", font=FONT_LABEL, bg=BG, fg=MUTED).grid(row=0, column=1, sticky="w", padx=(16,0), pady=(0,6))


        in_frame = tk.Frame(panels, bg=BORDER, bd=1)
        in_frame.grid(row=1, column=0, sticky="nsew")
        self.input_text = tk.Text(
            in_frame, font=FONT_BODY, bg=PANEL, fg=TEXT_FG,
            insertbackground=ACCENT2, relief="flat", wrap="word",
            padx=14, pady=12, selectbackground=ACCENT, selectforeground="#fff"
        )
        self.input_text.pack(fill="both", expand=True)
        self.input_text.bind("<KeyRelease>", self._aggiorna_stats_input)


        out_frame = tk.Frame(panels, bg=BORDER, bd=1)
        out_frame.grid(row=1, column=1, sticky="nsew", padx=(16, 0))
        self.output_text = tk.Text(
            out_frame, font=FONT_BODY, bg=PANEL, fg=TEXT_FG,
            insertbackground=ACCENT2, relief="flat", wrap="word",
            padx=14, pady=12, selectbackground=ACCENT, selectforeground="#fff",
            state="disabled"
        )
        self.output_text.pack(fill="both", expand=True)


        # ── Barra inferiore
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=30, pady=(0, 20))


        self.stats_input  = tk.Label(bottom, text="0 parole · 0s di lettura", font=FONT_SMALL, bg=BG, fg=MUTED)
        self.stats_input.pack(side="left")
        self.stats_output = tk.Label(bottom, text="", font=FONT_SMALL, bg=BG, fg=MUTED)
        self.stats_output.pack(side="left", padx=(20, 0))


        tk.Button(
            bottom, text="⎘  Copia", font=FONT_BTN,
            bg=PANEL, fg=MUTED, relief="flat", padx=14, pady=8,
            cursor="hand2", bd=0, command=self._copia_output
        ).pack(side="right", padx=(10, 0))


        tk.Button(
            bottom, text="✕  Cancella", font=FONT_BTN,
            bg=PANEL, fg=MUTED, relief="flat", padx=14, pady=8,
            cursor="hand2", bd=0, command=self._cancella
        ).pack(side="right", padx=(10, 0))


        self.run_btn = tk.Button(
            bottom, text="▶  Trasforma", font=FONT_BTN,
            bg=ACCENT, fg="#fff", relief="flat", padx=20, pady=8,
            cursor="hand2", bd=0, command=self._esegui
        )
        self.run_btn.pack(side="right")


        self.status = tk.Label(self, text="Pronto — incolla il testo o inizia a scrivere",
                               font=FONT_SMALL, bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x", padx=30, pady=(0, 10))


    # ── API KEY ───────────────────────────────────────────────────────────────
    def _toggle_api_visibility(self):
        self._api_key_visible = not self._api_key_visible
        self._api_entry.config(show="" if self._api_key_visible else "•")
        self._toggle_btn.config(text="🔒  Nascondi" if self._api_key_visible else "👁  Mostra")


    def _salva_api_key(self):
        key = self._api_key_var.get().strip()
        if not key:
            self._api_status.config(text="⚠ Chiave vuota!", fg=DANGER)
            return
        self._api_status.config(text="✓ Chiave salvata", fg=SUCCESS)
        self.after(2500, lambda: self._api_status.config(text=""))


    def _get_api_key(self):
        return self._api_key_var.get().strip()


    # ── SELEZIONE TONO ────────────────────────────────────────────────────────
    def _seleziona_tono(self, tono):
        self.tono_selezionato.set(tono)
        for t, btn in self._tono_buttons.items():
            if t == tono:
                btn.config(bg=ACCENT, fg="#fff", highlightbackground=ACCENT)
            else:
                btn.config(bg=PANEL, fg=MUTED, highlightbackground=BORDER)


    # ── INCOLLA AUTOMATICO ────────────────────────────────────────────────────
    def _incolla_automatico(self):
        try:
            clipboard = pyperclip.paste()
            if clipboard and clipboard.strip():
                self.input_text.insert("1.0", clipboard)
                self._aggiorna_stats_input()
                self._set_status("📋 Testo incollato automaticamente dagli appunti")
        except Exception:
            pass


    # ── STATISTICHE ───────────────────────────────────────────────────────────
    def _aggiorna_stats_input(self, *_):
        txt = self.input_text.get("1.0", "end-1c")
        self.stats_input.config(text=f"Originale: {conta_parole(txt)} parole · {tempo_lettura(txt)}")


    def _aggiorna_stats_output(self, txt):
        self.stats_output.config(text=f"Elaborato: {conta_parole(txt)} parole · {tempo_lettura(txt)}")


    # ── STATUS ────────────────────────────────────────────────────────────────
    def _set_status(self, msg, color=None):
        self.status.config(text=msg, fg=color or MUTED)


    # ── CANCELLA ──────────────────────────────────────────────────────────────
    def _cancella(self):
        self.input_text.delete("1.0", "end")
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")
        self.stats_input.config(text="0 parole · 0s di lettura")
        self.stats_output.config(text="")
        self._set_status("Campi cancellati")


    # ── COPIA OUTPUT ──────────────────────────────────────────────────────────
    def _copia_output(self):
        risultato = self.output_text.get("1.0", "end-1c")
        if risultato.strip():
            pyperclip.copy(risultato)
            self._set_status("✓ Testo copiato negli appunti!", SUCCESS)
        else:
            self._set_status("Nessun testo da copiare.", MUTED)


    # ── ESEGUI ────────────────────────────────────────────────────────────────
    def _esegui(self):
        testo = self.input_text.get("1.0", "end-1c").strip()
        if not testo:
            messagebox.showwarning("Nessun testo", "Inserisci o incolla del testo prima di procedere.")
            return
        chiave = self._get_api_key()
        if not chiave or chiave == "LA_TUA_API_KEY_QUI":
            messagebox.showwarning("Chiave API mancante", "Inserisci una chiave API valida nel pannello in alto.")
            return
        tono = self.tono_selezionato.get()
        self.run_btn.config(state="disabled", text="⏳  Elaborazione…")
        self._set_status(f"Invio a Gemini API — modalità: {tono}…")
        threading.Thread(target=self._chiama_api, args=(testo, tono, chiave), daemon=True).start()


    def _chiama_api(self, testo, tono, chiave):
        try:
            client = genai.Client(api_key=chiave)
            chat = client.chats.create(model="gemini-3-flash-preview")
            prompt = TONE_PROMPTS[tono] + f"\n\nTesto:\n{testo}"
            risposta = chat.send_message(prompt)
            risultato = risposta.text
            self.after(0, self._mostra_risultato, risultato)
        except Exception as e:
            self.after(0, self._mostra_errore, f"❌ Errore: {e}")


    def _mostra_risultato(self, risultato):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", risultato)
        self.output_text.config(state="disabled")
        self._aggiorna_stats_output(risultato)
        self.run_btn.config(state="normal", text="▶  Trasforma")
        self._set_status("✓ Elaborazione completata!", SUCCESS)


    def _mostra_errore(self, msg):
        self.run_btn.config(state="normal", text="▶  Trasforma")
        self._set_status(msg, DANGER)
        messagebox.showerror("Errore", msg)




# ── AVVIO ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ToneShift()
    app.mainloop()

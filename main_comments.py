# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         TONESHIFT — CODICE COMMENTATO                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── IMPORT ────────────────────────────────────────────────────────────────────
import tkinter as tk                # Libreria standard Python per creare GUI (finestre, bottoni, ecc.)
from tkinter import messagebox      # Modulo di tkinter per mostrare finestre di dialogo (errori, avvisi)
import pyperclip                    # Libreria esterna per leggere/scrivere negli appunti di sistema
from google import genai            # Libreria Google per usare le API di Gemini (il modello AI)
import threading                    # Modulo standard Python per eseguire codice in parallelo (thread)

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Chiave API di default: se vuota, l'utente dovrà inserirla manualmente nell'app
DEFAULT_API_KEY = ""

# Lista dei toni disponibili — vengono usati sia per i pulsanti che come chiavi del dizionario sotto
TONI = ["Correggi", "Formale", "Informale", "Amichevole", "Persuasivo", "Assertivo", "Semplifica"]

# Dizionario che associa ogni tono al suo prompt specifico per Gemini.
# Ogni prompt istruisce il modello su COME riscrivere il testo.
# Tutti chiedono di restituire SOLO il testo, senza spiegazioni extra.
TONE_PROMPTS = {
    "Correggi":   "Correggi tutti gli errori grammaticali, ortografici e di punteggiatura nel testo seguente. Preserva esattamente il significato e il tono originale. Restituisci solo il testo corretto, e magari migliora il testo rendendolo più fluido e naturale, ma senza cambiare il suo stile o registro.",
    "Formale":    "Riscrivi il testo seguente in un tono formale e professionale, adatto a un contesto lavorativo o accademico. Restituisci solo il testo riscritto, nient'altro.",
    "Informale":  "Riscrivi il testo seguente in un tono rilassato e colloquiale, come in una conversazione quotidiana. Restituisci solo il testo riscritto, nient'altro.",
    "Amichevole": "Riscrivi il testo seguente in un tono caldo, amichevole e accogliente. Restituisci solo il testo riscritto, nient'altro.",
    "Persuasivo": "Riscrivi il testo seguente in modo convincente e persuasivo, spingendo il lettore ad essere d'accordo o ad agire. Restituisci solo il testo riscritto, nient'altro.",
    "Assertivo":  "Riscrivi il testo seguente in un tono sicuro, diretto e assertivo. Restituisci solo il testo riscritto, nient'altro.",
    "Semplifica": "Riscrivi il testo seguente in modo che anche un bambino di 5 anni possa capirlo. Usa parole semplici e frasi brevi. Restituisci solo il testo riscritto, nient'altro.",
}

# ── COLORI & FONT ─────────────────────────────────────────────────────────────
# Palette colori usata in tutta l'app (tema scuro / dark mode)
BG      = "#0f0f13"   # Sfondo principale: quasi nero con leggera tinta viola
PANEL   = "#1a1a24"   # Sfondo dei pannelli interni: grigio scuro viola
ACCENT  = "#7c6af7"   # Viola primario — usato per bottoni attivi e selezioni
ACCENT2 = "#a78bfa"   # Viola più chiaro — usato per il titolo e il cursore testo
TEXT_FG = "#e8e6f0"   # Colore del testo principale: bianco/grigio chiaro
MUTED   = "#6b6880"   # Testo secondario/disabilitato: grigio viola
SUCCESS = "#4ade80"   # Verde — messaggi di successo
BORDER  = "#2a2a3a"   # Colore dei bordi sottili tra i pannelli
DANGER  = "#f87171"   # Rosso — messaggi di errore

# Definizioni dei font usati nei vari elementi dell'interfaccia
# Formato: (nome_font, dimensione, stile)
FONT_TITLE = ("Georgia",    22, "bold")   # Titolo grande dell'app
FONT_LABEL = ("Helvetica",  10, "bold")   # Etichette sezione (es. "MODALITÀ")
FONT_BODY  = ("Helvetica",  11)           # Testo nelle aree di input/output
FONT_BTN   = ("Helvetica",  10, "bold")   # Testo dei pulsanti
FONT_SMALL = ("Helvetica",   9)           # Testo piccolo (statistiche, status bar)
FONT_MONO  = ("Courier",    10)           # Font a larghezza fissa — usato per il campo API key

# ── FUNZIONI HELPER ───────────────────────────────────────────────────────────

def conta_parole(testo):
    """
    Conta le parole in una stringa.
    testo.split() divide il testo in lista di parole (separa per spazi/newline).
    Restituisce 0 se il testo è vuoto o contiene solo spazi bianchi.
    """
    return len(testo.split()) if testo.strip() else 0

def tempo_lettura(testo):
    """
    Stima il tempo di lettura del testo.
    Usa la velocità media di lettura di 200 parole al minuto.
    int(...) arrotonda verso il basso il risultato.
    Se il tempo è sotto il minuto, mostra solo i secondi.
    Altrimenti usa divisione intera (//) per i minuti e modulo (%) per i secondi rimanenti.
    """
    secs = int((conta_parole(testo) / 200) * 60)
    if secs < 60:
        return f"{secs}s di lettura"
    return f"{secs//60}m {secs%60}s di lettura"


# ── CLASSE PRINCIPALE ─────────────────────────────────────────────────────────

class ToneShift(tk.Tk):
    """
    Classe principale dell'applicazione.
    Eredita da tk.Tk, che rappresenta la finestra principale di tkinter.
    Tutto ciò che riguarda UI e logica è contenuto in questa classe.
    """

    def __init__(self):
        """
        Costruttore: viene chiamato automaticamente quando si crea un'istanza della classe.
        Configura la finestra e avvia la costruzione dell'interfaccia.
        """
        super().__init__()  # Chiama il costruttore della classe padre (tk.Tk) — obbligatorio

        # Impostazioni della finestra principale
        self.title("ToneShift — Editor di Testo Intelligente")  # Titolo nella barra in alto
        self.geometry("1100x780")   # Dimensione iniziale: larghezza x altezza in pixel
        self.minsize(900, 650)      # Dimensione minima: l'utente non può rimpicciolire oltre
        self.configure(bg=BG)       # Colore di sfondo della finestra
        self.resizable(True, True)  # Permette di ridimensionare sia in larghezza che in altezza

        # Variabile di stato: tiene traccia se la API key è visibile o mascherata
        self._api_key_visible = False

        # Costruisce tutti i widget dell'interfaccia
        self._build_ui()

        # Al lancio dell'app, incolla automaticamente il testo dagli appunti (se presente)
        self._incolla_automatico()

    # ── COSTRUZIONE UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        """
        Costruisce l'intera interfaccia grafica.
        I widget vengono creati dall'alto verso il basso con .pack() o .grid().
        """

        # ── INTESTAZIONE (header) ─────────────────────────────────────────────
        # Frame = contenitore invisibile che raggruppa widget — come un <div> in HTML
        header = tk.Frame(self, bg=BG, pady=16)
        header.pack(fill="x", padx=30)  # fill="x" → si estende per tutta la larghezza

        # Titolo "ToneShift" in viola chiaro
        tk.Label(header, text="ToneShift", font=FONT_TITLE, bg=BG, fg=ACCENT2).pack(side="left")

        # Sottotitolo descrittivo in grigio
        tk.Label(header, text="  correggi · riscrivi · trasforma",
                 font=("Helvetica", 11), bg=BG, fg=MUTED).pack(side="left", pady=6)

        # ── PANNELLO API KEY ──────────────────────────────────────────────────
        # Contenitore con sfondo PANEL per la riga della chiave API
        api_frame = tk.Frame(self, bg=PANEL, pady=10, padx=16)
        api_frame.pack(fill="x", padx=30, pady=(0, 12))  # pady=(0,12) → solo margine in basso

        # Etichetta fissa "🔑 CHIAVE API"
        tk.Label(api_frame, text="🔑  CHIAVE API", font=FONT_LABEL,
                 bg=PANEL, fg=MUTED).pack(side="left", padx=(0, 10))

        # Variabile tkinter collegata al campo di testo — aggiornata in tempo reale
        self._api_key_var = tk.StringVar(value=DEFAULT_API_KEY)

        # Campo di input per la chiave API
        # show="•" → maschera i caratteri come una password
        self._api_entry = tk.Entry(
            api_frame, textvariable=self._api_key_var,
            font=FONT_MONO, bg=BG, fg=TEXT_FG,
            insertbackground=ACCENT2,   # Colore del cursore lampeggiante
            relief="flat",              # Nessun bordo in rilievo (stile flat)
            show="•",                   # Maschera il testo (come campo password)
            width=52,                   # Larghezza in caratteri
            selectbackground=ACCENT, selectforeground="#fff"  # Colori selezione testo
        )
        self._api_entry.pack(side="left", padx=(0, 8), ipady=5)  # ipady → padding interno verticale

        # Bottone per mostrare/nascondere la chiave API
        self._toggle_btn = tk.Button(
            api_frame, text="👁  Mostra", font=FONT_BTN,
            bg=BG, fg=MUTED, relief="flat", padx=10, pady=4,
            cursor="hand2",         # Il cursore diventa una mano al passaggio
            bd=0,                   # Nessun bordo attorno al bottone
            command=self._toggle_api_visibility  # Funzione chiamata al click
        )
        self._toggle_btn.pack(side="left", padx=(0, 6))

        # Bottone "Salva" — conferma che la chiave è stata inserita
        tk.Button(
            api_frame, text="✓  Salva", font=FONT_BTN,
            bg=ACCENT, fg="#fff", relief="flat", padx=10, pady=4,
            cursor="hand2", bd=0, command=self._salva_api_key
        ).pack(side="left")

        # Etichetta di stato (vuota di default, mostra feedback dopo il salvataggio)
        self._api_status = tk.Label(api_frame, text="", font=FONT_SMALL, bg=PANEL, fg=SUCCESS)
        self._api_status.pack(side="left", padx=(10, 0))

        # ── PULSANTI MODALITÀ TONO ────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=30, pady=(0, 14))

        tk.Label(btn_frame, text="MODALITÀ", font=FONT_LABEL, bg=BG, fg=MUTED).pack(side="left", padx=(0, 12))

        # StringVar per tenere traccia del tono attualmente selezionato
        self.tono_selezionato = tk.StringVar(value=TONI[0])  # Default: primo tono ("Correggi")

        # Dizionario che mappa nome tono → oggetto bottone (per poterli aggiornare dopo)
        self._tono_buttons = {}

        # Crea dinamicamente un bottone per ogni tono nella lista TONI
        for tono in TONI:
            btn = tk.Button(
                btn_frame, text=tono, font=FONT_BTN,
                bg=PANEL, fg=MUTED, relief="flat",
                padx=12, pady=6, cursor="hand2",
                bd=0, highlightthickness=1, highlightbackground=BORDER,
                # lambda con argomento di default t=tono: necessario per "catturare"
                # il valore corrente di 'tono' nel loop, evitando il problema del late binding
                command=lambda t=tono: self._seleziona_tono(t)
            )
            btn.pack(side="left", padx=4)
            self._tono_buttons[tono] = btn  # Salva riferimento al bottone

        # Evidenzia il primo tono come selezionato di default
        self._seleziona_tono(TONI[0])

        # ── PANNELLI TESTO (input e output affiancati) ────────────────────────
        # Frame principale che contiene entrambi i pannelli testo
        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="both", expand=True, padx=30, pady=(0, 10))
        # expand=True → il frame si espande per riempire lo spazio disponibile

        # Configurazione griglia: 2 colonne di peso uguale (si espandono proporzionalmente)
        panels.columnconfigure(0, weight=1)  # Colonna 0: input
        panels.columnconfigure(1, weight=1)  # Colonna 1: output
        panels.rowconfigure(1, weight=1)     # Riga 1 (testo): si espande verticalmente

        # Etichette sopra i pannelli
        tk.Label(panels, text="TESTO ORIGINALE", font=FONT_LABEL,
                 bg=BG, fg=MUTED).grid(row=0, column=0, sticky="w", pady=(0, 6))
        tk.Label(panels, text="TESTO ELABORATO", font=FONT_LABEL,
                 bg=BG, fg=MUTED).grid(row=0, column=1, sticky="w", padx=(16, 0), pady=(0, 6))

        # Frame bordo per il pannello di input (simula un bordo colorato attorno al Text)
        in_frame = tk.Frame(panels, bg=BORDER, bd=1)
        in_frame.grid(row=1, column=0, sticky="nsew")  # sticky="nsew" → si espande in tutte le direzioni

        # Area di testo input — dove l'utente scrive o incolla il testo
        self.input_text = tk.Text(
            in_frame, font=FONT_BODY, bg=PANEL, fg=TEXT_FG,
            insertbackground=ACCENT2, relief="flat", wrap="word",  # wrap="word" → a capo per parole intere
            padx=14, pady=12,
            selectbackground=ACCENT, selectforeground="#fff"
        )
        self.input_text.pack(fill="both", expand=True)

        # Evento: ogni volta che l'utente rilascia un tasto, aggiorna le statistiche
        self.input_text.bind("<KeyRelease>", self._aggiorna_stats_input)

        # Frame bordo per il pannello di output
        out_frame = tk.Frame(panels, bg=BORDER, bd=1)
        out_frame.grid(row=1, column=1, sticky="nsew", padx=(16, 0))

        # Area di testo output — mostra il testo elaborato da Gemini
        # state="disabled" → l'utente non può modificarlo manualmente
        self.output_text = tk.Text(
            out_frame, font=FONT_BODY, bg=PANEL, fg=TEXT_FG,
            insertbackground=ACCENT2, relief="flat", wrap="word",
            padx=14, pady=12,
            selectbackground=ACCENT, selectforeground="#fff",
            state="disabled"  # Sola lettura — viene abilitato solo quando si scrive il risultato
        )
        self.output_text.pack(fill="both", expand=True)

        # ── BARRA INFERIORE (statistiche + bottoni azione) ────────────────────
        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=30, pady=(0, 20))

        # Statistiche testo input (parole + tempo di lettura)
        self.stats_input = tk.Label(bottom, text="0 parole · 0s di lettura",
                                    font=FONT_SMALL, bg=BG, fg=MUTED)
        self.stats_input.pack(side="left")

        # Statistiche testo output (aggiornate dopo elaborazione)
        self.stats_output = tk.Label(bottom, text="", font=FONT_SMALL, bg=BG, fg=MUTED)
        self.stats_output.pack(side="left", padx=(20, 0))

        # Bottone "Copia" — copia il testo elaborato negli appunti
        tk.Button(
            bottom, text="⎘  Copia", font=FONT_BTN,
            bg=PANEL, fg=MUTED, relief="flat", padx=14, pady=8,
            cursor="hand2", bd=0, command=self._copia_output
        ).pack(side="right", padx=(10, 0))

        # Bottone "Cancella" — svuota entrambi i campi testo
        tk.Button(
            bottom, text="✕  Cancella", font=FONT_BTN,
            bg=PANEL, fg=MUTED, relief="flat", padx=14, pady=8,
            cursor="hand2", bd=0, command=self._cancella
        ).pack(side="right", padx=(10, 0))

        # Bottone principale "Trasforma" — avvia l'elaborazione AI
        # Viene salvato in self.run_btn per poterlo disabilitare durante la chiamata API
        self.run_btn = tk.Button(
            bottom, text="▶  Trasforma", font=FONT_BTN,
            bg=ACCENT, fg="#fff", relief="flat", padx=20, pady=8,
            cursor="hand2", bd=0, command=self._esegui
        )
        self.run_btn.pack(side="right")

        # Barra di stato in fondo all'app — mostra messaggi contestuali
        self.status = tk.Label(self, text="Pronto — incolla il testo o inizia a scrivere",
                               font=FONT_SMALL, bg=BG, fg=MUTED, anchor="w")
        self.status.pack(fill="x", padx=30, pady=(0, 10))

    # ── GESTIONE API KEY ──────────────────────────────────────────────────────

    def _toggle_api_visibility(self):
        """
        Alterna la visibilità della chiave API nel campo di testo.
        Quando visibile: mostra i caratteri in chiaro.
        Quando nascosta: li maschera con il carattere "•".
        Aggiorna anche il testo del bottone toggle di conseguenza.
        """
        self._api_key_visible = not self._api_key_visible  # Inverte il booleano
        # Se visibile → show="" (nessuna maschera), altrimenti → show="•" (pallino)
        self._api_entry.config(show="" if self._api_key_visible else "•")
        self._toggle_btn.config(text="🔒  Nascondi" if self._api_key_visible else "👁  Mostra")

    def _salva_api_key(self):
        """
        Valida la chiave API inserita e mostra feedback visivo.
        Se la chiave è vuota mostra un avviso in rosso.
        Altrimenti mostra "✓ Chiave salvata" in verde per 2,5 secondi,
        poi rimuove il messaggio con self.after() (timer non-bloccante).
        """
        key = self._api_key_var.get().strip()  # Legge il valore ed elimina spazi iniziali/finali
        if not key:
            self._api_status.config(text="⚠ Chiave vuota!", fg=DANGER)
            return
        self._api_status.config(text="✓ Chiave salvata", fg=SUCCESS)
        # after(ms, funzione) → chiama la funzione dopo il numero di millisecondi specificato
        self.after(2500, lambda: self._api_status.config(text=""))

    def _get_api_key(self):
        """Restituisce la chiave API corrente, rimovendo spazi bianchi iniziali/finali."""
        return self._api_key_var.get().strip()

    # ── SELEZIONE TONO ────────────────────────────────────────────────────────

    def _seleziona_tono(self, tono):
        """
        Aggiorna l'interfaccia visiva per evidenziare il tono selezionato.
        Il bottone attivo diventa viola (ACCENT) con testo bianco.
        Tutti gli altri tornano al colore neutro (PANEL/MUTED).
        """
        self.tono_selezionato.set(tono)  # Aggiorna la StringVar con il tono scelto

        for t, btn in self._tono_buttons.items():
            if t == tono:
                # Bottone attivo: sfondo viola, testo bianco, bordo viola
                btn.config(bg=ACCENT, fg="#fff", highlightbackground=ACCENT)
            else:
                # Bottoni inattivi: sfondo scuro, testo grigio, bordo sottile
                btn.config(bg=PANEL, fg=MUTED, highlightbackground=BORDER)

    # ── INCOLLA AUTOMATICO ────────────────────────────────────────────────────

    def _incolla_automatico(self):
        """
        All'avvio, legge il contenuto degli appunti di sistema.
        Se c'è del testo, lo inserisce automaticamente nell'area di input.
        Il try/except gestisce il caso in cui gli appunti siano vuoti o
        non accessibili (es. su alcuni sistemi Linux senza clipboard manager).
        """
        try:
            clipboard = pyperclip.paste()       # Legge gli appunti
            if clipboard and clipboard.strip():  # Verifica che non sia vuoto
                self.input_text.insert("1.0", clipboard)  # "1.0" = riga 1, colonna 0 (inizio)
                self._aggiorna_stats_input()
                self._set_status("📋 Testo incollato automaticamente dagli appunti")
        except Exception:
            pass  # Ignora silenziosamente qualsiasi errore

    # ── STATISTICHE ───────────────────────────────────────────────────────────

    def _aggiorna_stats_input(self, *_):
        """
        Aggiorna le statistiche del testo originale (parole + tempo di lettura).
        Il parametro *_ raccoglie ed ignora l'evento tkinter passato da bind().
        get("1.0", "end-1c") legge tutto il testo dal widget:
          - "1.0" = inizio (riga 1, col 0)
          - "end-1c" = fine meno 1 carattere (esclude il newline finale aggiunto da tkinter)
        """
        txt = self.input_text.get("1.0", "end-1c")
        self.stats_input.config(text=f"Originale: {conta_parole(txt)} parole · {tempo_lettura(txt)}")

    def _aggiorna_stats_output(self, txt):
        """Aggiorna le statistiche del testo elaborato ricevuto dall'API."""
        self.stats_output.config(text=f"Elaborato: {conta_parole(txt)} parole · {tempo_lettura(txt)}")

    # ── STATUS BAR ────────────────────────────────────────────────────────────

    def _set_status(self, msg, color=None):
        """
        Aggiorna il messaggio nella barra di stato in fondo all'app.
        Se non viene specificato un colore, usa MUTED (grigio) di default.
        """
        self.status.config(text=msg, fg=color or MUTED)

    # ── CANCELLA ──────────────────────────────────────────────────────────────

    def _cancella(self):
        """
        Svuota entrambe le aree di testo e azzera le statistiche.
        Il widget output deve essere abilitato temporaneamente per poter
        cancellare il contenuto (state="normal"), poi ridisabilitato.
        """
        self.input_text.delete("1.0", "end")          # Cancella tutto l'input

        self.output_text.config(state="normal")        # Abilita temporaneamente l'output
        self.output_text.delete("1.0", "end")          # Cancella tutto l'output
        self.output_text.config(state="disabled")      # Ridisabilita l'output

        self.stats_input.config(text="0 parole · 0s di lettura")
        self.stats_output.config(text="")
        self._set_status("Campi cancellati")

    # ── COPIA OUTPUT ──────────────────────────────────────────────────────────

    def _copia_output(self):
        """
        Copia il contenuto del pannello output negli appunti di sistema.
        Usa pyperclip.copy() per la compatibilità cross-platform.
        Mostra un messaggio di feedback verde se c'è testo, grigio se è vuoto.
        """
        risultato = self.output_text.get("1.0", "end-1c")
        if risultato.strip():
            pyperclip.copy(risultato)
            self._set_status("✓ Testo copiato negli appunti!", SUCCESS)
        else:
            self._set_status("Nessun testo da copiare.", MUTED)

    # ── ESEGUI (avvio elaborazione) ───────────────────────────────────────────

    def _esegui(self):
        """
        Punto di ingresso per l'elaborazione AI. Esegue le validazioni necessarie,
        poi avvia la chiamata API in un thread separato per non bloccare l'interfaccia.
        
        Senza threading, tkinter si "congelerebbe" durante la chiamata API
        e l'app sembrerebbe non rispondere.
        """
        # Legge ed elimina spazi iniziali/finali dal testo inserito
        testo = self.input_text.get("1.0", "end-1c").strip()

        # Validazione 1: testo non vuoto
        if not testo:
            messagebox.showwarning("Nessun testo", "Inserisci o incolla del testo prima di procedere.")
            return

        # Validazione 2: chiave API presente e non placeholder
        chiave = self._get_api_key()
        if not chiave or chiave == "LA_TUA_API_KEY_QUI":
            messagebox.showwarning("Chiave API mancante", "Inserisci una chiave API valida nel pannello in alto.")
            return

        tono = self.tono_selezionato.get()  # Legge il tono attualmente selezionato

        # Disabilita il bottone "Trasforma" e cambia il testo per indicare il caricamento
        self.run_btn.config(state="disabled", text="⏳  Elaborazione…")
        self._set_status(f"Invio a Gemini API — modalità: {tono}…")

        # Crea e avvia un thread daemon in background per la chiamata API
        # daemon=True → il thread si chiude automaticamente se l'app principale viene chiusa
        threading.Thread(
            target=self._chiama_api,
            args=(testo, tono, chiave),
            daemon=True
        ).start()

    # ── CHIAMATA API (eseguita nel thread secondario) ─────────────────────────

    def _chiama_api(self, testo, tono, chiave):
        """
        Esegue la chiamata effettiva all'API di Google Gemini.
        Questo metodo gira in un thread separato (non nel thread principale di tkinter).
        
        IMPORTANTE: Non si può aggiornare la GUI direttamente da un thread secondario.
        Per questo si usa self.after(0, funzione) che pianifica l'esecuzione
        della funzione nel thread principale di tkinter.
        """
        try:
            # Crea il client Gemini con la chiave API fornita
            client = genai.Client(api_key=chiave)

            # Crea una sessione di chat con il modello specificato
            chat = client.chats.create(model="gemini-3-flash-preview")

            # Costruisce il prompt finale: istruzioni del tono + testo dell'utente
            prompt = TONE_PROMPTS[tono] + f"\n\nTesto:\n{testo}"

            # Invia il messaggio e attende la risposta (operazione bloccante — per questo è in un thread)
            risposta = chat.send_message(prompt)

            # Estrae il testo dalla risposta
            risultato = risposta.text

            # Pianifica l'aggiornamento della GUI nel thread principale
            self.after(0, self._mostra_risultato, risultato)

        except Exception as e:
            # In caso di errore, pianifica la visualizzazione dell'errore nel thread principale
            self.after(0, self._mostra_errore, f"❌ Errore: {e}")

    # ── MOSTRA RISULTATO (eseguito nel thread principale) ─────────────────────

    def _mostra_risultato(self, risultato):
        """
        Aggiorna il pannello output con il testo restituito da Gemini.
        Questo metodo viene sempre eseguito nel thread principale (tramite self.after).
        Sequenza: abilita output → cancella vecchio contenuto → inserisce nuovo → disabilita.
        Poi aggiorna statistiche, riabilita il bottone e mostra messaggio di successo.
        """
        self.output_text.config(state="normal")      # Abilita la modifica del widget
        self.output_text.delete("1.0", "end")         # Rimuove eventuale testo precedente
        self.output_text.insert("1.0", risultato)     # Inserisce il nuovo testo
        self.output_text.config(state="disabled")     # Torna in sola lettura

        self._aggiorna_stats_output(risultato)
        self.run_btn.config(state="normal", text="▶  Trasforma")  # Riabilita il bottone
        self._set_status("✓ Elaborazione completata!", SUCCESS)

    # ── MOSTRA ERRORE (eseguito nel thread principale) ────────────────────────

    def _mostra_errore(self, msg):
        """
        Gestisce gli errori provenienti dalla chiamata API.
        Riabilita il bottone, aggiorna la status bar in rosso e mostra una finestra di errore.
        """
        self.run_btn.config(state="normal", text="▶  Trasforma")
        self._set_status(msg, DANGER)
        messagebox.showerror("Errore", msg)  # Finestra di dialogo modale con il messaggio di errore


# ── PUNTO DI INGRESSO ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Questo blocco viene eseguito SOLO se il file viene lanciato direttamente
    (non se viene importato come modulo in un altro script).
    Crea l'istanza dell'app e avvia il loop principale degli eventi di tkinter.
    mainloop() tiene in esecuzione l'app e gestisce tutti gli eventi
    (click, tastiera, ridimensionamento, ecc.) fino alla chiusura della finestra.
    """
    app = ToneShift()
    app.mainloop()

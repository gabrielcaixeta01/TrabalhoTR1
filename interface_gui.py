# -*- coding: utf-8 -*-
"""
INTERFACE GRÁFICA
=================
Usa GTK 3 (requisito do trabalho) quando disponível; cai para tkinter
automaticamente em ambientes sem GTK instalado (ex.: Windows sem sudo).

Dependências para GTK (Linux):
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
  pip install matplotlib
"""

# ── Detecta qual backend de GUI está disponível ──────────────────────────────
try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    from matplotlib.backends.backend_gtk3agg import (
        FigureCanvasGTK3Agg as FigureCanvas)
    _BACKEND = "gtk"
except Exception:
    import tkinter as tk
    from tkinter import ttk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    _BACKEND = "tk"

from matplotlib.figure import Figure
import simulador


# ── Opções dos campos de seleção ─────────────────────────────────────────────
OPCOES_ENQUADRAMENTO = [("Contagem de caracteres", "contagem"),
                        ("FLAGs + inserção de bytes", "bytes"),
                        ("FLAGs + inserção de bits", "bits")]
OPCOES_DETECCAO = [("Nenhuma", "nenhum"),
                   ("Bit de paridade par", "paridade"),
                   ("Checksum", "checksum"),
                   ("CRC-32 (IEEE 802)", "crc")]
OPCOES_CORRECAO = [("Nenhuma", "nenhum"), ("Hamming", "hamming")]
OPCOES_MOD_DIGITAL = [("NRZ-Polar", "nrz"),
                      ("Manchester", "manchester"),
                      ("Bipolar (AMI)", "bipolar")]
OPCOES_MOD_PORTADORA = [("Nenhuma (banda-base)", "nenhuma"),
                        ("ASK", "ask"), ("FSK", "fsk"),
                        ("QPSK", "qpsk"), ("16-QAM", "16qam")]

MAX_AMOSTRAS_GRAFICO = 4000
MAX_BITS_TEXTO = 2048


def _bits_str(bits):
    if bits is None:
        return "-"
    s = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        s += f"... ({len(bits)} bits no total)"
    return s


# ═════════════════════════════════════════════════════════════════════════════
# IMPLEMENTAÇÃO GTK 3  (usada no Linux — requisito do trabalho)
# ═════════════════════════════════════════════════════════════════════════════
if _BACKEND == "gtk":

    class JanelaSimulador(Gtk.Window):
        """Janela principal do simulador (GTK 3)."""

        def __init__(self):
            super().__init__(title="Simulador TR1 - Camadas Física e de Enlace")
            self.set_default_size(1200, 750)
            self.connect("destroy", Gtk.main_quit)

            raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            raiz.set_border_width(8)
            self.add(raiz)

            raiz.pack_start(self._montar_painel_config(), False, False, 0)
            raiz.pack_start(self._montar_painel_resultados(), True, True, 0)

        # ── Construção ────────────────────────────────────────────────────

        def _montar_painel_config(self):
            grade = Gtk.Grid(column_spacing=6, row_spacing=6)
            linha = 0

            def rotulo(texto):
                lbl = Gtk.Label(label=texto, xalign=0)
                return lbl

            def adicionar(widget_rotulo, widget):
                nonlocal linha
                grade.attach(rotulo(widget_rotulo), 0, linha, 1, 1)
                grade.attach(widget, 1, linha, 1, 1)
                linha += 1

            self.entrada_texto = Gtk.Entry(text="Ola, TR1!")
            adicionar("Texto de entrada:", self.entrada_texto)

            self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
            self.spin_quadro.set_value(8)
            adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

            self.combo_enq = self._novo_combo(OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento:", self.combo_enq)

            self.combo_det = self._novo_combo(OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros:", self.combo_det)

            self.combo_cor = self._novo_combo(OPCOES_CORRECAO, 1)
            adicionar("Correção de erros:", self.combo_cor)

            self.combo_dig = self._novo_combo(OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital:", self.combo_dig)

            self.combo_port = self._novo_combo(OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora:", self.combo_port)

            self.spin_media = Gtk.SpinButton.new_with_range(-2.0, 2.0, 0.01)
            self.spin_media.set_digits(2)
            self.spin_media.set_value(0.0)
            adicionar("Ruído - média x (V):", self.spin_media)

            self.spin_sigma = Gtk.SpinButton.new_with_range(0.0, 2.0, 0.01)
            self.spin_sigma.set_digits(2)
            self.spin_sigma.set_value(0.10)
            adicionar("Ruído - desvio σ (V):", self.spin_sigma)

            botao = Gtk.Button(label="Transmitir")
            botao.connect("clicked", self._ao_transmitir)
            grade.attach(botao, 0, linha, 2, 1)
            linha += 1

            self.lbl_status = Gtk.Label(label="", xalign=0)
            self.lbl_status.set_line_wrap(True)
            self.lbl_status.set_max_width_chars(34)
            grade.attach(self.lbl_status, 0, linha, 2, 1)
            return grade

        def _novo_combo(self, opcoes, indice_padrao):
            combo = Gtk.ComboBoxText()
            for rotulo, _ in opcoes:
                combo.append_text(rotulo)
            combo.set_active(indice_padrao)
            combo._opcoes = opcoes
            return combo

        @staticmethod
        def _valor_combo(combo):
            return combo._opcoes[combo.get_active()][1]

        def _montar_painel_resultados(self):
            notebook = Gtk.Notebook()

            self.txt_tx = self._nova_caixa_texto()
            self.fig_tx = Figure(figsize=(7, 4))
            self.canvas_tx = FigureCanvas(self.fig_tx)
            notebook.append_page(
                self._aba(self.txt_tx, self.canvas_tx),
                Gtk.Label(label="Transmissor (Tx)"))

            self.txt_rx = self._nova_caixa_texto()
            self.fig_rx = Figure(figsize=(7, 4))
            self.canvas_rx = FigureCanvas(self.fig_rx)
            notebook.append_page(
                self._aba(self.txt_rx, self.canvas_rx),
                Gtk.Label(label="Receptor (Rx)"))
            return notebook

        @staticmethod
        def _nova_caixa_texto():
            tv = Gtk.TextView(editable=False, monospace=True)
            tv.set_wrap_mode(Gtk.WrapMode.CHAR)
            return tv

        @staticmethod
        def _aba(textview, canvas):
            caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            rolagem = Gtk.ScrolledWindow()
            rolagem.set_min_content_height(260)
            rolagem.add(textview)
            caixa.pack_start(rolagem, True, True, 0)
            caixa.pack_start(canvas, True, True, 0)
            return caixa

        # ── Lógica ────────────────────────────────────────────────────────

        def _ler_config(self):
            return {
                "texto": self.entrada_texto.get_text(),
                "tam_max_quadro": int(self.spin_quadro.get_value()),
                "enquadramento": self._valor_combo(self.combo_enq),
                "deteccao": self._valor_combo(self.combo_det),
                "correcao": self._valor_combo(self.combo_cor),
                "mod_digital": self._valor_combo(self.combo_dig),
                "mod_portadora": self._valor_combo(self.combo_port),
                "ruido_media": self.spin_media.get_value(),
                "ruido_sigma": self.spin_sigma.get_value(),
            }

        def _ao_transmitir(self, _botao):
            config = self._ler_config()
            if not config["texto"]:
                self.lbl_status.set_text("Digite um texto para transmitir.")
                return
            try:
                r = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.set_text(f"Erro: {erro}")
                return

            texto_tx = (
                f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(r['tx_bits_aplicacao'])} bits):\n"
                f"{_bits_str(r['tx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE BITS - ENLACE/quadros ({len(r['tx_bits_enlace'])} bits):\n"
                f"{_bits_str(r['tx_bits_enlace'])}\n"
            )
            self.txt_tx.get_buffer().set_text(texto_tx)
            self._plotar(self.fig_tx, self.canvas_tx,
                         ("Sinal banda-base (Tx)", r["tx_sinal_banda_base"]),
                         ("Sinal transmitido ao meio (Tx)", r["tx_sinal_transmitido"]))

            linhas_quadros = "\n".join(
                f"  Quadro {q['quadro']}: "
                f"EDC {'OK' if q['edc_ok'] else 'ERRO DETECTADO'}"
                + (f", {q['corrigidos']} bit(s) corrigido(s) por Hamming"
                   if config["correcao"] == "hamming" else "")
                + (", ERRO DUPLO detectado" if q["erro_duplo"] else "")
                for q in r["rx_relatorio_quadros"]) or "  (nenhum quadro recuperado)"
            texto_rx = (
                f"SAÍDA DE BITS - FÍSICA/demodulados "
                f"({len(r['rx_bits_fisica'])} bits):\n"
                f"{_bits_str(r['rx_bits_fisica'])}\n\n"
                f"RELATÓRIO DOS QUADROS (enlace):\n{linhas_quadros}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(r['rx_bits_aplicacao'])} bits):\n"
                f"{_bits_str(r['rx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE TEXTO:\n{r['rx_texto']}\n"
            )
            self.txt_rx.get_buffer().set_text(texto_rx)
            self._plotar(self.fig_rx, self.canvas_rx,
                         ("Sinal recebido com ruído (Rx)", r["rx_sinal_recebido"]),
                         ("Banda-base reconstruído (Rx)", r["rx_sinal_banda_base"]))

            ok = (r["rx_texto"] == config["texto"])
            ps, pr = r["potencia_sinal_w"], r["potencia_ruido_w"]
            self.lbl_status.set_text(
                f"Potência do sinal: {ps:.3f} W | do ruído: {pr:.4f} W\n"
                f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}.")

        @staticmethod
        def _plotar(figura, canvas, *series):
            figura.clear()
            n = len(series)
            for k, (titulo, sinal) in enumerate(series, start=1):
                eixo = figura.add_subplot(n, 1, k)
                eixo.plot(sinal[:MAX_AMOSTRAS_GRAFICO], linewidth=0.8)
                eixo.set_title(titulo, fontsize=9)
                eixo.set_ylabel("V", fontsize=8)
                eixo.tick_params(labelsize=7)
            figura.tight_layout()
            canvas.draw()

        def executar(self):
            self.show_all()
            Gtk.main()


# ═════════════════════════════════════════════════════════════════════════════
# IMPLEMENTAÇÃO TKINTER  (fallback automático quando GTK não está disponível)
# ═════════════════════════════════════════════════════════════════════════════
else:

    class JanelaSimulador(tk.Tk):
        """Janela principal do simulador (tkinter — fallback sem GTK)."""

        def __init__(self):
            super().__init__()
            self.title("Simulador TR1 - Camadas Física e de Enlace")
            self.geometry("1200x750")
            self.protocol("WM_DELETE_WINDOW", self.destroy)

            raiz = ttk.Frame(self, padding=8)
            raiz.pack(fill=tk.BOTH, expand=True)

            self._montar_painel_config(raiz)
            self._montar_painel_resultados(raiz)

        # ── Construção ────────────────────────────────────────────────────

        def _montar_painel_config(self, parent):
            frame = ttk.LabelFrame(parent, text="Configuração", padding=6)
            frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

            linha = 0

            def adicionar(rotulo_texto, widget):
                nonlocal linha
                ttk.Label(frame, text=rotulo_texto, anchor="w").grid(
                    row=linha, column=0, sticky="w", padx=2, pady=3)
                widget.grid(row=linha, column=1, sticky="we", padx=2, pady=3)
                linha += 1

            self.entrada_texto = ttk.Entry(frame, width=24)
            self.entrada_texto.insert(0, "Ola, TR1!")
            adicionar("Texto de entrada:", self.entrada_texto)

            self.spin_quadro = ttk.Spinbox(frame, from_=1, to=100, width=7)
            self.spin_quadro.set(8)
            adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

            self.combo_enq = self._novo_combo(frame, OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento:", self.combo_enq)

            self.combo_det = self._novo_combo(frame, OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros:", self.combo_det)

            self.combo_cor = self._novo_combo(frame, OPCOES_CORRECAO, 1)
            adicionar("Correção de erros:", self.combo_cor)

            self.combo_dig = self._novo_combo(frame, OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital:", self.combo_dig)

            self.combo_port = self._novo_combo(frame, OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora:", self.combo_port)

            self.spin_media = ttk.Spinbox(
                frame, from_=-2.0, to=2.0, increment=0.01, width=7, format="%.2f")
            self.spin_media.set("0.00")
            adicionar("Ruído - média x (V):", self.spin_media)

            self.spin_sigma = ttk.Spinbox(
                frame, from_=0.0, to=2.0, increment=0.01, width=7, format="%.2f")
            self.spin_sigma.set("0.10")
            adicionar("Ruído - desvio σ (V):", self.spin_sigma)

            ttk.Button(frame, text="Transmitir", command=self._ao_transmitir).grid(
                row=linha, column=0, columnspan=2, pady=10)
            linha += 1

            self.lbl_status = ttk.Label(
                frame, text="", wraplength=220, justify="left", anchor="nw")
            self.lbl_status.grid(row=linha, column=0, columnspan=2, sticky="w")

        def _novo_combo(self, parent, opcoes, indice_padrao):
            valores = [r for r, _ in opcoes]
            combo = ttk.Combobox(parent, values=valores, state="readonly", width=22)
            combo.set(valores[indice_padrao])
            combo._opcoes = opcoes
            return combo

        @staticmethod
        def _valor_combo(combo):
            return combo._opcoes[combo.current()][1]

        def _montar_painel_resultados(self, parent):
            notebook = ttk.Notebook(parent)
            notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tab_tx = ttk.Frame(notebook)
            self.txt_tx, self.fig_tx, self.canvas_tx = self._criar_aba(tab_tx)
            notebook.add(tab_tx, text="Transmissor (Tx)")

            tab_rx = ttk.Frame(notebook)
            self.txt_rx, self.fig_rx, self.canvas_rx = self._criar_aba(tab_rx)
            notebook.add(tab_rx, text="Receptor (Rx)")

        def _criar_aba(self, parent):
            txt_frame = ttk.Frame(parent)
            txt_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(txt_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            txt = tk.Text(txt_frame, wrap=tk.CHAR, font=("Courier", 9),
                          yscrollcommand=scrollbar.set, height=13,
                          state=tk.DISABLED)
            txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=txt.yview)

            fig = Figure(figsize=(7, 4))
            canvas = FigureCanvas(fig, master=parent)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            return txt, fig, canvas

        # ── Lógica ────────────────────────────────────────────────────────

        def _ler_config(self):
            return {
                "texto": self.entrada_texto.get(),
                "tam_max_quadro": int(self.spin_quadro.get()),
                "enquadramento": self._valor_combo(self.combo_enq),
                "deteccao": self._valor_combo(self.combo_det),
                "correcao": self._valor_combo(self.combo_cor),
                "mod_digital": self._valor_combo(self.combo_dig),
                "mod_portadora": self._valor_combo(self.combo_port),
                "ruido_media": float(self.spin_media.get()),
                "ruido_sigma": float(self.spin_sigma.get()),
            }

        def _ao_transmitir(self):
            config = self._ler_config()
            if not config["texto"]:
                self.lbl_status.config(text="Digite um texto para transmitir.")
                return
            try:
                r = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.config(text=f"Erro: {erro}")
                return

            texto_tx = (
                f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(r['tx_bits_aplicacao'])} bits):\n"
                f"{_bits_str(r['tx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE BITS - ENLACE/quadros ({len(r['tx_bits_enlace'])} bits):\n"
                f"{_bits_str(r['tx_bits_enlace'])}\n"
            )
            self._set_texto(self.txt_tx, texto_tx)
            self._plotar(self.fig_tx, self.canvas_tx,
                         ("Sinal banda-base (Tx)", r["tx_sinal_banda_base"]),
                         ("Sinal transmitido ao meio (Tx)", r["tx_sinal_transmitido"]))

            linhas_quadros = "\n".join(
                f"  Quadro {q['quadro']}: "
                f"EDC {'OK' if q['edc_ok'] else 'ERRO DETECTADO'}"
                + (f", {q['corrigidos']} bit(s) corrigido(s) por Hamming"
                   if config["correcao"] == "hamming" else "")
                + (", ERRO DUPLO detectado" if q["erro_duplo"] else "")
                for q in r["rx_relatorio_quadros"]) or "  (nenhum quadro recuperado)"
            texto_rx = (
                f"SAÍDA DE BITS - FÍSICA/demodulados "
                f"({len(r['rx_bits_fisica'])} bits):\n"
                f"{_bits_str(r['rx_bits_fisica'])}\n\n"
                f"RELATÓRIO DOS QUADROS (enlace):\n{linhas_quadros}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(r['rx_bits_aplicacao'])} bits):\n"
                f"{_bits_str(r['rx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE TEXTO:\n{r['rx_texto']}\n"
            )
            self._set_texto(self.txt_rx, texto_rx)
            self._plotar(self.fig_rx, self.canvas_rx,
                         ("Sinal recebido com ruído (Rx)", r["rx_sinal_recebido"]),
                         ("Banda-base reconstruído (Rx)", r["rx_sinal_banda_base"]))

            ok = (r["rx_texto"] == config["texto"])
            ps, pr = r["potencia_sinal_w"], r["potencia_ruido_w"]
            self.lbl_status.config(
                text=(f"Potência do sinal: {ps:.3f} W | do ruído: {pr:.4f} W\n"
                      f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}."))

        @staticmethod
        def _set_texto(widget, conteudo):
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.insert(tk.END, conteudo)
            widget.config(state=tk.DISABLED)

        @staticmethod
        def _plotar(figura, canvas, *series):
            figura.clear()
            n = len(series)
            for k, (titulo, sinal) in enumerate(series, start=1):
                eixo = figura.add_subplot(n, 1, k)
                eixo.plot(sinal[:MAX_AMOSTRAS_GRAFICO], linewidth=0.8)
                eixo.set_title(titulo, fontsize=9)
                eixo.set_ylabel("V", fontsize=8)
                eixo.tick_params(labelsize=7)
            figura.tight_layout()
            canvas.draw()

        def executar(self):
            self.mainloop()

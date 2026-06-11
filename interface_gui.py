# -*- coding: utf-8 -*-
"""
INTERFACE GRÁFICA (GTK 3)
=========================
Janela única dividida em:

  * Painel esquerdo - CONFIGURAÇÃO GERAL (os mesmos campos do diagrama
    do enunciado): texto de entrada, tamanho máximo de quadro, tipo de
    enquadramento, tipo de detecção/correção, modulação digital,
    modulação por portadora e parâmetros do ruído (x e sigma).

  * Painel direito - abas TRANSMISSOR e RECEPTOR mostrando a "saída de
    texto" e as "saídas de bits" de cada camada, além dos gráficos dos
    sinais (banda-base e modulado/recebido) desenhados com matplotlib
    embutido no GTK.

Dependências (Linux):
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
  pip install matplotlib
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)

import simulador


# Rótulos exibidos na GUI -> valores internos usados pelo config.
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

MAX_AMOSTRAS_GRAFICO = 4000     # limita o gráfico p/ não travar com textos longos
MAX_BITS_TEXTO = 2048           # idem para as caixas de bits


def _bits_str(bits):
    """Formata uma lista de bits como string, truncando se for longa."""
    if bits is None:
        return "-"
    s = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        s += f"... ({len(bits)} bits no total)"
    return s


class JanelaSimulador(Gtk.Window):
    """Janela principal do simulador."""

    def __init__(self):
        super().__init__(title="Simulador TR1 - Camadas Física e de Enlace")
        self.set_default_size(1200, 750)
        self.connect("destroy", Gtk.main_quit)

        raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        raiz.set_border_width(8)
        self.add(raiz)

        raiz.pack_start(self._montar_painel_config(), False, False, 0)
        raiz.pack_start(self._montar_painel_resultados(), True, True, 0)

    # ------------------------------------------------------------------ #
    # Construção da interface                                            #
    # ------------------------------------------------------------------ #
    def _montar_painel_config(self):
        """Cria o formulário de configuração geral (lado esquerdo)."""
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

        # Texto a transmitir (entrada da aplicação de rede).
        self.entrada_texto = Gtk.Entry(text="Ola, TR1!")
        adicionar("Texto de entrada:", self.entrada_texto)

        # Tamanho máximo de quadro (bytes de dados por quadro).
        self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.spin_quadro.set_value(8)
        adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

        # Combos de seleção de protocolo (um para cada bloco do diagrama).
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

        # Parâmetros do ruído gaussiano n(x, sigma) do meio.
        self.spin_media = Gtk.SpinButton.new_with_range(-2.0, 2.0, 0.01)
        self.spin_media.set_digits(2)
        self.spin_media.set_value(0.0)
        adicionar("Ruído - média x (V):", self.spin_media)

        self.spin_sigma = Gtk.SpinButton.new_with_range(0.0, 2.0, 0.01)
        self.spin_sigma.set_digits(2)
        self.spin_sigma.set_value(0.10)
        adicionar("Ruído - desvio σ (V):", self.spin_sigma)

        # Botão que dispara a simulação completa.
        botao = Gtk.Button(label="Transmitir")
        botao.connect("clicked", self._ao_transmitir)
        grade.attach(botao, 0, linha, 2, 1)
        linha += 1

        # Rótulo de status (SNR, erros detectados etc.).
        self.lbl_status = Gtk.Label(label="", xalign=0)
        self.lbl_status.set_line_wrap(True)
        self.lbl_status.set_max_width_chars(34)
        grade.attach(self.lbl_status, 0, linha, 2, 1)
        return grade

    def _novo_combo(self, opcoes, indice_padrao):
        """Cria um Gtk.ComboBoxText a partir de [(rótulo, valor), ...]."""
        combo = Gtk.ComboBoxText()
        for rotulo, _ in opcoes:
            combo.append_text(rotulo)
        combo.set_active(indice_padrao)
        combo._opcoes = opcoes                   # guarda o mapeamento
        return combo

    @staticmethod
    def _valor_combo(combo):
        """Devolve o valor interno associado ao rótulo selecionado."""
        return combo._opcoes[combo.get_active()][1]

    def _montar_painel_resultados(self):
        """Cria o notebook com as abas Transmissor e Receptor."""
        notebook = Gtk.Notebook()

        # ------- Aba TX: bits de cada camada + gráficos dos sinais --------
        self.txt_tx = self._nova_caixa_texto()
        self.fig_tx = Figure(figsize=(7, 4))
        self.canvas_tx = FigureCanvas(self.fig_tx)
        notebook.append_page(
            self._aba(self.txt_tx, self.canvas_tx),
            Gtk.Label(label="Transmissor (Tx)"))

        # ------- Aba RX: sinal recebido + bits/quadros decodificados ------
        self.txt_rx = self._nova_caixa_texto()
        self.fig_rx = Figure(figsize=(7, 4))
        self.canvas_rx = FigureCanvas(self.fig_rx)
        notebook.append_page(
            self._aba(self.txt_rx, self.canvas_rx),
            Gtk.Label(label="Receptor (Rx)"))
        return notebook

    @staticmethod
    def _nova_caixa_texto():
        """TextView somente-leitura com fonte monoespaçada para os bits."""
        tv = Gtk.TextView(editable=False, monospace=True)
        tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        return tv

    @staticmethod
    def _aba(textview, canvas):
        """Empilha a caixa de texto (rolável) sobre o gráfico em uma aba."""
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rolagem = Gtk.ScrolledWindow()
        rolagem.set_min_content_height(260)
        rolagem.add(textview)
        caixa.pack_start(rolagem, True, True, 0)
        caixa.pack_start(canvas, True, True, 0)
        return caixa

    # ------------------------------------------------------------------ #
    # Lógica: coleta a configuração, roda a simulação e exibe os dados   #
    # ------------------------------------------------------------------ #
    def _ler_config(self):
        """Monta o dicionário de configuração a partir dos widgets."""
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
        """Callback do botão: executa a simulação e atualiza as duas abas."""
        config = self._ler_config()
        if not config["texto"]:
            self.lbl_status.set_text("Digite um texto para transmitir.")
            return
        try:
            r = simulador.executar_simulacao(config)
        except ValueError as erro:                # ex.: quadro > 255 bytes
            self.lbl_status.set_text(f"Erro: {erro}")
            return

        # ---------------- Aba do transmissor ----------------
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
                     ("Sinal transmitido ao meio (Tx)",
                      r["tx_sinal_transmitido"]))

        # ---------------- Aba do receptor ----------------
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

        # ---------------- Status / métricas ----------------
        ok = (r["rx_texto"] == config["texto"])
        ps, pr = r["potencia_sinal_w"], r["potencia_ruido_w"]
        self.lbl_status.set_text(
            f"Potência do sinal: {ps:.3f} W | do ruído: {pr:.4f} W\n"
            f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}.")

    @staticmethod
    def _plotar(figura, canvas, *series):
        """Desenha até duas séries (título, amostras) na figura da aba."""
        figura.clear()
        n = len(series)
        for k, (titulo, sinal) in enumerate(series, start=1):
            eixo = figura.add_subplot(n, 1, k)
            recorte = sinal[:MAX_AMOSTRAS_GRAFICO]   # evita gráficos gigantes
            eixo.plot(recorte, linewidth=0.8)
            eixo.set_title(titulo, fontsize=9)
            eixo.set_ylabel("V", fontsize=8)
            eixo.tick_params(labelsize=7)
        figura.tight_layout()
        canvas.draw()

    def executar(self):
        """Exibe a janela e entra no loop de eventos do GTK."""
        self.show_all()
        Gtk.main()
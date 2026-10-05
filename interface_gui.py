# -*- coding: utf-8 -*-
"""
INTERFACE GRÁFICA (GTK 3)
=========================
Enunciado: "NÃO É UMA TELA DE TERMINAL - utilize bibliotecas Linux para GUI.
Preferência: GTK". Usamos Python + GTK 3 (PyGObject) e matplotlib para os
gráficos dos sinais.

ESTE ARQUIVO JÁ VEM PRONTO (decisão do grupo: a GUI não é o foco do trabalho).
Está comentado para que todos entendam o que cada parte faz.

O QUE A GUI MOSTRA (Figura 1 do enunciado, bloco "Interface gráfica"):

  CONFIGURAÇÃO GERAL (entradas)
    - Texto a transmitir (a "entrada de texto" do chat)
    - Tamanho máximo de quadro (bytes)
    - Tipo de enquadramento, de detecção e de correção de erros
    - Tipo de modulação digital (banda-base) e por portadora
    - Ruído: média x e desvio padrão sigma (em Volts)

  SAÍDAS, separadas em Tx e Rx
    - Tx: texto de entrada, bits da aplicação, bits do enlace e os sinais
      da camada física (banda-base e o sinal transmitido).
    - Rx: bits demodulados, relatório por quadro (EDC ok? bits corrigidos?
      erro duplo?), bits da aplicação e o TEXTO final, além do sinal
      recebido (com ruído).
    - Potência do sinal e do ruído (W).

ARQUITETURA: a GUI NÃO implementa nenhum protocolo. Ela só (1) lê os campos,
(2) monta o dict `config`, (3) chama simulador.executar_simulacao(config) e
(4) exibe o dict de resultados. Assim os protocolos são testáveis sem GTK
(python3 testes.py).

INSTALAÇÃO (Linux):
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
  pip install matplotlib
Documentação GTK: https://python-gtk-3-tutorial.readthedocs.io/en/latest/
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

import simulador


# ── Opções dos campos de seleção: (texto mostrado, valor usado em `config`) ──
OPCOES_ENQUADRAMENTO = [("Contagem de caracteres", "contagem"),
                        ("Entrelaçamento de bits", "entrelacamento"),
                        ("FLAGs + inserção de bytes", "bytes"),
                        ("FLAGs + inserção de bits", "bits")]
OPCOES_DETECCAO = [("Nenhuma", "nenhum"),
                   ("Bit de paridade par", "paridade"),
                   ("Checksum", "checksum"),
                   ("CRC-32 (IEEE 802)", "crc")]
OPCOES_CORRECAO = [("Nenhuma", "nenhum"), ("Hamming", "hamming")]
OPCOES_MOD_DIGITAL = [("NRZ-Polar", "nrz"),
                      ("Manchester", "manchester"),
                      ("Bipolar", "bipolar")]
OPCOES_MOD_PORTADORA = [("Nenhuma (banda-base)", "nenhuma"),
                        ("ASK", "ask"), ("FSK", "fsk"),
                        ("8PSK", "8psk"), ("32-QAM", "32qam")]

MAX_AMOSTRAS_GRAFICO = 4000   # plotar milhões de pontos travaria a GUI
MAX_BITS_TEXTO = 2048         # idem para as caixas de texto


def bits_str(bits):
    """Formata uma lista de bits como string '0101...' para exibir na GUI
    (corta em MAX_BITS_TEXTO bits e avisa o total)."""
    if bits is None:
        return "-"
    texto = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        texto += f"... ({len(bits)} bits no total)"
    return texto


class JanelaSimulador(Gtk.Window):
    """Janela principal: painel de configuração à esquerda e, à direita, um
    Gtk.Notebook com as abas Transmissor (Tx) e Receptor (Rx)."""

    def __init__(self):
        super().__init__(title="Simulador TR1 - Camadas Física e de Enlace")
        self.set_default_size(1200, 750)
        # Sem isto o processo continuaria vivo depois de fechar a janela.
        self.connect("destroy", Gtk.main_quit)

        raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        raiz.set_border_width(8)
        self.add(raiz)

        # pack_start(widget, expand, fill, padding): a configuração mantém o
        # tamanho natural; os resultados ocupam todo o espaço que sobrar.
        raiz.pack_start(self.montar_painel_config(), False, False, 0)
        raiz.pack_start(self.montar_painel_resultados(), True, True, 0)

    # ── Construção da interface ──────────────────────────────────────────
    def montar_painel_config(self):
        """Painel esquerdo: campos de configuração + botão Transmitir."""
        grade = Gtk.Grid(column_spacing=6, row_spacing=6)
        linha = 0

        def adicionar(rotulo, widget):
            """Coloca 'rótulo | widget' na próxima linha da grade."""
            nonlocal linha
            grade.attach(Gtk.Label(label=rotulo, xalign=0), 0, linha, 1, 1)
            grade.attach(widget, 1, linha, 1, 1)
            linha += 1

        self.entrada_texto = Gtk.Entry(text=simulador.CONFIG_PADRAO["texto"])
        adicionar("Texto de entrada:", self.entrada_texto)

        # SpinButton.new_with_range(mínimo, máximo, passo)
        self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.spin_quadro.set_value(simulador.CONFIG_PADRAO["tam_max_quadro"])
        adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

        # O 2º argumento de novo_combo é o item inicialmente selecionado.
        self.combo_enq = self.novo_combo(OPCOES_ENQUADRAMENTO, 3)
        adicionar("Enquadramento:", self.combo_enq)

        self.combo_det = self.novo_combo(OPCOES_DETECCAO, 3)
        adicionar("Detecção de erros:", self.combo_det)

        self.combo_cor = self.novo_combo(OPCOES_CORRECAO, 1)
        adicionar("Correção de erros:", self.combo_cor)

        self.combo_dig = self.novo_combo(OPCOES_MOD_DIGITAL, 0)
        adicionar("Modulação digital:", self.combo_dig)

        self.combo_port = self.novo_combo(OPCOES_MOD_PORTADORA, 3)
        adicionar("Modulação por portadora:", self.combo_port)

        self.spin_media = Gtk.SpinButton.new_with_range(-2.0, 2.0, 0.01)
        self.spin_media.set_digits(2)
        self.spin_media.set_value(simulador.CONFIG_PADRAO["ruido_media"])
        adicionar("Ruído - média x (V):", self.spin_media)

        self.spin_sigma = Gtk.SpinButton.new_with_range(0.0, 2.0, 0.01)
        self.spin_sigma.set_digits(2)
        self.spin_sigma.set_value(simulador.CONFIG_PADRAO["ruido_sigma"])
        adicionar("Ruído - desvio σ (V):", self.spin_sigma)

        botao = Gtk.Button(label="Transmitir")
        botao.connect("clicked", self.ao_transmitir)   # liga o clique ao método
        grade.attach(botao, 0, linha, 2, 1)
        linha += 1

        # Área de mensagens: erros, potências e se o texto foi recuperado.
        self.lbl_status = Gtk.Label(label="", xalign=0)
        self.lbl_status.set_line_wrap(True)
        self.lbl_status.set_max_width_chars(34)
        grade.attach(self.lbl_status, 0, linha, 2, 1)
        return grade

    def novo_combo(self, opcoes, indice_padrao):
        """Cria um combo (lista suspensa) com os rótulos de `opcoes`.

        A lista de opções é guardada no próprio widget (combo._opcoes) para
        que valor_combo() traduza o item escolhido no valor de `config`."""
        combo = Gtk.ComboBoxText()
        for rotulo, _ in opcoes:
            combo.append_text(rotulo)
        combo.set_active(indice_padrao)
        combo._opcoes = opcoes
        return combo

    @staticmethod
    def valor_combo(combo):
        """Valor de `config` do item selecionado (ex.: 'crc', '8psk')."""
        return combo._opcoes[combo.get_active()][1]

    def montar_painel_resultados(self):
        """Painel direito: abas Tx e Rx, cada uma com texto + gráfico."""
        notebook = Gtk.Notebook()

        self.txt_tx = self.nova_caixa_texto()
        self.fig_tx = Figure(figsize=(7, 4))
        self.canvas_tx = FigureCanvas(self.fig_tx)
        notebook.append_page(self.montar_aba(self.txt_tx, self.canvas_tx),
                             Gtk.Label(label="Transmissor (Tx)"))

        self.txt_rx = self.nova_caixa_texto()
        self.fig_rx = Figure(figsize=(7, 4))
        self.canvas_rx = FigureCanvas(self.fig_rx)
        notebook.append_page(self.montar_aba(self.txt_rx, self.canvas_rx),
                             Gtk.Label(label="Receptor (Rx)"))
        return notebook

    @staticmethod
    def nova_caixa_texto():
        """TextView somente leitura, fonte monoespaçada, quebra por caractere
        (os fluxos de bits não têm espaços para quebrar)."""
        tv = Gtk.TextView(editable=False, monospace=True)
        tv.set_wrap_mode(Gtk.WrapMode.CHAR)
        return tv

    @staticmethod
    def montar_aba(textview, canvas):
        """Empilha, na vertical, a caixa de texto (com rolagem) e o gráfico."""
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        rolagem = Gtk.ScrolledWindow()
        rolagem.set_min_content_height(260)
        rolagem.add(textview)
        caixa.pack_start(rolagem, True, True, 0)
        caixa.pack_start(canvas, True, True, 0)
        return caixa

    # ── Lógica ───────────────────────────────────────────────────────────
    def ler_config(self):
        """Lê os campos da tela e devolve o dict `config` do simulador."""
        return {
            "texto": self.entrada_texto.get_text(),
            "tam_max_quadro": int(self.spin_quadro.get_value()),
            "enquadramento": self.valor_combo(self.combo_enq),
            "deteccao": self.valor_combo(self.combo_det),
            "correcao": self.valor_combo(self.combo_cor),
            "mod_digital": self.valor_combo(self.combo_dig),
            "mod_portadora": self.valor_combo(self.combo_port),
            "ruido_media": self.spin_media.get_value(),
            "ruido_sigma": self.spin_sigma.get_value(),
        }

    def ao_transmitir(self, _botao):
        """Callback do botão: roda a simulação e atualiza as duas abas."""
        config = self.ler_config()
        if not config["texto"]:
            self.lbl_status.set_text("Digite um texto para transmitir.")
            return
        try:
            resultado = simulador.executar_simulacao(config)
        except ValueError as erro:
            # Ex.: quadro maior que 255 bytes no enquadramento por contagem.
            self.lbl_status.set_text(f"Erro: {erro}")
            return

        # ---- Aba Tx ----
        texto_tx = (
            f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
            f"SAÍDA DE BITS - APLICAÇÃO ({len(resultado['tx_bits_aplicacao'])} bits):\n"
            f"{bits_str(resultado['tx_bits_aplicacao'])}\n\n"
            f"SAÍDA DE BITS - ENLACE/quadros ({len(resultado['tx_bits_enlace'])} bits):\n"
            f"{bits_str(resultado['tx_bits_enlace'])}\n"
        )
        self.txt_tx.get_buffer().set_text(texto_tx)
        self.plotar(self.fig_tx, self.canvas_tx,
                    ("Sinal banda-base (Tx)", resultado["tx_sinal_banda_base"]),
                    ("Sinal transmitido ao meio (Tx)", resultado["tx_sinal_transmitido"]))

        # ---- Aba Rx ----
        linhas_quadros = "\n".join(
            f"  Quadro {q['quadro']}: "
            f"EDC {'OK' if q['edc_ok'] else 'ERRO DETECTADO'}"
            + (f", {q['corrigidos']} bit(s) corrigido(s) por Hamming"
               if config["correcao"] == "hamming" else "")
            + (", ERRO DUPLO detectado" if q["erro_duplo"] else "")
            for q in resultado["rx_relatorio_quadros"]) or "  (nenhum quadro recuperado)"
        texto_rx = (
            f"SAÍDA DE BITS - FÍSICA/demodulados "
            f"({len(resultado['rx_bits_fisica'])} bits):\n"
            f"{bits_str(resultado['rx_bits_fisica'])}\n\n"
            f"RELATÓRIO DOS QUADROS (enlace):\n{linhas_quadros}\n\n"
            f"SAÍDA DE BITS - APLICAÇÃO ({len(resultado['rx_bits_aplicacao'])} bits):\n"
            f"{bits_str(resultado['rx_bits_aplicacao'])}\n\n"
            f"SAÍDA DE TEXTO:\n{resultado['rx_texto']}\n"
        )
        self.txt_rx.get_buffer().set_text(texto_rx)
        self.plotar(self.fig_rx, self.canvas_rx,
                    ("Sinal recebido com ruído (Rx)", resultado["rx_sinal_recebido"]),
                    ("Banda-base reconstruído (Rx)", resultado["rx_sinal_banda_base"]))

        # ---- Status ----
        ok = (resultado["rx_texto"] == config["texto"])
        self.lbl_status.set_text(
            f"Potência do sinal: {resultado['potencia_sinal_w']:.3f} W | "
            f"do ruído: {resultado['potencia_ruido_w']:.4f} W\n"
            f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}.")

    @staticmethod
    def plotar(figura, canvas, *series):
        """Desenha cada série (titulo, amostras) em um subplot empilhado."""
        figura.clear()
        n = len(series)
        for k, (titulo, sinal) in enumerate(series, start=1):
            eixo = figura.add_subplot(n, 1, k)      # n linhas, 1 coluna, posição k
            eixo.plot(sinal[:MAX_AMOSTRAS_GRAFICO], linewidth=0.8)
            eixo.set_title(titulo, fontsize=9)
            eixo.set_ylabel("V", fontsize=8)
            eixo.tick_params(labelsize=7)
        figura.tight_layout()
        canvas.draw()

    def executar(self):
        """Mostra a janela e entra no laço de eventos do GTK."""
        self.show_all()
        Gtk.main()

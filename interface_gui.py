# -*- coding: utf-8 -*-
"""
Interface gráfica (GTK 3).

Janela única com o que o enunciado pede:
  - configuração: texto, tamanho máximo do quadro, enquadramento, detecção e
    correção de erros, modulação digital e por portadora, ruído (média e sigma);
  - saídas do transmissor (bits da aplicação e do enlace) e do receptor (bits
    demodulados, relatório dos quadros, bits da aplicação e texto final);
  - gráficos dos sinais (banda-base, transmitido, recebido com ruído);
  - potência do sinal e do ruído.

A GUI não implementa protocolo: lê os campos, monta o dict `config`, chama
simulador.executar_simulacao(config) e mostra o resultado.

Dependências (Linux): python3-gi, gir1.2-gtk-3.0 e matplotlib.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

import simulador


# Opções das listas: (valor usado em `config`, texto mostrado)
OPCOES_ENQUADRAMENTO = [("contagem", "Contagem de caracteres"),
                        ("entrelacamento", "Entrelaçamento de bits"),
                        ("bytes", "FLAGs + inserção de bytes"),
                        ("bits", "FLAGs + inserção de bits")]
OPCOES_DETECCAO = [("nenhum", "Nenhuma"),
                   ("paridade", "Bit de paridade par"),
                   ("checksum", "Checksum"),
                   ("crc", "CRC-32")]
OPCOES_CORRECAO = [("nenhum", "Nenhuma"),
                   ("hamming", "Hamming")]
OPCOES_MOD_DIGITAL = [("nrz", "NRZ-Polar"),
                      ("manchester", "Manchester"),
                      ("bipolar", "Bipolar")]
OPCOES_MOD_PORTADORA = [("nenhuma", "Nenhuma (só banda-base)"),
                        ("ask", "ASK"),
                        ("fsk", "FSK"),
                        ("8psk", "8PSK"),
                        ("32qam", "32-QAM")]

# Limites para a tela não travar com mensagens grandes
MAX_BITS_TEXTO = 2000
MAX_AMOSTRAS_GRAFICO = 4000


def bits_str(bits):
    """Transforma a lista de bits em texto '0101...' (corta se for muito longo)."""
    texto = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        texto += f"... ({len(bits)} bits no total)"
    return texto


class JanelaSimulador(Gtk.Window):
    """Janela principal: configuração à esquerda, resultados à direita."""

    def __init__(self):
        super().__init__(title="Simulador TR1")
        self.set_default_size(1100, 700)
        self.connect("destroy", Gtk.main_quit)      # fechar a janela encerra o programa

        raiz = Gtk.Box(spacing=8)
        raiz.set_border_width(8)
        self.add(raiz)
        raiz.pack_start(self.montar_config(), False, False, 0)
        raiz.pack_start(self.montar_resultados(), True, True, 0)

    # construção da tela
    def montar_config(self):
        """Painel da esquerda: campos de configuração, botão e mensagem de status."""
        padrao = simulador.CONFIG_PADRAO
        grade = Gtk.Grid(column_spacing=6, row_spacing=6)

        self.entrada_texto = Gtk.Entry(text=padrao["texto"])
        self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
        self.spin_quadro.set_value(padrao["tam_max_quadro"])
        self.combo_enq = self.novo_combo(OPCOES_ENQUADRAMENTO, padrao["enquadramento"])
        self.combo_det = self.novo_combo(OPCOES_DETECCAO, padrao["deteccao"])
        self.combo_cor = self.novo_combo(OPCOES_CORRECAO, padrao["correcao"])
        self.combo_dig = self.novo_combo(OPCOES_MOD_DIGITAL, padrao["mod_digital"])
        self.combo_port = self.novo_combo(OPCOES_MOD_PORTADORA, padrao["mod_portadora"])
        self.spin_media = Gtk.SpinButton.new_with_range(-2.0, 2.0, 0.01)
        self.spin_media.set_digits(2)
        self.spin_media.set_value(padrao["ruido_media"])
        self.spin_sigma = Gtk.SpinButton.new_with_range(0.0, 2.0, 0.01)
        self.spin_sigma.set_digits(2)
        self.spin_sigma.set_value(padrao["ruido_sigma"])

        campos = [("Texto:", self.entrada_texto),
                  ("Tam. máx. do quadro (bytes):", self.spin_quadro),
                  ("Enquadramento:", self.combo_enq),
                  ("Detecção de erros:", self.combo_det),
                  ("Correção de erros:", self.combo_cor),
                  ("Modulação digital:", self.combo_dig),
                  ("Modulação por portadora:", self.combo_port),
                  ("Ruído - média x (V):", self.spin_media),
                  ("Ruído - desvio σ (V):", self.spin_sigma)]
        for linha, (rotulo, campo) in enumerate(campos):
            grade.attach(Gtk.Label(label=rotulo, xalign=0), 0, linha, 1, 1)
            grade.attach(campo, 1, linha, 1, 1)

        botao = Gtk.Button(label="Transmitir")
        botao.connect("clicked", self.ao_transmitir)
        grade.attach(botao, 0, len(campos), 2, 1)

        self.lbl_status = Gtk.Label(xalign=0)
        self.lbl_status.set_line_wrap(True)
        self.lbl_status.set_max_width_chars(34)
        grade.attach(self.lbl_status, 0, len(campos) + 1, 2, 1)
        return grade

    @staticmethod
    def novo_combo(opcoes, valor_inicial):
        """Cria uma lista suspensa. Cada item guarda o valor de `config` como id."""
        combo = Gtk.ComboBoxText()
        for valor, rotulo in opcoes:
            combo.append(valor, rotulo)
        combo.set_active_id(valor_inicial)
        return combo

    def montar_resultados(self):
        """Painel da direita: texto com as saídas do Tx e do Rx e os gráficos."""
        caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        self.saida = Gtk.TextView(editable=False, monospace=True)
        self.saida.set_wrap_mode(Gtk.WrapMode.CHAR)    # bits não têm espaço para quebrar
        rolagem = Gtk.ScrolledWindow()
        rolagem.add(self.saida)
        caixa.pack_start(rolagem, True, True, 0)

        self.figura = Figure(figsize=(7, 5))
        self.canvas = FigureCanvas(self.figura)
        caixa.pack_start(self.canvas, True, True, 0)
        return caixa

    # lógica
    def ler_config(self):
        """Lê os campos da tela e devolve o dict `config` do simulador."""
        return {
            "texto": self.entrada_texto.get_text(),
            "tam_max_quadro": int(self.spin_quadro.get_value()),
            "enquadramento": self.combo_enq.get_active_id(),
            "deteccao": self.combo_det.get_active_id(),
            "correcao": self.combo_cor.get_active_id(),
            "mod_digital": self.combo_dig.get_active_id(),
            "mod_portadora": self.combo_port.get_active_id(),
            "ruido_media": self.spin_media.get_value(),
            "ruido_sigma": self.spin_sigma.get_value(),
        }

    def ao_transmitir(self, _botao):
        """Clique em "Transmitir": roda a simulação e mostra os resultados."""
        config = self.ler_config()
        if not config["texto"]:
            self.lbl_status.set_text("Digite um texto para transmitir.")
            return
        try:
            r = simulador.executar_simulacao(config)
        except ValueError as erro:      # ex.: quadro com mais de 255 bytes na contagem
            self.lbl_status.set_text(f"Erro: {erro}")
            return

        self.mostrar_texto(config, r)
        self.plotar([("Banda-base (Tx)", r["tx_sinal_banda_base"]),
                     ("Sinal transmitido (Tx)", r["tx_sinal_transmitido"]),
                     ("Sinal recebido com ruído (Rx)", r["rx_sinal_recebido"]),
                     ("Banda-base reconstruído (Rx)", r["rx_sinal_banda_base"])])

        recuperado = r["rx_texto"] == config["texto"]
        self.lbl_status.set_text(
            f"Potência do sinal: {r['potencia_sinal_w']:.3f} W\n"
            f"Potência do ruído: {r['potencia_ruido_w']:.4f} W\n"
            f"Texto recuperado {'corretamente' if recuperado else 'com diferenças'}.")

    def mostrar_texto(self, config, r):
        """Escreve na caixa de texto as saídas de cada camada, do Tx e do Rx."""
        quadros = ""
        for q in r["rx_relatorio_quadros"]:
            quadros += f"  Quadro {q['quadro']}: EDC {'ok' if q['edc_ok'] else 'COM ERRO'}"
            if config["correcao"] == "hamming":
                quadros += f", {q['corrigidos']} bit(s) corrigido(s)"
            if q["erro_duplo"]:
                quadros += ", erro incorrigível"
            quadros += "\n"

        texto = (
            f"--- TRANSMISSOR ---\n"
            f"Texto: {config['texto']}\n"
            f"Bits da aplicação ({len(r['tx_bits_aplicacao'])}):\n"
            f"{bits_str(r['tx_bits_aplicacao'])}\n"
            f"Bits do enlace ({len(r['tx_bits_enlace'])}):\n"
            f"{bits_str(r['tx_bits_enlace'])}\n\n"
            f"--- RECEPTOR ---\n"
            f"Bits demodulados ({len(r['rx_bits_fisica'])}):\n"
            f"{bits_str(r['rx_bits_fisica'])}\n"
            f"Quadros:\n{quadros}"
            f"Bits da aplicação ({len(r['rx_bits_aplicacao'])}):\n"
            f"{bits_str(r['rx_bits_aplicacao'])}\n"
            f"Texto: {r['rx_texto']}\n")
        self.saida.get_buffer().set_text(texto)

    def plotar(self, series):
        """Desenha cada série (título, amostras) em um gráfico, um embaixo do outro."""
        self.figura.clear()
        for k, (titulo, sinal) in enumerate(series, start=1):
            eixo = self.figura.add_subplot(len(series), 1, k)
            eixo.plot(sinal[:MAX_AMOSTRAS_GRAFICO], linewidth=0.8)
            eixo.set_title(titulo, fontsize=9)
            eixo.set_ylabel("V", fontsize=8)
            eixo.tick_params(labelsize=7)
        self.figura.tight_layout()
        self.canvas.draw()

    def executar(self):
        """Mostra a janela e entra no laço de eventos do GTK."""
        self.show_all()
        Gtk.main()

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
    from gi.repository import Gtk, GLib, Gdk, Pango
    from matplotlib.backends.backend_gtk3agg import (
        FigureCanvasGTK3Agg as FigureCanvas)
    BACKEND = "gtk"
except Exception:
    import tkinter as tk
    from tkinter import ttk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    BACKEND = "tk"

from matplotlib.figure import Figure
import camada_enlace
import camada_fisica
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

ROTULOS_ENQUADRAMENTO = {valor: rotulo for rotulo, valor in OPCOES_ENQUADRAMENTO}
ROTULOS_DETECCAO = {valor: rotulo for rotulo, valor in OPCOES_DETECCAO}
ROTULOS_CORRECAO = {valor: rotulo for rotulo, valor in OPCOES_CORRECAO}
ROTULOS_DIGITAL = {valor: rotulo for rotulo, valor in OPCOES_MOD_DIGITAL}
ROTULOS_PORTADORA = {valor: rotulo for rotulo, valor in OPCOES_MOD_PORTADORA}
BITS_POR_SIMBOLO = {"ask": 1, "fsk": 1, "qpsk": 2, "16qam": 4}

MAX_AMOSTRAS_GRAFICO = 4000
MAX_BITS_TEXTO = 2048


def bits_str(bits):
    if bits is None:
        return "-"
    texto = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        texto += f"... ({len(bits)} bits no total)"
    return texto


def plural_bits(n):
    return f"{n} bit" if n == 1 else f"{n} bits"


def plural_amostras(n):
    return f"{n} amostra" if n == 1 else f"{n} amostras"


def plural_quadros(n):
    return f"{n} quadro" if n == 1 else f"{n} quadros"


def detalhe_deteccao(tipo, n_quadros):
    if tipo == "nenhum":
        return "Nenhum EDC anexado; o receptor não valida corrupção."
    if tipo == "paridade":
        return f"Adiciona 1 byte por quadro: {n_quadros} x 8 bits."
    if tipo == "checksum":
        return f"Adiciona 2 bytes por quadro: {n_quadros} x 16 bits."
    return f"Adiciona 4 bytes por quadro: {n_quadros} x 32 bits."


def detalhe_correcao(tipo):
    if tipo == "hamming":
        return "Hamming(8,4) dobra payload + EDC: cada 4 bits viram 8 bits."
    return "Nenhuma redundância de correção foi adicionada."


def detalhe_enquadramento(tipo, n_quadros):
    if tipo == "contagem":
        return f"Adiciona 1 byte de contagem por quadro: {n_quadros} x 8 bits."
    if tipo == "bytes":
        return "Adiciona FLAGs e ESCs quando payload contém bytes especiais."
    return "Adiciona FLAGs e bits 0 após sequências de cinco bits 1."


def diagnosticar_camadas(bits_app, resultado, config):
    tam_bits = config["tam_max_quadro"] * 8
    blocos = [bits_app[i:i + tam_bits] for i in range(0, len(bits_app), tam_bits)]
    bits_blocos = sum(len(bloco) for bloco in blocos)

    payloads_edc = [
        camada_enlace.ADICIONAR_EDC[config["deteccao"]](bloco)
        for bloco in blocos
    ]
    bits_apos_edc = sum(len(payload) for payload in payloads_edc)
    bits_edc = bits_apos_edc - bits_blocos

    payloads_correcao = []
    for payload in payloads_edc:
        if config["correcao"] == "hamming":
            payloads_correcao.append(camada_enlace.codificar_hamming(payload))
        else:
            payloads_correcao.append(payload)
    bits_apos_correcao = sum(len(payload) for payload in payloads_correcao)
    bits_correcao = bits_apos_correcao - bits_apos_edc

    fluxo_enquadrado = camada_enlace.ENQUADRAR[config["enquadramento"]](
        payloads_correcao)
    bits_enlace = len(fluxo_enquadrado)
    bits_enquadramento = bits_enlace - bits_apos_correcao

    amostras_digitais = len(resultado["tx_sinal_banda_base"])
    amostras_tx = len(resultado["tx_sinal_transmitido"])
    if config["mod_portadora"] == "nenhuma":
        saida_portadora = plural_amostras(amostras_tx)
        padding_portadora = 0
        detalhe_portadora = "Sem portadora: o sinal banda-base trafega no meio."
    else:
        bits_por_simbolo = BITS_POR_SIMBOLO[config["mod_portadora"]]
        simbolos = (bits_enlace + bits_por_simbolo - 1) // bits_por_simbolo
        bits_representados = simbolos * bits_por_simbolo
        padding_portadora = bits_representados - bits_enlace
        saida_portadora = f"{simbolos} símbolo(s), {plural_amostras(amostras_tx)}"
        detalhe_portadora = (
            f"{bits_por_simbolo} bit(s) por símbolo; padding de "
            f"{plural_bits(padding_portadora)} quando necessário.")

    return {
        "bits_aplicacao": len(bits_app),
        "bits_enlace": bits_enlace,
        "bits_adicionados": bits_enlace - len(bits_app),
        "bits_edc": bits_edc,
        "bits_correcao": bits_correcao,
        "bits_enquadramento": bits_enquadramento,
        "padding_portadora": padding_portadora,
        "fases": [
            {
                "nome": "Aplicação: texto -> bits",
                "entrada": f"{len(config['texto'].encode('utf-8'))} byte(s) UTF-8",
                "saida": plural_bits(len(bits_app)),
                "delta": "0 bits",
                "detalhe": "Converte bytes UTF-8 em bits; não adiciona redundância.",
            },
            {
                "nome": "Divisão em quadros",
                "entrada": plural_bits(len(bits_app)),
                "saida": f"{plural_quadros(len(blocos))}, {plural_bits(bits_blocos)}",
                "delta": "0 bits",
                "detalhe": f"Cada quadro carrega até {config['tam_max_quadro']} byte(s).",
            },
            {
                "nome": f"Detecção de erros: {ROTULOS_DETECCAO[config['deteccao']]}",
                "entrada": plural_bits(bits_blocos),
                "saida": plural_bits(bits_apos_edc),
                "delta": plural_bits(bits_edc),
                "detalhe": detalhe_deteccao(config["deteccao"], len(blocos)),
            },
            {
                "nome": f"Correção de erros: {ROTULOS_CORRECAO[config['correcao']]}",
                "entrada": plural_bits(bits_apos_edc),
                "saida": plural_bits(bits_apos_correcao),
                "delta": plural_bits(bits_correcao),
                "detalhe": detalhe_correcao(config["correcao"]),
            },
            {
                "nome": f"Enquadramento: {ROTULOS_ENQUADRAMENTO[config['enquadramento']]}",
                "entrada": plural_bits(bits_apos_correcao),
                "saida": plural_bits(bits_enlace),
                "delta": plural_bits(bits_enquadramento),
                "detalhe": detalhe_enquadramento(config["enquadramento"], len(blocos)),
            },
            {
                "nome": f"Modulação digital: {ROTULOS_DIGITAL[config['mod_digital']]}",
                "entrada": plural_bits(bits_enlace),
                "saida": plural_amostras(amostras_digitais),
                "delta": "0 bits",
                "detalhe": (
                    f"Cada bit vira {camada_fisica.AMOSTRAS_POR_BIT} amostras em Volts."
                ),
            },
            {
                "nome": f"Modulação por portadora: {ROTULOS_PORTADORA[config['mod_portadora']]}",
                "entrada": plural_bits(bits_enlace),
                "saida": saida_portadora,
                "delta": plural_bits(padding_portadora),
                "detalhe": detalhe_portadora,
            },
            {
                "nome": "Meio ruidoso",
                "entrada": plural_amostras(amostras_tx),
                "saida": plural_amostras(len(resultado["rx_sinal_recebido"])),
                "delta": "0 bits",
                "detalhe": (
                    f"Ruído gaussiano: média {config['ruido_media']:.2f} V, "
                    f"sigma {config['ruido_sigma']:.2f} V por amostra."
                ),
            },
        ],
    }


def formatar_diagnostico(diagnostico, resultado, config):
    linhas = [
        "PROCESSAMENTO POR FASE",
        (
            f"Resumo: aplicação {plural_bits(diagnostico['bits_aplicacao'])} -> "
            f"enlace {plural_bits(diagnostico['bits_enlace'])} | "
            f"adicionados {plural_bits(diagnostico['bits_adicionados'])}"
        ),
        (
            f"EDC +{plural_bits(diagnostico['bits_edc'])} | "
            f"Hamming +{plural_bits(diagnostico['bits_correcao'])} | "
            f"Enquadramento +{plural_bits(diagnostico['bits_enquadramento'])} | "
            f"Padding portadora +{plural_bits(diagnostico['padding_portadora'])}"
        ),
        (
            f"Potência sinal {resultado['potencia_sinal_w']:.4f} W | "
            f"potência ruído {resultado['potencia_ruido_w']:.4f} W | "
            f"sigma {config['ruido_sigma']:.2f} V"
        ),
        "",
    ]
    for indice, fase in enumerate(diagnostico["fases"], start=1):
        linhas.append(
            f"{indice:02d}. {fase['nome']}\n"
            f"    entrada: {fase['entrada']}\n"
            f"    saida:   {fase['saida']}\n"
            f"    delta:   {fase['delta']}\n"
            f"    nota:    {fase['detalhe']}"
        )
    return "\n".join(linhas)


# ═════════════════════════════════════════════════════════════════════════════
# IMPLEMENTAÇÃO GTK 3  (usada no Linux — requisito do trabalho)
# ═════════════════════════════════════════════════════════════════════════════
if BACKEND == "gtk":

    class JanelaSimulador(Gtk.Window):
        """Janela principal do simulador (GTK 3)."""

        def __init__(self):
            super().__init__(title="Simulador TR1 - Camadas Física e de Enlace")
            self.set_default_size(1280, 820)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.connect("destroy", self.ao_fechar)
            self.continuo_id = None
            self.contador_continuo = 0
            self.metricas = {}
            self.linhas_fases = []
            self.aplicar_tema_claro()

            raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            raiz.set_border_width(12)
            raiz.set_hexpand(True)
            raiz.set_vexpand(True)
            raiz.set_halign(Gtk.Align.FILL)
            raiz.set_valign(Gtk.Align.FILL)
            raiz.get_style_context().add_class("app-root")
            self.add(raiz)

            raiz.pack_start(self.montar_painel_config(), False, False, 0)
            raiz.pack_start(self.montar_painel_resultados(), True, True, 0)
            self.inicializar_resultados()

        @staticmethod
        def aplicar_tema_claro():
            css = b"""
            * {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            window, .app-root, .main-panel, scrolledwindow {
                background: #eef2f7;
                color: #111827;
            }
            label {
                color: #111827;
            }
            entry, spinbutton, combobox, scale {
                background: #ffffff;
                color: #111827;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                min-height: 30px;
            }
            button {
                border-radius: 6px;
                min-height: 34px;
                font-weight: 700;
            }
            button.primary {
                background: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
            }
            button.secondary {
                background: #ffffff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
            }
            .sidebar, .card, .metric-card, .status-banner {
                background: #ffffff;
                border: 1px solid #dbe3ef;
                border-radius: 8px;
            }
            .title {
                font-size: 20px;
                font-weight: 800;
            }
            .subtitle {
                color: #475569;
                font-size: 12px;
            }
            .field-label {
                font-weight: 700;
                font-size: 12px;
            }
            .mode-panel {
                background: #f8fafc;
                border: 1px solid #dbe3ef;
                border-radius: 6px;
            }
            .status-banner {
                border-left: 6px solid #059669;
            }
            .status-error {
                border-left-color: #dc2626;
            }
            .status-warn {
                border-left-color: #d97706;
            }
            .metric-label, .phase-header {
                color: #475569;
                font-size: 11px;
                font-weight: 800;
            }
            .metric-value {
                color: #0f172a;
                font-size: 22px;
                font-weight: 900;
            }
            .phase-cell {
                color: #1f2937;
                font-size: 12px;
            }
            .phase-delta {
                color: #047857;
                font-weight: 900;
            }
            .phase-zero {
                color: #64748b;
                font-weight: 800;
            }
            .console, .console text {
                background: #0f172a;
                color: #f8fafc;
                font-family: Menlo, Consolas, monospace;
                font-size: 11px;
            }
            .pill {
                background: #f8fafc;
                border: 1px solid #dbe3ef;
                border-radius: 14px;
                color: #0f172a;
                font-weight: 700;
            }
            """
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

        @staticmethod
        def ao_fechar(*_args):
            if Gtk.main_level() > 0:
                Gtk.main_quit()

        @staticmethod
        def adicionar_classes(widget, *classes):
            contexto = widget.get_style_context()
            for classe in classes:
                contexto.add_class(classe)

        @staticmethod
        def label(texto="", classe=None, xalign=0, wrap=False):
            label = Gtk.Label(label=texto, xalign=xalign)
            if wrap:
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            if classe:
                label.get_style_context().add_class(classe)
            return label

        def novo_card(self, classe="card"):
            cartao = Gtk.EventBox()
            cartao.get_style_context().add_class(classe)
            conteudo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            conteudo.set_border_width(12)
            cartao.add(conteudo)
            return cartao, conteudo

        # ── Construção ────────────────────────────────────────────────────

        def montar_painel_config(self):
            cartao, caixa = self.novo_card("sidebar")
            cartao.set_size_request(300, -1)
            caixa.set_size_request(276, -1)

            titulo = self.label("Simulador TR1", "title")
            caixa.pack_start(titulo, False, False, 0)
            subtitulo = self.label(
                "Transmissão completa: aplicação, enlace, física e meio ruidoso.",
                "subtitle",
                wrap=True,
            )
            subtitulo.set_width_chars(26)
            subtitulo.set_max_width_chars(30)
            caixa.pack_start(subtitulo, False, False, 0)

            def adicionar(rotulo_texto, widget):
                grupo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                grupo.pack_start(self.label(rotulo_texto, "field-label"), False, False, 0)
                grupo.pack_start(widget, False, True, 0)
                caixa.pack_start(grupo, False, True, 0)

            self.entrada_texto = Gtk.Entry(text="Ola, TR1!")
            self.entrada_texto.set_width_chars(22)
            adicionar("Texto de entrada", self.entrada_texto)

            self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
            self.spin_quadro.set_value(8)
            self.spin_quadro.set_size_request(260, 34)
            adicionar("Tamanho máximo do quadro", self.spin_quadro)

            self.combo_enq = self.novo_combo(OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento", self.combo_enq)

            self.combo_det = self.novo_combo(OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros", self.combo_det)

            self.combo_cor = self.novo_combo(OPCOES_CORRECAO, 1)
            adicionar("Correção de erros", self.combo_cor)

            self.combo_dig = self.novo_combo(OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital", self.combo_dig)

            self.combo_port = self.novo_combo(OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora", self.combo_port)

            self.spin_media = Gtk.SpinButton.new_with_range(-2.0, 2.0, 0.01)
            self.spin_media.set_digits(2)
            self.spin_media.set_value(0.0)
            self.spin_media.set_size_request(260, 34)
            adicionar("Ruído - média x (V)", self.spin_media)

            self.spin_sigma = Gtk.Scale.new_with_range(
                Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.01)
            self.spin_sigma.set_digits(2)
            self.spin_sigma.set_draw_value(False)
            self.spin_sigma.set_value(0.10)
            self.spin_sigma.set_hexpand(True)
            self.spin_sigma.set_size_request(178, 34)
            self.lbl_sigma_valor = self.label("0.10 V", "pill", xalign=0.5)
            self.lbl_sigma_valor.set_size_request(66, 28)
            self.spin_sigma.connect("value-changed", self.ao_mudar_sigma)
            linha_sigma = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            linha_sigma.pack_start(self.spin_sigma, True, True, 0)
            linha_sigma.pack_start(self.lbl_sigma_valor, False, False, 0)
            adicionar("Ruído - desvio σ (V)", linha_sigma)

            self.spin_intervalo = Gtk.SpinButton.new_with_range(250, 5000, 50)
            self.spin_intervalo.set_value(900)
            self.spin_intervalo.set_size_request(260, 34)
            adicionar("Intervalo contínuo (ms)", self.spin_intervalo)

            botoes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.botao_transmitir = Gtk.Button(label="Transmitir uma vez")
            self.botao_transmitir.get_style_context().add_class("primary")
            self.botao_transmitir.connect("clicked", self.ao_transmitir)
            botoes.pack_start(self.botao_transmitir, True, True, 0)

            self.botao_continuo = Gtk.ToggleButton(label="Iniciar contínua")
            self.botao_continuo.get_style_context().add_class("secondary")
            self.botao_continuo.connect("toggled", self.ao_alternar_continua)
            botoes.pack_start(self.botao_continuo, True, True, 0)
            caixa.pack_start(botoes, False, True, 4)

            self.lbl_modo = Gtk.Label(label="Modo manual", xalign=0)
            modo_box = Gtk.EventBox()
            modo_box.get_style_context().add_class("mode-panel")
            modo_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            modo_inner.set_border_width(8)
            modo_inner.pack_start(self.lbl_modo, False, False, 0)
            modo_box.add(modo_inner)
            caixa.pack_start(modo_box, False, True, 0)

            self.lbl_status = Gtk.Label(label="", xalign=0)
            self.lbl_status.set_line_wrap(True)
            self.lbl_status.set_max_width_chars(34)
            modo_inner.pack_start(self.lbl_status, False, False, 0)
            return cartao

        def ao_mudar_sigma(self, escala):
            self.lbl_sigma_valor.set_text(f"{escala.get_value():.2f} V")

        def novo_combo(self, opcoes, indice_padrao):
            combo = Gtk.ComboBoxText()
            for rotulo, _ in opcoes:
                combo.append_text(rotulo)
            combo.set_active(indice_padrao)
            combo.set_hexpand(True)
            combo.set_size_request(260, 34)
            combo._opcoes = opcoes
            return combo

        @staticmethod
        def valor_combo(combo):
            return combo._opcoes[combo.get_active()][1]

        def montar_painel_resultados(self):
            rolagem = Gtk.ScrolledWindow()
            rolagem.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            rolagem.set_hexpand(True)
            rolagem.set_vexpand(True)

            painel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            painel.get_style_context().add_class("main-panel")
            painel.set_hexpand(True)
            painel.set_vexpand(True)
            rolagem.add(painel)

            self.banner_status = Gtk.EventBox()
            self.banner_status.get_style_context().add_class("status-banner")
            banner_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            banner_inner.set_border_width(12)
            self.lbl_banner = self.label("Pronto para transmitir.")
            self.lbl_banner.set_line_wrap(True)
            self.lbl_banner.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            self.lbl_banner.set_max_width_chars(60)
            banner_inner.pack_start(self.lbl_banner, False, False, 0)
            self.banner_status.add(banner_inner)
            painel.pack_start(self.banner_status, False, True, 0)

            painel.pack_start(self.montar_metricas(), False, True, 0)
            painel.pack_start(self.montar_tabela_diagnostico(), False, True, 0)
            painel.pack_start(self.montar_resultados_duplos(), True, True, 0)
            return rolagem

        def montar_metricas(self):
            grade = Gtk.Grid(column_spacing=10, row_spacing=10)
            grade.set_column_homogeneous(True)
            itens = [
                ("bits_aplicacao", "Bits da aplicação"),
                ("bits_enlace", "Bits no enlace"),
                ("bits_adicionados", "Bits adicionados"),
                ("potencia_sinal", "Potência do sinal"),
                ("potencia_ruido", "Potência do ruído"),
                ("texto_recuperado", "Texto recuperado"),
            ]
            for indice, (chave, rotulo) in enumerate(itens):
                cartao, conteudo = self.novo_card("metric-card")
                conteudo.pack_start(self.label(rotulo, "metric-label"), False, False, 0)
                valor = self.label("-", "metric-value")
                conteudo.pack_start(valor, False, False, 0)
                self.metricas[chave] = valor
                coluna = indice % 2
                linha = indice // 2
                grade.attach(cartao, coluna, linha, 1, 1)
            return grade

        def montar_tabela_diagnostico(self):
            cartao, conteudo = self.novo_card("card")
            titulo = self.label("Processamento por fase", "title")
            conteudo.pack_start(titulo, False, False, 0)

            grade = Gtk.Grid(column_spacing=14, row_spacing=8)
            conteudo.pack_start(grade, False, True, 0)

            colunas = [
                ("FASE", 18),
                ("ENTRADA", 10),
                ("SAÍDA", 11),
                ("ADICIONOU", 9),
                ("DIAGNÓSTICO", 24),
            ]
            for coluna, (texto, largura) in enumerate(colunas):
                cabecalho = self.label(texto, "phase-header")
                cabecalho.set_width_chars(largura)
                grade.attach(cabecalho, coluna, 0, 1, 1)

            for linha in range(1, 9):
                labels = {}
                for coluna, (chave, largura, classe) in enumerate([
                    ("nome", 18, "phase-cell"),
                    ("entrada", 10, "phase-cell"),
                    ("saida", 11, "phase-cell"),
                    ("delta", 9, "phase-zero"),
                    ("detalhe", 24, "phase-cell"),
                ]):
                    label = self.label("-", classe, wrap=True)
                    label.set_width_chars(largura)
                    label.set_max_width_chars(largura)
                    grade.attach(label, coluna, linha, 1, 1)
                    labels[chave] = label
                self.linhas_fases.append(labels)
            return cartao

        def montar_resultados_duplos(self):
            linha = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            linha.set_homogeneous(True)

            card_tx, self.txt_tx, self.fig_tx, self.canvas_tx = \
                self.criar_cartao_resultado("Transmissor (Tx)")
            linha.pack_start(card_tx, True, True, 0)

            card_rx, self.txt_rx, self.fig_rx, self.canvas_rx = \
                self.criar_cartao_resultado("Receptor (Rx)")
            linha.pack_start(card_rx, True, True, 0)
            return linha

        def criar_cartao_resultado(self, titulo):
            cartao, conteudo = self.novo_card("card")
            cartao.set_size_request(340, -1)
            conteudo.pack_start(self.label(titulo, "title"), False, False, 0)

            texto = self.nova_caixa_texto()
            rolagem = Gtk.ScrolledWindow()
            rolagem.set_min_content_width(300)
            rolagem.set_min_content_height(150)
            rolagem.add(texto)
            conteudo.pack_start(rolagem, False, True, 0)

            figura = Figure(figsize=(6.4, 3.1), facecolor="#ffffff")
            canvas = FigureCanvas(figura)
            canvas.set_size_request(-1, 285)
            conteudo.pack_start(canvas, True, True, 0)
            return cartao, texto, figura, canvas

        @staticmethod
        def nova_caixa_texto():
            tv = Gtk.TextView(editable=False, monospace=True)
            tv.set_wrap_mode(Gtk.WrapMode.CHAR)
            tv.get_style_context().add_class("console")
            return tv

        # ── Lógica ────────────────────────────────────────────────────────

        def inicializar_resultados(self):
            self.definir_banner(
                "Escolha os parâmetros e rode a simulação para ver bits, quadros, sinais e texto recuperado.",
                "ok",
            )
            for valor in self.metricas.values():
                valor.set_text("-")
            for labels in self.linhas_fases:
                for label in labels.values():
                    label.set_text("-")
            self.txt_tx.get_buffer().set_text(
                "TEXTO DE ENTRADA:\n\nSAÍDA DE BITS - APLICAÇÃO:\n\nSAÍDA DE BITS - ENLACE/quadros:")
            self.txt_rx.get_buffer().set_text(
                "SAÍDA DE BITS - FÍSICA/demodulados:\n\nRELATÓRIO DOS QUADROS (enlace):\n\nSAÍDA DE TEXTO:")

        def definir_banner(self, texto, estado):
            contexto = self.banner_status.get_style_context()
            contexto.remove_class("status-error")
            contexto.remove_class("status-warn")
            if estado == "erro":
                contexto.add_class("status-error")
            elif estado == "warn":
                contexto.add_class("status-warn")
            self.lbl_banner.set_text(texto)

        def atualizar_metricas(self, resultado, diagnostico, config, ok):
            self.metricas["bits_aplicacao"].set_text(
                str(diagnostico["bits_aplicacao"]))
            self.metricas["bits_enlace"].set_text(str(diagnostico["bits_enlace"]))
            self.metricas["bits_adicionados"].set_text(
                str(diagnostico["bits_adicionados"]))
            self.metricas["potencia_sinal"].set_text(
                f"{resultado['potencia_sinal_w']:.4f} W")
            self.metricas["potencia_ruido"].set_text(
                f"{resultado['potencia_ruido_w']:.4f} W")
            self.metricas["texto_recuperado"].set_text(
                "OK" if ok else "com diferenças")

            sufixo_continuo = (
                f" | contínua #{self.contador_continuo}"
                if self.botao_continuo.get_active() else "")
            self.definir_banner(
                (
                    "Texto recuperado corretamente."
                    if ok else "Texto recuperado com diferenças."
                ) + f" | sigma {config['ruido_sigma']:.2f} V{sufixo_continuo}",
                "ok" if ok else "warn",
            )

        def atualizar_tabela_diagnostico(self, diagnostico):
            for labels, fase in zip(self.linhas_fases, diagnostico["fases"]):
                labels["nome"].set_text(fase["nome"])
                labels["entrada"].set_text(fase["entrada"])
                labels["saida"].set_text(fase["saida"])
                labels["delta"].set_text(fase["delta"])
                labels["detalhe"].set_text(fase["detalhe"])

                contexto = labels["delta"].get_style_context()
                contexto.remove_class("phase-zero")
                contexto.remove_class("phase-delta")
                if fase["delta"] == "0 bits":
                    contexto.add_class("phase-zero")
                else:
                    contexto.add_class("phase-delta")

        def ler_config(self):
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

        def ao_alternar_continua(self, botao):
            if botao.get_active():
                self.contador_continuo = 0
                botao.set_label("Parar contínua")
                self.lbl_modo.set_text("Modo contínuo")
                self.ao_tick_continuo()
                intervalo = int(self.spin_intervalo.get_value())
                self.continuo_id = GLib.timeout_add(intervalo, self.ao_tick_continuo)
            else:
                botao.set_label("Iniciar contínua")
                self.lbl_modo.set_text("Modo manual")
                if self.continuo_id is not None:
                    GLib.source_remove(self.continuo_id)
                    self.continuo_id = None

        def ao_tick_continuo(self):
            if not self.botao_continuo.get_active():
                self.continuo_id = None
                return False
            self.contador_continuo += 1
            self.ao_transmitir(None)
            return self.botao_continuo.get_active()

        def ao_transmitir(self, _botao=None):
            config = self.ler_config()
            if not config["texto"]:
                self.lbl_status.set_text("Digite um texto para transmitir.")
                self.definir_banner("Digite um texto para transmitir.", "erro")
                return
            try:
                resultado = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.set_text(f"Erro: {erro}")
                self.definir_banner(f"Erro: {erro}", "erro")
                return

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

            diagnostico = diagnosticar_camadas(
                resultado["tx_bits_aplicacao"], resultado, config)
            self.atualizar_tabela_diagnostico(diagnostico)

            ok = (resultado["rx_texto"] == config["texto"])
            pot_sinal = resultado["potencia_sinal_w"]
            pot_ruido = resultado["potencia_ruido_w"]
            self.atualizar_metricas(resultado, diagnostico, config, ok)
            self.lbl_status.set_text(
                f"Potência do sinal: {pot_sinal:.3f} W | do ruído: {pot_ruido:.4f} W\n"
                f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}.")

        @staticmethod
        def plotar(figura, canvas, *series):
            figura.clear()
            figura.patch.set_facecolor("#ffffff")
            num_series = len(series)
            for k, (titulo, sinal) in enumerate(series, start=1):
                eixo = figura.add_subplot(num_series, 1, k)
                eixo.set_facecolor("#ffffff")
                eixo.plot(
                    sinal[:MAX_AMOSTRAS_GRAFICO],
                    linewidth=0.9,
                    color="#0f766e",
                )
                eixo.set_title(titulo, fontsize=9, color="#0f172a", loc="left")
                eixo.set_ylabel("V", fontsize=8, color="#475569")
                eixo.tick_params(labelsize=7, colors="#475569")
                eixo.grid(True, color="#e2e8f0", linewidth=0.7)
                for spine in eixo.spines.values():
                    spine.set_color("#cbd5e1")
            figura.subplots_adjust(hspace=0.55, top=0.92, bottom=0.12)
            canvas.draw()

        def executar(self):
            self.show_all()
            self.present()
            Gtk.main()


# ═════════════════════════════════════════════════════════════════════════════
# IMPLEMENTAÇÃO TKINTER  (fallback automático quando GTK não está disponível)
# ═════════════════════════════════════════════════════════════════════════════
else:

    COR_FUNDO = "#111827"
    COR_PAINEL = "#1f2937"
    COR_CAMPO = "#374151"
    COR_TEXTO = "#f9fafb"
    COR_TEXTO_SECUNDARIO = "#d1d5db"
    COR_BORDA = "#4b5563"
    COR_BOTAO = "#2563eb"
    COR_BOTAO_ATIVO = "#1d4ed8"
    COR_LINHA = "#60a5fa"

    class JanelaSimulador(tk.Tk):
        """Janela principal do simulador (tkinter — fallback sem GTK)."""

        def __init__(self):
            super().__init__()
            self.title("Simulador TR1 - Camadas Física e de Enlace")
            self.geometry("1200x750")
            self.protocol("WM_DELETE_WINDOW", self.destroy)
            self.configure(bg=COR_FUNDO)
            self.configurar_tema()

            raiz = tk.Frame(self, bg=COR_FUNDO, padx=8, pady=8)
            raiz.pack(fill=tk.BOTH, expand=True)

            self.montar_painel_config(raiz)
            self.montar_painel_resultados(raiz)
            self.lbl_status.config(text="Pronto. Ajuste os parâmetros e clique em Transmitir.")
            self.set_texto(self.txt_tx, "Transmissor (Tx)\n\nClique em Transmitir para gerar bits e sinais.")
            self.set_texto(self.txt_rx, "Receptor (Rx)\n\nClique em Transmitir para recuperar a mensagem.")

        # ── Construção ────────────────────────────────────────────────────

        def configurar_tema(self):
            """Define defaults legíveis no Tk antigo do macOS em modo escuro."""
            self.option_add("*Background", COR_PAINEL)
            self.option_add("*Foreground", COR_TEXTO)
            self.option_add("*Entry.Background", COR_CAMPO)
            self.option_add("*Text.Background", COR_CAMPO)
            self.option_add("*selectBackground", COR_BOTAO)
            self.option_add("*selectForeground", COR_TEXTO)

        def montar_painel_config(self, parent):
            frame = tk.LabelFrame(parent, text="Configuração", bg=COR_PAINEL,
                                  fg=COR_TEXTO, padx=8, pady=8,
                                  highlightbackground=COR_BORDA,
                                  highlightcolor=COR_BORDA)
            frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

            linha = 0

            def adicionar(rotulo_texto, widget):
                nonlocal linha
                tk.Label(frame, text=rotulo_texto, anchor="w", bg=COR_PAINEL,
                         fg=COR_TEXTO).grid(
                    row=linha, column=0, sticky="w", padx=2, pady=3)
                widget.grid(row=linha, column=1, sticky="we", padx=2, pady=3)
                linha += 1

            self.entrada_texto = tk.Entry(frame, width=24, bg=COR_PAINEL,
                                          fg=COR_TEXTO,
                                          insertbackground=COR_TEXTO,
                                          highlightthickness=1,
                                          highlightbackground=COR_BORDA,
                                          highlightcolor=COR_LINHA)
            self.entrada_texto.insert(0, "Ola, TR1!")
            adicionar("Texto de entrada:", self.entrada_texto)

            self.spin_quadro = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                         fg=COR_TEXTO,
                                         insertbackground=COR_TEXTO,
                                         highlightthickness=1,
                                         highlightbackground=COR_BORDA,
                                         highlightcolor=COR_LINHA)
            self.spin_quadro.delete(0, tk.END)
            self.spin_quadro.insert(0, "8")
            adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

            self.combo_enq = self.novo_combo(frame, OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento:", self.combo_enq)

            self.combo_det = self.novo_combo(frame, OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros:", self.combo_det)

            self.combo_cor = self.novo_combo(frame, OPCOES_CORRECAO, 1)
            adicionar("Correção de erros:", self.combo_cor)

            self.combo_dig = self.novo_combo(frame, OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital:", self.combo_dig)

            self.combo_port = self.novo_combo(frame, OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora:", self.combo_port)

            self.spin_media = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                       fg=COR_TEXTO,
                                       insertbackground=COR_TEXTO,
                                       highlightthickness=1,
                                       highlightbackground=COR_BORDA,
                                       highlightcolor=COR_LINHA)
            self.spin_media.delete(0, tk.END)
            self.spin_media.insert(0, "0.00")
            adicionar("Ruído - média x (V):", self.spin_media)

            self.spin_sigma = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                       fg=COR_TEXTO,
                                       insertbackground=COR_TEXTO,
                                       highlightthickness=1,
                                       highlightbackground=COR_BORDA,
                                       highlightcolor=COR_LINHA)
            self.spin_sigma.delete(0, tk.END)
            self.spin_sigma.insert(0, "0.10")
            adicionar("Ruído - desvio σ (V):", self.spin_sigma)

            tk.Button(frame, text="Transmitir", command=self.ao_transmitir,
                      bg=COR_BOTAO, fg=COR_TEXTO,
                      activebackground=COR_BOTAO_ATIVO,
                      activeforeground=COR_TEXTO,
                      relief=tk.FLAT).grid(
                row=linha, column=0, columnspan=2, sticky="we", pady=10)
            linha += 1

            self.lbl_status = tk.Label(
                frame, text="", wraplength=220, justify="left", anchor="nw",
                bg=COR_PAINEL, fg=COR_TEXTO)
            self.lbl_status.grid(row=linha, column=0, columnspan=2, sticky="w")

        def novo_combo(self, parent, opcoes, indice_padrao):
            valores = [r for r, _ in opcoes]
            var = tk.StringVar(parent)
            var.set(valores[indice_padrao])
            combo = tk.OptionMenu(parent, var, *valores)
            combo.config(width=22, anchor="w", bg=COR_CAMPO, fg=COR_TEXTO,
                         activebackground=COR_BOTAO,
                         activeforeground=COR_TEXTO,
                         highlightthickness=1,
                         highlightbackground=COR_BORDA,
                         relief=tk.FLAT)
            combo["menu"].config(bg=COR_CAMPO, fg=COR_TEXTO,
                                 activebackground=COR_BOTAO,
                                 activeforeground=COR_TEXTO)
            combo._var = var
            combo._valor_por_rotulo = {rotulo: valor for rotulo, valor in opcoes}
            return combo

        @staticmethod
        def valor_combo(combo):
            return combo._valor_por_rotulo[combo._var.get()]

        def montar_painel_resultados(self, parent):
            painel = tk.Frame(parent, bg=COR_FUNDO)
            painel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tab_tx = tk.LabelFrame(painel, text="Transmissor (Tx)",
                                   bg=COR_PAINEL, fg=COR_TEXTO, padx=6, pady=6)
            tab_tx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
            self.txt_tx, self.fig_tx, self.canvas_tx = self.criarmontar_aba(tab_tx)

            tab_rx = tk.LabelFrame(painel, text="Receptor (Rx)",
                                   bg=COR_PAINEL, fg=COR_TEXTO, padx=6, pady=6)
            tab_rx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
            self.txt_rx, self.fig_rx, self.canvas_rx = self.criarmontar_aba(tab_rx)

        def criarmontar_aba(self, parent):
            txt_frame = tk.Frame(parent, bg=COR_PAINEL)
            txt_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            txt = tk.Text(txt_frame, wrap=tk.CHAR, font=("Courier", 9),
                          yscrollcommand=scrollbar.set, height=13,
                          state=tk.DISABLED, bg=COR_CAMPO, fg=COR_TEXTO,
                          insertbackground=COR_TEXTO,
                          relief=tk.SOLID, borderwidth=1)
            txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=txt.yview)

            fig = Figure(figsize=(7, 4), facecolor=COR_PAINEL)
            canvas = FigureCanvas(fig, master=parent)
            canvas.get_tk_widget().configure(bg=COR_PAINEL, highlightthickness=0)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            return txt, fig, canvas

        # ── Lógica ────────────────────────────────────────────────────────

        def ler_config(self):
            return {
                "texto": self.entrada_texto.get(),
                "tam_max_quadro": int(self.spin_quadro.get()),
                "enquadramento": self.valor_combo(self.combo_enq),
                "deteccao": self.valor_combo(self.combo_det),
                "correcao": self.valor_combo(self.combo_cor),
                "mod_digital": self.valor_combo(self.combo_dig),
                "mod_portadora": self.valor_combo(self.combo_port),
                "ruido_media": float(self.spin_media.get()),
                "ruido_sigma": float(self.spin_sigma.get()),
            }

        def ao_transmitir(self):
            config = self.ler_config()
            if not config["texto"]:
                self.lbl_status.config(text="Digite um texto para transmitir.")
                return
            try:
                resultado = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.config(text=f"Erro: {erro}")
                return

            texto_tx = (
                f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(resultado['tx_bits_aplicacao'])} bits):\n"
                f"{bits_str(resultado['tx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE BITS - ENLACE/quadros ({len(resultado['tx_bits_enlace'])} bits):\n"
                f"{bits_str(resultado['tx_bits_enlace'])}\n"
            )
            self.set_texto(self.txt_tx, texto_tx)
            self.plotar(self.fig_tx, self.canvas_tx,
                        ("Sinal banda-base (Tx)", resultado["tx_sinal_banda_base"]),
                        ("Sinal transmitido ao meio (Tx)", resultado["tx_sinal_transmitido"]))

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
            self.set_texto(self.txt_rx, texto_rx)
            self.plotar(self.fig_rx, self.canvas_rx,
                        ("Sinal recebido com ruído (Rx)", resultado["rx_sinal_recebido"]),
                        ("Banda-base reconstruído (Rx)", resultado["rx_sinal_banda_base"]))

            ok = (resultado["rx_texto"] == config["texto"])
            pot_sinal = resultado["potencia_sinal_w"]
            pot_ruido = resultado["potencia_ruido_w"]
            self.lbl_status.config(
                text=(f"Potência do sinal: {pot_sinal:.3f} W | do ruído: {pot_ruido:.4f} W\n"
                      f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}."))

        @staticmethod
        def set_texto(widget, conteudo):
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.insert(tk.END, conteudo)
            widget.config(state=tk.DISABLED)

        @staticmethod
        def plotar(figura, canvas, *series):
            figura.clear()
            figura.patch.set_facecolor(COR_PAINEL)
            num_series = len(series)
            for k, (titulo, sinal) in enumerate(series, start=1):
                eixo = figura.add_subplot(num_series, 1, k)
                eixo.set_facecolor(COR_PAINEL)
                eixo.plot(sinal[:MAX_AMOSTRAS_GRAFICO], linewidth=0.9,
                          color=COR_LINHA)
                eixo.set_title(titulo, fontsize=9, color=COR_TEXTO)
                eixo.set_ylabel("V", fontsize=8, color=COR_TEXTO_SECUNDARIO)
                eixo.tick_params(labelsize=7, colors=COR_TEXTO_SECUNDARIO)
                eixo.grid(True, color=COR_BORDA, linewidth=0.35, alpha=0.7)
                for spine in eixo.spines.values():
                    spine.set_color(COR_BORDA)
            figura.tight_layout()
            canvas.draw()

        def executar(self):
            self.mainloop()

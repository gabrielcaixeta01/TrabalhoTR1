"""
InterfaceGUI.py — Interface gráfica GTK para o simulador TR1.
Exibe formas de onda via matplotlib embutido no GTK.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import numpy as np
import matplotlib
matplotlib.use("GTK3Agg")
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure


class JanelaPrincipal(Gtk.Window):

    def __init__(self, callback_transmitir):
        """
        callback_transmitir(config) → (sinal_tx, sinal_rx, bits_tx, bits_rx)
        config: dict com todas as opções selecionadas pelo usuário.
        """
        super().__init__(title="Simulador TR1")
        self.callback_transmitir = callback_transmitir
        self.set_default_size(1100, 700)
        self.connect("destroy", Gtk.main_quit)

        raiz = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        raiz.set_margin_start(10)
        raiz.set_margin_end(10)
        raiz.set_margin_top(10)
        raiz.set_margin_bottom(10)
        self.add(raiz)

        raiz.pack_start(self._painel_config(), False, False, 0)
        raiz.pack_start(self._painel_grafico(), True, True, 0)

    # ─── Painel de configuração ────────────────────────────────────────────────

    def _painel_config(self) -> Gtk.Box:
        painel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        painel.set_size_request(260, -1)

        painel.pack_start(Gtk.Label(label="<b>Configurações</b>",
                                    use_markup=True), False, False, 4)

        # Mensagem
        painel.pack_start(Gtk.Label(label="Mensagem:", xalign=0), False, False, 0)
        self.entrada_msg = Gtk.Entry()
        self.entrada_msg.set_text("Hello TR1")
        painel.pack_start(self.entrada_msg, False, False, 0)

        # Tamanho máximo do quadro
        painel.pack_start(Gtk.Label(label="Tamanho máx. do quadro (bytes):",
                                    xalign=0), False, False, 0)
        self.spin_quadro = Gtk.SpinButton.new_with_range(1, 256, 1)
        self.spin_quadro.set_value(8)
        painel.pack_start(self.spin_quadro, False, False, 0)

        # Tamanho do EDC
        painel.pack_start(Gtk.Label(label="Tamanho EDC:", xalign=0), False, False, 0)
        self.spin_edc = Gtk.SpinButton.new_with_range(1, 32, 1)
        self.spin_edc.set_value(8)
        painel.pack_start(self.spin_edc, False, False, 0)

        # Tipo de enquadramento
        painel.pack_start(Gtk.Label(label="Enquadramento:", xalign=0), False, False, 0)
        self.combo_enquad = Gtk.ComboBoxText()
        for op in ["Contagem de caracteres",
                   "Flags + inserção de bytes",
                   "Flags + inserção de bits"]:
            self.combo_enquad.append_text(op)
        self.combo_enquad.set_active(0)
        painel.pack_start(self.combo_enquad, False, False, 0)

        # Detecção / correção de erros
        painel.pack_start(Gtk.Label(label="Detecção/Correção:", xalign=0), False, False, 0)
        self.combo_edc = Gtk.ComboBoxText()
        for op in ["Paridade par", "Checksum", "CRC-32", "Hamming"]:
            self.combo_edc.append_text(op)
        self.combo_edc.set_active(0)
        painel.pack_start(self.combo_edc, False, False, 0)

        # Modulação digital (banda-base)
        painel.pack_start(Gtk.Label(label="Modulação digital:", xalign=0), False, False, 0)
        self.combo_mod_digital = Gtk.ComboBoxText()
        for op in ["NRZ-Polar", "Manchester", "Bipolar"]:
            self.combo_mod_digital.append_text(op)
        self.combo_mod_digital.set_active(0)
        painel.pack_start(self.combo_mod_digital, False, False, 0)

        # Modulação analógica (por portadora)
        painel.pack_start(Gtk.Label(label="Modulação analógica:", xalign=0), False, False, 0)
        self.combo_mod_analog = Gtk.ComboBoxText()
        for op in ["Nenhuma (banda-base)", "ASK", "FSK", "PSK", "QPSK", "16-QAM"]:
            self.combo_mod_analog.append_text(op)
        self.combo_mod_analog.set_active(0)
        painel.pack_start(self.combo_mod_analog, False, False, 0)

        # Ruído (desvio padrão em V)
        painel.pack_start(Gtk.Label(label="Ruído σ (V):", xalign=0), False, False, 0)
        self.spin_ruido = Gtk.SpinButton.new_with_range(0.0, 5.0, 0.05)
        self.spin_ruido.set_digits(2)
        self.spin_ruido.set_value(0.1)
        painel.pack_start(self.spin_ruido, False, False, 0)

        # Botão transmitir
        btn = Gtk.Button(label="Transmitir")
        btn.connect("clicked", self._on_transmitir)
        painel.pack_start(btn, False, False, 8)

        # Label de status
        self.label_status = Gtk.Label(label="Aguardando transmissão…", xalign=0)
        self.label_status.set_line_wrap(True)
        painel.pack_start(self.label_status, False, False, 0)

        return painel

    # ─── Painel gráfico ────────────────────────────────────────────────────────

    def _painel_grafico(self) -> FigureCanvas:
        self.figura = Figure(figsize=(8, 6), layout="tight")
        self.canvas = FigureCanvas(self.figura)
        return self.canvas

    def _atualizar_graficos(self, sinal_tx: np.ndarray, sinal_rx: np.ndarray,
                             sinal_canal: np.ndarray) -> None:
        """Redesenha os subplots TX / Canal / RX."""
        self.figura.clear()

        ax1 = self.figura.add_subplot(3, 1, 1)
        ax1.plot(sinal_tx, color="steelblue", linewidth=0.8)
        ax1.set_title("Sinal Transmitido (TX)")
        ax1.set_ylabel("Amplitude (V)")
        ax1.grid(True, linestyle="--", alpha=0.4)

        ax2 = self.figura.add_subplot(3, 1, 2)
        ax2.plot(sinal_canal, color="tomato", linewidth=0.8)
        ax2.set_title("Sinal no Canal (com ruído)")
        ax2.set_ylabel("Amplitude (V)")
        ax2.grid(True, linestyle="--", alpha=0.4)

        ax3 = self.figura.add_subplot(3, 1, 3)
        ax3.plot(sinal_rx, color="seagreen", linewidth=0.8)
        ax3.set_title("Sinal Recebido (RX demodulado)")
        ax3.set_ylabel("Amplitude (V)")
        ax3.set_xlabel("Amostras")
        ax3.grid(True, linestyle="--", alpha=0.4)

        self.canvas.draw()

    # ─── Callbacks ────────────────────────────────────────────────────────────

    def _on_transmitir(self, _botao) -> None:
        """Lê configurações, chama o simulador e atualiza a GUI."""
        config = {
            "mensagem":     self.entrada_msg.get_text(),
            "tamanho_quad": int(self.spin_quadro.get_value()),
            "tamanho_edc":  int(self.spin_edc.get_value()),
            "enquadramento": self.combo_enquad.get_active_text(),
            "edc":           self.combo_edc.get_active_text(),
            "mod_digital":   self.combo_mod_digital.get_active_text(),
            "mod_analog":    self.combo_mod_analog.get_active_text(),
            "ruido_sigma":   self.spin_ruido.get_value(),
        }
        try:
            sinal_tx, sinal_canal, sinal_rx, msg_rx = self.callback_transmitir(config)
            self._atualizar_graficos(sinal_tx, sinal_rx, sinal_canal)
            status = f"RX: {msg_rx!r}"
            if msg_rx == config["mensagem"]:
                status += " ✓ (sem erros)"
            else:
                status += " ✗ (erro detectado)"
            self.label_status.set_text(status)
        except Exception as exc:
            self.label_status.set_text(f"Erro: {exc}")


def iniciar(callback_transmitir) -> None:
    """Cria a janela principal e inicia o loop GTK."""
    janela = JanelaPrincipal(callback_transmitir)
    janela.show_all()
    Gtk.main()

# -*- coding: utf-8 -*-
"""
Gera as imagens para o relatório LaTeX.
Executar da raiz do projeto: python gerar_imagens_relatorio.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import math

import camada_fisica as fisica
import meio_comunicacao as meio

OUT = os.path.join(os.path.dirname(__file__), "relatorio")
BITS_DEMO = [1, 0, 1, 1, 0, 0, 1, 0]


# ---------------------------------------------------------------------------
# 1. sinais_banda_base.png
# ---------------------------------------------------------------------------
def gerar_sinais_banda_base():
    N = fisica.AMOSTRAS_POR_BIT
    bits = BITS_DEMO
    sinais = [
        (fisica.modular_nrz_polar(bits),  "NRZ-Polar"),
        (fisica.modular_manchester(bits), "Manchester"),
        (fisica.modular_bipolar(bits),    "Bipolar (AMI)"),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
    x = list(range(len(sinais[0][0])))

    for ax, (sinal, titulo) in zip(axes, sinais):
        ax.plot(x, sinal, linewidth=1.4, color="#2874a6")
        ax.set_title(titulo, fontsize=11, fontweight="bold")
        ax.set_ylabel("Tensão (V)", fontsize=9)
        ax.set_ylim(-1.4, 1.6)
        ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
        # rótulo de cada bit no topo
        for i, bit in enumerate(bits):
            ax.text(i * N + N / 2, 1.35, str(bit),
                    ha="center", va="bottom", fontsize=10,
                    color="#c0392b", fontweight="bold")
        # separadores entre bits
        for i in range(len(bits) + 1):
            ax.axvline(i * N, color="#aaaaaa", linewidth=0.4, linestyle=":")
        ax.tick_params(labelsize=8)
        ax.set_yticks([-1, 0, 1])

    axes[-1].set_xlabel("Amostras", fontsize=9)
    fig.suptitle(f"Modulações Banda-Base  —  bits transmitidos: {''.join(map(str, bits))}",
                 fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "sinais_banda_base.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK sinais_banda_base.png")


# ---------------------------------------------------------------------------
# 2. constelacoes_portadora.png
# ---------------------------------------------------------------------------
def gerar_constelacoes_portadora():
    V = fisica.V
    A_QPSK = V / math.sqrt(2)
    escala_qam = V / 3

    # pontos QPSK com labels Gray
    qpsk_pts = {
        "00": ( A_QPSK,  A_QPSK),
        "01": (-A_QPSK,  A_QPSK),
        "11": (-A_QPSK, -A_QPSK),
        "10": ( A_QPSK, -A_QPSK),
    }

    # pontos 16-QAM
    niveis = {(0,0):-3, (0,1):-1, (1,1):1, (1,0):3}
    qam16_pts = {}
    for (b0,b1), ni in niveis.items():
        for (b2,b3), nq in niveis.items():
            label = f"{b0}{b1}{b2}{b3}"
            qam16_pts[label] = (ni * escala_qam, nq * escala_qam)

    # sinais ASK e FSK para 6 bits
    bits6 = [1, 0, 1, 0, 1, 1]
    sinal_ask = fisica.modular_ask(bits6)
    sinal_fsk = fisica.modular_fsk(bits6)
    N = fisica.AMOSTRAS_POR_SIMBOLO
    x6 = list(range(len(sinal_ask)))

    fig = plt.figure(figsize=(12, 9))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    # ── QPSK ──
    ax1 = fig.add_subplot(gs[0, 0])
    for label, (xi, qi) in qpsk_pts.items():
        ax1.scatter(xi, qi, s=120, color="#1a5276", zorder=5)
        ax1.annotate(label, (xi, qi), textcoords="offset points",
                     xytext=(6, 6), fontsize=9, color="#1a5276")
    circ = plt.Circle((0, 0), V, fill=False, linestyle="--",
                       color="#aaaaaa", linewidth=0.8)
    ax1.add_patch(circ)
    ax1.axhline(0, color="gray", linewidth=0.5)
    ax1.axvline(0, color="gray", linewidth=0.5)
    ax1.set_xlim(-1.4, 1.4); ax1.set_ylim(-1.4, 1.4)
    ax1.set_aspect("equal")
    ax1.set_title("Constelação QPSK  (2 bits/símbolo)", fontsize=10, fontweight="bold")
    ax1.set_xlabel("I"); ax1.set_ylabel("Q")
    ax1.tick_params(labelsize=8)

    # ── 16-QAM ──
    ax2 = fig.add_subplot(gs[0, 1])
    for label, (xi, qi) in qam16_pts.items():
        ax2.scatter(xi, qi, s=80, color="#1a5276", zorder=5)
        ax2.annotate(label, (xi, qi), textcoords="offset points",
                     xytext=(3, 4), fontsize=7, color="#1a5276")
    ax2.axhline(0, color="gray", linewidth=0.5)
    ax2.axvline(0, color="gray", linewidth=0.5)
    ax2.set_xlim(-1.4, 1.4); ax2.set_ylim(-1.4, 1.4)
    ax2.set_aspect("equal")
    ax2.set_title("Constelação 16-QAM  (4 bits/símbolo)", fontsize=10, fontweight="bold")
    ax2.set_xlabel("I"); ax2.set_ylabel("Q")
    ax2.tick_params(labelsize=8)

    # ── ASK ──
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(x6, sinal_ask, linewidth=1.2, color="#117a65")
    ax3.set_title(f"ASK — bits: {''.join(map(str,bits6))}", fontsize=10, fontweight="bold")
    ax3.set_ylabel("V"); ax3.set_xlabel("Amostras")
    for i, b in enumerate(bits6):
        ax3.text(i*N + N/2, 1.1, str(b), ha="center", fontsize=9,
                 color="#c0392b", fontweight="bold")
        ax3.axvline(i*N, color="#aaaaaa", linewidth=0.4, linestyle=":")
    ax3.axvline(len(bits6)*N, color="#aaaaaa", linewidth=0.4, linestyle=":")
    ax3.set_ylim(-1.3, 1.4); ax3.tick_params(labelsize=8)

    # ── FSK ──
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(x6, sinal_fsk, linewidth=1.2, color="#7d3c98")
    ax4.set_title(f"FSK — bits: {''.join(map(str,bits6))}", fontsize=10, fontweight="bold")
    ax4.set_ylabel("V"); ax4.set_xlabel("Amostras")
    for i, b in enumerate(bits6):
        ax4.text(i*N + N/2, 1.1, str(b), ha="center", fontsize=9,
                 color="#c0392b", fontweight="bold")
        ax4.axvline(i*N, color="#aaaaaa", linewidth=0.4, linestyle=":")
    ax4.axvline(len(bits6)*N, color="#aaaaaa", linewidth=0.4, linestyle=":")
    ax4.set_ylim(-1.3, 1.4); ax4.tick_params(labelsize=8)

    fig.suptitle("Modulações por Portadora", fontsize=13, fontweight="bold")
    fig.savefig(os.path.join(OUT, "constelacoes_portadora.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK constelacoes_portadora.png")


# ---------------------------------------------------------------------------
# 3. sinal_com_ruido.png
# ---------------------------------------------------------------------------
def gerar_sinal_com_ruido():
    bits = BITS_DEMO
    sinal_tx = fisica.modular_qpsk(bits)
    sinal_rx_limpo = fisica.modular_qpsk(bits)  # para mostrar overlay
    sinal_rx = meio.transmitir(sinal_tx, media=0.0, sigma=0.25)

    N = fisica.AMOSTRAS_POR_SIMBOLO
    mostrar = 4 * N  # mostra 4 símbolos
    x = list(range(mostrar))

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)

    axes[0].plot(x, sinal_tx[:mostrar], linewidth=1.4, color="#2874a6", label="Sinal TX (limpo)")
    axes[0].set_title("Sinal transmitido (QPSK, sem ruído)", fontsize=10, fontweight="bold")
    axes[0].set_ylabel("V"); axes[0].set_ylim(-1.5, 1.5)
    axes[0].axhline(0, color="gray", linewidth=0.5, linestyle="--")
    axes[0].tick_params(labelsize=8)

    axes[1].plot(x, sinal_rx[:mostrar], linewidth=0.9, color="#cb4335",
                 alpha=0.85, label="Sinal RX (com ruído σ=0.25)")
    axes[1].plot(x, sinal_tx[:mostrar], linewidth=1.2, color="#2874a6",
                 alpha=0.5, linestyle="--", label="Sinal TX (referência)")
    axes[1].set_title("Sinal recebido com ruído gaussiano (σ = 0,25 V)", fontsize=10, fontweight="bold")
    axes[1].set_ylabel("V"); axes[1].set_xlabel("Amostras")
    axes[1].set_ylim(-1.8, 1.8)
    axes[1].axhline(0, color="gray", linewidth=0.5, linestyle="--")
    axes[1].legend(fontsize=8, loc="upper right")
    axes[1].tick_params(labelsize=8)

    for ax in axes:
        for i in range(5):
            ax.axvline(i * N, color="#aaaaaa", linewidth=0.4, linestyle=":")

    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "sinal_com_ruido.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK sinal_com_ruido.png")


# ---------------------------------------------------------------------------
# 4. diagrama_pilha.png
# ---------------------------------------------------------------------------
def gerar_diagrama_pilha():
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7)
    ax.axis("off")

    def caixa(ax, x, y, w, h, texto, cor_fundo, cor_borda="#333333", fontsize=10):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.08",
            facecolor=cor_fundo, edgecolor=cor_borda, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, texto,
                ha="center", va="center", fontsize=fontsize, fontweight="bold")

    def seta(ax, x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.5))

    # Colunas: TX (x=0.3), MEIO (x=4.3), RX (x=7.8)
    # Camadas de cima para baixo
    camadas_tx = [
        ("Aplicação\n(texto → bits)", "#d6eaf8"),
        ("Enlace\n(EDC + Hamming\n+ Enquadramento)", "#d5f5e3"),
        ("Física\n(Banda-base\n+ Portadora)", "#fdebd0"),
    ]
    camadas_rx = [
        ("Aplicação\n(bits → texto)", "#d6eaf8"),
        ("Enlace\n(Desenquadrar\n+ Hamming + EDC)", "#d5f5e3"),
        ("Física\n(Demod. Banda-base\n+ Portadora)", "#fdebd0"),
    ]

    ys = [4.8, 2.8, 0.7]
    h = 1.7; w = 2.8

    for (texto, cor), y in zip(camadas_tx, ys):
        caixa(ax, 0.2, y, w, h, texto, cor, fontsize=9)
    for (texto, cor), y in zip(camadas_rx, ys):
        caixa(ax, 7.9, y, w, h, texto, cor, fontsize=9)

    # Setas TX (descendo)
    for y_top, y_bot in zip(ys[:-1], ys[1:]):
        seta(ax, 1.6, y_top, 1.6, y_bot + h)

    # Setas RX (subindo)
    for y_top, y_bot in zip(ys[:-1], ys[1:]):
        seta(ax, 9.3, y_bot + h, 9.3, y_top)

    # Bloco do canal
    caixa(ax, 3.8, 0.7, 3.3, 1.7,
          "Canal (Meio)\n+ ruído gaussiano\nn(x, σ)", "#f9ebea",
          cor_borda="#922b21", fontsize=9)

    # Seta TX → canal
    seta(ax, 3.0, 1.55, 3.8, 1.55)
    # Seta canal → RX
    seta(ax, 7.1, 1.55, 7.9, 1.55)

    # Títulos das colunas
    ax.text(1.6, 6.8, "TRANSMISSOR (TX)", ha="center", fontsize=11,
            fontweight="bold", color="#1a5276")
    ax.text(5.45, 6.8, "MEIO", ha="center", fontsize=11,
            fontweight="bold", color="#922b21")
    ax.text(9.3, 6.8, "RECEPTOR (RX)", ha="center", fontsize=11,
            fontweight="bold", color="#1a5276")

    # Rótulos de fluxo
    ax.text(3.4, 1.75, "sinal (V)", ha="center", fontsize=8, color="#555555", style="italic")
    ax.text(7.5, 1.75, "sinal+ruído (V)", ha="center", fontsize=8, color="#555555", style="italic")

    fig.suptitle("Diagrama de Pilha — Fluxo TX → Meio → RX", fontsize=13, fontweight="bold", y=0.98)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "diagrama_pilha.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK diagrama_pilha.png")


# ---------------------------------------------------------------------------
# 5. hamming_8_4.png
# ---------------------------------------------------------------------------
def gerar_hamming():
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(-0.5, 8.5); ax.set_ylim(-1.5, 4.5)
    ax.axis("off")

    posicoes = ["1\n(p1)", "2\n(p2)", "3\n(d1)", "4\n(p4)",
                "5\n(d2)", "6\n(d3)", "7\n(d4)", "8\n(p0)"]
    cor_paridade = "#aed6f1"
    cor_dado     = "#a9dfbf"
    cor_p0       = "#f9e79f"

    cores = [cor_paridade, cor_paridade, cor_dado, cor_paridade,
             cor_dado, cor_dado, cor_dado, cor_p0]

    # Desenha as caixas
    for i, (pos, cor) in enumerate(zip(posicoes, cores)):
        rect = mpatches.FancyBboxPatch(
            (i + 0.05, 2.5), 0.9, 1.4,
            boxstyle="round,pad=0.05",
            facecolor=cor, edgecolor="#555555", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(i + 0.5, 3.2, pos, ha="center", va="center", fontsize=10, fontweight="bold")

    # Legenda das cores
    ax.text(-0.3, 2.3, "Legenda:", fontsize=9, fontweight="bold")
    for cor, label, xi in [
        (cor_paridade, "Bit de paridade (p1, p2, p4)", 1.0),
        (cor_dado,     "Bit de dado (d1–d4)",          3.8),
        (cor_p0,       "Paridade geral (p0 — SECDED)", 6.2),
    ]:
        r = mpatches.Rectangle((xi, 1.95), 0.3, 0.25, facecolor=cor, edgecolor="#555555")
        ax.add_patch(r)
        ax.text(xi + 0.4, 2.07, label, fontsize=8.5, va="center")

    # Cobertura das paridades (arcos/linhas abaixo)
    coberturas = [
        ("p1 cobre: 1,3,5,7", [0, 2, 4, 6], "#2874a6"),
        ("p2 cobre: 2,3,6,7", [1, 2, 5, 6], "#1e8449"),
        ("p4 cobre: 4,5,6,7", [3, 4, 5, 6], "#7d3c98"),
    ]
    ys_linha = [1.3, 0.7, 0.1]
    for (label, indices, cor), y in zip(coberturas, ys_linha):
        xs = [i + 0.5 for i in indices]
        ax.plot(xs, [y]*len(xs), "o-", color=cor, linewidth=2,
                markersize=6, alpha=0.8)
        ax.text(-0.4, y, label, fontsize=8.5, color=cor, va="center", fontweight="bold")
        # linhas verticais conectando ao bloco
        for xi in xs:
            ax.plot([xi, xi], [2.5, y + 0.05], "--", color=cor,
                    linewidth=0.8, alpha=0.5)

    # Fórmula da síndrome
    ax.text(4.0, -0.6,
            "Síndrome:  S = s4·4 + s2·2 + s1   →   posição do bit errado (1 a 7)",
            ha="center", fontsize=10, style="italic",
            bbox=dict(boxstyle="round", facecolor="#fdfefe", edgecolor="#aaaaaa"))

    fig.suptitle("Código Hamming(8,4) estendido (SECDED) — layout dos 8 bits", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "hamming_8_4.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK hamming_8_4.png")


# ---------------------------------------------------------------------------
# 6. qpsk_com_ruido.png  (imagem extra sugerida: diagrama de olho / dispersão)
# ---------------------------------------------------------------------------
def gerar_dispersao_ruido():
    """Mostra como o ruído desloca os pontos da constelação QPSK."""
    import random
    random.seed(42)

    V = fisica.V
    A = V / math.sqrt(2)
    qpsk = [(A, A), (-A, A), (-A, -A), (A, -A)]
    sigmas = [0.0, 0.10, 0.25]
    NUM_SIMBOLOS = 200

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, sigma in zip(axes, sigmas):
        for (I, Q) in qpsk:
            Is = [I + random.gauss(0, sigma) for _ in range(NUM_SIMBOLOS // 4)]
            Qs = [Q + random.gauss(0, sigma) for _ in range(NUM_SIMBOLOS // 4)]
            ax.scatter(Is, Qs, s=8, alpha=0.6, color="#1a5276")
        # pontos ideais
        for (I, Q) in qpsk:
            ax.scatter(I, Q, s=80, color="#cb4335", zorder=5, marker="x", linewidths=2)
        circ = plt.Circle((0, 0), V, fill=False, linestyle="--",
                           color="#aaaaaa", linewidth=0.8)
        ax.add_patch(circ)
        ax.axhline(0, color="gray", linewidth=0.4)
        ax.axvline(0, color="gray", linewidth=0.4)
        ax.set_xlim(-1.6, 1.6); ax.set_ylim(-1.6, 1.6)
        ax.set_aspect("equal")
        ax.set_title(f"σ = {sigma:.2f} V", fontsize=10, fontweight="bold")
        ax.set_xlabel("I"); ax.set_ylabel("Q")
        ax.tick_params(labelsize=8)

    fig.suptitle("Dispersão dos símbolos QPSK com diferentes níveis de ruído", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "qpsk_dispersao_ruido.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("OK qpsk_dispersao_ruido.png")


# ---------------------------------------------------------------------------
# Executa tudo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    gerar_sinais_banda_base()
    gerar_constelacoes_portadora()
    gerar_sinal_com_ruido()
    gerar_diagrama_pilha()
    gerar_hamming()
    gerar_dispersao_ruido()
    print("\nTodas as imagens geradas em:", OUT)

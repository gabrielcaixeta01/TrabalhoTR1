"""
camada física do simulador.

os bits são convertidos em amostras de tensão. primeiro pode haver uma
codificação em banda-base; depois, se configurado, os mesmos bits são
modulados em uma portadora ask, fsk, qpsk ou 16-qam.
"""

import math

V = 1.0                      # amplitude de referência do sinal, em volts
AMOSTRAS_POR_BIT = 100       # resolução do sinal banda-base
AMOSTRAS_POR_SIMBOLO = 100   # resolução de cada símbolo da portadora
CICLOS_PORTADORA = 4         # ciclos de portadora por símbolo
CICLOS_FSK = (2, 4)          # fsk: f1 (bit 0) e f2 (bit 1), em ciclos/símbolo


# modulação digital em banda-base
def modular_nrz_polar(bits):
    """nrz-polar: bit 1 vira +v e bit 0 vira -v."""
    sinal = []
    for bit in bits:
        if bit == 1:
            nivel = V
        else:
            nivel = -V
        sinal += [nivel] * AMOSTRAS_POR_BIT
    return sinal


def demodular_nrz_polar(sinal):
    """decide cada bit pela média das amostras."""
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        if media > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_manchester(bits):
    """manchester: bit 0 sobe no meio; bit 1 desce no meio."""
    metade = AMOSTRAS_POR_BIT // 2
    sinal = []
    for bit in bits:
        if bit == 0:
            sinal += [-V] * metade + [V] * (AMOSTRAS_POR_BIT - metade)
        else:
            sinal += [V] * metade + [-V] * (AMOSTRAS_POR_BIT - metade)
    return sinal


def demodular_manchester(sinal):
    """compara as médias das duas metades de cada bit."""
    metade = AMOSTRAS_POR_BIT // 2
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        m1 = sum(sinal[k:k + metade]) / metade
        m2 = sum(sinal[k + metade:k + AMOSTRAS_POR_BIT]) / (AMOSTRAS_POR_BIT - metade)
        if m1 > m2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_bipolar(bits):
    """bipolar ami: bit 0 vira 0 v; bits 1 alternam +v e -v."""
    sinal = []
    polaridade = V
    for bit in bits:
        if bit == 0:
            sinal += [0.0] * AMOSTRAS_POR_BIT
        else:
            sinal += [polaridade] * AMOSTRAS_POR_BIT
            polaridade = -polaridade
    return sinal


def demodular_bipolar(sinal):
    """decide pelo módulo da média de cada intervalo."""
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        if abs(media) > V / 2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


# modulação por portadora
def onda(i, q, ciclos):
    """gera um símbolo por i/q: s(t) = i*cos(wt) - q*sin(wt)."""
    N = AMOSTRAS_POR_SIMBOLO
    amostras = []
    for n in range(N):
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
    return amostras


def correlacionar(simbolo, ciclos):
    """estima as componentes i/q por correlação com a portadora."""
    N = len(simbolo)
    soma_cos = 0.0
    soma_sen = 0.0
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / N
        soma_cos += amostra * math.cos(angulo)
        soma_sen += amostra * math.sin(angulo)
    i = 2 / N * soma_cos
    q = -2 / N * soma_sen
    return i, q


def pad(bits, tamanho):
    """completa com zeros até fechar um símbolo inteiro."""
    resto = len(bits) % tamanho
    if resto == 0:
        return bits                         
    faltam = tamanho - resto
    return bits + [0] * faltam


def bits_do_ponto_mais_proximo(i, q, constelacao):
    """escolhe os bits do ponto mais próximo na constelação."""
    melhor_bits = None
    menor_dist = None
    for bits_simbolo, (i_ref, q_ref) in constelacao.items():
        dist = (i_ref - i) ** 2 + (q_ref - q) ** 2
        if menor_dist is None or dist < menor_dist:
            menor_dist = dist
            melhor_bits = bits_simbolo
    return list(melhor_bits)


def modular_ask(bits):
    """ask: bit 1 transmite portadora; bit 0 transmite amplitude zero."""
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, CICLOS_PORTADORA)
        else:
            sinal += onda(0.0, 0.0, CICLOS_PORTADORA)
    return sinal


def demodular_ask(sinal):
    """decide ask pela amplitude estimada do símbolo."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        if math.hypot(i, q) > V / 2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_fsk(bits):
    """fsk: bit 0 e bit 1 usam frequências diferentes."""
    f0, f1 = CICLOS_FSK
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, f1)
        else:
            sinal += onda(V, 0.0, f0)
    return sinal


def demodular_fsk(sinal):
    """decide fsk comparando a energia nas duas frequências."""
    f0, f1 = CICLOS_FSK
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        simbolo = sinal[k:k + N]
        e0 = math.hypot(*correlacionar(simbolo, f0))
        e1 = math.hypot(*correlacionar(simbolo, f1))
        if e1 > e0:
            bits.append(1)
        else:
            bits.append(0)
    return bits


# qpsk usa mapeamento gray: pontos vizinhos mudam só um bit.
A_QPSK = V / math.sqrt(2)
MAPA_QPSK = {(0, 0): (A_QPSK, A_QPSK), (0, 1): (-A_QPSK, A_QPSK),
              (1, 1): (-A_QPSK, -A_QPSK), (1, 0): (A_QPSK, -A_QPSK)}


def modular_qpsk(bits):
    """qpsk: agrupa bits em pares e transmite um ponto da constelação."""
    bits = pad(bits, 2)
    sinal = []
    for k in range(0, len(bits), 2):
        i, q = MAPA_QPSK[(bits[k], bits[k + 1])]
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def demodular_qpsk(sinal):
    """recupera o dibit pelo ponto qpsk mais próximo."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits += bits_do_ponto_mais_proximo(i, q, MAPA_QPSK)
    return bits


# 16-qam usa dois bits para i e dois bits para q.
NIVEIS_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
BITS_DO_NIVEL = {nivel: bits for bits, nivel in NIVEIS_GRAY.items()}
ESCALA_QAM = V / 3


def modular_16qam(bits):
    """16-qam: transmite quatro bits por símbolo em uma grade 4x4."""
    bits = pad(bits, 4)
    sinal = []
    for k in range(0, len(bits), 4):
        i = NIVEIS_GRAY[(bits[k], bits[k + 1])] * ESCALA_QAM
        q = NIVEIS_GRAY[(bits[k + 2], bits[k + 3])] * ESCALA_QAM
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def decidir_nivel_gray(valor):
    """escolhe o nível gray mais próximo de um eixo da constelação."""
    melhor_nivel = None
    menor_dist = None
    for nivel in (-3, -1, 1, 3):
        dist = abs(nivel * ESCALA_QAM - valor)
        if menor_dist is None or dist < menor_dist:
            menor_dist = dist
            melhor_nivel = nivel
    return list(BITS_DO_NIVEL[melhor_nivel])


def demodular_16qam(sinal):
    """decide 16-qam separando os eixos i e q."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits += decidir_nivel_gray(i) + decidir_nivel_gray(q)
    return bits


# despacho usado pelo simulador e pela interface
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}

MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "qpsk": (modular_qpsk, demodular_qpsk),
                        "16qam": (modular_16qam, demodular_16qam)}


def modular_digital(bits, tipo):
    """aplica a modulação banda-base escolhida."""
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    """aplica o demodulador banda-base correspondente."""
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    """aplica a modulação por portadora escolhida."""
    if tipo == "nenhuma":
        return None
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    """aplica o demodulador por portadora correspondente."""
    return MODULACOES_PORTADORA[tipo][1](sinal)

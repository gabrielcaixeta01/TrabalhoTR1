# -*- coding: utf-8 -*-
"""
Camada física.

bits -> sinais elétricos (listas de amostras em Volts) e o contrário.
Duas etapas:
  - banda-base: NRZ-Polar, Manchester e Bipolar
  - portadora:  ASK, FSK, 8PSK e 32-QAM

Na banda-base cada bit ocupa AMOSTRAS_POR_BIT amostras. Na portadora cada
símbolo ocupa AMOSTRAS_POR_SIMBOLO amostras e carrega 1 bit (ASK, FSK),
3 bits (8PSK) ou 5 bits (32-QAM). Todo modulador tem um demodulador que desfaz
a operação.

Como o receptor decide, já que o canal soma ruído em cada amostra:
  - banda-base: usa a média das amostras de cada bit (o ruído tem média ~0);
  - portadora: correlaciona com cos/sen de referência para recuperar o ponto
    (I, Q) do símbolo e escolhe o ponto da constelação mais próximo.
"""

import math

V = 1.0                      # amplitude de referência, em Volts
AMOSTRAS_POR_BIT = 100       # resolução do sinal banda-base
AMOSTRAS_POR_SIMBOLO = 100   # resolução de cada símbolo da portadora
CICLOS_PORTADORA = 4         # ciclos de portadora por símbolo (inteiro)
CICLOS_FSK = (2, 4)          # FSK: ciclos/símbolo para o bit 0 e para o bit 1


# banda base
def modular_nrz_polar(bits):
    """NRZ-Polar: bit 1 -> +V e bit 0 -> -V durante todo o tempo do bit."""
    sinal = []
    for bit in bits:
        nivel = V if bit == 1 else -V
        sinal += [nivel] * AMOSTRAS_POR_BIT
    return sinal


def demodular_nrz_polar(sinal):
    """Decide cada bit pela média da janela: acima de 0 V é 1, senão 0.

    A média diminui o efeito do ruído, que tem média perto de zero.
    """
    bits = []
    for inicio in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        janela = sinal[inicio:inicio + AMOSTRAS_POR_BIT]
        media = sum(janela) / AMOSTRAS_POR_BIT
        bits.append(1 if media > 0 else 0)
    return bits


def modular_manchester(bits):
    """Manchester: sempre há uma transição no meio do bit.

    Convenção do slide 8 do CF-10 (dado XOR clock):
        bit 0 -> -V na 1ª metade e +V na 2ª (baixo -> alto)
        bit 1 -> +V na 1ª metade e -V na 2ª (alto -> baixo)
    A IEEE 802.3 usa a convenção inversa; aqui seguimos a dos slides.
    """
    metade = AMOSTRAS_POR_BIT // 2
    resto = AMOSTRAS_POR_BIT - metade
    sinal = []
    for bit in bits:
        primeira, segunda = (V, -V) if bit == 1 else (-V, V)
        sinal += [primeira] * metade + [segunda] * resto
    return sinal


def demodular_manchester(sinal):
    """Compara a média das duas metades do bit: se caiu, é 1; se subiu, é 0.

    Comparar as metades (e não olhar o nível absoluto) funciona mesmo se o
    ruído tiver média diferente de zero.
    """
    metade = AMOSTRAS_POR_BIT // 2
    bits = []
    for inicio in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        primeira = sinal[inicio:inicio + metade]
        segunda = sinal[inicio + metade:inicio + AMOSTRAS_POR_BIT]
        m1 = sum(primeira) / len(primeira)
        m2 = sum(segunda) / len(segunda)
        bits.append(1 if m1 > m2 else 0)
    return bits


def modular_bipolar(bits):
    """Bipolar (AMI): bit 0 -> 0 V; bit 1 alterna entre +V e -V.

    O primeiro 1 é +V, o seguinte -V, e assim por diante. Com isso o nível
    médio da linha fica perto de zero.
    """
    sinal = []
    polaridade = V
    for bit in bits:
        if bit == 1:
            sinal += [polaridade] * AMOSTRAS_POR_BIT
            polaridade = -polaridade
        else:
            sinal += [0.0] * AMOSTRAS_POR_BIT
    return sinal


def demodular_bipolar(sinal):
    """Decide pelo módulo da média, já que o 1 pode vir em +V ou em -V.

    O limiar V/2 fica no meio entre os níveis 0 e V.
    """
    bits = []
    for inicio in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        janela = sinal[inicio:inicio + AMOSTRAS_POR_BIT]
        media = sum(janela) / AMOSTRAS_POR_BIT
        bits.append(1 if abs(media) > V / 2 else 0)
    return bits


# portadora 
# as modulações geram o mesmo tipo de sinal:
#       s(t) = I * cos(2*pi*f*t) - Q * sen(2*pi*f*t)
# e o que muda é o ponto (I, Q) escolhido pelos bits:
#   ASK  : (0, 0) ou (V, 0)                  -> muda a amplitude
#   FSK  : (V, 0), mas a frequência muda
#   8PSK : (V*cos(fase), V*sen(fase))        -> muda a fase
#   32QAM: ponto de uma grade em cruz        -> muda amplitude e fase

def onda(i, q, ciclos):
    """Gera um símbolo da portadora (AMOSTRAS_POR_SIMBOLO amostras) para o ponto (i, q).

    `ciclos` é a frequência em ciclos por símbolo.
    """
    n_total = AMOSTRAS_POR_SIMBOLO
    simbolo = []
    for n in range(n_total):
        angulo = 2 * math.pi * ciclos * n / n_total
        simbolo.append(i * math.cos(angulo) - q * math.sin(angulo))
    return simbolo


def correlacionar(simbolo, ciclos):
    """Faz o inverso de onda(): recupera (i, q) de um símbolo recebido.

    O sinal negativo no Q vem do "- Q*sen" usado em onda().
    """
    n_total = len(simbolo)
    soma_i = 0.0
    soma_q = 0.0
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / n_total
        soma_i += amostra * math.cos(angulo)
        soma_q += amostra * math.sin(angulo)
    return (2 / n_total) * soma_i, -(2 / n_total) * soma_q


def pad(bits, tamanho):
    """Completa com zeros até o número de bits ser múltiplo de `tamanho`.

    8PSK usa 3 bits por símbolo e 32-QAM usa 5; sem isso o último símbolo
    ficaria incompleto. O receptor descarta o excedente no desenquadramento.
    """
    resto = len(bits) % tamanho
    if resto == 0:
        return list(bits)
    return list(bits) + [0] * (tamanho - resto)


def bits_do_ponto_mais_proximo(i, q, constelacao):
    """Decisão por mínima distância: devolve os bits do ponto de referência mais perto de (i, q).

    `constelacao` é um dict {tupla_de_bits: (I_ref, Q_ref)}. Comparamos a
    distância ao quadrado, pois a raiz não muda qual é a menor.
    """
    melhor_bits = None
    melhor_dist = None
    for bits, (i_ref, q_ref) in constelacao.items():
        dist = (i_ref - i) ** 2 + (q_ref - q) ** 2
        if melhor_dist is None or dist < melhor_dist:
            melhor_dist = dist
            melhor_bits = bits
    return list(melhor_bits)


def _simbolos(sinal):
    """Fatia o sinal em janelas de um símbolo, ignorando uma sobra incompleta."""
    n = AMOSTRAS_POR_SIMBOLO
    return [sinal[k:k + n] for k in range(0, len(sinal) - n + 1, n)]


# ask
def modular_ask(bits):
    """ASK on-off: bit 1 -> portadora com amplitude V; bit 0 -> sem portadora."""
    sinal = []
    for bit in bits:
        i = V if bit == 1 else 0.0
        sinal += onda(i, 0.0, CICLOS_PORTADORA)
    return sinal


def demodular_ask(sinal):
    """Mede a amplitude de cada símbolo e compara com o limiar V/2."""
    bits = []
    for simbolo in _simbolos(sinal):
        i, q = correlacionar(simbolo, CICLOS_PORTADORA)
        amplitude = math.hypot(i, q)
        bits.append(1 if amplitude > V / 2 else 0)
    return bits


# fsk
def modular_fsk(bits):
    """FSK binário: a amplitude é sempre V e a frequência depende do bit."""
    sinal = []
    for bit in bits:
        sinal += onda(V, 0.0, CICLOS_FSK[bit])
    return sinal


def demodular_fsk(sinal):
    """Correlaciona com as duas frequências e escolhe a de maior energia.

    Usar o módulo (hypot) em vez de só o I deixa a decisão independente da
    fase do sinal.
    """
    bits = []
    for simbolo in _simbolos(sinal):
        e0 = math.hypot(*correlacionar(simbolo, CICLOS_FSK[0]))
        e1 = math.hypot(*correlacionar(simbolo, CICLOS_FSK[1]))
        bits.append(1 if e1 > e0 else 0)
    return bits


# 8psk
GRAY_3_BITS = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0),
               (1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)]

MAPA_8PSK = {}
for _k, _bits in enumerate(GRAY_3_BITS):
    _fase = _k * math.pi / 4
    MAPA_8PSK[_bits] = (V * math.cos(_fase), V * math.sin(_fase))


def modular_8psk(bits):
    """Agrupa os bits de 3 em 3 e transmite um símbolo de fase para cada grupo."""
    bits = pad(bits, 3)
    sinal = []
    for k in range(0, len(bits), 3):
        i, q = MAPA_8PSK[tuple(bits[k:k + 3])]
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def demodular_8psk(sinal):
    """Recupera (i, q) de cada símbolo e decide pelo ponto mais próximo.

    A saída pode ter bits de padding no fim; o enlace descarta.
    """
    bits = []
    for simbolo in _simbolos(sinal):
        i, q = correlacionar(simbolo, CICLOS_PORTADORA)
        bits += bits_do_ponto_mais_proximo(i, q, MAPA_8PSK)
    return bits


# 32-qam
ESCALA_QAM = V / 5
CICLO_QUADRANTE = [(1, 1), (3, 1), (5, 1), (5, 3), (3, 3), (3, 5), (1, 5), (1, 3)]
QUADRANTES = {(1, 1): (0, 0), (-1, 1): (0, 1), (-1, -1): (1, 1), (1, -1): (1, 0)}

def montar_mapa_32qam():
    """Monta o dict {5 bits: (I, Q)}.

    Cada quadrante tem 8 pontos. O ponto da posição p do ciclo ganha os 3 bits
    Gray de posição p, precedidos pelos 2 bits do quadrante. As coordenadas
    saem do ponto do ciclo com o sinal do quadrante, vezes ESCALA_QAM.
    """
    mapa = {}
    for (sinal_i, sinal_q), bits_quadrante in QUADRANTES.items():
        for posicao, (nivel_i, nivel_q) in enumerate(CICLO_QUADRANTE):
            rotulo = bits_quadrante + GRAY_3_BITS[posicao]
            i = sinal_i * nivel_i * ESCALA_QAM
            q = sinal_q * nivel_q * ESCALA_QAM
            mapa[rotulo] = (i, q)
    return mapa


MAPA_32QAM = montar_mapa_32qam()


def modular_32qam(bits):
    """Agrupa os bits de 5 em 5 e transmite um símbolo (I, Q) para cada grupo."""
    bits = pad(bits, 5)
    sinal = []
    for k in range(0, len(bits), 5):
        i, q = MAPA_32QAM[tuple(bits[k:k + 5])]
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def demodular_32qam(sinal):
    """Recupera (i, q) de cada símbolo e decide pelo ponto mais próximo.

    Não dá para decidir cada eixo separado, porque a cruz não é uma grade
    completa (faltam os cantos); por isso a mínima distância é feita sobre os
    32 pontos.
    """
    bits = []
    for simbolo in _simbolos(sinal):
        i, q = correlacionar(simbolo, CICLOS_PORTADORA)
        bits += bits_do_ponto_mais_proximo(i, q, MAPA_32QAM)
    return bits


# Despacho: interface única usada pelo Simulador e pela GUI.
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}

MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "8psk": (modular_8psk, demodular_8psk),
                        "32qam": (modular_32qam, demodular_32qam)}


def modular_digital(bits, tipo):
    """Aplica a modulação banda-base escolhida na GUI."""
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    """Aplica o decodificador banda-base correspondente."""
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    """Aplica a modulação por portadora escolhida (tipo "nenhuma" devolve None)."""
    if tipo == "nenhuma":
        return None
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    """Aplica o demodulador por portadora correspondente."""
    return MODULACOES_PORTADORA[tipo][1](sinal)

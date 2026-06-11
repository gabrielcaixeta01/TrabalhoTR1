# -*- coding: utf-8 -*-
"""
CAMADA FÍSICA
=============
Converte bits em SINAIS ELÉTRICOS (listas de amostras em Volts) e
vice-versa, em duas etapas, como no diagrama do enunciado:

  1) MODULAÇÃO DIGITAL (banda-base): NRZ-Polar, Manchester e Bipolar (AMI)
  2) MODULAÇÃO POR PORTADORA: ASK, FSK, QPSK e 16-QAM

Convenções:
  - Sinal = list[float] de amostras em VOLTS.
  - Cada bit (banda-base) ou símbolo (portadora) ocupa AMOSTRAS_POR_BIT /
    AMOSTRAS_POR_SIMBOLO amostras.
  - Os demoduladores foram projetados para tolerar ruído: decidem por
    MÉDIA (banda-base) ou por CORRELAÇÃO com portadoras de referência
    (detecção coerente) seguida da escolha do ponto de constelação mais
    próximo.

ATENÇÃO (Manchester): adotamos a convenção do Forouzan/IEEE 802.3:
  bit 0 -> transição ALTO->BAIXO no meio do bit
  bit 1 -> transição BAIXO->ALTO no meio do bit
Confirme nos slides da disciplina se a convenção é a mesma; se for a
oposta (Tanenbaum), basta inverter os sinais em modular/demodular.
"""

import math

# ---------------------------------------------------------------------------
# Parâmetros globais do simulador (em um só lugar para facilitar ajustes)
# ---------------------------------------------------------------------------
V = 1.0                      # amplitude de referência do sinal, em Volts
AMOSTRAS_POR_BIT = 100       # resolução do sinal banda-base
AMOSTRAS_POR_SIMBOLO = 100   # resolução de cada símbolo da portadora
CICLOS_PORTADORA = 4         # ciclos de portadora por símbolo (nº inteiro!)
CICLOS_FSK = (2, 4)          # FSK: f1 (bit 0) e f2 (bit 1), em ciclos/símbolo
                             # Frequências inteiras e distintas mantêm as
                             # portadoras ORTOGONAIS dentro do símbolo, o que
                             # é essencial para a demodulação por correlação.


# ===========================================================================
# 1) MODULAÇÃO DIGITAL (BANDA-BASE)
# ===========================================================================
def modular_nrz_polar(bits):
    """NRZ-Polar: bit 1 -> +V constante; bit 0 -> -V constante."""
    sinal = []
    for bit in bits:
        nivel = V if bit == 1 else -V
        sinal += [nivel] * AMOSTRAS_POR_BIT      # mantém o nível o bit inteiro
    return sinal


def demodular_nrz_polar(sinal):
    """Decide cada bit pela MÉDIA das suas amostras (robusto a ruído):
    média > 0 -> 1; média <= 0 -> 0."""
    bits = []
    for i in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[i:i + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        bits.append(1 if media > 0 else 0)
    return bits


def modular_manchester(bits):
    """Manchester: sempre há transição no MEIO do bit (autossincronização).
    bit 0: +V na 1ª metade, -V na 2ª  (alto -> baixo)
    bit 1: -V na 1ª metade, +V na 2ª  (baixo -> alto)
    Equivale a XOR do NRZ com o clock."""
    metade = AMOSTRAS_POR_BIT // 2
    sinal = []
    for bit in bits:
        if bit == 0:
            sinal += [V] * metade + [-V] * (AMOSTRAS_POR_BIT - metade)
        else:
            sinal += [-V] * metade + [V] * (AMOSTRAS_POR_BIT - metade)
    return sinal


def demodular_manchester(sinal):
    """Compara a média da 1ª metade com a da 2ª metade de cada bit:
    se a 2ª metade for maior, houve transição de subida -> bit 1."""
    metade = AMOSTRAS_POR_BIT // 2
    bits = []
    for i in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        m1 = sum(sinal[i:i + metade]) / metade
        m2 = sum(sinal[i + metade:i + AMOSTRAS_POR_BIT]) / (AMOSTRAS_POR_BIT - metade)
        bits.append(1 if m2 > m1 else 0)
    return bits


def modular_bipolar(bits):
    """Bipolar/AMI: bit 0 -> 0 V; bit 1 -> alterna entre +V e -V.
    A alternância elimina o nível DC médio da linha."""
    sinal = []
    polaridade = V                               # próximo "1" será +V
    for bit in bits:
        if bit == 0:
            sinal += [0.0] * AMOSTRAS_POR_BIT
        else:
            sinal += [polaridade] * AMOSTRAS_POR_BIT
            polaridade = -polaridade             # inverte para o próximo 1
    return sinal


def demodular_bipolar(sinal):
    """Decide pelo MÓDULO da média: perto de 0 -> bit 0; perto de V
    (em qualquer polaridade) -> bit 1. Limiar no meio do caminho (V/2)."""
    bits = []
    for i in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[i:i + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        bits.append(1 if abs(media) > V / 2 else 0)
    return bits


# ===========================================================================
# 2) MODULAÇÃO POR PORTADORA
#
# Todas geram s(t) = I.cos(2*pi*f*t) - Q.sen(2*pi*f*t)  (representação I/Q),
# onde o par (I, Q) é o ponto da constelação escolhido pelos bits.
# A demodulação coerente recupera I e Q por correlação:
#     I = (2/N) * soma( s[n] * cos(...) )      (idem para Q com -sen)
# e então escolhe o ponto de constelação MAIS PRÓXIMO do (I, Q) medido -
# é isso que dá robustez ao ruído.
# ===========================================================================
def _onda(c_i, c_q, ciclos):
    """Gera um símbolo de AMOSTRAS_POR_SIMBOLO amostras com componentes
    em fase (c_i) e em quadratura (c_q) sobre a portadora de `ciclos`
    ciclos por símbolo."""
    N = AMOSTRAS_POR_SIMBOLO
    return [c_i * math.cos(2 * math.pi * ciclos * n / N) -
            c_q * math.sin(2 * math.pi * ciclos * n / N) for n in range(N)]


def _correlacionar(simbolo, ciclos):
    """Extrai as componentes (I, Q) de um símbolo recebido, projetando-o
    sobre cos e -sen da portadora de referência (produto interno)."""
    N = len(simbolo)
    i_comp = 2 / N * sum(s * math.cos(2 * math.pi * ciclos * n / N)
                         for n, s in enumerate(simbolo))
    q_comp = -2 / N * sum(s * math.sin(2 * math.pi * ciclos * n / N)
                          for n, s in enumerate(simbolo))
    return i_comp, q_comp


def _pad(bits, multiplo):
    """Completa a lista de bits com zeros até um múltiplo do nº de bits
    por símbolo (necessário para QPSK e 16-QAM). O desenquadramento do
    receptor descarta esse excedente naturalmente."""
    return bits + [0] * ((-len(bits)) % multiplo)


# --------------------------------- ASK ------------------------------------
def modular_ask(bits):
    """ASK (on-off keying): bit 1 -> portadora com amplitude V;
    bit 0 -> ausência de portadora (0 V)."""
    sinal = []
    for bit in bits:
        sinal += _onda(V if bit == 1 else 0.0, 0.0, CICLOS_PORTADORA)
    return sinal


def demodular_ask(sinal):
    """Mede a AMPLITUDE de cada símbolo via correlação (sqrt(I²+Q²)) e
    compara com o limiar V/2 (meio do caminho entre 0 e V)."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i_c, q_c = _correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits.append(1 if math.hypot(i_c, q_c) > V / 2 else 0)
    return bits


# --------------------------------- FSK ------------------------------------
def modular_fsk(bits):
    """FSK: bit 0 -> portadora de frequência f1; bit 1 -> frequência f2.
    A amplitude é sempre V; só a frequência muda."""
    f0, f1 = CICLOS_FSK
    sinal = []
    for bit in bits:
        sinal += _onda(V, 0.0, f1 if bit == 1 else f0)
    return sinal


def demodular_fsk(sinal):
    """Demodulação não-coerente: mede a ENERGIA do símbolo em cada uma
    das duas frequências (correlação com cos e sen de f1 e de f2) e
    escolhe a frequência com mais energia."""
    f0, f1 = CICLOS_FSK
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        simbolo = sinal[k:k + N]
        e0 = math.hypot(*_correlacionar(simbolo, f0))   # energia em f1
        e1 = math.hypot(*_correlacionar(simbolo, f1))   # energia em f2
        bits.append(1 if e1 > e0 else 0)
    return bits


# --------------------------------- QPSK -----------------------------------
# Mapeamento Gray (2 bits/símbolo): símbolos vizinhos diferem em 1 só bit,
# minimizando bits errados quando o ruído empurra para o vizinho.
#   dibit : fase      (I, Q) = (cos, sen) * V/sqrt(2)
#   00    : 45 graus   (+a, +a)
#   01    : 135 graus  (-a, +a)
#   11    : 225 graus  (-a, -a)
#   10    : 315 graus  (+a, -a)
_A_QPSK = V / math.sqrt(2)
_MAPA_QPSK = {(0, 0): (_A_QPSK, _A_QPSK), (0, 1): (-_A_QPSK, _A_QPSK),
              (1, 1): (-_A_QPSK, -_A_QPSK), (1, 0): (_A_QPSK, -_A_QPSK)}


def modular_qpsk(bits):
    """QPSK: agrupa os bits em pares (dibits) e transmite um símbolo de
    fase correspondente. Dobra a taxa em relação ao PSK binário."""
    bits = _pad(bits, 2)
    sinal = []
    for k in range(0, len(bits), 2):
        i_c, q_c = _MAPA_QPSK[(bits[k], bits[k + 1])]
        sinal += _onda(i_c, q_c, CICLOS_PORTADORA)
    return sinal


def demodular_qpsk(sinal):
    """Recupera (I, Q) por correlação e decide pelo QUADRANTE: o sinal de
    I e de Q determina diretamente o dibit (decisão de mínima distância)."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i_c, q_c = _correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        # Procura o ponto da constelação mais próximo do (I,Q) medido.
        melhor = min(_MAPA_QPSK.items(),
                     key=lambda kv: (kv[1][0] - i_c) ** 2 + (kv[1][1] - q_c) ** 2)
        bits += list(melhor[0])
    return bits


# -------------------------------- 16-QAM ----------------------------------
# 4 bits/símbolo: os 2 primeiros escolhem o nível de I e os 2 últimos o
# nível de Q, ambos com código Gray sobre os níveis {-3, -1, +1, +3}*(V/3).
_NIVEIS_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
_ESCALA_QAM = V / 3                              # nível máximo = V


def modular_16qam(bits):
    """16-QAM: varia amplitude E fase simultaneamente. Constelação 4x4
    de 16 pontos -> 4 bits por símbolo."""
    bits = _pad(bits, 4)
    sinal = []
    for k in range(0, len(bits), 4):
        i_c = _NIVEIS_GRAY[(bits[k], bits[k + 1])] * _ESCALA_QAM
        q_c = _NIVEIS_GRAY[(bits[k + 2], bits[k + 3])] * _ESCALA_QAM
        sinal += _onda(i_c, q_c, CICLOS_PORTADORA)
    return sinal


def _decidir_nivel_gray(valor):
    """Escolhe o nível {-3,-1,1,3} mais próximo do valor medido e devolve
    o par de bits Gray correspondente."""
    nivel = min((-3, -1, 1, 3), key=lambda n: abs(n * _ESCALA_QAM - valor))
    for bits_, n in _NIVEIS_GRAY.items():
        if n == nivel:
            return list(bits_)


def demodular_16qam(sinal):
    """Correlaciona para obter (I, Q) e decide cada eixo separadamente
    (a constelação é um produto cartesiano, então a decisão por eixo é
    equivalente à decisão de mínima distância no plano)."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i_c, q_c = _correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits += _decidir_nivel_gray(i_c) + _decidir_nivel_gray(q_c)
    return bits


# ===========================================================================
# DESPACHO (interface única usada pelo Simulador e pela GUI)
# ===========================================================================
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}

MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "qpsk": (modular_qpsk, demodular_qpsk),
                        "16qam": (modular_16qam, demodular_16qam)}


def modular_digital(bits, tipo):
    """Aplica a modulação banda-base escolhida na GUI."""
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    """Aplica o decodificador banda-base correspondente."""
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    """Aplica a modulação por portadora escolhida (ou nenhuma)."""
    if tipo == "nenhuma":
        return None
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    """Aplica o demodulador por portadora correspondente."""
    return MODULACOES_PORTADORA[tipo][1](sinal)
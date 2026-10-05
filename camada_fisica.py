# -*- coding: utf-8 -*-
"""
CAMADA FÍSICA
=============
Converte bits em SINAIS ELÉTRICOS (listas de amostras em Volts) e vice-versa.
O enunciado (seção 1.2) pede duas etapas, como na Figura 1 do PDF:

  [1/2] MODULAÇÃO DIGITAL (banda-base):  NRZ-Polar, Manchester e Bipolar
  [2/2] MODULAÇÃO POR PORTADORA:         ASK, FSK, 8PSK e 32-QAM

Convenções do projeto:
  - Sinal = list[float] de amostras em VOLTS.
  - Na banda-base, cada bit ocupa AMOSTRAS_POR_BIT amostras.
  - Na portadora, cada símbolo ocupa AMOSTRAS_POR_SIMBOLO amostras. Um símbolo
    carrega 1 bit (ASK, FSK), 3 bits (8PSK) ou 5 bits (32-QAM).
  - Todo modulador tem um demodulador correspondente que desfaz a operação.

COMO O RECEPTOR DECIDE (importante para o relatório e para a defesa oral):
  O canal soma ruído gaussiano às amostras. O demodulador não pode olhar uma
  amostra isolada; ele usa estratégias que "promediam" o ruído:
    - Banda-base: MÉDIA das amostras de cada bit.
    - Portadora : CORRELAÇÃO com cos/sen de referência (detecção coerente),
      que recupera o ponto (I, Q) do símbolo, seguida de decisão pelo ponto
      da constelação MAIS PRÓXIMO (mínima distância).
Slides de apoio (Moodle): tópico "Modulação" (banda-base e portadora).
Material de estudo: estudos/01-camada-fisica-portadora.md.
"""

import math

# ---------------------------------------------------------------------------
# Parâmetros globais do simulador (em um só lugar para facilitar ajustes)
# ---------------------------------------------------------------------------
V = 1.0                      # amplitude de referência do sinal, em Volts
AMOSTRAS_POR_BIT = 100       # resolução do sinal banda-base
AMOSTRAS_POR_SIMBOLO = 100   # resolução de cada símbolo da portadora
CICLOS_PORTADORA = 4         # ciclos de portadora por símbolo (nº INTEIRO!)
CICLOS_FSK = (2, 4)          # FSK: f0 (bit 0) e f1 (bit 1), em ciclos/símbolo
                             # Frequências inteiras e distintas mantêm as
                             # portadoras ORTOGONAIS dentro do símbolo, o que
                             # é essencial para a demodulação por correlação.


# ===========================================================================
# 1) MODULAÇÃO DIGITAL (BANDA-BASE)
#    Cada bit vira AMOSTRAS_POR_BIT amostras de tensão.
# ===========================================================================
def modular_nrz_polar(bits):
    """NRZ-Polar (Non-Return to Zero Polar).

    REGRA
        bit 1 -> +V durante todo o tempo de bit
        bit 0 -> -V durante todo o tempo de bit
        ("Polar" = dois níveis de polaridades opostas; "NRZ" = o sinal nunca
        volta a zero no meio do bit.)

    COMO FAZER
        Para cada bit, acrescente AMOSTRAS_POR_BIT amostras do nível certo.
        Dica: sinal += [nivel] * AMOSTRAS_POR_BIT
    """
    # TODO: implementar conforme a regra acima.
    raise NotImplementedError("camada_fisica.modular_nrz_polar")


def demodular_nrz_polar(sinal):
    """Decodificador NRZ-Polar: sinal ruidoso -> bits.

    COMO FAZER
        1. Percorra o sinal em passos de AMOSTRAS_POR_BIT amostras
           (range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT)).
        2. Calcule a MÉDIA das amostras da janela. O ruído tem média ~0, então
           a média recupera o nível transmitido mesmo com ruído forte.
        3. Decisão com limiar em 0 V:  média > 0 -> bit 1;  senão bit 0.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_nrz_polar")


def modular_manchester(bits):
    """Manchester: sempre há transição no MEIO do bit (autossincronização).

    CONVENÇÃO (slide 8 do CF-10 - Canal banda base): dado XOR clock.
        bit 0 -> -V na 1ª metade, +V na 2ª  (transição BAIXO -> ALTO)
        bit 1 -> +V na 1ª metade, -V na 2ª  (transição ALTO -> BAIXO)
    (Confirmado no slide 8 do CF-10: bit 1 sobe a 1ª metade e desce a 2ª.
    Atenção: a convenção de G.E. Thomas/Tanenbaum é essa; a IEEE 802.3 é a
    inversa. Modulador, demodulador e testes devem usar a mesma.)

    COMO FAZER
        metade = AMOSTRAS_POR_BIT // 2. Para cada bit, acrescente `metade`
        amostras de um nível e (AMOSTRAS_POR_BIT - metade) do outro. (O
        "- metade" evita perder uma amostra se alguém mudar para um nº ímpar.)
    """
    # TODO: implementar conforme a convenção acima.
    raise NotImplementedError("camada_fisica.modular_manchester")


def demodular_manchester(sinal):
    """Decodificador Manchester.

    COMO FAZER
        1. Para cada janela de AMOSTRAS_POR_BIT amostras, calcule a média da
           1ª metade (m1) e a da 2ª metade (m2).
        2. Se m1 > m2 houve transição de DESCIDA -> bit 1; senão bit 0.
        Comparar as duas metades (em vez de olhar o sinal absoluto) torna a
        decisão imune a um deslocamento DC (média do ruído diferente de zero).
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_manchester")


def modular_bipolar(bits):
    """Bipolar (AMI - Alternate Mark Inversion).

    REGRA
        bit 0 -> 0 V
        bit 1 -> alterna entre +V e -V a cada novo "1" (o primeiro 1 é +V)
        A alternância faz o nível DC médio da linha ser ~0.

    COMO FAZER
        Mantenha uma variável `polaridade` (começa em +V). A cada bit 1,
        emita `polaridade` e depois inverta o sinal dela (polaridade = -polaridade).
        Bit 0 não altera a polaridade.
    """
    # TODO: implementar conforme a regra acima.
    raise NotImplementedError("camada_fisica.modular_bipolar")


def demodular_bipolar(sinal):
    """Decodificador Bipolar.

    COMO FAZER
        1. Média de cada janela de AMOSTRAS_POR_BIT amostras.
        2. Decida pelo MÓDULO da média, pois o "1" pode vir em +V ou -V:
               abs(media) > V/2 -> bit 1;  senão bit 0.
        V/2 é o ponto médio entre os níveis 0 e V (limiar de decisão ótimo).
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_bipolar")


# ===========================================================================
# 2) MODULAÇÃO POR PORTADORA
#
# Representação I/Q (a "grande ideia" do estudo 01): TODAS as modulações
# abaixo geram o mesmo tipo de sinal
#
#       s(t) = I * cos(2*pi*f*t)  -  Q * sen(2*pi*f*t)
#
# onde o par (I, Q) é o ponto da constelação escolhido pelos bits:
#   ASK  : (I, Q) = (0, 0) ou (V, 0)           -> muda a amplitude
#   FSK  : (I, Q) = (V, 0), mas f muda         -> muda a frequência
#   8PSK : (I, Q) = (V*cos(fase), V*sen(fase)) -> muda a fase (8 fases)
#   32QAM: (I, Q) em grade 6x6 sem os 4 cantos -> muda amplitude e fase
#
# O DEMODULADOR recupera I e Q por CORRELAÇÃO com a portadora de referência:
#       I =  (2/N) * soma( s[n] * cos(2*pi*f*n/N) )
#       Q = -(2/N) * soma( s[n] * sen(2*pi*f*n/N) )
# e escolhe o ponto de constelação mais próximo do (I, Q) medido.
# (Prova: como a média de cos² em ciclos inteiros é 1/2, a soma devolve I/2,
# daí o fator 2/N. A média de cos*sen em ciclos inteiros é 0, por isso I e Q
# não se misturam. Por isso CICLOS_* precisam ser inteiros.)
# ===========================================================================
def onda(i, q, ciclos):
    """Gera UM símbolo da portadora a partir do ponto (i, q).

    ENTRADA
        i, q   : coordenadas do ponto da constelação (em Volts)
        ciclos : frequência da portadora, em ciclos POR SÍMBOLO (inteiro)
    SAÍDA
        list[float] com AMOSTRAS_POR_SIMBOLO amostras.

    FÓRMULA (para n = 0 .. N-1, com N = AMOSTRAS_POR_SIMBOLO)
        angulo = 2 * pi * ciclos * n / N
        amostra = i * cos(angulo) - q * sen(angulo)
    """
    # TODO: implementar conforme a fórmula acima.
    raise NotImplementedError("camada_fisica.onda")


def correlacionar(simbolo, ciclos):
    """Operação INVERSA de onda(): recupera (I, Q) de um símbolo recebido.

    FÓRMULA (N = len(simbolo))
        angulo_n = 2 * pi * ciclos * n / N
        I =  (2/N) * soma( simbolo[n] * cos(angulo_n) )
        Q = -(2/N) * soma( simbolo[n] * sen(angulo_n) )
    O sinal negativo em Q vem do "- Q*sen" usado em onda().

    SAÍDA
        tupla (i, q).

    DICA
        Teste isolado: correlacionar(onda(0.3, -0.7, 4), 4) deve devolver
        algo muito próximo de (0.3, -0.7).
    """
    # TODO: implementar conforme a fórmula acima.
    raise NotImplementedError("camada_fisica.correlacionar")


def pad(bits, tamanho):
    """Completa `bits` com zeros até o comprimento ser múltiplo de `tamanho`.

    POR QUÊ?
        8PSK agrupa 3 bits por símbolo e 32-QAM agrupa 5. Se sobrarem bits no
        final, o último símbolo ficaria incompleto. O excedente é descartado
        pelo receptor no desenquadramento (o enquadramento sabe onde a
        mensagem termina).

    EXEMPLO
        pad([1, 0, 1, 1], 3)  ->  [1, 0, 1, 1, 0, 0]
        pad([1, 0, 1], 3)     ->  [1, 0, 1]   (já é múltiplo: devolve igual)
    """
    # TODO: implementar (resto = len(bits) % tamanho; complete com zeros).
    raise NotImplementedError("camada_fisica.pad")


def bits_do_ponto_mais_proximo(i, q, constelacao):
    """Decisão de MÍNIMA DISTÂNCIA no plano I/Q.

    ENTRADA
        i, q        : ponto medido pelo receptor (com ruído)
        constelacao : dict {tupla_de_bits: (I_ref, Q_ref)}
    SAÍDA
        list[int] com os bits do ponto de referência mais perto de (i, q).

    COMO FAZER
        Para cada ponto de referência calcule a distância ao quadrado
            (I_ref - i)**2 + (Q_ref - q)**2
        (não precisa da raiz quadrada: só estamos COMPARANDO distâncias) e
        guarde o menor. É isso que dá robustez ao ruído: o símbolo só é
        decidido errado se o ruído empurrar o ponto para além da fronteira
        entre dois pontos vizinhos.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.bits_do_ponto_mais_proximo")


# --------------------------------- ASK ------------------------------------
def modular_ask(bits):
    """ASK (Amplitude Shift Keying) em forma on-off.

    REGRA
        bit 1 -> portadora com amplitude V      (i = V, q = 0)
        bit 0 -> ausência de portadora (0 V)    (i = 0, q = 0)
    Use onda(i, q, CICLOS_PORTADORA) para cada bit e concatene.
    """
    # TODO: implementar conforme a regra acima.
    raise NotImplementedError("camada_fisica.modular_ask")


def demodular_ask(sinal):
    """Demodulador ASK.

    COMO FAZER
        1. Fatie o sinal em janelas de AMOSTRAS_POR_SIMBOLO amostras.
        2. correlacionar(janela, CICLOS_PORTADORA) -> (i, q).
        3. Amplitude = math.hypot(i, q)  (= raiz de i² + q²).
        4. Limiar V/2:  amplitude > V/2 -> 1;  senão 0.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_ask")


# --------------------------------- FSK ------------------------------------
def modular_fsk(bits):
    """FSK (Frequency Shift Keying) binário.

    REGRA
        bit 0 -> portadora com CICLOS_FSK[0] ciclos/símbolo
        bit 1 -> portadora com CICLOS_FSK[1] ciclos/símbolo
        A amplitude é sempre V; só a frequência muda: onda(V, 0.0, ciclos).
    """
    # TODO: implementar conforme a regra acima.
    raise NotImplementedError("camada_fisica.modular_fsk")


def demodular_fsk(sinal):
    """Demodulador FSK (detecção não-coerente por energia).

    COMO FAZER
        Para cada janela de símbolo:
        1. Correlacione com a frequência f0 e depois com f1.
        2. A "energia" em cada frequência é math.hypot(i, q) de cada
           correlação. (Usar o módulo, e não só I, torna a decisão
           independente da fase do sinal.)
        3. Escolha a frequência com MAIS energia: e1 > e0 -> bit 1; senão 0.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_fsk")


# --------------------------------- 8PSK -----------------------------------
# 8PSK (Phase Shift Keying com 8 fases): 3 bits por símbolo. Os 8 pontos ficam
# em uma circunferência de raio V, separados por 45 graus.
#
#   fase_k = k * 45 graus  (k = 0..7)          (I, Q) = (V*cos(fase), V*sen(fase))
#
# Use MAPEAMENTO GRAY (confirmado nos slides CF-12, 5 e 9): pontos vizinhos na
# circunferência diferem em APENAS 1 bit. Assim, o erro mais provável (ruído empurra para o vizinho)
# corrompe só 1 dos 3 bits. Sequência Gray de 3 bits, em ordem de fase:
#       000, 001, 011, 010, 110, 111, 101, 100
#
# TODO: preencher MAPA_8PSK = {(b1, b2, b3): (I, Q), ...} com 8 entradas.
#       Pode montar com um laço usando a lista Gray acima e math.cos/math.sin.
MAPA_8PSK = {}


def modular_8psk(bits):
    """8PSK: agrupa os bits de 3 em 3 e transmite um símbolo de fase.

    COMO FAZER
        1. bits = pad(bits, 3).
        2. Para cada grupo (bits[k], bits[k+1], bits[k+2]) busque (I, Q) em
           MAPA_8PSK e gere onda(i, q, CICLOS_PORTADORA).
        3. Concatene os símbolos.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.modular_8psk")


def demodular_8psk(sinal):
    """Demodulador 8PSK.

    COMO FAZER
        Para cada janela de símbolo: correlacionar -> (i, q) e depois
        bits_do_ponto_mais_proximo(i, q, MAPA_8PSK). Concatene os trios de bits.
        O fluxo devolvido pode ter bits de padding no fim (o enlace descarta).
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_8psk")


# -------------------------------- 32-QAM ----------------------------------
# 32-QAM (Quadrature Amplitude Modulation): 5 bits por símbolo (2^5 = 32
# pontos). Varia AMPLITUDE E FASE ao mesmo tempo.
#
# Constelação em "CRUZ": uma grade 6x6 (36 pontos) com os 4 cantos removidos
# (36 - 4 = 32). Níveis de cada eixo: {-5, -3, -1, +1, +3, +5} * ESCALA_QAM.
# Remover os cantos (os pontos de maior energia) economiza potência de pico.
#
#            Q
#      . x x x x .        x = ponto da constelação
#      x x x x x x        . = canto removido: (±5, ±5)
#      x x x x x x   I
#      x x x x x x
#      x x x x x x
#      . x x x x .
#
# ESCALA_QAM normaliza para que o maior |I| ou |Q| (= 5 níveis) seja V.
ESCALA_QAM = V / 5

# Formato em cruz confirmado no slide 4 do CF-13; níveis de I/Q e rotulagem dos
# 5 bits NÃO constam nos slides. DECISÃO DE PROJETO (docs/DECISOES.md):
#
# Rotulagem de 5 bits = 2 bits de QUADRANTE + 3 bits de POSIÇÃO:
#   - Quadrante, em Gray ao redor da origem:
#         (I>0, Q>0) = 00   (I<0, Q>0) = 01   (I<0, Q<0) = 11   (I>0, Q<0) = 10
#   - Posição: cada quadrante tem 8 pontos (3x3 níveis |I|,|Q| em {1,3,5} menos o
#     canto (5,5)). Eles formam um CICLO em que cada ponto é vizinho do
#     seguinte: (1,1) (3,1) (5,1) (5,3) (3,3) (3,5) (1,5) (1,3) e de volta ao
#     início. Rotule ao longo desse ciclo com o Gray de 3 bits
#     000, 001, 011, 010, 110, 111, 101, 100 (o mesmo do 8PSK).
#   - A posição só depende de (|I|, |Q|); quadrantes vizinhos repetem os 3 bits
#     de posição e diferem só nos 2 bits de quadrante (1 bit, pois estão em Gray).
# Gray perfeito é impossível na cruz: dos 52 pares de pontos vizinhos, 48
# diferem em 1 bit e 4 em 3 bits. O que NÃO pode faltar: os 32 rótulos são
# DISTINTOS (um-para-um), senão o receptor não consegue decodificar.
#
# TODO: preencher MAPA_32QAM = {(b1, b2, b3, b4, b5): (I, Q), ...} com 32 entradas,
#       com I e Q em Volts = nível * ESCALA_QAM.
MAPA_32QAM = {}


def modular_32qam(bits):
    """32-QAM: agrupa os bits de 5 em 5 e transmite um símbolo (I, Q).

    COMO FAZER
        1. bits = pad(bits, 5).
        2. Para cada grupo de 5 bits, busque (I, Q) em MAPA_32QAM e gere
           onda(i, q, CICLOS_PORTADORA).
        3. Concatene os símbolos.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.modular_32qam")


def demodular_32qam(sinal):
    """Demodulador 32-QAM.

    COMO FAZER
        Para cada janela de símbolo: correlacionar -> (i, q) e depois
        bits_do_ponto_mais_proximo(i, q, MAPA_32QAM).
        ATENÇÃO: diferente do 16-QAM, NÃO dá para decidir cada eixo
        separadamente, porque a constelação em cruz não é um produto
        cartesiano (faltam os cantos). Use a decisão de mínima distância
        sobre os 32 pontos.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_fisica.demodular_32qam")


# ===========================================================================
# DESPACHO (interface única usada pelo Simulador e pela GUI)
# Cada entrada é uma tupla (função_de_modulação, função_de_demodulação).
# Acesso: MODULACOES_DIGITAIS["nrz"][0] é o modulador; [1] o demodulador.
# ===========================================================================
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}

MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "8psk": (modular_8psk, demodular_8psk),
                        "32qam": (modular_32qam, demodular_32qam)}


def modular_digital(bits, tipo):
    """Aplica a modulação banda-base escolhida na GUI (chave de MODULACOES_DIGITAIS)."""
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    """Aplica o decodificador banda-base correspondente."""
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    """Aplica a modulação por portadora escolhida (tipo "nenhuma" -> None)."""
    if tipo == "nenhuma":
        return None
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    """Aplica o demodulador por portadora correspondente."""
    return MODULACOES_PORTADORA[tipo][1](sinal)

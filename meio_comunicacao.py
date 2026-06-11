# -*- coding: utf-8 -*-
"""
MEIO DE COMUNICAÇÃO
===================
Simula o canal físico entre o transmissor e o receptor, conforme exigido
no enunciado:

  "Tem que ser implementado com valores de eletricidade - V/W.
   O ruído tem que ser acrescido a partir de um valor de V/W partindo de
   uma variável aleatória gaussiana (normal) - n(x, sigma)"

Ou seja: o sinal que trafega no meio é uma sequência de amostras em
VOLTS, e a cada amostra somamos uma realização independente de uma
variável aleatória normal N(x, sigma) - ruído AWGN (Additive White
Gaussian Noise) com média x e desvio padrão sigma, ambos configuráveis
pela interface gráfica.
"""

import random


def transmitir(sinal, media, sigma):
    """Propaga o sinal pelo meio, somando ruído gaussiano amostra a amostra.

    Parâmetros:
      sinal : list[float] - amostras do sinal transmitido, em Volts
      media : float       - média (x) do ruído, em Volts. Uma média != 0
                            representa um nível DC espúrio no canal.
      sigma : float       - desvio padrão do ruído, em Volts. Quanto maior,
                            mais "borrado" o sinal chega ao receptor.

    Retorna a lista de amostras recebidas (sinal + ruído).
    """
    if sigma == 0 and media == 0:
        return list(sinal)                       # canal ideal (sem ruído)
    # random.gauss implementa a distribuição normal; nenhum protocolo é
    # "importado pronto" aqui - o ruído É uma variável aleatória, e usar o
    # gerador padrão da linguagem é o procedimento esperado.
    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    """Potência média do sinal em Watts (sobre carga normalizada de 1 ohm):
    P = média de v(t)^2. Útil para relatar a relação sinal-ruído (SNR)
    na interface gráfica."""
    if not sinal:
        return 0.0
    return sum(v * v for v in sinal) / len(sinal)
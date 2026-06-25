# -*- coding: utf-8 -*-
"""
MEIO DE COMUNICAÇÃO
===================
Simula o canal físico entre o transmissor e o receptor.

O sinal que trafega no meio é uma sequência de amostras em
VOLTS, e a cada amostra somamos uma realização independente de uma
variável aleatória normal N(x, sigma) - ruído AWGN (Additive White
Gaussian Noise) com média x e desvio padrão sigma, ambos configuráveis
pela interface gráfica.
"""

import random


def transmitir(sinal, media, sigma):
    if sigma == 0 and media == 0:
        return list(sinal)  # canal ideal (sem ruído)
    
    # random.gauss implementa a distribuição normal; nenhum protocolo é "importado pronto" aqui
    # o ruído é uma variável aleatória

    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    if not sinal:
        return 0.0
    
    # potência média sobre resistência de 1 ohm
    return sum(amostra * amostra for amostra in sinal) / len(sinal)

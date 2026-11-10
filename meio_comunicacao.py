# -*- coding: utf-8 -*-
"""
Meio de comunicação.

O ruído é gaussiano: para cada amostra sorteamos um valor de uma distribuição
normal com média x e desvio padrão sigma (os dois configuráveis na interface)
"""

import random


def transmitir(sinal, media, sigma):
    """
    Passa o sinal pelo canal e devolve o que o receptor vai enxergar.
    """
    # Canal ideal
    if media == 0 and sigma == 0:
        return list(sinal)

    recebido = []
    for amostra in sinal:
        recebido.append(amostra + random.gauss(media, sigma))
    return recebido


def potencia_media(sinal):
    """
    Serve para tirar a relação sinal-ruído.

    A potência instantânea é v²/R; com R = 1 ohm vira só v². 
    A média é a soma dos quadrados das amostras dividida pela quantidade de amostras.
    """
    # Lista vazia: evita dividir por zero.
    if len(sinal) == 0:
        return 0.0

    soma_quadrados = 0.0
    for v in sinal:
        soma_quadrados += v * v

    return soma_quadrados / len(sinal)

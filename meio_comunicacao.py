# -*- coding: utf-8 -*-
"""
Meio de comunicação.

Canal entre o transmissor e o receptor. O sinal que passa por aqui é
uma lista de amostras de tensão (em Volts), e o canal não é perfeito: cada
amostra chega com um pouco de ruído somado.

O ruído é gaussiano: para cada amostra sorteamos um valor de uma distribuição
normal com média x e desvio padrão sigma (os dois configuráveis na interface),
sempre de forma independente das outras amostras:

    sinal_recebido[k] = sinal_enviado[k] + ruido[k]
"""

import random


def transmitir(sinal, media, sigma):
    """Passa o sinal pelo canal e devolve o que o receptor vai enxergar.

    Para cada amostra de tensão que saiu do transmissor, soma um valor sorteado
    de uma normal (media, sigma). O resultado é uma lista nova do mesmo tamanho;
    a original não é mexida, porque o simulador ainda precisa dela para medir
    a potência do ruído depois.
    """
    # Canal ideal: sem ruído nenhum. Devolve uma cópia só para o receptor não
    # ficar com a mesma lista do transmissor.
    if media == 0 and sigma == 0:
        return list(sinal)

    # Um sorteio gaussiano novo para cada amostra.
    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    """Calcula, em Watts, considerando carga de 1 ohm.

    Serve para tirar a relação sinal-ruído.

    A potência instantânea é v²/R; com R = 1 ohm vira só v². A média é a soma
    dos quadrados das amostras dividida pela quantidade de amostras.
    """
    # Lista vazia: evita dividir por zero.
    if len(sinal) == 0:
        return 0.0

    return sum(v * v for v in sinal) / len(sinal)

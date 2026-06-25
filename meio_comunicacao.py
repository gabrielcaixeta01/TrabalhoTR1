"""
canal físico entre transmissor e receptor.

o sinal é uma sequência de amostras em volts. o meio soma uma variável
normal independente em cada amostra, com média e desvio padrão definidos
na interface.
"""

import random


def transmitir(sinal, media, sigma):
    if sigma == 0 and media == 0:
        return list(sinal)

    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    if not sinal:
        return 0.0

    return sum(amostra * amostra for amostra in sinal) / len(sinal)

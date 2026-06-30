"""
canal físico entre transmissor e receptor.

o sinal é uma sequência de amostras em volts. o meio soma uma variável
normal independente em cada amostra, com média e desvio padrão definidos
na interface.
"""

import random


def transmitir(sinal, media, sigma):
    # se não tem ruido nenhum, devolve uma copia do sinal.
    # copia evita que alguem altere a lista original sem querer.
    if sigma == 0 and media == 0:
        return list(sinal)

    # o meio soma uma amostra aleatoria em cada ponto do sinal.
    # random.gauss(media, sigma) gera ruido gaussiano: média desloca o centro
    # e sigma controla o espalhamento/força do ruido.
    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    # potência média aqui é a média de v² das amostras.
    # serve para comparar sinal e ruido depois da transmissão.
    if not sinal:
        return 0.0

    return sum(amostra * amostra for amostra in sinal) / len(sinal)

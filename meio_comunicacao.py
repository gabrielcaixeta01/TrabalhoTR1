# -*- coding: utf-8 -*-
"""
MEIO DE COMUNICAÇÃO
===================
Enunciado, seção 1.1. Simula o canal físico entre o transmissor e o receptor.

REQUISITOS DO PROFESSOR
  1. Representação física: o sinal que trafega é uma lista de amostras de
     TENSÃO, em Volts (V). Nada de bits "puros" passando pelo canal.
  2. Ruído AWGN (Additive White Gaussian Noise): a CADA amostra do sinal soma-se
     um valor sorteado de uma variável aleatória Gaussiana (Normal) n(x, sigma):
         x     = média do ruído (V)
         sigma = desvio padrão do ruído (V)
     Ambos configuráveis pela interface gráfica.

     Aditivo -> sinal_recebido[k] = sinal_enviado[k] + ruido[k]
     Branco  -> cada ruido[k] é sorteado de forma independente dos outros.
     Gaussiano -> ruido[k] ~ Normal(x, sigma).

RESTRIÇÃO DO TRABALHO
  O enunciado proíbe importar bibliotecas externas que entreguem o protocolo
  pronto (ex.: zlib para CRC). Gerar números aleatórios com o módulo padrão
  `random` do Python é permitido: ele é apenas o gerador da variável
  aleatória, não implementa nenhum protocolo.
"""

import random


def transmitir(sinal, media, sigma):
    """Passa o sinal pelo canal e devolve o sinal recebido (com ruído).

    ENTRADA
        sinal : list[float]  amostras em Volts, vindas do transmissor
        media : float        média x do ruído gaussiano (V)
        sigma : float        desvio padrão do ruído gaussiano (V)
    SAÍDA
        list[float] com o MESMO tamanho de `sinal`.

    COMO FAZER
        1. (Opcional, mas recomendado) Se media == 0 e sigma == 0 não há
           ruído: devolva uma CÓPIA do sinal (list(sinal)) para não devolver
           a mesma lista do transmissor.
        2. Caso contrário, para cada amostra some um sorteio gaussiano:
               amostra + random.gauss(media, sigma)
           random.gauss(mu, sigma) sorteia um valor de N(mu, sigma).
        3. NÃO altere a lista original (o simulador a usa depois para
           calcular a potência do ruído).

    DICA
        Uma list comprehension resolve em uma linha:
            [a + random.gauss(media, sigma) for a in sinal]
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("meio_comunicacao.transmitir")


def potencia_media(sinal):
    """Potência média de um sinal, em Watts, assumindo carga de 1 ohm.

    FÓRMULA
        Para tensão v sobre resistência R, a potência instantânea é v²/R.
        Com R = 1 ohm:   P = (1/N) * soma( v[k]² )   para k = 0..N-1.

    USO
        O simulador calcula a potência do sinal e a do ruído para mostrar na
        GUI (e dá para estimar a relação sinal-ruído SNR = P_sinal / P_ruido).

    CASOS DE BORDA
        Lista vazia -> devolver 0.0 (evita divisão por zero).
    """
    # TODO: implementar conforme a fórmula acima.
    raise NotImplementedError("meio_comunicacao.potencia_media")

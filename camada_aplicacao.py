# -*- coding: utf-8 -*-
"""
CAMADA DE APLICAÇÃO
===================
Responsável pela fronteira entre o "mundo humano" (texto) e o "mundo da
rede" (bits). Corresponde aos blocos "Entrada de texto / Codificador em
bits" (TX) e "Conversor bits em texto / Saída de texto" (RX) do diagrama
do enunciado.

Convenção adotada em todo o simulador:
  - Bits são representados como list[int] contendo apenas 0s e 1s.
  - Cada caractere é codificado em UTF-8 e cada byte é expandido em
    8 bits, do bit mais significativo (MSB) para o menos significativo.
"""


def texto_para_bits(texto):
    """Converte uma string em uma lista de bits (codificador em bits do TX).

    Exemplo: 'A' -> byte 0x41 -> [0, 1, 0, 0, 0, 0, 0, 1]
    """
    bits = []
    for byte in texto.encode("utf-8"):          # cada caractere vira 1+ bytes UTF-8
        for i in range(7, -1, -1):              # percorre do bit 7 (MSB) ao bit 0 (LSB)
            bits.append((byte >> i) & 1)        # isola o i-ésimo bit do byte
    return bits


def bits_para_texto(bits):
    """Converte uma lista de bits de volta para string (conversor do RX).

    Agrupa os bits de 8 em 8, reconstrói os bytes e decodifica como UTF-8.
    Se o ruído corromper bits a ponto de gerar bytes inválidos em UTF-8,
    usamos errors='replace' para que o caractere ilegível apareça como '�'
    em vez de derrubar o programa.
    """
    n_bytes = len(bits) // 8 
    dados = bytearray() # mesma coisa que usar []
    for i in range(n_bytes):
        byte = 0
        for bit in bits[i * 8:(i + 1) * 8]:     # logica pra pegar o 1,2,3... bytes certinho
            byte = (byte << 1) | bit            # desloca e insere o próximo bit
        dados.append(byte)
    return dados.decode("utf-8", errors="replace") # esse replace insere um <EFBFBD> ao inves de travar o programa
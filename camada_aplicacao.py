# -*- coding: utf-8 -*-
#Camada de aplicação.

def texto_para_bits(texto):
    bits = []
    dados = texto.encode("utf-8") # string -> bytes

    for byte in dados:
        for posicao in range(7, -1, -1):
            bits.append((byte >> posicao) & 1)
    return bits


def bits_para_texto(bits):
    dados = bytearray()
    for inicio in range(0, len(bits) // 8 * 8, 8):
        byte = 0
        for bit in bits[inicio:inicio + 8]:
            byte = (byte << 1) | bit
        dados.append(byte)

    dados = dados.decode("utf-8", errors="replace") #bytes -> string
    return dados

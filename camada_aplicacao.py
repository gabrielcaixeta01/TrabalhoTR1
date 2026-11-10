# -*- coding: utf-8 -*-
#Camada de aplicação.

def texto_para_bits(texto):
    """Converte o texto digitado no simulador em bits.

    Codifica a string em bytes UTF-8 e expande cada byte em 8 bits, do mais
    significativo para o menos. Caracteres fora do ASCII ocupam mais de um byte. "ç" -> 16 bits.
    """
    bits = []
    dados = texto.encode("utf-8") # string -> bytes

    for byte in dados:
        for posicao in range(7, -1, -1):
            bits.append((byte >> posicao) & 1)
    return bits


def bits_para_texto(bits):
    """
    Agrupa os bits em bytes (descarta a sobra) e decodifica em UTF-8. Com errors="replace", bytes inválidos
    viram '�' em vez de gerar exceção.
    """
    dados = bytearray()
    for inicio in range(0, len(bits) // 8 * 8, 8):
        byte = 0
        for bit in bits[inicio:inicio + 8]:
            byte = (byte << 1) | bit
        dados.append(byte)

    dados = dados.decode("utf-8", errors="replace") #bytes -> string
    return dados

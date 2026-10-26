# -*- coding: utf-8 -*-
"""
Camada de aplicação (chat de texto).

Faz só as duas conversões entre o texto e os bits da rede:
  - TX: texto digitado -> texto_para_bits() -> bits para a camada de enlace
  - RX: bits do enlace -> bits_para_texto() -> texto legível

Convenções do projeto (valem para todos os módulos):
  - Bits = list[int] com valores 0 ou 1.
  - Ordem = bit mais significativo primeiro. Ex.: 'A' = 0x41 = 01000001.
  - Caracteres em UTF-8, que inclui o ASCII e também acentos como 'ç' e 'ã'.
"""


def texto_para_bits(texto):
    """Converte o texto digitado na GUI na sequência de bits enviada ao enlace.

    Codifica a string em bytes UTF-8 e expande cada byte em 8 bits, do mais
    significativo para o menos. Caracteres fora do ASCII ocupam mais de um byte.
    Ex.: "A" -> [0, 1, 0, 0, 0, 0, 0, 1]; "ç" -> 16 bits.
    """
    bits = []
    for byte in texto.encode("utf-8"):
        for posicao in range(7, -1, -1):
            bits.append((byte >> posicao) & 1)  # isola o bit da posição
    return bits


def bits_para_texto(bits):
    """Reconstrói o texto a partir dos bits entregues pelas camadas inferiores.

    Agrupa os bits de 8 em 8 em bytes (uma sobra incompleta no final é
    ignorada) e decodifica em UTF-8. Com errors="replace", bytes inválidos
    viram '�' em vez de gerar exceção: se o canal corromper bits, queremos
    mostrar a mensagem corrompida, não travar o simulador.
    Ex.: [0, 1, 0, 0, 0, 0, 0, 1] -> "A"
    """
    dados = bytearray()
    for inicio in range(0, len(bits) // 8 * 8, 8):
        byte = 0
        for bit in bits[inicio:inicio + 8]:
            byte = (byte << 1) | bit            # empurra o valor e encaixa o bit
        dados.append(byte)
    return dados.decode("utf-8", errors="replace")

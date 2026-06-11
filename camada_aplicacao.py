"""Conversão entre texto UTF-8 e lista de bits."""

from __future__ import annotations


def texto_para_bits(texto: str) -> list[int]:
    """Codifica texto em UTF-8 e expande cada byte em 8 bits."""
    bits: list[int] = []
    for byte in texto.encode("utf-8"):
        for deslocamento in range(7, -1, -1):
            bits.append((byte >> deslocamento) & 1)
    return bits


def bits_para_texto(bits: list[int]) -> str:
    """Agrupa bits em bytes e decodifica UTF-8 com substituição de erros."""
    if not bits:
        return ""

    bytes_saida = bytearray()
    limite = len(bits) - (len(bits) % 8)
    for indice in range(0, limite, 8):
        valor = 0
        for deslocamento, bit in enumerate(bits[indice:indice + 8]):
            valor |= (bit & 1) << (7 - deslocamento)
        bytes_saida.append(valor)
    return bytes_saida.decode("utf-8", errors="replace")


def bits_para_bytes(bits: list[int]) -> bytes:
    """Converte uma lista de bits em bytes, descartando bits excedentes."""
    if not bits:
        return b""

    bytes_saida = bytearray()
    limite = len(bits) - (len(bits) % 8)
    for indice in range(0, limite, 8):
        valor = 0
        for deslocamento, bit in enumerate(bits[indice:indice + 8]):
            valor |= (bit & 1) << (7 - deslocamento)
        bytes_saida.append(valor)
    return bytes(bytes_saida)


def bytes_para_bits(dados: bytes) -> list[int]:
    """Converte bytes em uma lista de bits, MSB primeiro."""
    bits: list[int] = []
    for byte in dados:
        for deslocamento in range(7, -1, -1):
            bits.append((byte >> deslocamento) & 1)
    return bits
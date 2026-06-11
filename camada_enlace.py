"""API em snake_case para enquadramento, EDC e Hamming."""

from __future__ import annotations

import CamadaEnlace as _legacy

from camada_aplicacao import bytes_para_bits, bits_para_bytes


FLAG = bytes_para_bits(_legacy.FLAG_BYTE)
ESC = bytes_para_bits(_legacy.ESC_BYTE)


def enquadrar_contagem(bits: list[int], tam_max_quadro: int) -> list[list[int]]:
    quadros = _legacy.enquadrar_contagem(bits_para_bytes(bits), tam_max_quadro)
    return [bytes_para_bits(quadro) for quadro in quadros]


def desenquadrar_contagem(quadros: list[list[int]]) -> list[int]:
    quadros_bytes = [bits_para_bytes(quadro) for quadro in quadros]
    return bytes_para_bits(_legacy.desenquadrar_contagem(quadros_bytes))


def enquadrar_bytes(bits: list[int], tam_max_quadro: int) -> list[list[int]]:
    quadros = _legacy.enquadrar_insercao_bytes(bits_para_bytes(bits), tam_max_quadro)
    return [bytes_para_bits(quadro) for quadro in quadros]


def desenquadrar_bytes(quadros: list[list[int]]) -> list[int]:
    quadros_bytes = [bits_para_bytes(quadro) for quadro in quadros]
    return bytes_para_bits(_legacy.desenquadrar_insercao_bytes(quadros_bytes))


def enquadrar_bits(bits: list[int], tam_max_quadro: int) -> list[list[int]]:
    return _legacy.enquadrar_insercao_bits(bits_para_bytes(bits), tam_max_quadro)


def desenquadrar_bits(quadros: list[list[int]]) -> list[int]:
    return bytes_para_bits(_legacy.desenquadrar_insercao_bits(quadros))


def adicionar_paridade_par(bits: list[int]) -> list[int]:
    return bytes_para_bits(_legacy.paridade_par(bits_para_bytes(bits)))


def verificar_paridade_par(bits: list[int]) -> tuple[list[int], bool]:
    dados = bits_para_bytes(bits)
    ok = _legacy.verificar_paridade_par(dados)
    return bytes_para_bits(dados[:-1]), ok


def adicionar_checksum(bits: list[int]) -> list[int]:
    return bytes_para_bits(_legacy.checksum(bits_para_bytes(bits)))


def verificar_checksum(bits: list[int]) -> tuple[list[int], bool]:
    dados = bits_para_bytes(bits)
    ok = _legacy.verificar_checksum(dados)
    return bytes_para_bits(dados[:-2]), ok


def adicionar_crc32(bits: list[int]) -> list[int]:
    return bytes_para_bits(_legacy.crc32(bits_para_bytes(bits)))


def verificar_crc32(bits: list[int]) -> tuple[list[int], bool]:
    dados = bits_para_bytes(bits)
    ok = _legacy.verificar_crc32(dados)
    return bytes_para_bits(dados[:-4]), ok


def codificar_hamming(bits: list[int]) -> list[int]:
    return _legacy.hamming_codificar(bits)


def decodificar_hamming(bits: list[int]) -> tuple[list[int], int]:
    return _legacy.hamming_decodificar(bits)
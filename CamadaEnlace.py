"""
CamadaEnlace.py — Enquadramento, detecção e correção de erros.
Trabalha com listas de bits (int 0/1) ou bytes conforme o protocolo.
"""

import struct


# ─── Enquadramento ─────────────────────────────────────────────────────────────

def enquadrar_contagem(dados: bytes, tamanho_max: int) -> list[bytes]:
    """
    Enquadramento por contagem de caracteres.
    Prefixo de 1 byte indica o tamanho total do quadro (incluindo o prefixo).
    """
    quadros = []
    for i in range(0, len(dados), tamanho_max):
        payload = dados[i:i + tamanho_max]
        tamanho = len(payload) + 1  # +1 pelo byte de contagem
        quadros.append(bytes([tamanho]) + payload)
    return quadros


def desenquadrar_contagem(quadros: list[bytes]) -> bytes:
    """Remove o byte de contagem e concatena os payloads."""
    return b"".join(q[1:] for q in quadros)


FLAG_BYTE = b"\x7E"   # flag padrão HDLC
ESC_BYTE  = b"\x7D"   # byte de escape
ESC_XOR   = 0x20      # máscara XOR aplicada ao byte escapado


def enquadrar_insercao_bytes(dados: bytes, tamanho_max: int) -> list[bytes]:
    """
    Enquadramento com flags + inserção de bytes (byte stuffing).
    Bytes FLAG e ESC no payload são escapados com ESC_BYTE XOR 0x20.
    """
    quadros = []
    for i in range(0, len(dados), tamanho_max):
        payload = dados[i:i + tamanho_max]
        stuffed = bytearray()
        for byte in payload:
            if byte in (FLAG_BYTE[0], ESC_BYTE[0]):
                stuffed.append(ESC_BYTE[0])
                stuffed.append(byte ^ ESC_XOR)
            else:
                stuffed.append(byte)
        quadros.append(FLAG_BYTE + bytes(stuffed) + FLAG_BYTE)
    return quadros


def desenquadrar_insercao_bytes(quadros: list[bytes]) -> bytes:
    """Remove flags e desfaz o byte stuffing."""
    resultado = bytearray()
    for quadro in quadros:
        payload = quadro[1:-1]  # remove flags inicial e final
        i = 0
        while i < len(payload):
            if payload[i] == ESC_BYTE[0]:
                i += 1
                resultado.append(payload[i] ^ ESC_XOR)
            else:
                resultado.append(payload[i])
            i += 1
    return bytes(resultado)


FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]  # 0x7E em bits


def _bytes_para_bits(dados: bytes) -> list[int]:
    bits = []
    for byte in dados:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_para_bytes(bits: list[int]) -> bytes:
    resultado = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j, bit in enumerate(bits[i:i+8]):
            byte |= bit << (7 - j)
        resultado.append(byte)
    return bytes(resultado)


def enquadrar_insercao_bits(dados: bytes, tamanho_max: int) -> list[list[int]]:
    """
    Enquadramento com flags + inserção de bits (bit stuffing).
    Após 5 bits '1' consecutivos no payload, insere um bit '0'.
    """
    quadros = []
    for i in range(0, len(dados), tamanho_max):
        payload_bits = _bytes_para_bits(dados[i:i + tamanho_max])
        stuffed = []
        consecutivos = 0
        for bit in payload_bits:
            stuffed.append(bit)
            if bit == 1:
                consecutivos += 1
                if consecutivos == 5:
                    stuffed.append(0)  # insere bit de stuffing
                    consecutivos = 0
            else:
                consecutivos = 0
        quadros.append(FLAG_BITS + stuffed + FLAG_BITS)
    return quadros


def desenquadrar_insercao_bits(quadros: list[list[int]]) -> bytes:
    """Remove flags e desfaz o bit stuffing."""
    todos_bits = []
    flag_len = len(FLAG_BITS)
    for quadro in quadros:
        payload_bits = quadro[flag_len:-flag_len]
        destuffed = []
        consecutivos = 0
        i = 0
        while i < len(payload_bits):
            bit = payload_bits[i]
            destuffed.append(bit)
            if bit == 1:
                consecutivos += 1
                if consecutivos == 5:
                    i += 1  # pula o bit de stuffing
                    consecutivos = 0
            else:
                consecutivos = 0
            i += 1
        todos_bits.extend(destuffed)
    return _bits_para_bytes(todos_bits)


# ─── Detecção de erros ─────────────────────────────────────────────────────────

def paridade_par(dados: bytes) -> bytes:
    """Acrescenta 1 byte de paridade par ao final dos dados."""
    paridade = 0
    for byte in dados:
        paridade ^= byte
    # conta bits 1 — se ímpar, bit de paridade = 1
    contagem = bin(paridade).count("1")
    return dados + bytes([0 if contagem % 2 == 0 else 1])


def verificar_paridade_par(dados: bytes) -> bool:
    """Verifica paridade par; último byte é o bit de paridade."""
    paridade = 0
    for byte in dados:
        paridade ^= byte
    return bin(paridade).count("1") % 2 == 0


def checksum(dados: bytes) -> bytes:
    """
    Checksum de 16 bits (soma em complemento de 1, big-endian).
    Retorna dados + 2 bytes de checksum.
    """
    soma = 0
    # processa em palavras de 16 bits
    for i in range(0, len(dados) - 1, 2):
        palavra = (dados[i] << 8) + dados[i + 1]
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)  # carry
    if len(dados) % 2:  # byte restante
        soma += dados[-1] << 8
        soma = (soma & 0xFFFF) + (soma >> 16)
    cs = (~soma) & 0xFFFF
    return dados + struct.pack(">H", cs)


def verificar_checksum(dados: bytes) -> bool:
    """Verifica checksum; últimos 2 bytes são o checksum."""
    soma = 0
    for i in range(0, len(dados) - 1, 2):
        palavra = (dados[i] << 8) + dados[i + 1]
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    if len(dados) % 2:
        soma += dados[-1] << 8
        soma = (soma & 0xFFFF) + (soma >> 16)
    return soma == 0xFFFF


CRC32_POLY = 0xEDB88320  # IEEE 802, little-endian


def crc32(dados: bytes) -> bytes:
    """CRC-32 IEEE 802. Retorna dados + 4 bytes de CRC."""
    crc = 0xFFFFFFFF
    for byte in dados:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC32_POLY
            else:
                crc >>= 1
    crc ^= 0xFFFFFFFF
    return dados + struct.pack("<I", crc)


def verificar_crc32(dados: bytes) -> bool:
    """Verifica CRC-32; últimos 4 bytes são o CRC."""
    crc = 0xFFFFFFFF
    for byte in dados:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ CRC32_POLY
            else:
                crc >>= 1
    return (crc ^ 0xFFFFFFFF) == 0


# ─── Correção de erros — Hamming ───────────────────────────────────────────────

def _bits_hamming_necessarios(n_dados: int) -> int:
    """Calcula r bits de redundância para n_dados bits de dados."""
    r = 0
    while (2 ** r) < (n_dados + r + 1):
        r += 1
    return r


def hamming_codificar(bits: list[int]) -> list[int]:
    """
    Codificação Hamming(n, k).
    Insere bits de paridade nas posições potência de 2.
    """
    n_dados = len(bits)
    r = _bits_hamming_necessarios(n_dados)
    n_total = n_dados + r

    # Aloca vetor e posiciona bits de dados
    palavra = [0] * (n_total + 1)  # índice 1-based
    j = 0
    for i in range(1, n_total + 1):
        if (i & (i - 1)) != 0:  # não é potência de 2 → bit de dados
            palavra[i] = bits[j]
            j += 1

    # Calcula bits de paridade par
    for p in range(r):
        pos = 2 ** p
        paridade = 0
        for i in range(1, n_total + 1):
            if i & pos:
                paridade ^= palavra[i]
        palavra[pos] = paridade

    return palavra[1:]  # descarta índice 0


def hamming_decodificar(bits: list[int]) -> tuple[list[int], int]:
    """
    Decodificação Hamming com correção de erro único.
    Retorna (bits_dados, posição_erro) — posição 0 indica sem erro.
    """
    n_total = len(bits)
    palavra = [0] + list(bits)  # índice 1-based

    # Calcula síndrome
    sindrome = 0
    p = 1
    while p <= n_total:
        paridade = 0
        for i in range(1, n_total + 1):
            if i & p:
                paridade ^= palavra[i]
        if paridade:
            sindrome += p
        p <<= 1

    # Corrige erro se síndrome != 0
    if sindrome:
        palavra[sindrome] ^= 1

    # Extrai bits de dados (posições não potência de 2)
    dados = [palavra[i] for i in range(1, n_total + 1)
             if (i & (i - 1)) != 0]
    return dados, sindrome

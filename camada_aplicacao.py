def texto_para_bits(texto):
    """converte texto em bits, mantendo a ordem mais significativa primeiro."""
    bits = []
    for byte in texto.encode("utf-8"):
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_para_texto(bits):
    """reconstrói texto a partir dos bits recebidos pelo receptor."""
    n_bytes = len(bits) // 8
    dados = bytearray()

    for i in range(n_bytes):
        byte = 0
        for bit in bits[i * 8:(i + 1) * 8]:
            byte = (byte << 1) | bit
        dados.append(byte)

    return dados.decode("utf-8", errors="replace")

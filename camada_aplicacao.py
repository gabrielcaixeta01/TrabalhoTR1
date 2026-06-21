# -*- coding: utf-8 -*-
def texto_para_bits(texto):
    # Converte uma string em uma lista de bits (codificador em bits do TX).
    # A -> byte 0x41 -> [0, 1, 0, 0, 0, 0, 0, 1]
    
    bits = []
    for byte in texto.encode("utf-8"):          
        for i in range(7, -1, -1):              
            bits.append((byte >> i) & 1)    
    return bits


def bits_para_texto(bits):
    # Converte uma lista de bits de volta para string (conversor do RX).
    
    n_bytes = len(bits) // 8 
    dados = bytearray() 
    
    for i in range(n_bytes):
        byte = 0
        for bit in bits[i * 8:(i + 1) * 8]:    
            byte = (byte << 1) | bit           
        dados.append(byte)

    return dados.decode("utf-8", errors="replace") # esse replace insere um <EFBFBD> ao inves de travar o programa
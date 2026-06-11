# -*- coding: utf-8 -*-
"""
TESTES DE IDA E VOLTA
=====================
Roda sem GTK: `python3 testes.py`.

A estratégia de todos os testes é a mesma do README: aplicar a operação
de TX e a de RX em sequência e verificar que a saída é IDÊNTICA à
entrada (sem ruído), além de alguns casos com valores conhecidos (CRC)
e com erros injetados manualmente (paridade, CRC, Hamming).
"""

import random

import camada_aplicacao as app
import camada_enlace as enlace
import camada_fisica as fisica
import meio_comunicacao as meio
import simulador


def _bits_aleatorios(n_bytes):
    """Gera n_bytes*8 bits pseudoaleatórios para os testes."""
    return [random.randint(0, 1) for _ in range(n_bytes * 8)]


def testar(nome, condicao):
    """Imprime PASS/FAIL e acumula falhas."""
    print(f"[{'PASS' if condicao else 'FAIL'}] {nome}")
    return condicao


def main():
    random.seed(42)                              # testes reprodutíveis
    ok = True
    texto = "Mensagem de teste TR1 - açúcar, çãõ, 123! ~}"

    # ---------------- aplicação ----------------
    bits = app.texto_para_bits(texto)
    ok &= testar("aplicacao: texto -> bits -> texto",
                 app.bits_para_texto(bits) == texto)

    # ---------------- enquadramento ----------------
    payloads = [_bits_aleatorios(7) for _ in range(3)]
    for tipo in ("contagem", "bytes", "bits"):
        fluxo = enlace._ENQUADRAR[tipo](payloads)
        ok &= testar(f"enquadramento '{tipo}': ida e volta",
                     enlace._DESENQUADRAR[tipo](fluxo) == payloads)

    # Caso crítico do bit stuffing: payload cheio de 1s (força o stuffing).
    p = [[1] * 40]
    fluxo = enlace.enquadrar_bits(p)
    ok &= testar("bit stuffing com payload só de 1s",
                 enlace.desenquadrar_bits(fluxo) == p)

    # Caso crítico do byte stuffing: payload contendo FLAG e ESC.
    p = [enlace._bytes_para_bits([0x7E, 0x7D, 0x41, 0x7E])]
    fluxo = enlace.enquadrar_bytes(p)
    ok &= testar("byte stuffing com FLAG/ESC no payload",
                 enlace.desenquadrar_bytes(fluxo) == p)

    # ---------------- detecção de erros ----------------
    dados = _bits_aleatorios(10)
    for tipo in ("paridade", "checksum", "crc"):
        com_edc = enlace._ADICIONAR_EDC[tipo](dados)
        payload, valido = enlace._VERIFICAR_EDC[tipo](com_edc)
        ok &= testar(f"{tipo}: aceita payload íntegro",
                     valido and payload == dados)
        corrompido = com_edc[:]
        corrompido[3] ^= 1                       # inverte 1 bit
        _, valido = enlace._VERIFICAR_EDC[tipo](corrompido)
        ok &= testar(f"{tipo}: detecta 1 bit invertido", not valido)

    # CRC-32 contra valor conhecido: CRC32("123456789") = 0xCBF43926.
    bits_123 = app.texto_para_bits("123456789")
    ok &= testar("crc32 do vetor de teste '123456789' == 0xCBF43926",
                 enlace._calcular_crc32(bits_123) == 0xCBF43926)

    # ---------------- Hamming ----------------
    dados = _bits_aleatorios(6)
    cod = enlace.codificar_hamming(dados)
    dec, n, duplo = enlace.decodificar_hamming(cod)
    ok &= testar("hamming: ida e volta sem erro",
                 dec == dados and n == 0 and not duplo)
    cod_err = cod[:]
    cod_err[5] ^= 1                              # 1 erro no 1º bloco
    dec, n, _ = enlace.decodificar_hamming(cod_err)
    ok &= testar("hamming: corrige 1 bit invertido", dec == dados and n == 1)
    cod_err[6] ^= 1                              # 2º erro no mesmo bloco
    _, _, duplo = enlace.decodificar_hamming(cod_err)
    ok &= testar("hamming: detecta erro duplo", duplo)

    # ---------------- camada física ----------------
    bits = _bits_aleatorios(5)
    for tipo in fisica.MODULACOES_DIGITAIS:
        sinal = fisica.modular_digital(bits, tipo)
        ok &= testar(f"banda-base '{tipo}': ida e volta sem ruído",
                     fisica.demodular_digital(sinal, tipo) == bits)
        ruidoso = meio.transmitir(sinal, 0.0, 0.2)
        ok &= testar(f"banda-base '{tipo}': ida e volta com ruído σ=0.2",
                     fisica.demodular_digital(ruidoso, tipo) == bits)

    for tipo in fisica.MODULACOES_PORTADORA:
        sinal = fisica.modular_portadora(bits, tipo)
        demod = fisica.demodular_portadora(sinal, tipo)
        ok &= testar(f"portadora '{tipo}': ida e volta sem ruído",
                     demod[:len(bits)] == bits)  # ignora padding final
        ruidoso = meio.transmitir(sinal, 0.0, 0.1)
        demod = fisica.demodular_portadora(ruidoso, tipo)
        ok &= testar(f"portadora '{tipo}': ida e volta com ruído σ=0.1",
                     demod[:len(bits)] == bits)

    # ---------------- simulação completa ----------------
    for enq in ("contagem", "bytes", "bits"):
        for port in ("nenhuma", "ask", "fsk", "qpsk", "16qam"):
            config = dict(simulador.CONFIG_PADRAO,
                          texto=texto, enquadramento=enq,
                          mod_portadora=port, ruido_sigma=0.05)
            r = simulador.executar_simulacao(config)
            ok &= testar(f"simulação completa enq={enq} portadora={port}",
                         r["rx_texto"] == texto)

    print("\nRESULTADO GERAL:", "TODOS OS TESTES PASSARAM" if ok
          else "HÁ TESTES FALHANDO")


if __name__ == "__main__":
    main()
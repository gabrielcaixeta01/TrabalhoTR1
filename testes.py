# -*- coding: utf-8 -*-
"""
TESTES DE IDA E VOLTA
=====================
Roda sem GTK: `python3 testes.py`.

COMO USAR DURANTE O DESENVOLVIMENTO
  Cada função ainda não implementada lança NotImplementedError; o teste dela
  aparece como [TODO] (não derruba os demais). Conforme vocês implementam, os
  [TODO] viram [PASS] (ou [FAIL], se há bug). O objetivo é zerar os [TODO] e
  os [FAIL].

ESTRATÉGIA
  Aplicar a operação de TX e a de RX em sequência e verificar que a saída é
  IDÊNTICA à entrada (sem ruído), além de casos com valores conhecidos (CRC-32)
  e com erros injetados manualmente (paridade, checksum, CRC, Hamming).
"""

import random

import camada_aplicacao as app
import camada_enlace as enlace
import camada_fisica as fisica
import meio_comunicacao as meio
import simulador

RESULTADOS = {"PASS": 0, "FAIL": 0, "TODO": 0}


def _bits_aleatorios(n_bytes):
    """Gera n_bytes*8 bits pseudoaleatórios para os testes."""
    return [random.randint(0, 1) for _ in range(n_bytes * 8)]


def testar(nome, funcao):
    """Executa `funcao` (sem argumentos, devolve bool) e imprime o resultado.

    PASS  -> a função devolveu True
    FAIL  -> devolveu False ou lançou outra exceção (bug)
    TODO  -> lançou NotImplementedError (função ainda não implementada)
    """
    try:
        status = "PASS" if funcao() else "FAIL"
    except NotImplementedError as erro:
        status = "TODO"
        nome += f"   (falta implementar: {erro})"
    except Exception as erro:  # um bug não deve esconder os outros testes
        status = "FAIL"
        nome += f"   (exceção: {type(erro).__name__}: {erro})"
    RESULTADOS[status] += 1
    print(f"[{status}] {nome}")


def main():
    random.seed(42)                              # testes reprodutíveis
    texto = "Mensagem de teste TR1 - açúcar, çãõ, 123! ~}"

    # ---------------- meio de comunicação ----------------
    testar("meio: sigma=0 devolve o mesmo sinal",
           lambda: meio.transmitir([1.0, -1.0, 0.5], 0.0, 0.0) == [1.0, -1.0, 0.5])
    testar("meio: ruído muda o sinal mas mantém o tamanho",
           lambda: (lambda r: len(r) == 1000 and r != [0.0] * 1000)(
               meio.transmitir([0.0] * 1000, 0.0, 0.5)))
    testar("meio: potência de [1,-1,1,-1] == 1 W",
           lambda: abs(meio.potencia_media([1, -1, 1, -1]) - 1.0) < 1e-9)

    # ---------------- aplicação ----------------
    testar("aplicacao: 'A' -> 01000001",
           lambda: app.texto_para_bits("A") == [0, 1, 0, 0, 0, 0, 0, 1])
    testar("aplicacao: texto -> bits -> texto (com acentos)",
           lambda: app.bits_para_texto(app.texto_para_bits(texto)) == texto)

    # ---------------- enquadramento ----------------
    payloads = [_bits_aleatorios(7) for _ in range(3)]
    for tipo in ("contagem", "entrelacamento", "bytes", "bits"):
        testar(f"enquadramento '{tipo}': ida e volta",
               lambda tipo=tipo: enlace.DESENQUADRAR[tipo](
                   enlace.ENQUADRAR[tipo](payloads)) == payloads)


    # Exemplo 7x7 do slide 24 (TR1_09): linha de paridade por coluna.
    def paridade_slide():
        linhas = ("1001110", "1100101", "1110100", "1110111",
                  "1101111", "1110010", "1101011")
        matriz = [int(c) for linha in linhas for c in linha]
        return enlace.entrelacar(matriz, 7)[-7:] == [1, 0, 1, 1, 1, 1, 0]
    testar("entrelaçamento: paridade do exemplo 7x7 dos slides == 1011110",
           paridade_slide)
    testar("contagem: 2 bytes de dados -> cabeçalho vale 3 (inclui o cabeçalho)",
           lambda: enlace.enquadrar_contagem([_bits_aleatorios(2)])[:8]
           == [0, 0, 0, 0, 0, 0, 1, 1])

    # Caso crítico do bit stuffing: payload cheio de 1s (força o stuffing).
    p_uns = [[1] * 40]
    testar("bit stuffing com payload só de 1s",
           lambda: enlace.desenquadrar_bits(enlace.enquadrar_bits(p_uns)) == p_uns)

    # Caso crítico do byte stuffing: payload contendo FLAG e ESC.
    def byte_stuffing():
        p_flag = [enlace.bytes_para_bits([0x7E, 0x7D, 0x41, 0x7E])]
        return enlace.desenquadrar_bytes(enlace.enquadrar_bytes(p_flag)) == p_flag
    testar("byte stuffing com FLAG/ESC no payload", byte_stuffing)

    # Padding das modulações: zeros no fim do fluxo não podem virar quadros.
    for tipo in ("contagem", "entrelacamento", "bytes", "bits"):
        testar(f"enquadramento '{tipo}': ignora padding de zeros no final",
               lambda tipo=tipo: enlace.DESENQUADRAR[tipo](
                   enlace.ENQUADRAR[tipo](payloads) + [0] * 4) == payloads)

    # ---------------- detecção de erros ----------------
    dados = _bits_aleatorios(10)
    for tipo in ("paridade", "checksum", "crc"):
        def integro(tipo=tipo):
            payload, valido = enlace.VERIFICAR_EDC[tipo](
                enlace.ADICIONAR_EDC[tipo](dados))
            return valido and payload == dados

        def com_erro(tipo=tipo):
            corrompido = enlace.ADICIONAR_EDC[tipo](dados)[:]
            corrompido[3] ^= 1                   # inverte 1 bit
            return not enlace.VERIFICAR_EDC[tipo](corrompido)[1]

        testar(f"{tipo}: aceita payload íntegro", integro)
        testar(f"{tipo}: detecta 1 bit invertido", com_erro)

    testar("EDC: tamanhos batem com TAMANHO_EDC",
           lambda: all(len(enlace.ADICIONAR_EDC[t](dados)) - len(dados)
                       == 8 * enlace.TAMANHO_EDC[t]
                       for t in ("paridade", "checksum", "crc")))
    # CRC (divisão módulo 2 pura): uma rajada de até 32 bits é sempre detectada.
    def crc_rajada():
        com_crc = enlace.adicionar_crc32(dados)
        return all(not enlace.verificar_crc32(
            com_crc[:i] + [b ^ 1 for b in com_crc[i:i + 32]] + com_crc[i + 32:])[1]
            for i in range(0, len(com_crc) - 32, 7))
    testar("crc32: detecta rajada de 32 bits invertidos", crc_rajada)

    # ---------------- Hamming ----------------
    dados = _bits_aleatorios(6)
    testar("hamming: ida e volta sem erro",
           lambda: enlace.decodificar_hamming(enlace.codificar_hamming(dados))
           == (dados, 0, False))

    def hamming_1_erro():
        cod = enlace.codificar_hamming(dados)
        cod[5] ^= 1                              # 1 erro no 1º bloco (11 bits)
        dec, n, duplo = enlace.decodificar_hamming(cod)
        return dec == dados and n == 1 and not duplo

    testar("hamming: corrige 1 bit invertido", hamming_1_erro)
    def hamming_todas_posicoes():
        cod = enlace.codificar_hamming(dados)
        for pos in range(11):                    # 1 erro em cada posição do 1º bloco
            err = cod[:]
            err[pos] ^= 1
            if enlace.decodificar_hamming(err)[0] != dados:
                return False
        return True

    testar("hamming (11,7): corrige 1 erro em cada uma das 11 posições",
           hamming_todas_posicoes)

    # ---------------- camada física: constelações ----------------
    testar("8PSK: mapa com 8 pontos distintos no raio V",
           lambda: len(fisica.MAPA_8PSK) == 8 and all(
               abs(i * i + q * q - fisica.V ** 2) < 1e-9
               for i, q in fisica.MAPA_8PSK.values()))
    testar("32-QAM: mapa com 32 rótulos e 32 pontos distintos",
           lambda: len(fisica.MAPA_32QAM) == 32
           and len(set(fisica.MAPA_32QAM.values())) == 32)

    # ---------------- camada física: modulações ----------------
    bits = _bits_aleatorios(5)
    for tipo in fisica.MODULACOES_DIGITAIS:
        testar(f"banda-base '{tipo}': ida e volta sem ruído",
               lambda tipo=tipo: fisica.demodular_digital(
                   fisica.modular_digital(bits, tipo), tipo) == bits)
        testar(f"banda-base '{tipo}': ida e volta com ruído sigma=0.2",
               lambda tipo=tipo: fisica.demodular_digital(
                   meio.transmitir(fisica.modular_digital(bits, tipo), 0.0, 0.2),
                   tipo) == bits)

    for tipo in fisica.MODULACOES_PORTADORA:
        testar(f"portadora '{tipo}': ida e volta sem ruído",
               lambda tipo=tipo: fisica.demodular_portadora(
                   fisica.modular_portadora(bits, tipo), tipo)[:len(bits)] == bits)
        testar(f"portadora '{tipo}': ida e volta com ruído sigma=0.1",
               lambda tipo=tipo: fisica.demodular_portadora(
                   meio.transmitir(fisica.modular_portadora(bits, tipo), 0.0, 0.1),
                   tipo)[:len(bits)] == bits)

    # ---------------- simulação completa ----------------
    for enq in ("contagem", "entrelacamento", "bytes", "bits"):
        for port in ("nenhuma",) + tuple(fisica.MODULACOES_PORTADORA):
            def completa(enq=enq, port=port):
                config = dict(simulador.CONFIG_PADRAO,
                              texto=texto, enquadramento=enq,
                              mod_portadora=port, ruido_sigma=0.05)
                return simulador.executar_simulacao(config)["rx_texto"] == texto
            testar(f"simulação completa enq={enq} portadora={port}", completa)

    print(f"\nRESUMO: {RESULTADOS['PASS']} PASS | {RESULTADOS['FAIL']} FAIL | "
          f"{RESULTADOS['TODO']} TODO")
    if RESULTADOS["FAIL"] == 0 and RESULTADOS["TODO"] == 0:
        print("TODOS OS TESTES PASSARAM")


if __name__ == "__main__":
    main()

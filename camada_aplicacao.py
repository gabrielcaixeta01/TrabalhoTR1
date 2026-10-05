# -*- coding: utf-8 -*-
"""
CAMADA DE APLICAÇÃO (chat de texto)
===================================
Enunciado, seção 1.4: a aplicação é um chat de texto. Aqui ficam só as duas
conversões que ligam o mundo "humano" (strings) ao mundo da rede (bits):

  TX: texto digitado  ->  texto_para_bits()  ->  bits para a camada de enlace
  RX: bits da camada de enlace  ->  bits_para_texto()  ->  texto legível

CONVENÇÕES DO PROJETO (valem para TODOS os módulos):
  - Bits   = list[int] com valores 0 ou 1.
  - Ordem  = MSB primeiro (o bit mais significativo de cada byte vem antes).
             Ex.: 'A' = 0x41 = 01000001 -> [0, 1, 0, 0, 0, 0, 0, 1]
  - Codificação de caracteres = UTF-8 (superconjunto do ASCII que o
    enunciado cita; assim acentos como 'ç' e 'ã' também funcionam).
"""


def texto_para_bits(texto):
    """Converte uma string em uma lista de bits (codificador em bits do TX).

    OBJETIVO
        Transformar o texto digitado na GUI na sequência de bits que será o
        payload entregue à camada de enlace ("Integração Vertical").

    COMO FAZER
        1. Converta a string em bytes:  texto.encode("utf-8")
           (devolve um objeto `bytes`; iterar sobre ele dá inteiros 0..255).
        2. Para cada byte, extraia os 8 bits do MAIS significativo (bit 7)
           para o MENOS significativo (bit 0).
        3. Para extrair o bit de posição i de um byte use deslocamento + máscara:
               bit = (byte >> i) & 1
           `byte >> i` empurra o bit i para a posição 0 e `& 1` isola só ele.
        4. Acumule tudo em uma única lista.

    EXEMPLO
        texto_para_bits("A")  ->  [0, 1, 0, 0, 0, 0, 0, 1]
        texto_para_bits("ç")  ->  16 bits (ç ocupa 2 bytes em UTF-8)

    DICA
        range(7, -1, -1) percorre 7, 6, 5, ..., 0.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_aplicacao.texto_para_bits")


def bits_para_texto(bits):
    """Converte uma lista de bits de volta para string (conversor do RX).

    OBJETIVO
        Reconstruir a mensagem legível a partir do fluxo de bits que as
        camadas inferiores entregaram ("Saída de Dados" do receptor).

    COMO FAZER
        1. Calcule quantos bytes completos existem: len(bits) // 8
           (bits sobrando no final, que não formam um byte, são ignorados).
        2. Para cada grupo de 8 bits monte o inteiro correspondente:
               byte = 0
               para cada bit do grupo:  byte = (byte << 1) | bit
           (a cada passo "abre espaço" à direita com << 1 e encaixa o novo bit
           com |).
        3. Junte os bytes em um `bytearray` (ou em uma lista + bytes(lista)).
        4. Decodifique:  dados.decode("utf-8", errors="replace")

    POR QUE errors="replace"?
        Se o canal corromper bits, a sequência de bytes pode não ser UTF-8
        válido. Com "replace" o Python troca o trecho inválido por '�'
        em vez de lançar exceção e derrubar o simulador: queremos MOSTRAR a
        mensagem corrompida, não travar.

    EXEMPLO
        bits_para_texto([0, 1, 0, 0, 0, 0, 0, 1])  ->  "A"
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_aplicacao.bits_para_texto")

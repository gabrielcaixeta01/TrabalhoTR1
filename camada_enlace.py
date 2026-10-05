# -*- coding: utf-8 -*-
"""
CAMADA DE ENLACE
================
Implementa os três blocos exigidos no enunciado (seção 1.3):

  [1/3] ENQUADRAMENTO........ contagem de caracteres, entrelaçamento de bits,
                              FLAGs + inserção de bytes, FLAGs + inserção de bits
  [2/3] DETECÇÃO DE ERROS.... bit de paridade par, checksum, CRC-32 (IEEE 802)
  [3/3] CORREÇÃO DE ERROS.... código de Hamming

Fluxo no TRANSMISSOR (função transmitir):
  bits da aplicação
      -> divididos em blocos de até `tam_max_quadro` bytes
      -> cada bloco recebe o EDC (detecção) no final
      -> o bloco (payload + EDC) é codificado com Hamming (se habilitado)
      -> os blocos são enquadrados segundo o protocolo escolhido
      -> o resultado é um único fluxo de bits entregue à camada física

Fluxo no RECEPTOR (função receber): exatamente o caminho inverso
  desenquadrar -> Hamming (corrige) -> EDC (verifica) -> bits para a aplicação

DECISÕES DE PROJETO (o enunciado deixa em aberto; todas estão justificadas em
docs/DECISOES.md, que também alimenta o relatório):
  - Todos os EDCs geram saída alinhada em BYTES, pois contagem e inserção de
    bytes operam sobre bytes:
        paridade par -> 1 byte  (7 zeros + bit de paridade)
        checksum     -> 2 bytes (16 bits)
        CRC-32       -> 4 bytes (32 bits)
  - O Hamming é o (11,7) dos slides (TR1_09, 38-39): 7 bits de dados viram 11.
    Corrige 1 erro por bloco, mas NÃO detecta erro duplo. 11 bits não fecham
    em bytes: completamos os dados com zeros até múltiplo de 7 e a saída com
    zeros até múltiplo de 8 (o decodificador descarta o enchimento).
  - FLAG = 0x7E (01111110) e ESC = 0x7D, como no HDLC/PPP.

Ordem de implementação: ver docs/DESENVOLVIMENTO.md.
Material de estudo: estudos/02, 03 e 04. Detalhes dos slides: docs/referencias/. Decisões: docs/DECISOES.md.
"""


FLAG_BYTE = 0x7E          # 01111110 - delimitador de quadro
ESC_BYTE = 0x7D           # 01111101 - caractere de escape p/ inserção de bytes
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]

# Quantos BYTES cada técnica de detecção acrescenta ao final do payload
TAMANHO_EDC = {"nenhum": 0, "paridade": 1, "checksum": 2, "crc": 4}

# Entrelaçamento por matriz: nº de colunas (decisão de projeto; os slides não fixam N).
# Com 8 colunas cada linha é um byte e o quadro continua alinhado em bytes.
N_COLUNAS_ENTRELACAMENTO = 8


# ===========================================================================
# FUNÇÕES AUXILIARES (usadas por quase tudo neste módulo)
# ===========================================================================
def bits_para_bytes(bits):
    """Agrupa a lista de bits (múltiplo de 8) em uma lista de inteiros 0-255.

    EXEMPLO
        bits_para_bytes([0,1,0,0,0,0,0,1, 0,1,0,0,0,0,1,0])  ->  [65, 66]

    COMO FAZER
        De 8 em 8 bits: byte = 0; para cada bit: byte = (byte << 1) | bit.
        (<< 1 abre espaço à direita; | encaixa o novo bit.)
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.bits_para_bytes")


def bytes_para_bits(lista_bytes):
    """Expande cada byte (int 0-255) em 8 bits, MSB primeiro.

    EXEMPLO
        bytes_para_bits([65])  ->  [0, 1, 0, 0, 0, 0, 0, 1]

    COMO FAZER
        Para cada byte, para i de 7 até 0: bit = (byte >> i) & 1.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.bytes_para_bits")


# ===========================================================================
# [1/3] ENQUADRAMENTO
#    Cada função de TX recebe uma LISTA DE PAYLOADS (cada payload é uma lista
#    de bits alinhada em bytes) e devolve o fluxo ÚNICO de bits (todos os
#    quadros concatenados).
#    Cada função de RX faz o inverso: fluxo de bits -> lista de payloads.
#
#    ATENÇÃO - PADDING: as modulações por portadora (8PSK usa 3 bits/símbolo,
#    32-QAM usa 5) completam o fim do fluxo com bits 0 para fechar o último
#    símbolo. O desenquadramento tem de IGNORAR esse lixo final sem inventar
#    quadros extras (veja a nota em cada protocolo).
# ===========================================================================

# ------------------------- contagem de caracteres -------------------------
def enquadrar_contagem(payloads):
    """Contagem de caracteres: quadro = [1 byte de cabeçalho] + payload.

    Pelos slides (TR1_08, 28-30) a contagem INCLUI o próprio byte de cabeçalho:
    para enviar 2 bytes de dados o cabeçalho vale 3.

        | contagem (1 B) | payload (contagem - 1 bytes) | contagem | payload | ...

    O receptor lê o cabeçalho e sabe quantos bytes consumir em seguida.
    LIMITAÇÃO: o cabeçalho tem 8 bits, então o quadro inteiro (cabeçalho +
    payload) tem no máximo 255 bytes, ou seja, payload de até 254 bytes
    (transmitir() valida isso e lança ValueError).
    Fraqueza clássica (para o relatório): se um bit do cabeçalho for
    corrompido, o receptor perde o sincronismo de TODOS os quadros seguintes.

    COMO FAZER
        Para cada payload: contagem = len(payload) // 8 + 1; emita
        bytes_para_bits([contagem]) e depois o payload.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.enquadrar_contagem")


def desenquadrar_contagem(bits):
    """Percorre o fluxo lendo [contagem][payload] repetidamente.

    COMO FAZER
        pos = 0. Enquanto restarem ao menos 8 bits a partir de pos:
          1. Leia o cabeçalho (8 bits) -> contagem.
          2. contagem == 0: é o PADDING da modulação (um byte 00000000 nunca é
             um quadro válido). Pare.
          3. O payload tem (contagem - 1) bytes. Se ele ultrapassa o fim do
             fluxo, o quadro está truncado/corrompido: pare.
          4. Caso contrário guarde esses bits como payload e avance pos.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.desenquadrar_contagem")


# ----------------------- entrelaçamento de bits ---------------------------
# Algoritmo dos slides (TR1_09, 23-24):
#   1. Arrume os dados em uma matriz de M linhas x N colunas.
#   2. Calcule 1 bit de paridade (par) POR COLUNA e coloque-o numa linha extra.
#   3. Transmita linha por linha (cima para baixo, esquerda para a direita);
#      a última linha enviada é a de paridade.
#   4. O receptor remonta a matriz, recalcula a paridade de cada coluna e compara.
# Efeito: uma rajada de até N bits atinge no máximo 1 bit por coluna, e a
# paridade da coluna detecta isso.
# Exemplo dos slides (7x7): a matriz de 7 linhas
#   1001110 / 1100101 / 1110100 / 1110111 / 1101111 / 1110010 / 1101011
# gera a linha de paridade 1011110.
#
# O QUE OS SLIDES NÃO DIZEM (decisões de projeto, ver docs/DECISOES.md):
#   - o valor de N: sugestão N_COLUNAS_ENTRELACAMENTO = 8, assim cada linha é
#     um byte e a linha de paridade é 1 byte (quadro continua alinhado);
#   - como delimitar o quadro: sugestão reaproveitar a contagem de caracteres;
#   - o padding: o cabeçalho 0 da contagem encerra a leitura.
def paridade_colunas(bits, n_colunas):
    """Paridade par de cada coluna de uma matriz de linhas com n_colunas bits.

    COMO FAZER
        Crie uma lista de n_colunas zeros. Para cada bit na posição k, faça
        XOR dele na coluna k % n_colunas.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.paridade_colunas")


def entrelacar(bits, n_colunas):
    """Devolve os dados seguidos da linha de paridade das colunas.

    Como a matriz é transmitida linha a linha, "montar a matriz" é só
    interpretar os bits em linhas de n_colunas; basta anexar a paridade.
    Se len(bits) não for múltiplo de n_colunas, levante ValueError.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.entrelacar")


def desentrelacar(bits, n_colunas):
    """Inverso de entrelacar. Devolve (dados, colunas_com_erro).

    COMO FAZER
        Separe os últimos n_colunas bits (paridade recebida) do resto
        (dados), recalcule a paridade dos dados e liste os índices das
        colunas em que a paridade recebida e a calculada diferem.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.desentrelacar")


def enquadrar_entrelacamento(payloads, n_colunas=N_COLUNAS_ENTRELACAMENTO):
    """Cada payload vira uma matriz com linha de paridade, delimitada pela contagem.

    COMO FAZER (decisão de projeto)
        Aplique entrelacar() a cada payload e passe a lista resultante para
        enquadrar_contagem().
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.enquadrar_entrelacamento")


def desenquadrar_entrelacamento(bits, n_colunas=N_COLUNAS_ENTRELACAMENTO):
    """Inverso: desenquadra pela contagem e remove a linha de paridade.

    COMO FAZER
        desenquadrar_contagem() e, para cada quadro, desentrelacar() ficando
        só com os dados. (A lista de colunas com erro pode ser usada para
        sinalizar o quadro; o relatório por quadro de receber() é opcional.)
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.desenquadrar_entrelacamento")


# ------------------- FLAGs com inserção de bytes (byte stuffing) ----------
def enquadrar_bytes(payloads):
    """Quadro = FLAG + payload_com_escape + FLAG.

    PROBLEMA QUE ISSO RESOLVE
        Se os dados contiverem um byte igual à FLAG (0x7E), o receptor
        pensaria que o quadro acabou. A solução é o "byte stuffing".

    REGRA
        Percorra os bytes do payload. Se o byte for FLAG_BYTE ou ESC_BYTE,
        insira um ESC_BYTE ANTES dele. Depois feche o quadro com outra FLAG.

        Ex.: dados [0x41, 0x7E, 0x42] -> 7E 41 7D 7E 42 7E
    """
    # TODO: implementar conforme a regra acima (use bits_para_bytes e
    #       bytes_para_bits para ir e voltar entre bits e bytes).
    raise NotImplementedError("camada_enlace.enquadrar_bytes")


def desenquadrar_bytes(bits):
    """Máquina de estados sobre os bytes do fluxo.

    ESTADOS
        - fora de quadro : ignora tudo até achar uma FLAG (abre o quadro);
        - dentro de quadro:
            * byte == ESC  -> o PRÓXIMO byte é dado literal (mesmo que seja
                              FLAG ou ESC): marque `escapado = True`;
            * byte == FLAG -> fim do quadro: guarde o quadro e volte a "fora";
            * outro byte   -> é dado: acrescente ao quadro atual.
        - quadros vazios (duas FLAGs seguidas) devem ser ignorados.
    """
    # TODO: implementar a máquina de estados descrita acima.
    raise NotImplementedError("camada_enlace.desenquadrar_bytes")


# -------------------- FLAGs com inserção de bits (bit stuffing) -----------
def enquadrar_bits(payloads):
    """Quadro = FLAG(01111110) + payload_com_stuffing + FLAG.

    PROBLEMA QUE ISSO RESOLVE
        O payload não pode conter 01111110. Regra do bit stuffing (HDLC):
        sempre que o transmissor enviar CINCO bits 1 consecutivos, insere
        automaticamente um bit 0 logo depois. Assim 6 uns seguidos só
        existem na FLAG.

    COMO FAZER
        Percorra os bits do payload mantendo um contador de uns consecutivos:
        bit 1 -> contador += 1; bit 0 -> contador = 0. Ao chegar a 5, insira
        um 0 e zere o contador. Coloque FLAG_BITS antes e depois.
    """
    # TODO: implementar conforme a regra acima.
    raise NotImplementedError("camada_enlace.enquadrar_bits")


def desenquadrar_bits(bits):
    """Localiza pares de FLAGs e remove os bits de stuffing entre elas.

    COMO FAZER
        1. Procure (bit a bit, deslizando uma janela de 8) a FLAG de abertura.
        2. A partir dela procure a FLAG de fechamento. Se não achar, pare.
        3. Entre as duas FLAGs, remova o stuffing: depois de cinco 1s
           consecutivos o bit seguinte (um 0) foi inserido pelo transmissor e
           deve ser DESCARTADO; o contador de uns zera.
        4. Guarde o payload (ignore quadros vazios) e continue a busca logo
           após a FLAG de fechamento.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.desenquadrar_bits")


# ===========================================================================
# [2/3] DETECÇÃO DE ERROS
#    "adicionar_*" anexam o EDC (código de detecção) ao FINAL do payload (TX).
#    "verificar_*" devolvem (payload_sem_edc, ok: bool) (RX).
# ===========================================================================

# ----------------------------- paridade par -------------------------------
def adicionar_paridade_par(bits):
    """Anexa 1 byte: 7 zeros + o bit de paridade par de todo o payload.

    PARIDADE PAR: o bit extra é escolhido para que o total de uns (payload +
    bit de paridade) seja PAR.  paridade = (soma dos bits) % 2.
    Usamos 1 byte inteiro (7 zeros + paridade) só para manter o alinhamento
    em bytes exigido pelos enquadramentos.
    Limite (para o relatório): só detecta número ÍMPAR de bits errados.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.adicionar_paridade_par")


def verificar_paridade_par(bits):
    """Retorna (payload_sem_o_byte_de_paridade, ok).

    COMO FAZER
        O total de uns do fluxo recebido (incluindo o byte de paridade) deve
        ser par. Se len(bits) < 8 não há byte de paridade: devolva (bits, False).
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.verificar_paridade_par")


# ------------------------------- checksum ---------------------------------
def soma_complemento1(palavras):
    """Soma palavras de 16 bits em aritmética de COMPLEMENTO DE 1.

    A soma em complemento de 1 devolve ao resultado todo "vai-um" que estoura
    o 16º bit (end-around carry):
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    onde (soma & 0xFFFF) mantém os 16 bits baixos e (soma >> 16) é o carry.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.soma_complemento1")


def bits_para_palavras16(bits):
    """Agrupa os bits em palavras de 16 bits (ints 0..65535).

    Se o total não for múltiplo de 16, complete com zeros à direita.
    Use bits_para_bytes e junte dois bytes: palavra = (byte_alto << 8) | byte_baixo.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.bits_para_palavras16")


def adicionar_checksum(bits):
    """Anexa 2 bytes com o checksum (algoritmo visto em sala).

    ALGORITMO (TX)
        1. Divida o payload em palavras de 16 bits.
        2. Some todas em complemento de 1 (soma_complemento1).
        3. checksum = complemento de 1 da soma = (~soma) & 0xFFFF.
           O "& 0xFFFF" é necessário: ~ em Python produz um número NEGATIVO
           (ints têm precisão infinita); a máscara reduz a 16 bits.
        4. Anexe checksum como 2 bytes (alto primeiro).
    """
    # TODO: implementar conforme o algoritmo acima.
    raise NotImplementedError("camada_enlace.adicionar_checksum")


def verificar_checksum(bits):
    """Retorna (payload_sem_checksum, ok).

    ALGORITMO (RX)
        Some em complemento de 1 as palavras do payload MAIS a palavra do
        checksum. Se não houve erro, o resultado tem todos os 16 bits em 1
        (0xFFFF). Se len(bits) < 16 devolva (bits, False).
    """
    # TODO: implementar conforme o algoritmo acima.
    raise NotImplementedError("camada_enlace.verificar_checksum")


# -------------------------------- CRC-32 ----------------------------------
# Algoritmo dos slides (TR1_09, 30-33): divisão polinomial MÓDULO 2 pura.
#   TX: anexar k zeros à mensagem (k = grau de G), dividir por G(x) com XOR,
#       o resto de k bits é o CRC e vai no lugar dos zeros.
#   RX: dividir o quadro recebido (dados + CRC) por G(x): resto 0 = sem erro.
# Regra do gerador: o bit mais e o menos significativo de G(x) são 1.
# G(x) do CRC-32 IEEE 802 (grau 32, 33 bits):
#   x^32 + x^26 + x^23 + x^22 + x^16 + x^12 + x^11 + x^10 + x^8 + x^7 + x^5
#   + x^4 + x^2 + x + 1   ->  0x104C11DB7
# Os slides NÃO falam de valor inicial, XOR final nem reflexão de bits; a
# versão pura NÃO dá 0xCBF43926 para "123456789" (esse valor é do CRC-32 padrão
# refletido de Ethernet/zlib, que é uma variante opcional - veja estudos/03).
# É proibido usar zlib/binascii: a divisão deve ser feita à mão.
GERADOR_CRC32 = 0x104C11DB7


def resto_mod2(bits):
    """Resto da divisão polinomial módulo 2 de `bits` por GERADOR_CRC32.

    ALGORITMO (registrador de 32 bits)
        resto = 0
        para cada bit: resto = (resto << 1) | bit
                       se o bit de grau 32 do resto ficou ligado
                       (resto >> 32 != 0): resto ^= GERADOR_CRC32
        devolve resto  (um int de até 32 bits)
    """
    # TODO: implementar conforme o algoritmo acima.
    raise NotImplementedError("camada_enlace.resto_mod2")


def calcular_crc32(bits):
    """CRC = resto de M(x)*x^32 por G(x): divida (bits + 32 zeros) usando resto_mod2."""
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.calcular_crc32")


def adicionar_crc32(bits):
    """Anexa o CRC-32 do payload como 4 bytes (byte mais significativo primeiro).

    Extração dos bytes de um int de 32 bits: (crc >> 24) & 0xFF, (crc >> 16) & 0xFF,
    (crc >> 8) & 0xFF e crc & 0xFF. Converta com bytes_para_bits.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.adicionar_crc32")


def verificar_crc32(bits):
    """Retorna (payload_sem_crc, ok).

    COMO FAZER
        Como nos slides: divida o quadro INTEIRO (payload + 4 bytes de CRC)
        por G(x); resto 0 = sem erro. O payload devolvido são os bits sem os
        últimos 32. Se len(bits) < 32 devolva (bits, False).
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.verificar_crc32")


# ===========================================================================
# [3/3] CORREÇÃO DE ERROS - HAMMING (11,7)   (slides TR1_09, 38-39)
#
# 7 bits de dados + 4 de paridade = 11 bits por bloco:
#     posição:  1   2   3   4   5   6   7   8   9   10   11
#     conteúdo: P1  P2  M3  P4  M5  M6  M7  P8  M9  M10  M11
# As posições potência de 2 (1, 2, 4, 8) guardam paridade; as demais
# (3, 5, 6, 7, 9, 10, 11) guardam os dados. Paridade PAR (^ = XOR):
#     P1 = M3 ^ M5 ^ M7 ^ M9 ^ M11
#     P2 = M3 ^ M6 ^ M7 ^ M10 ^ M11
#     P4 = M5 ^ M6 ^ M7
#     P8 = M9 ^ M10 ^ M11
#
# DECODIFICAÇÃO - a SÍNDROME:
#   s1 = P1 ^ M3 ^ M5 ^ M7 ^ M9 ^ M11   (idem s2, s4, s8, sempre incluindo o
#   próprio bit de paridade recebido). S = (s8 s4 s2 s1) em binário.
#   S == 0 -> sem erro;  S > 0 -> S é a POSIÇÃO (1..11) do bit errado: inverta-o.
# Sem paridade geral (não é SECDED): erro duplo não é detectado. Só dá para
# suspeitar quando S > 11 (posição inexistente).
#
# ALINHAMENTO (decisão de projeto, os slides não tratam): complete os dados com
# zeros até múltiplo de 7 e a SAÍDA com zeros até múltiplo de 8 (o enquadramento
# trabalha em bytes). O decodificador descarta o enchimento no final.
# ===========================================================================
def codificar_hamming(bits):
    """Codifica o payload em blocos Hamming(11,7).

    COMO FAZER
        1. Complete bits com zeros até múltiplo de 7.
        2. Para cada bloco de 7 bits: crie um vetor de 11 posições, coloque os
           dados nas posições 3, 5, 6, 7, 9, 10, 11, calcule P1, P2, P4, P8 e
           coloque-os nas posições 1, 2, 4, 8.
        3. Concatene os blocos e complete a saída com zeros até múltiplo de 8.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.codificar_hamming")


def decodificar_hamming(bits):
    """Decodifica blocos Hamming(11,7), corrigindo até 1 erro por bloco.

    Retorna (dados, n_corrigidos, erro_incorrigivel):
      - dados             : bits de dados recuperados (7 por bloco de 11),
                            cortados para um múltiplo de 8 (sem o enchimento);
      - n_corrigidos      : quantos bits foram corrigidos no total;
      - erro_incorrigivel : True se alguma síndrome apontou posição > 11.

    COMO FAZER
        Para cada bloco COMPLETO de 11 bits (use len(bits) // 11 blocos; o resto
        é enchimento): calcule s1, s2, s4, s8 e a síndrome. Se 0 < S <= 11,
        inverta a posição S (trabalhe numa CÓPIA) e conte a correção. Se S > 11
        marque erro_incorrigivel. Extraia os dados das posições 3, 5, 6, 7, 9,
        10, 11.
    """
    # TODO: implementar conforme a descrição acima.
    raise NotImplementedError("camada_enlace.decodificar_hamming")


# ===========================================================================
# ORQUESTRAÇÃO DA CAMADA (chamada pelo Simulador)
# As tabelas abaixo ligam o texto escolhido na GUI à função correspondente.
# ===========================================================================
ENQUADRAR = {"contagem": enquadrar_contagem,
             "entrelacamento": enquadrar_entrelacamento,
             "bytes": enquadrar_bytes,
             "bits": enquadrar_bits}
DESENQUADRAR = {"contagem": desenquadrar_contagem,
                "entrelacamento": desenquadrar_entrelacamento,
                "bytes": desenquadrar_bytes,
                "bits": desenquadrar_bits}
ADICIONAR_EDC = {"nenhum": lambda b: b,
                 "paridade": adicionar_paridade_par,
                 "checksum": adicionar_checksum,
                 "crc": adicionar_crc32}
VERIFICAR_EDC = {"nenhum": lambda b: (b, True),
                 "paridade": verificar_paridade_par,
                 "checksum": verificar_checksum,
                 "crc": verificar_crc32}


def transmitir(bits, config):
    """Pipeline completo da camada de enlace no TRANSMISSOR.

    `config` usa as chaves: 'enquadramento', 'deteccao', 'correcao' e
    'tam_max_quadro' (em BYTES de dados da aplicação por quadro).

    COMO FAZER
        1. Valide: na "contagem" (e no "entrelacamento", que usa a contagem) o
           quadro inteiro precisa caber em 255 bytes, contando o cabeçalho
           (1 byte) e, no entrelaçamento, a linha de paridade (1 byte):
               tam_final = tam_max_quadro + TAMANHO_EDC[deteccao]
               se correcao == "hamming": tam_final = bytes da saída de
                   codificar_hamming para esse nº de bits
           Se tam_final + cabeçalho (+ paridade) passar de 255, lance
           ValueError("Quadro final excede 255 bytes ...").
        2. Divida `bits` em blocos de tam_max_quadro * 8 bits (o último pode
           ser menor).
        3. Para cada bloco, NESTA ORDEM:
             a) ADICIONAR_EDC[deteccao](bloco)       # anexa o EDC
             b) codificar_hamming(bloco), se correcao == "hamming"
                                                      # protege payload + EDC
        4. Passe a lista de payloads para ENQUADRAR[enquadramento] e devolva
           o fluxo de bits.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.transmitir")


def receber(bits, config):
    """Pipeline inverso no RECEPTOR.

    Retorna (bits_da_aplicacao, relatorio). `relatorio` é uma lista de
    dicionários (um por quadro) que a GUI mostra, com as chaves:
        "quadro"     : nº do quadro (1, 2, ...)
        "corrigidos" : bits corrigidos pelo Hamming nesse quadro
        "erro_duplo" : True se o Hamming apontou erro incorrigível (síndrome > 11)
        "edc_ok"     : True se o EDC confere

    COMO FAZER (ordem inversa do transmissor)
        1. payloads = DESENQUADRAR[enquadramento](bits)
        2. Para cada payload:
             a) se correcao == "hamming": decodificar_hamming (corrige)
             b) VERIFICAR_EDC[deteccao] -> (payload_sem_edc, ok)
             c) acrescente payload_sem_edc aos bits da aplicação e registre
                o dicionário do relatório.
        Quadros com EDC inválido são SINALIZADOS no relatório (o enunciado
        permite "descartar ou sinalizar"). DECISÃO DE PROJETO (docs/DECISOES.md):
        os bits do quadro são MANTIDOS no texto recebido e o quadro é marcado
        com edc_ok = False; assim a GUI mostra o erro e o texto corrompido.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("camada_enlace.receber")

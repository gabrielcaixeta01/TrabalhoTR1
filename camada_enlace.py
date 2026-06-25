# -*- coding: utf-8 -*-
"""
CAMADA DE ENLACE
================
Implementa os três blocos exigidos no enunciado:

  1) ENQUADRAMENTO............ contagem de caracteres, FLAGs + inserção de
                               bytes, FLAGs + inserção de bits
  2) DETECÇÃO DE ERROS........ bit de paridade par, checksum (complemento
                               de 1, 16 bits), CRC-32 (IEEE 802)
  3) CORREÇÃO DE ERROS........ código de Hamming

Fluxo no TRANSMISSOR (função transmitir):
  bits da aplicação
      -> divididos em blocos de até `tam_max_quadro` bytes
      -> cada bloco recebe o EDC (detecção) no final
      -> o bloco (payload + EDC) é codificado com Hamming (se habilitado)
      -> cada bloco vira um quadro segundo o enquadramento escolhido
      -> os quadros são concatenados em um único fluxo de bits

Fluxo no RECEPTOR (função receber): exatamente o caminho inverso.

DECISÕES DE PROJETO (documentar no relatório):
  - Todos os EDCs foram desenhados para gerar saída alinhada em BYTES,
    pois os enquadramentos de contagem e de inserção de bytes operam
    sobre bytes:
        paridade par -> 1 byte  (7 zeros + bit de paridade)
        checksum     -> 2 bytes (16 bits)
        CRC-32       -> 4 bytes (32 bits)
  - O Hamming usado é o Hamming(8,4) estendido (SECDED): cada 4 bits de
    dados viram 8 bits de código. Isso DOBRA o tamanho do payload, mas
    mantém o alinhamento em bytes e permite corrigir 1 erro e detectar
    2 erros por bloco de 8 bits.
  - FLAG = 0x7E (01111110) e ESC = 0x7D, como no HDLC/PPP.
"""


FLAG_BYTE = 0x7E          # 01111110 - delimitador de quadro 
ESC_BYTE = 0x7D           # 01111101 - caractere de escape p/ inserção de bytes
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]

# quantos bytes cada técnica de detecção acrescenta ao final do payload
TAMANHO_EDC = {"nenhum": 0, "paridade": 1, "checksum": 2, "crc": 4}



def bits_para_bytes(bits):
    """Agrupa a lista de bits (múltipla de 8) em uma lista de inteiros 0-255."""
    resultado = []
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        resultado.append(byte)
    return resultado


def bytes_para_bits(lista_bytes):
    """Expande cada byte (int 0-255) em 8 bits, MSB primeiro."""
    bits = []
    for byte in lista_bytes:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            bits.append(bit)
    return bits


# ===========================================================================
# 1) enquadramento
#    no tx, cada função recebe payloads e devolve um fluxo único de bits.
#    no rx, cada função faz o caminho inverso.
# ===========================================================================

# ------------------------- contagem de caracteres -------------------------
def enquadrar_contagem(payloads):
    """Quadro = [1 byte de cabeçalho com o nº de bytes do payload] + payload.

    O receptor lê o cabeçalho e sabe exatamente quantos bytes consumir.
    Limitação: o cabeçalho tem 8 bits, logo o payload de um quadro pode
    ter no máximo 255 bytes (validado em transmitir()).
    """
    fluxo = []
    for payload in payloads:
        n_bytes = len(payload) // 8
        fluxo += bytes_para_bits([n_bytes])    # cabeçalho com a contagem
        fluxo += payload                        # payload em seguida
    return fluxo


def desenquadrar_contagem(bits):
    """Percorre o fluxo lendo [contagem][payload] repetidamente."""
    payloads = []
    pos = 0
    while pos + 8 <= len(bits):
        n_bytes = bits_para_bytes(bits[pos:pos + 8])[0]   # lê o cabeçalho
        pos += 8
        if n_bytes == 0:
            # byte 0x00 indica padding da portadora; não é quadro real.
            break
        fim = pos + n_bytes * 8
        if fim > len(bits):
            break                                # quadro truncado/corrompido
        payloads.append(bits[pos:fim])
        pos = fim
    return payloads


# ------------------- flags com inserção de bytes (byte stuffing) ----------
def enquadrar_bytes(payloads):
    """Quadro = FLAG + payload_com_escape + FLAG.

    Se um byte do payload for igual à FLAG ou ao ESC, inserimos um ESC
    antes dele. Assim o receptor nunca confunde dados com delimitador.
    """
    fluxo = []
    for payload in payloads:
        quadro = [FLAG_BYTE]                     # abre o quadro
        for byte in bits_para_bytes(payload):
            if byte in (FLAG_BYTE, ESC_BYTE):    # byte "perigoso"?
                quadro.append(ESC_BYTE)          # insere escape antes dele
            quadro.append(byte)
        quadro.append(FLAG_BYTE)                 # fecha o quadro
        fluxo += bytes_para_bits(quadro)
    return fluxo


def desenquadrar_bytes(bits):
    """Máquina de estados sobre os bytes do fluxo:

    - fora de quadro: ignora tudo até achar uma FLAG;
    - dentro de quadro: ESC -> o próximo byte é dado literal;
                        FLAG -> fim do quadro atual.
    """
    payloads = []
    bytes_fluxo = bits_para_bytes(bits)
    dentro, escapado, atual = False, False, []
    for byte in bytes_fluxo:
        if not dentro:
            if byte == FLAG_BYTE:                # achou o início de um quadro
                dentro, atual = True, []
            continue
        if escapado:                             # byte após esc: sempre dado
            atual.append(byte)
            escapado = False
        elif byte == ESC_BYTE:
            escapado = True                      # marca p/ aceitar o próximo
        elif byte == FLAG_BYTE:                  # flag de fechamento
            if atual:                            # ignora quadros vazios
                payloads.append(bytes_para_bits(atual))
            dentro = False
        else:
            atual.append(byte)
    return payloads


# -------------------- flags com inserção de bits (bit stuffing) -----------
def enquadrar_bits(payloads):
    """Quadro = FLAG(01111110) + payload_stuffed + FLAG.

    Stuffing: após CINCO bits 1 consecutivos no payload, insere-se um 0.
    Garante que a sequência 01111110 jamais apareça dentro dos dados.
    """
    fluxo = []
    for payload in payloads:
        trem, uns = [], 0
        for bit in payload:
            trem.append(bit)

            if bit == 1:
                uns += 1
            else:
                uns = 0

            if uns == 5:
                trem.append(0)                
                uns = 0

        fluxo += FLAG_BITS + trem + FLAG_BITS
    return fluxo


def desenquadrar_bits(bits):
    """Localiza pares de FLAGs e remove os bits de stuffing entre elas."""
    payloads = []
    i = 0
    n = len(bits)
    while i + 8 <= n:
        if bits[i:i + 8] != FLAG_BITS:           # procura a flag de abertura
            i += 1
            continue
        j = i + 8                                # procura a flag de fechamento

        while j + 8 <= n and bits[j:j + 8] != FLAG_BITS:
            j += 1
        if j + 8 > n:                            # não há fechamento: descarta
            break

        # remove o stuffing: o 0 depois de cinco 1s é descartado.
        payload, uns, k = [], 0, i + 8
        while k < j:
            bit = bits[k]
            if uns == 5:                    # este bit é o 0 inserido pelo stuffing
                uns = 0                     # descarta (não adiciona ao payload)

            else:
                payload.append(bit)
                if bit == 1:
                    uns += 1

                else:
                    uns = 0

            k += 1

        if payload:
            payloads.append(payload)

        i = j + 8                                # continua após o fechamento
    return payloads


# ===========================================================================
# 2) detecção de erros
#    adicionar_* anexa o edc ao fim do payload; verificar_* remove e valida.
# ===========================================================================

# ----------------------------- paridade par -------------------------------
def adicionar_paridade_par(bits):
    # anexa 1 byte: 7 zeros + o bit de paridade par do payload.
    paridade = sum(bits) % 2                     # 1 se nº de 1s for ímpar
    return bits + [0] * 7 + [paridade]


def verificar_paridade_par(bits):
    # recalcula a paridade: a soma dos bits deve ser par.
    if len(bits) < 8:
        return bits, False
    ok = (sum(bits) % 2) == 0
    return bits[:-8], ok                         # remove o byte de paridade


# ------------------------------- checksum ---------------------------------
def soma_complemento1(palavras):
    """Soma palavras de 16 bits em aritmética de complemento de 1:
    todo "vai-um" que estoura o 16º bit é somado de volta no resultado
    (end-around carry."""
    soma = 0
    for palavra in palavras:
        soma += palavra
        # (soma & 0xffff) mantém só os 16 bits baixos
        # (soma >> 16) pega o carry que "estourou" os 16 bits e soma de volta
        soma = (soma & 0xFFFF) + (soma >> 16)
    return soma


def bits_para_palavras16(bits):
    # agrupa os bits em palavras de 16 bits, completando com zeros se necessário
    bits = bits + [0] * ((-len(bits)) % 16)    
    palavras = []
    for i in range(0, len(bits), 16):
        byte_alto = bits_para_bytes(bits[i:i + 8])[0]        # 8 bits mais altos
        byte_baixo = bits_para_bytes(bits[i + 8:i + 16])[0]  # 8 bits mais baixos

        palavra = (byte_alto << 8) | byte_baixo  # junta os dois bytes em 16 bits
        palavras.append(palavra)

    return palavras


def adicionar_checksum(bits):
    # anexa 2 bytes com o complemento de 1 da soma das palavras de 16 bits.

    soma = soma_complemento1(bits_para_palavras16(bits))
    checksum = (~soma) & 0xFFFF                  # sem o ffff ia virar um num negativo e nao complemento de 1

    return bits + bytes_para_bits([checksum >> 8, checksum & 0xFF])


def verificar_checksum(bits):
    # soma payload + checksum em complemento de 1 e compara com 0xffff.
    if len(bits) < 16:
        return bits, False
    payload = bits[:-16]
    total = soma_complemento1(bits_para_palavras16(payload) + bits_para_palavras16(bits[-16:]))
    return payload, total == 0xFFFF


# -------------------------------- crc-32 ----------------------------------
# implementação bit a bit do crc-32 ieee 802, sem zlib.
# o vetor "123456789" é usado nos testes para conferir 0xcbf43926.
POLI_CRC32_REFLETIDO = 0xEDB88320


def calcular_crc32(bits):
    """Divisão polinomial bit a bit em GF(2).

    O algoritmo refletido processa cada byte do LSB para o MSB; como a
    nossa convenção de lista é MSB primeiro, percorremos cada grupo de 8
    bits de trás para frente.
    """
    crc = 0xFFFFFFFF                             # registrador começa em todos 1s
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        for bit in reversed(byte):               # bit menos significativo primeiro
            # (crc ^ bit) & 1 compara a entrada com o bit baixo do registrador
            # se o resultado for 1, aplica xor com o polinômio
            # se for 0: apenas desloca (o bit se cancela sem deixar rastro)
            if (crc ^ bit) & 1:
                crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF                      # xor final do padrão crc-32


def adicionar_crc32(bits):
    """Anexa o CRC-32 do payload como 4 bytes (MSB primeiro)."""
    crc = calcular_crc32(bits)
    return bits + bytes_para_bits([(crc >> 24) & 0xFF, (crc >> 16) & 0xFF,
                                    (crc >> 8) & 0xFF, crc & 0xFF])


def verificar_crc32(bits):
    """Recalcula o CRC do payload e compara com os 4 bytes recebidos."""
    if len(bits) < 32:
        return bits, False
    payload = bits[:-32]
    recebido = 0
    for b in bits[-32:]:                         # remonta o crc recebido
        recebido = (recebido << 1) | b
    return payload, calcular_crc32(payload) == recebido


# ===========================================================================
# 3) correção de erros - hamming(8,4) estendido
#
# cada bloco de 4 bits de dados vira 8 bits:
#     posição:  1   2   3   4   5   6   7   8
#     conteúdo: p1  p2  d1  p4  d2  d3  d4  p0
# onde p1, p2 e p4 são paridades pares e p0 é a paridade geral.
# ===========================================================================
def codificar_hamming(bits):
    """Codifica o payload em blocos Hamming(8,4). 1 byte vira 2 bytes."""
    saida = []
    for i in range(0, len(bits), 4):             # processa 4 bits (1 nibble) por vez
        nibble = bits[i:i + 4]
        d1, d2, d3, d4 = nibble
        # cada bit de paridade cobre as posições cujo índice binário tem aquele bit = 1:
        # p1 cobre pos 1,3,5,7 (bit 0 do índice = 1): d1, d2, d4
        # p2 cobre pos 2,3,6,7 (bit 1 do índice = 1): d1, d3, d4
        # p4 cobre pos 4,5,6,7 (bit 2 do índice = 1): d2, d3, d4
        p1 = (d1 + d2 + d4) % 2
        p2 = (d1 + d3 + d4) % 2
        p4 = (d2 + d3 + d4) % 2
        # layout das posições 1-7: p1 p2 d1 p4 d2 d3 d4
        bloco = [p1, p2, d1, p4, d2, d3, d4]
        p0 = sum(bloco) % 2                      # paridade geral dos 7 primeiros bits
        saida += bloco + [p0]
    return saida


def decodificar_hamming(bits):
    """Decodifica blocos Hamming(8,4), corrigindo até 1 erro por bloco.

    Retorna (dados, n_corrigidos, erro_duplo):
      - n_corrigidos: quantos bits foram corrigidos no total;
      - erro_duplo: True se algum bloco apresentou erro duplo
        (detectável pela paridade geral, mas incorrigível).
    """
    dados, corrigidos, erro_duplo = [], 0, False
    for i in range(0, len(bits) - 7, 8):
        bloco = bits[i:i + 8][:]                 # cópia para poder corrigir sem alterar o original
        # bloco[0]=p1, bloco[1]=p2, bloco[2]=d1, bloco[3]=p4, bloco[4]=d2, bloco[5]=d3, bloco[6]=d4, bloco[7]=p0
        # síndrome: recalcula cada paridade incluindo o próprio bit de paridade
        # se não houve erro, a paridade bate e s=0; se houve, s≠0 aponta a posição
        s1 = (bloco[0] + bloco[2] + bloco[4] + bloco[6]) % 2   # posições 1,3,5,7
        s2 = (bloco[1] + bloco[2] + bloco[5] + bloco[6]) % 2   # posições 2,3,6,7
        s4 = (bloco[3] + bloco[4] + bloco[5] + bloco[6]) % 2   # posições 4,5,6,7
        # síndrome é um número binário de 3 bits: s4*4 + s2*2 + s1
        # esse número aponta diretamente a posição (1-7) do bit errado
        sindrome = s4 * 4 + s2 * 2 + s1
        par_geral = sum(bloco) % 2               # paridade de todos os 8 bits (incluindo p0)
        if sindrome != 0 and par_geral == 1:
            # erro simples: a síndrome aponta a posição exata
            bloco[sindrome - 1] ^= 1
            corrigidos += 1
        elif sindrome == 0 and par_geral == 1:
            # erro apenas no bit p0 (paridade geral): dados intactos
            corrigidos += 1
        elif sindrome != 0 and par_geral == 0:
            # erro duplo: detectado, mas não corrigível
            erro_duplo = True
        dados += [bloco[2], bloco[4], bloco[5], bloco[6]]   # extrai d1 d2 d3 d4
    return dados, corrigidos, erro_duplo


# ===========================================================================
# orquestração da camada
# ===========================================================================
ENQUADRAR = {"contagem": enquadrar_contagem,
              "bytes": enquadrar_bytes,
              "bits": enquadrar_bits}
DESENQUADRAR = {"contagem": desenquadrar_contagem,
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

    config usa as chaves: 'enquadramento', 'deteccao', 'correcao',
    'tam_max_quadro' (em bytes de dados da aplicação por quadro).
    """
    tam_bits = config["tam_max_quadro"] * 8      # tamanho do bloco de dados em bits

    # valida se o quadro final ainda cabe no byte de contagem.
    tam_quadro_final = config["tam_max_quadro"] + TAMANHO_EDC[config["deteccao"]]
    if config["correcao"] == "hamming":
        tam_quadro_final *= 2                    # hamming(8,4) dobra o tamanho
    if config["enquadramento"] == "contagem" and tam_quadro_final > 255:
        raise ValueError("Quadro final excede 255 bytes: reduza o "
                         "tamanho máximo de quadro.")

    payloads = []
    for i in range(0, len(bits), tam_bits):      # divide a mensagem em blocos
        bloco = bits[i:i + tam_bits]
        bloco = ADICIONAR_EDC[config["deteccao"]](bloco)   # 1º: anexa o edc
        if config["correcao"] == "hamming":                  # 2º: protege tudo
            bloco = codificar_hamming(bloco)                 #     protege com hamming
        payloads.append(bloco)
    return ENQUADRAR[config["enquadramento"]](payloads)     # 3º: enquadra


def receber(bits, config):
    """Pipeline inverso no RECEPTOR.

    Retorna (bits_da_aplicacao, relatorio), onde relatorio é uma lista de
    dicionários (um por quadro) com o resultado da verificação/correção -
    usada pela GUI para mostrar o que aconteceu com cada quadro.
    """
    payloads = DESENQUADRAR[config["enquadramento"]](bits)  # 1º: desenquadra
    bits_app, relatorio = [], []
    for n, payload in enumerate(payloads):
        info = {"quadro": n + 1, "corrigidos": 0,
                "erro_duplo": False, "edc_ok": True}
        if config["correcao"] == "hamming":                  # 2º: corrige
            payload, info["corrigidos"], info["erro_duplo"] = \
                decodificar_hamming(payload)
        payload, info["edc_ok"] = \
            VERIFICAR_EDC[config["deteccao"]](payload)      # 3º: verifica o edc
        bits_app += payload
        relatorio.append(info)
    return bits_app, relatorio

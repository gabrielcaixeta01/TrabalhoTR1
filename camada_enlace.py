"""
camada de enlace do simulador.

o transmissor divide os bits em quadros, adiciona detecção de erros,
opcionalmente aplica hamming e depois enquadra. o receptor faz o caminho
inverso.
"""


FLAG_BYTE = 0x7E          # delimitador de quadro
ESC_BYTE = 0x7D           # 01111101 - caractere de escape p/ inserção de bytes
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]

TAMANHO_EDC = {"nenhum": 0, "paridade": 1, "checksum": 2, "crc": 4}



def bits_para_bytes(bits):
    """agrupa bits em bytes inteiros."""
    resultado = []
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        resultado.append(byte)
    return resultado


def bytes_para_bits(lista_bytes):
    """expande bytes em bits, do mais significativo para o menos significativo."""
    bits = []
    for byte in lista_bytes:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            bits.append(bit)
    return bits


# enquadramento
def enquadrar_contagem(payloads):
    """monta quadros como [1 byte de tamanho] + payload."""
    fluxo = []
    for payload in payloads:
        n_bytes = len(payload) // 8
        fluxo += bytes_para_bits([n_bytes])
        fluxo += payload
    return fluxo


def desenquadrar_contagem(bits):
    """lê quadros de contagem até acabar o fluxo ou encontrar padding."""
    payloads = []
    pos = 0
    while pos + 8 <= len(bits):
        n_bytes = bits_para_bytes(bits[pos:pos + 8])[0]
        pos += 8
        if n_bytes == 0:
            break
        fim = pos + n_bytes * 8
        if fim > len(bits):
            break
        payloads.append(bits[pos:fim])
        pos = fim
    return payloads


def enquadrar_bytes(payloads):
    """delimita quadros com flag e escapa flag/escape no payload."""
    fluxo = []
    for payload in payloads:
        quadro = [FLAG_BYTE]
        for byte in bits_para_bytes(payload):
            if byte in (FLAG_BYTE, ESC_BYTE):
                quadro.append(ESC_BYTE)
            quadro.append(byte)
        quadro.append(FLAG_BYTE)
        fluxo += bytes_para_bits(quadro)
    return fluxo


def desenquadrar_bytes(bits):
    """remove flags e escapes usando uma pequena máquina de estados."""
    payloads = []
    bytes_fluxo = bits_para_bytes(bits)
    dentro, escapado, atual = False, False, []
    for byte in bytes_fluxo:
        if not dentro:
            if byte == FLAG_BYTE:
                dentro, atual = True, []
            continue
        if escapado:
            atual.append(byte)
            escapado = False
        elif byte == ESC_BYTE:
            escapado = True
        elif byte == FLAG_BYTE:
            if atual:
                payloads.append(bytes_para_bits(atual))
            dentro = False
        else:
            atual.append(byte)
    return payloads


def enquadrar_bits(payloads):
    """insere 0 após cinco bits 1 para evitar flag dentro do payload."""
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
    """localiza flags e remove os zeros inseridos pelo bit stuffing."""
    payloads = []
    i = 0
    n = len(bits)
    while i + 8 <= n:
        if bits[i:i + 8] != FLAG_BITS:
            i += 1
            continue
        j = i + 8

        while j + 8 <= n and bits[j:j + 8] != FLAG_BITS:
            j += 1
        if j + 8 > n:
            break

        payload, uns, k = [], 0, i + 8
        while k < j:
            bit = bits[k]
            if uns == 5:
                uns = 0

            else:
                payload.append(bit)
                if bit == 1:
                    uns += 1

                else:
                    uns = 0

            k += 1

        if payload:
            payloads.append(payload)

        i = j + 8
    return payloads


# detecção de erros
def adicionar_paridade_par(bits):
    paridade = sum(bits) % 2
    return bits + [0] * 7 + [paridade]


def verificar_paridade_par(bits):
    if len(bits) < 8:
        return bits, False
    ok = (sum(bits) % 2) == 0
    return bits[:-8], ok


def soma_complemento1(palavras):
    """soma palavras de 16 bits em complemento de 1."""
    soma = 0
    for palavra in palavras:
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    return soma


def bits_para_palavras16(bits):
    bits = bits + [0] * ((-len(bits)) % 16)
    palavras = []
    for i in range(0, len(bits), 16):
        byte_alto = bits_para_bytes(bits[i:i + 8])[0]
        byte_baixo = bits_para_bytes(bits[i + 8:i + 16])[0]
        palavra = (byte_alto << 8) | byte_baixo
        palavras.append(palavra)

    return palavras


def adicionar_checksum(bits):
    soma = soma_complemento1(bits_para_palavras16(bits))
    checksum = (~soma) & 0xFFFF

    return bits + bytes_para_bits([checksum >> 8, checksum & 0xFF])


def verificar_checksum(bits):
    if len(bits) < 16:
        return bits, False
    payload = bits[:-16]
    total = soma_complemento1(bits_para_palavras16(payload) + bits_para_palavras16(bits[-16:]))
    return payload, total == 0xFFFF


# implementação bit a bit do crc-32 ieee 802, sem zlib.
# o vetor "123456789" é usado nos testes para conferir 0xcbf43926.
POLI_CRC32_REFLETIDO = 0xEDB88320


def calcular_crc32(bits):
    """calcula crc-32 ieee 802 bit a bit."""
    # crc é como uma divisão polinomial em base 2.
    # aqui essa divisão não aparece como conta armada; ela vira deslocamento
    # de bits e xor com o polinomio. xor é a "subtração" nessa matematica.
    #
    # começa em ffffffff pq esse é o valor inicial usado no crc-32 ieee.
    # em binario isso é um registrador de 32 bits cheio de 1.
    crc = 0xFFFFFFFF

    # anda pela mensagem de 8 em 8 bits, ou seja, byte por byte.
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]

        # reversed(byte) faz o byte ser processado do ultimo bit para o primeiro.
        # por isso o algoritmo é refletido: ele trabalha lsb-first, começando
        # pelo bit menos significativo do byte.
        for bit in reversed(byte):
            # crc ^ bit faz xor entre o registrador e o bit que entrou.
            # o & 1 pega só o ultimo bit da direita.
            # se esse ultimo bit deu 1, quer dizer que precisa aplicar
            # o polinomio na divisão.
            if (crc ^ bit) & 1:
                # >> 1 desloca o registrador para a direita.
                # depois o xor com o polinomio refletido faz a redução
                # da divisão polinomial.
                crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
            else:
                # se não precisa reduzir pelo polinomio, só desloca.
                # isso equivale a continuar a divisão sem "subtrair" nada.
                crc >>= 1

    # no padrão crc-32 ieee o valor final tambem é invertido.
    # xor com ffffffff inverte todos os 32 bits.
    return crc ^ 0xFFFFFFFF


def adicionar_crc32(bits):
    """anexa o crc-32 do payload como 4 bytes."""
    # calcula o resto da divisão crc do payload.
    crc = calcular_crc32(bits)
    # separa os 32 bits em 4 bytes e anexa no final do quadro.
    # isso vira o campo de detecção de erro.
    return bits + bytes_para_bits([(crc >> 24) & 0xFF, (crc >> 16) & 0xFF,
                                    (crc >> 8) & 0xFF, crc & 0xFF])


def verificar_crc32(bits):
    """recalcula o crc e compara com o campo recebido."""
    # precisa ter 32 bits para existir um crc completo.
    if len(bits) < 32:
        return bits, False

    # tudo antes dos ultimos 32 bits é o payload.
    payload = bits[:-32]
    recebido = 0

    # remonta os ultimos 32 bits como um numero inteiro.
    for b in bits[-32:]:
        recebido = (recebido << 1) | b

    # se o crc recalculado do payload for igual ao recebido, o quadro passou.
    return payload, calcular_crc32(payload) == recebido


# correção de erros: hamming(8,4) estendido
def codificar_hamming(bits):
    """codifica o payload em blocos hamming(8,4)."""
    # hamming(8,4): cada grupo de 4 bits de dados vira 8 bits.
    # os dados são d1 d2 d3 d4 e entram junto com paridades p1, p2, p4 e p0.
    saida = []
    for i in range(0, len(bits), 4):
        nibble = bits[i:i + 4]
        d1, d2, d3, d4 = nibble

        # cada paridade cobre um conjunto diferente de posições.
        # essas combinações são o que depois permitem calcular a sindrome.
        p1 = (d1 + d2 + d4) % 2
        p2 = (d1 + d3 + d4) % 2
        p4 = (d2 + d3 + d4) % 2

        # posições do hamming: 1,2,4 são paridades; 3,5,6,7 são dados.
        bloco = [p1, p2, d1, p4, d2, d3, d4]
        # p0 é a paridade geral do bloco. ela ajuda a separar erro simples
        # de erro duplo.
        p0 = sum(bloco) % 2
        saida += bloco + [p0]
    return saida


def decodificar_hamming(bits):
    """decodifica hamming(8,4), corrigindo erro simples e detectando duplo."""
    # lê de 8 em 8 bits. cada bloco deve ter vindo de 4 bits originais.
    dados, corrigidos, erro_duplo = [], 0, False
    for i in range(0, len(bits) - 7, 8):
        bloco = bits[i:i + 8][:]

        # recalcula as paridades que deveriam bater.
        # s1, s2 e s4 formam a sindrome, que aponta a posição do erro.
        s1 = (bloco[0] + bloco[2] + bloco[4] + bloco[6]) % 2
        s2 = (bloco[1] + bloco[2] + bloco[5] + bloco[6]) % 2
        s4 = (bloco[3] + bloco[4] + bloco[5] + bloco[6]) % 2
        sindrome = s4 * 4 + s2 * 2 + s1

        # paridade geral diz se a quantidade total de erros parece impar.
        par_geral = sum(bloco) % 2

        if sindrome != 0 and par_geral == 1:
            # erro simples em uma das 7 primeiras posições.
            # a sindrome vira o indice, mas no python começa em zero,
            # então usa sindrome - 1.
            bloco[sindrome - 1] ^= 1
            corrigidos += 1
        elif sindrome == 0 and par_geral == 1:
            # erro simples no p0. os dados estão bons, só contabiliza correção.
            corrigidos += 1
        elif sindrome != 0 and par_geral == 0:
            # sindrome acusa algo, mas paridade geral não bate com erro simples.
            # isso indica erro duplo: detecta, mas não corrige.
            erro_duplo = True

        # devolve só as posições de dados originais.
        dados += [bloco[2], bloco[4], bloco[5], bloco[6]]
    return dados, corrigidos, erro_duplo


# orquestração da camada
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
    """aplica edc, hamming e enquadramento no transmissor."""
    tam_bits = config["tam_max_quadro"] * 8

    tam_quadro_final = config["tam_max_quadro"] + TAMANHO_EDC[config["deteccao"]]
    if config["correcao"] == "hamming":
        tam_quadro_final *= 2
    if config["enquadramento"] == "contagem" and tam_quadro_final > 255:
        raise ValueError("Quadro final excede 255 bytes: reduza o "
                         "tamanho máximo de quadro.")

    payloads = []
    for i in range(0, len(bits), tam_bits):
        bloco = bits[i:i + tam_bits]
        bloco = ADICIONAR_EDC[config["deteccao"]](bloco)
        if config["correcao"] == "hamming":
            bloco = codificar_hamming(bloco)
        payloads.append(bloco)

    return ENQUADRAR[config["enquadramento"]](payloads)


def receber(bits, config):
    """faz o caminho inverso no receptor e retorna bits + relatório."""
    payloads = DESENQUADRAR[config["enquadramento"]](bits)
    bits_app, relatorio = [], []
    for n, payload in enumerate(payloads):
        info = {"quadro": n + 1, "corrigidos": 0,
                "erro_duplo": False, "edc_ok": True}
        if config["correcao"] == "hamming":
            payload, info["corrigidos"], info["erro_duplo"] = \
                decodificar_hamming(payload)
        payload, info["edc_ok"] = \
            VERIFICAR_EDC[config["deteccao"]](payload)
        bits_app += payload
        relatorio.append(info)
    return bits_app, relatorio

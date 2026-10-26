# -*- coding: utf-8 -*-
"""
Camada de enlace.

Prepara os bits da aplicação para serem enviados e, no receptor, confere e
recupera esses bits. Tem três blocos:
  - enquadramento: contagem de caracteres, entrelaçamento, byte stuffing e bit stuffing
  - detecção de erros: paridade par, checksum e CRC-32
  - correção de erros: Hamming (11,7)

Transmissor (transmitir):
  bits da aplicação -> blocos de até `tam_max_quadro` bytes -> EDC no final de
  cada bloco -> Hamming (opcional) -> enquadramento -> fluxo único de bits.
Receptor (receber): o caminho inverso (desenquadra, corrige, verifica o EDC).

Decisões de projeto (justificadas em docs/DECISOES.md):
  - Todo EDC ocupa bytes inteiros, porque contagem e byte stuffing trabalham
    com bytes: paridade 1 byte, checksum 2 bytes, CRC-32 4 bytes.
  - O Hamming tem m bits de dados por bloco (configurável; 7 é o (11,7) dos
    slides) e r bits de paridade calculados a partir de m. Os dados levam um
    bit 1 de fim e zeros até múltiplo de m, e a saída é completada com zeros
    até múltiplo de 8; o decodificador descarta esse enchimento.
  - FLAG = 0x7E e ESC = 0x7D, como no HDLC/PPP.
"""


FLAG_BYTE = 0x7E          # 01111110, delimitador de quadro
ESC_BYTE = 0x7D           # caractere de escape do byte stuffing
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]

# Quantos bytes cada detecção acrescenta ao final do payload
TAMANHO_EDC = {"nenhum": 0, "paridade": 1, "checksum": 2, "crc": 4}

# Colunas da matriz do entrelaçamento. Com 8, cada linha é um byte e o quadro
# continua alinhado em bytes.
N_COLUNAS_ENTRELACAMENTO = 8


# auxiliares
def bits_para_bytes(bits):
    """Agrupa os bits de 8 em 8 em inteiros de 0 a 255 (uma sobra incompleta é ignorada).

    Ex.: [0,1,0,0,0,0,0,1, 0,1,0,0,0,0,1,0] -> [65, 66]
    """
    lista_bytes = []
    for inicio in range(0, len(bits) // 8 * 8, 8):
        valor = 0
        for bit in bits[inicio:inicio + 8]:
            valor = (valor << 1) | bit      # empurra o valor e encaixa o bit
        lista_bytes.append(valor)
    return lista_bytes


def bytes_para_bits(lista_bytes):
    """Expande cada byte em 8 bits, do mais significativo para o menos.

    Ex.: [65] -> [0, 1, 0, 0, 0, 0, 0, 1]
    """
    bits = []
    for valor in lista_bytes:
        for posicao in range(7, -1, -1):
            bits.append((valor >> posicao) & 1)
    return bits


# ===========================================================================
# 1) Enquadramento
# Cada enquadrar_* recebe uma lista de payloads (listas de bits em bytes
# inteiros) e devolve um fluxo único de bits com todos os quadros. Cada
# desenquadrar_* faz o inverso.
#
# Atenção: 8PSK e 32-QAM completam o fim do fluxo com zeros para fechar o
# último símbolo. O desenquadramento tem que ignorar esse lixo sem inventar
# quadros extras.
# ===========================================================================

# contagem de caracteres
def enquadrar_contagem(payloads):
    """Quadro = 1 byte de contagem + payload.

    A contagem inclui o próprio cabeçalho (2 bytes de dados -> contagem 3), como
    nos slides. O receptor lê a contagem e sabe quantos bytes consumir.
    Limite: o cabeçalho tem 8 bits, então o quadro tem no máximo 255 bytes.
    Fraqueza: se a contagem for corrompida, o receptor perde o sincronismo de
    todos os quadros seguintes.
    """
    bits = []
    for payload in payloads:
        contagem = len(payload) // 8 + 1
        bits += bytes_para_bits([contagem]) + payload
    return bits


def desenquadrar_contagem(bits):
    """Lê o fluxo quadro a quadro: [contagem][payload][contagem][payload]...

    Para se achar contagem 0 (é o padding da modulação, nunca um quadro
    válido) ou um quadro que passa do fim do fluxo (truncado/corrompido).
    """
    payloads = []
    pos = 0
    while pos + 8 <= len(bits):
        contagem = bits_para_bytes(bits[pos:pos + 8])[0]
        if contagem == 0:
            break
        fim = pos + contagem * 8            # a contagem inclui o cabeçalho
        if fim > len(bits):
            break
        payloads.append(bits[pos + 8:fim])
        pos = fim
    return payloads


# entrelaçamento de bits
# Algoritmo dos slides (TR1_09, 23-24): os dados formam uma matriz de linhas
# com N colunas; calcula-se um bit de paridade par por coluna, numa linha
# extra; a matriz é enviada linha por linha. Uma rajada de até N bits atinge
# no máximo 1 bit por coluna, e a paridade da coluna detecta isso.
#
# Os slides não definem N nem como delimitar o quadro (ver docs/DECISOES.md):
# usamos N = N_COLUNAS_ENTRELACAMENTO e a contagem de caracteres como delimitador.
def paridade_colunas(bits, n_colunas):
    """Calcula a paridade par de cada coluna da matriz (XOR dos bits da coluna)."""
    paridade = [0] * n_colunas
    for k, bit in enumerate(bits):
        paridade[k % n_colunas] ^= bit      # o bit k está na coluna k % n_colunas
    return paridade


def entrelacar(bits, n_colunas):
    """Devolve os dados seguidos da linha de paridade das colunas.

    A matriz é enviada linha a linha, então basta interpretar os bits em
    linhas de n_colunas e anexar a paridade no final.
    """
    if len(bits) % n_colunas != 0:
        raise ValueError("A quantidade de bits precisa ser múltipla de n_colunas")
    return bits + paridade_colunas(bits, n_colunas)


def desentrelacar(bits, n_colunas):
    """Inverso de entrelacar: devolve (dados, colunas_com_erro).

    Separa a linha de paridade recebida, recalcula a paridade dos dados e
    lista as colunas em que as duas diferem.
    """
    dados = bits[:-n_colunas]
    paridade_recebida = bits[-n_colunas:]
    paridade_calculada = paridade_colunas(dados, n_colunas)
    colunas_com_erro = [c for c in range(n_colunas)
                        if paridade_recebida[c] != paridade_calculada[c]]
    return dados, colunas_com_erro


def enquadrar_entrelacamento(payloads, n_colunas=N_COLUNAS_ENTRELACAMENTO):
    """Entrelaça cada payload (adiciona a linha de paridade) e delimita pela contagem."""
    return enquadrar_contagem([entrelacar(p, n_colunas) for p in payloads])


def desenquadrar_entrelacamento(bits, n_colunas=N_COLUNAS_ENTRELACAMENTO):
    """Desenquadra pela contagem e remove a linha de paridade de cada quadro."""
    quadros = desenquadrar_contagem(bits)
    return [desentrelacar(quadro, n_colunas)[0] for quadro in quadros]


# FLAGs com inserção de bytes (byte stuffing)
def enquadrar_bytes(payloads):
    """Quadro = FLAG + payload com escape + FLAG.

    Se os dados tiverem um byte igual à FLAG, o receptor acharia que o quadro
    acabou. Por isso, antes de todo byte que seja FLAG ou ESC, inserimos um ESC.
    Ex.: dados [0x41, 0x7E, 0x42] -> 7E 41 7D 7E 42 7E
    """
    saida = []
    for payload in payloads:
        saida.append(FLAG_BYTE)
        for byte in bits_para_bytes(payload):
            if byte == FLAG_BYTE or byte == ESC_BYTE:
                saida.append(ESC_BYTE)
            saida.append(byte)
        saida.append(FLAG_BYTE)
    return bytes_para_bits(saida)


def desenquadrar_bytes(bits):
    """Percorre os bytes do fluxo com uma pequena máquina de estados.

    Fora de quadro, ignora tudo até achar uma FLAG (abre o quadro). Dentro:
      - ESC: o próximo byte é dado literal, mesmo que seja FLAG ou ESC;
      - FLAG: fecha o quadro (quadros vazios são ignorados);
      - outro byte: é dado.
    Um quadro que não chegou a ser fechado é descartado.
    """
    payloads = []
    quadro = None           # None = fora de quadro
    escapado = False
    for byte in bits_para_bytes(bits):
        if quadro is None:
            if byte == FLAG_BYTE:
                quadro = []
        elif escapado:
            quadro.append(byte)
            escapado = False
        elif byte == ESC_BYTE:
            escapado = True
        elif byte == FLAG_BYTE:
            if quadro:
                payloads.append(bytes_para_bits(quadro))
            quadro = None
        else:
            quadro.append(byte)
    return payloads


# FLAGs com inserção de bits (bit stuffing)
def inserir_stuffing(payload):
    """Insere um 0 depois de cada sequência de cinco 1s seguidos.

    Assim o payload nunca tem seis 1s seguidos, e o padrão 01111110 da FLAG
    só aparece nos delimitadores.
    """
    saida = []
    uns = 0
    for bit in payload:
        saida.append(bit)
        uns = uns + 1 if bit == 1 else 0
        if uns == 5:
            saida.append(0)
            uns = 0
    return saida


def remover_stuffing(corpo):
    """Inverso de inserir_stuffing: descarta o 0 que vem depois de cinco 1s."""
    saida = []
    uns = 0
    for bit in corpo:
        if uns == 5:                # este é o 0 inserido pelo transmissor
            uns = 0
            continue
        saida.append(bit)
        uns = uns + 1 if bit == 1 else 0
    return saida


def achar_flag(bits, inicio):
    """Devolve a posição da próxima FLAG a partir de `inicio`, ou None se não houver."""
    for k in range(inicio, len(bits) - len(FLAG_BITS) + 1):
        if bits[k:k + len(FLAG_BITS)] == FLAG_BITS:
            return k
    return None


def enquadrar_bits(payloads):
    """Quadro = FLAG (01111110) + payload com bit stuffing + FLAG."""
    saida = []
    for payload in payloads:
        saida += FLAG_BITS + inserir_stuffing(payload) + FLAG_BITS
    return saida


def desenquadrar_bits(bits):
    """Procura pares de FLAGs e remove o stuffing do que está entre elas.

    Se não houver FLAG de abertura ou de fechamento, para (o resto é padding
    ou um quadro incompleto). Quadros vazios são ignorados.
    """
    payloads = []
    pos = 0
    while True:
        abertura = achar_flag(bits, pos)
        if abertura is None:
            break
        fechamento = achar_flag(bits, abertura + len(FLAG_BITS))
        if fechamento is None:
            break
        corpo = bits[abertura + len(FLAG_BITS):fechamento]
        payload = remover_stuffing(corpo)
        if payload:
            payloads.append(payload)
        pos = fechamento + len(FLAG_BITS)
    return payloads


# ===========================================================================
# 2) Detecção de erros
# adicionar_* anexam o EDC ao final do payload (transmissor).
# verificar_* devolvem (payload_sem_edc, ok) (receptor).
# ===========================================================================

# paridade par
def adicionar_paridade_par(bits):
    """Anexa 1 byte: 7 zeros + o bit de paridade par do payload.

    O bit de paridade deixa o total de 1s par (paridade = soma dos bits % 2).
    Usamos um byte inteiro só para manter o alinhamento em bytes.
    Limite: só detecta quantidade ímpar de bits errados.
    """
    paridade = sum(bits) % 2
    return bits + bytes_para_bits([paridade])


def verificar_paridade_par(bits):
    """Confere se o total de 1s (incluindo o byte de paridade) é par."""
    if len(bits) < 8:
        return bits, False
    return bits[:-8], sum(bits) % 2 == 0


# checksum
def soma_complemento1(palavras):
    """Soma palavras de 16 bits em complemento de 1.

    Todo "vai-um" que passa do 16º bit é somado de volta no resultado
    (end-around carry).
    """
    soma = 0
    for palavra in palavras:
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)   # 16 bits baixos + carry
    return soma


def bits_para_palavras16(bits):
    """Agrupa os bits em palavras de 16 bits, completando o final com zeros se precisar."""
    bits = bits + [0] * (-len(bits) % 16)
    lista_bytes = bits_para_bytes(bits)
    return [(lista_bytes[k] << 8) | lista_bytes[k + 1]
            for k in range(0, len(lista_bytes), 2)]


def adicionar_checksum(bits):
    """Anexa 2 bytes com o checksum do payload.

    Soma as palavras de 16 bits em complemento de 1 e anexa o complemento da
    soma. O "& 0xFFFF" é necessário porque ~ em Python gera um número negativo.
    """
    soma = soma_complemento1(bits_para_palavras16(bits))
    checksum = ~soma & 0xFFFF
    return bits + bytes_para_bits([checksum >> 8, checksum & 0xFF])


def verificar_checksum(bits):
    """Soma payload + checksum; se não houve erro o resultado é 0xFFFF (16 bits em 1)."""
    if len(bits) < 16:
        return bits, False
    payload = bits[:-16]
    palavras = bits_para_palavras16(payload) + bits_para_palavras16(bits[-16:])
    return payload, soma_complemento1(palavras) == 0xFFFF


# CRC-32
# Algoritmo dos slides (TR1_09, 30-33), divisão polinomial módulo 2:
#   TX: anexa 32 zeros à mensagem, divide por G(x) com XOR; o resto de 32
#       bits é o CRC.
#   RX: divide o quadro inteiro (dados + CRC) por G(x); resto 0 = sem erro.
# G(x) do CRC-32 IEEE 802 (grau 32, 33 bits): 0x104C11DB7.
# Os slides não falam de valor inicial, XOR final nem reflexão de bits, então
# o resultado não bate com o CRC-32 do zlib/Ethernet (e é proibido usar zlib).
GERADOR_CRC32 = 0x104C11DB7


def resto_mod2(bits):
    """Resto da divisão módulo 2 de `bits` por GERADOR_CRC32.

    Usa um registrador: entra um bit por vez e, sempre que o bit de grau 32
    liga, faz XOR com o gerador (que equivale a subtrair o gerador).
    """
    resto = 0
    for bit in bits:
        resto = (resto << 1) | bit
        if resto >> 32:                 # o bit de grau 32 ligou
            resto ^= GERADOR_CRC32
    return resto


def calcular_crc32(bits):
    """CRC = resto da divisão de (bits + 32 zeros) por G(x)."""
    return resto_mod2(bits + [0] * 32)


def adicionar_crc32(bits):
    """Anexa o CRC-32 do payload como 4 bytes, do mais significativo ao menos."""
    crc = calcular_crc32(bits)
    bytes_crc = [(crc >> 24) & 0xFF, (crc >> 16) & 0xFF, (crc >> 8) & 0xFF, crc & 0xFF]
    return bits + bytes_para_bits(bytes_crc)


def verificar_crc32(bits):
    """Divide o quadro inteiro (payload + CRC) por G(x): resto 0 significa sem erro."""
    if len(bits) < 32:
        return bits, False
    return bits[:-32], resto_mod2(bits) == 0


# ===========================================================================
# 3) Correção de erros: Hamming (m + r, m)
#
# Cada bloco tem m bits de dados e r bits de paridade. O r é o menor valor que
# satisfaz 2^r >= m + r + 1 (assim a síndrome consegue apontar qualquer
# posição do bloco). Os slides usam m = 7, que dá r = 4 e o código (11,7);
# aqui m é configurável (BITS_HAMMING_PADRAO é 7).
#
# Posições de 1 a n = m + r. As potências de 2 (1, 2, 4, 8, ...) guardam
# paridade; as demais guardam os dados. Ex. (11,7):
#     posição:  1   2   3   4   5   6   7   8   9   10   11
#     conteúdo: P1  P2  D3  P4  D5  D6  D7  P8  D9  D10  D11
# A paridade na posição p (par) cobre toda posição que tem o bit p ligado no
# binário: P1 cobre as ímpares (3, 5, 7, ...), P2 cobre 2, 3, 6, 7, 10, 11...
#
# Decodificação: recalcula-se cada paridade incluindo o próprio bit de
# paridade recebido. Os resultados formam a síndrome (s8 s4 s2 s1 ...):
#   síndrome 0 -> sem erro;  síndrome > 0 -> é a posição do bit errado, é só inverter.
# Não há paridade geral, então erro duplo não é detectado (só se a síndrome
# apontar uma posição que não existe, maior que n).
# ===========================================================================
BITS_HAMMING_PADRAO = 7


def bits_de_paridade(m):
    """Menor r tal que 2^r >= m + r + 1: bits de paridade para m bits de dados."""
    r = 1
    while 2 ** r < m + r + 1:
        r += 1
    return r


def posicoes_hamming(m):
    """Devolve (n, posicoes_paridade, posicoes_dados) de um bloco com m bits de dados."""
    r = bits_de_paridade(m)
    n = m + r
    posicoes_paridade = [2 ** k for k in range(r)]          # 1, 2, 4, 8, ...
    posicoes_dados = [p for p in range(1, n + 1) if p not in posicoes_paridade]
    return n, posicoes_paridade, posicoes_dados


def codificar_hamming(bits, m=BITS_HAMMING_PADRAO):
    """Codifica o payload em blocos Hamming de m bits de dados.

    Anexa um bit 1 de fim e completa com zeros até múltiplo de m (o receptor
    usa esse 1 para saber onde os dados terminam, qualquer que seja m). Monta
    cada bloco com os dados e as paridades e completa a saída com zeros até
    múltiplo de 8, para o enquadramento trabalhar em bytes.
    """
    n, posicoes_paridade, posicoes_dados = posicoes_hamming(m)
    bits = bits + [1]
    bits = bits + [0] * (-len(bits) % m)
    saida = []
    for inicio in range(0, len(bits), m):
        bloco = [0] * (n + 1)               # posições 1 a n (o índice 0 não é usado)
        for pos, dado in zip(posicoes_dados, bits[inicio:inicio + m]):
            bloco[pos] = dado
        for p in posicoes_paridade:
            for pos in range(1, n + 1):
                if pos & p and pos != p:    # posições cobertas pela paridade p
                    bloco[p] ^= bloco[pos]
        saida += bloco[1:]
    return saida + [0] * (-len(saida) % 8)


def decodificar_hamming(bits, m=BITS_HAMMING_PADRAO):
    """Decodifica os blocos, corrigindo até 1 erro por bloco.

    Devolve (dados, n_corrigidos, erro_incorrigivel):
      - dados: bits de dados recuperados, sem o enchimento do final;
      - n_corrigidos: quantos bits foram corrigidos no total;
      - erro_incorrigivel: True se alguma síndrome apontou posição maior que n.
    """
    n, posicoes_paridade, posicoes_dados = posicoes_hamming(m)
    dados = []
    n_corrigidos = 0
    erro_incorrigivel = False
    for inicio in range(0, len(bits) // n * n, n):      # só blocos completos
        bloco = [0] + bits[inicio:inicio + n]
        sindrome = 0
        for p in posicoes_paridade:
            soma = 0
            for pos in range(1, n + 1):
                if pos & p:                 # posições cobertas, incluindo a própria paridade
                    soma ^= bloco[pos]
            if soma:
                sindrome += p               # monta a síndrome em binário
        if 0 < sindrome <= n:
            bloco[sindrome] ^= 1            # a síndrome é a posição do erro
            n_corrigidos += 1
        elif sindrome > n:
            erro_incorrigivel = True
        dados += [bloco[pos] for pos in posicoes_dados]

    # Tira o enchimento: os zeros do final e o 1 de fim que o codificador anexou
    while dados and dados[-1] == 0:
        dados.pop()
    if dados:
        dados.pop()
    return dados, n_corrigidos, erro_incorrigivel


# ===========================================================================
# Orquestração da camada (chamada pelo Simulador)
# Ligam o texto escolhido na GUI à função correspondente.
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


def validar_tamanho_quadro(config):
    """Garante que o quadro cabe nos 255 bytes que a contagem consegue representar.

    Vale para "contagem" e "entrelacamento" (que usa a contagem). Soma ao
    tamanho dos dados o EDC, o Hamming (se ativo), o byte de cabeçalho e, no
    entrelaçamento, a linha de paridade.
    """
    if config["enquadramento"] not in ("contagem", "entrelacamento"):
        return
    tamanho = config["tam_max_quadro"] + TAMANHO_EDC[config["deteccao"]]
    if config["correcao"] == "hamming":
        m = config.get("bits_hamming", BITS_HAMMING_PADRAO)
        n = m + bits_de_paridade(m)
        blocos = -(-(tamanho * 8 + 1) // m)     # divisão para cima (+1 = bit de fim)
        tamanho = -(-blocos * n // 8)
    tamanho += 1                                # byte de contagem
    if config["enquadramento"] == "entrelacamento":
        tamanho += N_COLUNAS_ENTRELACAMENTO // 8    # linha de paridade
    if tamanho > 255:
        raise ValueError(f"Quadro final excede 255 bytes ({tamanho}); "
                         "reduza o tamanho máximo do quadro")


def transmitir(bits, config):
    """Pipeline completo do transmissor.

    `config` usa as chaves 'enquadramento', 'deteccao', 'correcao' e
    'tam_max_quadro' (bytes de dados da aplicação por quadro).
    Divide os bits em blocos, anexa o EDC em cada um, aplica o Hamming (que
    protege payload + EDC), enquadra tudo e devolve um único fluxo de bits.
    """
    validar_tamanho_quadro(config)
    tamanho_bloco = config["tam_max_quadro"] * 8
    payloads = []
    for inicio in range(0, len(bits), tamanho_bloco):
        bloco = bits[inicio:inicio + tamanho_bloco]
        bloco = ADICIONAR_EDC[config["deteccao"]](bloco)
        if config["correcao"] == "hamming":
            bloco = codificar_hamming(bloco, config.get("bits_hamming", BITS_HAMMING_PADRAO))
        payloads.append(bloco)
    return ENQUADRAR[config["enquadramento"]](payloads)


def receber(bits, config):
    """Pipeline inverso do receptor.

    Devolve (bits_da_aplicacao, relatorio). O relatório tem um dicionário por
    quadro, que a GUI mostra:
        "quadro"     : número do quadro (1, 2, ...)
        "corrigidos" : bits corrigidos pelo Hamming nesse quadro
        "erro_duplo" : True se o Hamming apontou erro incorrigível
        "edc_ok"     : True se o EDC confere

    Quadros com EDC inválido não são descartados: os bits ficam no texto
    recebido e o quadro é marcado com edc_ok = False (decisão de projeto, ver
    docs/DECISOES.md). Assim a GUI mostra o erro e o texto corrompido.
    """
    bits_aplicacao = []
    relatorio = []
    payloads = DESENQUADRAR[config["enquadramento"]](bits)
    for numero, payload in enumerate(payloads, start=1):
        corrigidos = 0
        erro_duplo = False
        if config["correcao"] == "hamming":
            m = config.get("bits_hamming", BITS_HAMMING_PADRAO)
            payload, corrigidos, erro_duplo = decodificar_hamming(payload, m)
        payload, edc_ok = VERIFICAR_EDC[config["deteccao"]](payload)
        bits_aplicacao += payload
        relatorio.append({"quadro": numero, "corrigidos": corrigidos,
                          "erro_duplo": erro_duplo, "edc_ok": edc_ok})
    return bits_aplicacao, relatorio

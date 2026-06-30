"""
camada física do simulador.

os bits são convertidos em amostras de tensão. primeiro pode haver uma
codificação em banda-base; depois, se configurado, os mesmos bits são
modulados em uma portadora ask, fsk, qpsk ou 16-qam.
"""

import math

V = 1.0                      # amplitude de referência do sinal, em volts
AMOSTRAS_POR_BIT = 100       # resolução do sinal banda-base
AMOSTRAS_POR_SIMBOLO = 100   # resolução de cada símbolo da portadora
CICLOS_PORTADORA = 4         # ciclos de portadora por símbolo
CICLOS_FSK = (2, 4)          # fsk: f1 (bit 0) e f2 (bit 1), em ciclos/símbolo


# modulação digital em banda-base
def modular_nrz_polar(bits):
    """nrz-polar: bit 1 vira +v e bit 0 vira -v."""
    # aqui a idéia é a mais direta possivel: cada bit ocupa uma janela fixa
    # de amostras. se o bit é 1, a tensão fica positiva; se é 0, fica negativa.
    # isso monta um sinal em degraus, ainda sem portadora.
    # entrada: lista de bits. saida: lista de tensoes, com 100 amostras por bit.
    sinal = []
    for bit in bits:
        # escolhe o nivel eletrico que representa esse bit.
        if bit == 1:
            nivel = V
        else:
            nivel = -V
        # repete o mesmo nivel varias vezes para virar um trecho de sinal.
        sinal += [nivel] * AMOSTRAS_POR_BIT
    return sinal


def demodular_nrz_polar(sinal):
    """decide cada bit pela média das amostras."""
    # o receptor corta o sinal em pedaços do tamanho de um bit.
    # se a média do pedaço ficou positiva, entende como 1.
    # se ficou negativa ou zero, entende como 0.
    # a media ajuda contra ruido pequeno, porque varias amostras compensam uma
    # amostra isolada que tenha sido deslocada pelo canal.
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        # k marca o inicio da janela de amostras que representa um bit.
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        if media > 0:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_manchester(bits):
    """manchester: bit 0 sobe no meio; bit 1 desce no meio."""
    # no manchester cada bit sempre tem uma transição no meio.
    # isso ajuda no sincronismo, pq o receptor consegue ver mudança dentro
    # de cada bit, não só uma tensão parada igual no nrz.
    # o sinal de cada bit e dividido em duas metades com niveis opostos.
    metade = AMOSTRAS_POR_BIT // 2
    sinal = []
    for bit in bits:
        # 0: começa baixo e termina alto.
        # 1: começa alto e termina baixo.
        if bit == 0:
            sinal += [-V] * metade + [V] * (AMOSTRAS_POR_BIT - metade)
        else:
            sinal += [V] * metade + [-V] * (AMOSTRAS_POR_BIT - metade)
    return sinal


def demodular_manchester(sinal):
    """compara as médias das duas metades de cada bit."""
    # aqui o bit é decidido comparando a primeira metade com a segunda.
    # se começou mais alto e terminou mais baixo, é 1.
    # se começou mais baixo e terminou mais alto, é 0.
    # o receptor nao procura uma tensão absoluta; ele procura a direcao da
    # transicao dentro do intervalo do bit.
    metade = AMOSTRAS_POR_BIT // 2
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        # m1 e m2 resumem as duas metades do bit recebido.
        m1 = sum(sinal[k:k + metade]) / metade
        m2 = sum(sinal[k + metade:k + AMOSTRAS_POR_BIT]) / (AMOSTRAS_POR_BIT - metade)
        if m1 > m2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_bipolar(bits):
    """bipolar ami: bit 0 vira 0 v; bits 1 alternam +v e -v."""
    # no bipolar o zero é ausencia de pulso.
    # os bits 1 aparecem como pulsos, mas alternando o sinal entre +v e -v.
    # essa alternancia evita uma componente dc muito forte no sinal.
    # a variavel polaridade guarda qual sinal sera usado no proximo bit 1.
    sinal = []
    polaridade = V
    for bit in bits:
        if bit == 0:
            sinal += [0.0] * AMOSTRAS_POR_BIT
        else:
            # depois de mandar um 1 com uma polaridade, inverte para o proximo 1.
            sinal += [polaridade] * AMOSTRAS_POR_BIT
            polaridade = -polaridade
    return sinal


def demodular_bipolar(sinal):
    """decide pelo módulo da média de cada intervalo."""
    # no receptor não importa se o pulso era positivo ou negativo.
    # se o modulo da média passou de um limiar, considera que tinha pulso,
    # então era bit 1. se ficou perto de zero, era bit 0.
    # por isso usa abs(media): +V e -V contam como pulso valido.
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        if abs(media) > V / 2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


# modulação por portadora
def onda(i, q, ciclos):
    """gera um símbolo por i/q: s(t) = i*cos(wt) - q*sin(wt)."""
    # essa função monta uma portadora usando duas partes:
    # i é a parte em fase, multiplicada por cos.
    # q é a parte em quadratura, multiplicada por sen.
    # juntando as duas da pra representar ask, qpsk e qam como pontos i/q.
    # ciclos controla quantas voltas da senoide cabem dentro de um simbolo.
    N = AMOSTRAS_POR_SIMBOLO
    amostras = []
    for n in range(N):
        # n anda pelas amostras do simbolo e o angulo anda pela senoide.
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
    return amostras


def correlacionar(simbolo, ciclos):
    """estima as componentes i/q por correlação com a portadora."""
    # correlação é tipo perguntar: "quanto desse simbolo parece com cos?"
    # e tambem "quanto parece com sen?". isso recupera as coordenadas i e q
    # que foram usadas na transmissão.
    # esse e um receptor coerente simplificado: ele conhece a mesma portadora
    # usada no transmissor e usa essa referencia para medir o simbolo recebido.
    N = len(simbolo)
    soma_cos = 0.0
    soma_sen = 0.0
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / N
        # multiplica a amostra pela referencia local da portadora.
        # se estiver alinhado, a soma cresce; se não estiver, tende a cancelar.
        soma_cos += amostra * math.cos(angulo)
        soma_sen += amostra * math.sin(angulo)
    # o fator 2/n normaliza a energia das senoides.
    # o q recebe sinal negativo para desfazer o "- q * sen" usado na onda.
    i = 2 / N * soma_cos
    q = -2 / N * soma_sen
    return i, q


def pad(bits, tamanho):
    """completa com zeros até fechar um símbolo inteiro."""
    # qpsk precisa de 2 bits por simbolo e 16-qam precisa de 4.
    # se sobrar bit incompleto no final, completa com zero só pra fechar grupo.
    # isso evita transmitir um simbolo quebrado no fim do fluxo.
    resto = len(bits) % tamanho
    if resto == 0:
        return bits                         
    faltam = tamanho - resto
    # os zeros adicionados sao padding fisico, nao bits novos da aplicacao.
    return bits + [0] * faltam


def bits_do_ponto_mais_proximo(i, q, constelacao):
    """escolhe os bits do ponto mais próximo na constelação."""
    # depois de estimar i e q no receptor, compara esse ponto com todos os
    # pontos ideais da constelação. o mais perto é a decisão do simbolo.
    # isso troca uma amostra ruidosa por um dos simbolos validos do protocolo.
    # constelacao e um dicionario: bits -> coordenada ideal (i, q).
    melhor_bits = None
    menor_dist = None
    for bits_simbolo, (i_ref, q_ref) in constelacao.items():
        # distancia quadrada evita usar raiz, mas mantém a mesma ordem.
        dist = (i_ref - i) ** 2 + (q_ref - q) ** 2
        if menor_dist is None or dist < menor_dist:
            menor_dist = dist
            melhor_bits = bits_simbolo
    return list(melhor_bits)


def modular_ask(bits):
    """ask: bit 1 transmite portadora; bit 0 transmite amplitude zero."""
    # ask muda a amplitude da portadora.
    # aqui o 1 manda uma senoide normal e o 0 manda amplitude zero.
    # cada bit ainda ocupa um simbolo completo, mesmo quando o bit 0 vira silencio.
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, CICLOS_PORTADORA)
        else:
            sinal += onda(0.0, 0.0, CICLOS_PORTADORA)
    return sinal


def demodular_ask(sinal):
    """decide ask pela amplitude estimada do símbolo."""
    # corta o sinal em simbolos e mede a amplitude pelo vetor i/q.
    # se a amplitude passou da metade de v, decide 1; senão, decide 0.
    # math.hypot(i, q) mede o tamanho do vetor, isto e, a amplitude recebida.
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        if math.hypot(i, q) > V / 2:
            bits.append(1)
        else:
            bits.append(0)
    return bits


def modular_fsk(bits):
    """fsk: bit 0 e bit 1 usam frequências diferentes."""
    # fsk não muda amplitude, muda a frequencia.
    # bit 0 usa f0 e bit 1 usa f1, definidos como ciclos por simbolo.
    # no projeto, essas frequencias sao relativas: ciclos dentro de um simbolo,
    # nao Hz reais, porque nao definimos tempo em segundos.
    f0, f1 = CICLOS_FSK
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, f1)
        else:
            sinal += onda(V, 0.0, f0)
    return sinal


def demodular_fsk(sinal):
    """decide fsk comparando a energia nas duas frequências."""
    # o receptor testa duas correlações: uma na frequencia do 0 e outra na do 1.
    # onde tiver mais energia, essa é a frequencia que provavelmente foi enviada.
    # a decisao nao depende de fase exata do bit; compara a presenca de cada tom.
    f0, f1 = CICLOS_FSK
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        simbolo = sinal[k:k + N]
        # correlacionar devolve (i, q); hypot transforma essas componentes
        # em uma unica medida de energia/amplitude para cada frequencia.
        e0 = math.hypot(*correlacionar(simbolo, f0))
        e1 = math.hypot(*correlacionar(simbolo, f1))
        if e1 > e0:
            bits.append(1)
        else:
            bits.append(0)
    return bits


# qpsk usa mapeamento gray: pontos vizinhos mudam só um bit.
A_QPSK = V / math.sqrt(2)
MAPA_QPSK = {(0, 0): (A_QPSK, A_QPSK), (0, 1): (-A_QPSK, A_QPSK),
              (1, 1): (-A_QPSK, -A_QPSK), (1, 0): (A_QPSK, -A_QPSK)}


def modular_qpsk(bits):
    """qpsk: agrupa bits em pares e transmite um ponto da constelação."""
    # qpsk transmite 2 bits por simbolo. cada par escolhe um ponto i/q.
    # o mapa usa gray, então pontos vizinhos mudam só um bit.
    # como usa pares, faz padding se a quantidade de bits for impar.
    bits = pad(bits, 2)
    sinal = []
    for k in range(0, len(bits), 2):
        # cada par de bits vira uma coordenada da constelacao qpsk.
        i, q = MAPA_QPSK[(bits[k], bits[k + 1])]
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def demodular_qpsk(sinal):
    """recupera o dibit pelo ponto qpsk mais próximo."""
    # em cada simbolo, recupera i/q por correlação e escolhe o ponto qpsk
    # mais proximo. esse ponto devolve os dois bits daquele simbolo.
    # "dibit" quer dizer exatamente o grupo de 2 bits carregado por um simbolo.
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits += bits_do_ponto_mais_proximo(i, q, MAPA_QPSK)
    return bits


# 16-qam usa 4 bits por simbolo: 2 bits escolhem o eixo i e 2 bits o eixo q.
# cada eixo tem 4 niveis possiveis; combinando i x q, formam-se 16 pontos.
# o mapeamento e Gray: niveis vizinhos mudam apenas um bit.
NIVEIS_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}

# mapa inverso usado na demodulacao: depois de decidir o nivel recebido,
# recupera quais 2 bits representavam aquele nivel.
BITS_DO_NIVEL = {nivel: bits for bits, nivel in NIVEIS_GRAY.items()}

# normaliza os niveis -3, -1, 1 e 3 para ficarem dentro da amplitude V.
# assim, o maior nivel vira +/-V e os internos viram +/-V/3.
ESCALA_QAM = V / 3


def modular_16qam(bits):
    """16-qam: transmite quatro bits por símbolo em uma grade 4x4."""
    # 16-qam manda 4 bits por simbolo: 2 bits escolhem o nivel do eixo i
    # e 2 bits escolhem o nivel do eixo q. isso forma uma grade 4x4.
    # como cada simbolo precisa de 4 bits, completa com zeros se faltar grupo.
    bits = pad(bits, 4)
    sinal = []
    for k in range(0, len(bits), 4):
        # os dois primeiros bits do grupo escolhem a coordenada i.
        i = NIVEIS_GRAY[(bits[k], bits[k + 1])] * ESCALA_QAM

        # os dois ultimos bits escolhem a coordenada q.
        q = NIVEIS_GRAY[(bits[k + 2], bits[k + 3])] * ESCALA_QAM

        # a coordenada (i, q) vira uma onda de portadora daquele simbolo.
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def decidir_nivel_gray(valor):
    """escolhe o nível gray mais próximo de um eixo da constelação."""
    # para 16-qam a decisão pode ser feita por eixo.
    # pega o valor estimado e escolhe entre -3, -1, 1 e 3 qual ficou mais perto.
    # a decisao e separada por eixo porque a grade qam combina um nivel de i
    # com um nivel de q, cada um codificando dois bits.
    # valor e uma coordenada estimada pela correlacao, ja no eixo i ou no eixo q.
    melhor_nivel = None
    menor_dist = None
    for nivel in (-3, -1, 1, 3):
        # compara o valor recebido com cada nivel ideal ja escalado.
        dist = abs(nivel * ESCALA_QAM - valor)
        if menor_dist is None or dist < menor_dist:
            menor_dist = dist
            melhor_nivel = nivel
    # volta do nivel decidido para os 2 bits Gray daquele eixo.
    return list(BITS_DO_NIVEL[melhor_nivel])


def demodular_16qam(sinal):
    """decide 16-qam separando os eixos i e q."""
    # recupera i e q do simbolo, decide o nivel gray de cada eixo
    # e junta os bits dos dois eixos para voltar aos 4 bits originais.
    # cada volta do laco processa um simbolo completo de 100 amostras.
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        # correlacao estima onde o simbolo recebido caiu na grade i/q.
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)

        # decide 2 bits pelo eixo i e 2 bits pelo eixo q.
        bits += decidir_nivel_gray(i) + decidir_nivel_gray(q)
    return bits


# despacho usado pelo simulador e pela interface
# cada chave textual aponta para um par: (funcao que modula, funcao que demodula).
# isso evita uma cadeia grande de if/elif para escolher o algoritmo.
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}

# mesma ideia para portadora: a configuracao escolhe o par correto pelo nome.
MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "qpsk": (modular_qpsk, demodular_qpsk),
                        # seleciona automaticamente o par modulador/demodulador 16-qam.
                        "16qam": (modular_16qam, demodular_16qam)}


def modular_digital(bits, tipo):
    """aplica a modulação banda-base escolhida."""
    # a tabela guarda pares (modulador, demodulador).
    # posição 0 é a função que modula.
    # tipo vem da configuracao/interface: "nrz", "manchester" ou "bipolar".
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    """aplica o demodulador banda-base correspondente."""
    # posição 1 da tabela é a função que desfaz a modulação.
    # usar a mesma chave garante que o receptor desfaça o mesmo esquema do tx.
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    """aplica a modulação por portadora escolhida."""
    # se a opção for nenhuma, a simulação fica só na modulação digital.
    if tipo == "nenhuma":
        return None
    # se tiver portadora, chama o modulador certo pela tabela.
    # o sinal retornado aqui e o que entra no meio de comunicacao.
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    """aplica o demodulador por portadora correspondente."""
    # aqui assume que existe uma portadora escolhida e chama o demodulador dela.
    # o resultado volta a ser fluxo de bits para a camada de enlace.
    return MODULACOES_PORTADORA[tipo][1](sinal)

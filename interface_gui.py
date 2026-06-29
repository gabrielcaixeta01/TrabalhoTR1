"""
interface gráfica do simulador.

usa gtk 3 quando disponível e mantém um fallback simples em tkinter para
ambientes sem gtk.
"""

try:
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, GLib, Gdk, Pango
    BACKEND = "gtk"
except Exception:
    import tkinter as tk
    BACKEND = "tk"

import camada_enlace
import camada_fisica
import simulador


OPCOES_ENQUADRAMENTO = [("Contagem de caracteres", "contagem"),
                        ("FLAGs + inserção de bytes", "bytes"),
                        ("FLAGs + inserção de bits", "bits")]
OPCOES_DETECCAO = [("Nenhuma", "nenhum"),
                   ("Bit de paridade par", "paridade"),
                   ("Checksum", "checksum"),
                   ("CRC-32 (IEEE 802)", "crc")]
OPCOES_CORRECAO = [("Nenhuma", "nenhum"), ("Hamming", "hamming")]
OPCOES_MOD_DIGITAL = [("NRZ-Polar", "nrz"),
                      ("Manchester", "manchester"),
                      ("Bipolar (AMI)", "bipolar")]
OPCOES_MOD_PORTADORA = [("Nenhuma (banda-base)", "nenhuma"),
                        ("ASK", "ask"), ("FSK", "fsk"),
                        ("QPSK", "qpsk"), ("16-QAM", "16qam")]

ROTULOS_ENQUADRAMENTO = {valor: rotulo for rotulo, valor in OPCOES_ENQUADRAMENTO}
ROTULOS_DETECCAO = {valor: rotulo for rotulo, valor in OPCOES_DETECCAO}
ROTULOS_CORRECAO = {valor: rotulo for rotulo, valor in OPCOES_CORRECAO}
ROTULOS_DIGITAL = {valor: rotulo for rotulo, valor in OPCOES_MOD_DIGITAL}
ROTULOS_PORTADORA = {valor: rotulo for rotulo, valor in OPCOES_MOD_PORTADORA}
BITS_POR_SIMBOLO = {"ask": 1, "fsk": 1, "qpsk": 2, "16qam": 4}

MAX_AMOSTRAS_GRAFICO = 4000
MAX_BITS_TEXTO = 2048

# larguras das colunas da tabela de fases em nº de caracteres; usar largura por
# caractere (e não pixels) fixa a largura natural do rótulo, então textos longos
# quebram em várias linhas em vez de empurrar as colunas vizinhas.
COL_FASE_NUM = 3
COL_FASE_NOME = 20
COL_FASE_ENTRADA = 12
COL_FASE_SAIDA = 14
COL_FASE_BITS = 8
COL_FASE_ESPACO = 8


def bits_str(bits):
    if bits is None:
        return "-"
    texto = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        texto += f"... ({len(bits)} bits no total)"
    return texto


def plural_bits(n):
    return f"{n} bit" if n == 1 else f"{n} bits"


def plural_amostras(n):
    return f"{n} amostra" if n == 1 else f"{n} amostras"


def plural_quadros(n):
    return f"{n} quadro" if n == 1 else f"{n} quadros"


def plural_bytes(n):
    return f"{n} byte" if n == 1 else f"{n} bytes"


def medida_bits_bytes(n_bits):
    bytes_cheios, resto = divmod(n_bits, 8)
    if resto == 0:
        return f"{plural_bits(n_bits)} / {plural_bytes(bytes_cheios)}"
    if bytes_cheios == 0:
        return f"{plural_bits(n_bits)} / byte parcial"
    return f"{plural_bits(n_bits)} / {plural_bytes(bytes_cheios)} + {plural_bits(resto)}"


def quadro_bits(bits, adicionados=None, payload=None, rotulo="bits"):
    if adicionados is None:
        adicionados = [False] * len(bits)
    if payload is None:
        payload = [False] * len(bits)

    grupos = []
    for i in range(0, min(len(bits), MAX_BITS_TEXTO), 8):
        grupo_bits = bits[i:i + 8]
        grupo_add = adicionados[i:i + 8]
        grupo_payload = payload[i:i + 8]
        grupos.append({
            "bits": "".join(str(bit) for bit in grupo_bits),
            "added": "".join("1" if valor else "0" for valor in grupo_add),
            "payload": "".join("1" if valor else "0" for valor in grupo_payload),
        })

    return {
        "tipo": "bits",
        "rotulo": rotulo,
        "medida": medida_bits_bytes(len(bits)),
        "total_bits": len(bits),
        "omitidos_bits": max(0, len(bits) - MAX_BITS_TEXTO),
        "grupos": grupos,
    }


def quadro_nota(texto):
    return {"tipo": "nota", "texto": texto}


def juntar_payloads(payloads):
    bits = []
    for payload in payloads:
        bits += payload
    return bits


def mascara_hamming(bits_codificados):
    padrao = [True, True, False, True, False, False, False, True]
    mascara = []
    for i in range(0, len(bits_codificados), 8):
        tamanho = min(8, len(bits_codificados) - i)
        mascara += padrao[:tamanho]
    return mascara


def mascara_payload_hamming(mascara_entrada):
    mascara = []
    for i in range(0, len(mascara_entrada), 4):
        nibble = mascara_entrada[i:i + 4]
        if len(nibble) < 4:
            nibble += [False] * (4 - len(nibble))
        d1, d2, d3, d4 = nibble
        mascara += [False, False, d1, False, d2, d3, d4, False]
    return mascara


def marcar_enquadramento(payloads, tipo, mascaras_payload=None):
    bits, adicionados, payload = [], [], []
    if mascaras_payload is None:
        mascaras_payload = [[False] * len(item) for item in payloads]

    if tipo == "contagem":
        for payload_bits, payload_mask in zip(payloads, mascaras_payload):
            n_bytes = len(payload_bits) // 8
            cabecalho = camada_enlace.bytes_para_bits([n_bytes])
            bits += cabecalho + payload_bits
            adicionados += [True] * len(cabecalho) + [False] * len(payload_bits)
            payload += [False] * len(cabecalho) + payload_mask
        return bits, adicionados, payload

    if tipo == "bytes":
        for payload_bits, payload_mask in zip(payloads, mascaras_payload):
            flag = camada_enlace.bytes_para_bits([camada_enlace.FLAG_BYTE])
            bits += flag
            adicionados += [True] * len(flag)
            payload += [False] * len(flag)
            for i, byte in enumerate(camada_enlace.bits_para_bytes(payload_bits)):
                if byte in (camada_enlace.FLAG_BYTE, camada_enlace.ESC_BYTE):
                    esc = camada_enlace.bytes_para_bits([camada_enlace.ESC_BYTE])
                    bits += esc
                    adicionados += [True] * len(esc)
                    payload += [False] * len(esc)
                byte_bits = camada_enlace.bytes_para_bits([byte])
                bits += byte_bits
                adicionados += [False] * len(byte_bits)
                payload += payload_mask[i * 8:i * 8 + 8]
            bits += flag
            adicionados += [True] * len(flag)
            payload += [False] * len(flag)
        return bits, adicionados, payload

    for payload_bits, payload_mask in zip(payloads, mascaras_payload):
        bits += camada_enlace.FLAG_BITS
        adicionados += [True] * len(camada_enlace.FLAG_BITS)
        payload += [False] * len(camada_enlace.FLAG_BITS)
        uns = 0
        for bit, bit_payload in zip(payload_bits, payload_mask):
            bits.append(bit)
            adicionados.append(False)
            payload.append(bit_payload)
            if bit == 1:
                uns += 1
            else:
                uns = 0
            if uns == 5:
                bits.append(0)
                adicionados.append(True)
                payload.append(False)
                uns = 0
        bits += camada_enlace.FLAG_BITS
        adicionados += [True] * len(camada_enlace.FLAG_BITS)
        payload += [False] * len(camada_enlace.FLAG_BITS)
    return bits, adicionados, payload


def resumir_texto(texto, limite=48):
    texto = texto.replace("\n", "\\n")
    if len(texto) <= limite:
        return texto
    return texto[:limite - 3] + "..."


def detalhe_deteccao(tipo, n_quadros):
    if tipo == "nenhum":
        return "Nenhum EDC anexado; o receptor não valida corrupção."
    if tipo == "paridade":
        return f"Adiciona 1 byte por quadro: {n_quadros} x 8 bits."
    if tipo == "checksum":
        return f"Adiciona 2 bytes por quadro: {n_quadros} x 16 bits."
    return f"Adiciona 4 bytes por quadro: {n_quadros} x 32 bits."


def detalhe_correcao(tipo):
    if tipo == "hamming":
        return "Hamming(8,4) dobra payload + EDC: cada 4 bits viram 8 bits."
    return "Nenhuma redundância de correção foi adicionada."


def detalhe_enquadramento(tipo, n_quadros):
    if tipo == "contagem":
        return f"Adiciona 1 byte de contagem por quadro: {n_quadros} x 8 bits."
    if tipo == "bytes":
        return "Adiciona FLAGs e ESCs quando payload contém bytes especiais."
    return "Adiciona FLAGs e bits 0 após sequências de cinco bits 1."


def diagnosticar_camadas(bits_app, resultado, config):
    tam_bits = config["tam_max_quadro"] * 8
    blocos = [bits_app[i:i + tam_bits] for i in range(0, len(bits_app), tam_bits)]
    bits_blocos = sum(len(bloco) for bloco in blocos)

    payloads_edc = [
        camada_enlace.ADICIONAR_EDC[config["deteccao"]](bloco)
        for bloco in blocos
    ]
    bits_apos_edc = sum(len(payload) for payload in payloads_edc)
    bits_edc = bits_apos_edc - bits_blocos

    payloads_correcao = []
    for payload in payloads_edc:
        if config["correcao"] == "hamming":
            payloads_correcao.append(camada_enlace.codificar_hamming(payload))
        else:
            payloads_correcao.append(payload)
    bits_apos_correcao = sum(len(payload) for payload in payloads_correcao)
    bits_correcao = bits_apos_correcao - bits_apos_edc

    fluxo_enquadrado = camada_enlace.ENQUADRAR[config["enquadramento"]](
        payloads_correcao)
    bits_enlace = len(fluxo_enquadrado)
    bits_enquadramento = bits_enlace - bits_apos_correcao

    bits_blocos_visual = juntar_payloads(blocos)
    payload_blocos = [True] * len(bits_blocos_visual)

    bits_edc_visual, mascara_edc, payload_edc_visual = [], [], []
    mascaras_payload_edc = []
    for bloco, payload in zip(blocos, payloads_edc):
        bits_edc_visual += payload
        mascara_edc += [False] * len(bloco)
        mascara_edc += [True] * (len(payload) - len(bloco))
        payload_mask = [True] * len(bloco)
        payload_mask += [False] * (len(payload) - len(bloco))
        payload_edc_visual += payload_mask
        mascaras_payload_edc.append(payload_mask)

    bits_correcao_visual, mascara_correcao, payload_correcao_visual = [], [], []
    mascaras_payload_correcao = []
    for payload, payload_mask_entrada in zip(payloads_correcao,
                                             mascaras_payload_edc):
        bits_correcao_visual += payload
        if config["correcao"] == "hamming":
            mascara_correcao += mascara_hamming(payload)
            payload_mask_saida = mascara_payload_hamming(payload_mask_entrada)
        else:
            mascara_correcao += [False] * len(payload)
            payload_mask_saida = payload_mask_entrada[:]
        payload_correcao_visual += payload_mask_saida
        mascaras_payload_correcao.append(payload_mask_saida)

    (
        bits_enquadramento_visual,
        mascara_enquadramento,
        payload_enquadramento_visual,
    ) = marcar_enquadramento(
        payloads_correcao, config["enquadramento"],
        mascaras_payload_correcao)

    amostras_digitais = len(resultado["tx_sinal_banda_base"])
    amostras_tx = len(resultado["tx_sinal_transmitido"])
    if config["mod_portadora"] == "nenhuma":
        saida_portadora = plural_amostras(amostras_tx)
        padding_portadora = 0
        detalhe_portadora = "Sem portadora: o sinal banda-base trafega no meio."
    else:
        bits_por_simbolo = BITS_POR_SIMBOLO[config["mod_portadora"]]
        simbolos = (bits_enlace + bits_por_simbolo - 1) // bits_por_simbolo
        bits_representados = simbolos * bits_por_simbolo
        padding_portadora = bits_representados - bits_enlace
        saida_portadora = f"{simbolos} símbolo(s), {plural_amostras(amostras_tx)}"
        detalhe_portadora = (
            f"{bits_por_simbolo} bit(s) por símbolo; padding de "
            f"{plural_bits(padding_portadora)} quando necessário.")

    bits_portadora_visual = fluxo_enquadrado + [0] * padding_portadora
    mascara_portadora = [False] * len(fluxo_enquadrado)
    mascara_portadora += [True] * padding_portadora
    payload_portadora = payload_enquadramento_visual + [False] * padding_portadora

    payload_rx_fisica = payload_enquadramento_visual[:]
    if len(resultado["rx_bits_fisica"]) > len(payload_rx_fisica):
        payload_rx_fisica += [False] * (
            len(resultado["rx_bits_fisica"]) - len(payload_rx_fisica))
    payload_rx_fisica = payload_rx_fisica[:len(resultado["rx_bits_fisica"])]
    payload_rx_aplicacao = [True] * len(resultado["rx_bits_aplicacao"])

    return {
        "bits_aplicacao": len(bits_app),
        "bits_enlace": bits_enlace,
        "bits_adicionados": bits_enlace - len(bits_app),
        "bits_edc": bits_edc,
        "bits_correcao": bits_correcao,
        "bits_enquadramento": bits_enquadramento,
        "padding_portadora": padding_portadora,
        "fases": [
            {
                "nome": "Texto de entrada",
                "entrada": f'"{resumir_texto(config["texto"])}"',
                "saida": f"{len(config['texto'].encode('utf-8'))} byte(s) UTF-8",
                "delta": "0 bits",
                "quadro": quadro_nota(
                    "Texto original; a próxima fase mostra os bytes UTF-8 em bits."),
                "detalhe": "Mensagem original recebida pela aplicação antes de virar bits.",
            },
            {
                "nome": "Aplicação: texto -> bits",
                "entrada": f"{len(config['texto'].encode('utf-8'))} byte(s) UTF-8",
                "saida": plural_bits(len(bits_app)),
                "delta": "0 bits",
                "quadro": quadro_bits(bits_app, payload=[True] * len(bits_app),
                                      rotulo="UTF-8"),
                "detalhe": "Cada byte UTF-8 é representado por 8 bits.",
            },
            {
                "nome": "Divisão em quadros",
                "entrada": plural_bits(len(bits_app)),
                "saida": f"{plural_quadros(len(blocos))}, {plural_bits(bits_blocos)}",
                "delta": "0 bits",
                "quadro": quadro_bits(bits_blocos_visual,
                                      payload=payload_blocos,
                                      rotulo="quadros"),
                "detalhe": f"Cada quadro carrega até {config['tam_max_quadro']} byte(s).",
            },
            {
                "nome": f"Detecção de erros: {ROTULOS_DETECCAO[config['deteccao']]}",
                "entrada": plural_bits(bits_blocos),
                "saida": plural_bits(bits_apos_edc),
                "delta": plural_bits(bits_edc),
                "quadro": quadro_bits(bits_edc_visual, mascara_edc,
                                      payload_edc_visual,
                                      rotulo="payload + EDC"),
                "detalhe": detalhe_deteccao(config["deteccao"], len(blocos)),
            },
            {
                "nome": f"Correção de erros: {ROTULOS_CORRECAO[config['correcao']]}",
                "entrada": plural_bits(bits_apos_edc),
                "saida": plural_bits(bits_apos_correcao),
                "delta": plural_bits(bits_correcao),
                "quadro": quadro_bits(bits_correcao_visual, mascara_correcao,
                                      payload_correcao_visual,
                                      rotulo="payload codificado"),
                "detalhe": detalhe_correcao(config["correcao"]),
            },
            {
                "nome": f"Enquadramento: {ROTULOS_ENQUADRAMENTO[config['enquadramento']]}",
                "entrada": plural_bits(bits_apos_correcao),
                "saida": plural_bits(bits_enlace),
                "delta": plural_bits(bits_enquadramento),
                "quadro": quadro_bits(bits_enquadramento_visual,
                                      mascara_enquadramento,
                                      payload_enquadramento_visual,
                                      rotulo="quadro Tx"),
                "detalhe": detalhe_enquadramento(config["enquadramento"], len(blocos)),
            },
            {
                "nome": f"Modulação digital: {ROTULOS_DIGITAL[config['mod_digital']]}",
                "entrada": plural_bits(bits_enlace),
                "saida": plural_amostras(amostras_digitais),
                "delta": "0 bits",
                "quadro": quadro_bits(fluxo_enquadrado,
                                      payload=payload_enquadramento_visual,
                                      rotulo="bits modulados"),
                "detalhe": (
                    f"Cada bit vira {camada_fisica.AMOSTRAS_POR_BIT} amostras em Volts."
                ),
            },
            {
                "nome": f"Modulação por portadora: {ROTULOS_PORTADORA[config['mod_portadora']]}",
                "entrada": plural_bits(bits_enlace),
                "saida": saida_portadora,
                "delta": plural_bits(padding_portadora),
                "quadro": quadro_bits(bits_portadora_visual, mascara_portadora,
                                      payload_portadora,
                                      rotulo="bits por símbolo"),
                "detalhe": detalhe_portadora,
            },
            {
                "nome": "Meio ruidoso",
                "entrada": plural_amostras(amostras_tx),
                "saida": plural_amostras(len(resultado["rx_sinal_recebido"])),
                "delta": "0 bits",
                "quadro": quadro_nota(
                    f"{plural_amostras(amostras_tx)} no meio; o ruído altera amostras."),
                "detalhe": (
                    f"Ruído gaussiano: média {config['ruido_media']:.2f} V, "
                    f"sigma {config['ruido_sigma']:.2f} V por amostra."
                ),
            },
            {
                "nome": "Receptor: bits -> texto",
                "entrada": plural_bits(len(resultado["rx_bits_aplicacao"])),
                "saida": f'"{resumir_texto(resultado["rx_texto"])}"',
                "delta": "0 bits",
                "quadro": quadro_bits(resultado["rx_bits_aplicacao"],
                                      payload=payload_rx_aplicacao,
                                      rotulo="bits RX"),
                "detalhe": "Demodula, valida enlace e reconstrói o texto de aplicação.",
            },
        ],
        "quadros_bits": {
            "texto_entrada": quadro_bits(bits_app, payload=[True] * len(bits_app),
                                         rotulo="UTF-8"),
            "fisica_rx": quadro_bits(resultado["rx_bits_fisica"],
                                     payload=payload_rx_fisica,
                                     rotulo="bits demodulados"),
            "quadros_rx": quadro_bits(resultado["rx_bits_aplicacao"],
                                      payload=payload_rx_aplicacao,
                                      rotulo="payload validado"),
            "aplicacao_rx": quadro_bits(resultado["rx_bits_aplicacao"],
                                        payload=payload_rx_aplicacao,
                                        rotulo="bits RX"),
        },
    }


def formatar_diagnostico(diagnostico, resultado, config):
    linhas = [
        "PROCESSAMENTO POR FASE",
        (
            f"Resumo: aplicação {plural_bits(diagnostico['bits_aplicacao'])} -> "
            f"enlace {plural_bits(diagnostico['bits_enlace'])} | "
            f"adicionados {plural_bits(diagnostico['bits_adicionados'])}"
        ),
        (
            f"EDC +{plural_bits(diagnostico['bits_edc'])} | "
            f"Hamming +{plural_bits(diagnostico['bits_correcao'])} | "
            f"Enquadramento +{plural_bits(diagnostico['bits_enquadramento'])} | "
            f"Padding portadora +{plural_bits(diagnostico['padding_portadora'])}"
        ),
        (
            f"Potência sinal {resultado['potencia_sinal_w']:.4f} W | "
            f"potência ruído {resultado['potencia_ruido_w']:.4f} W | "
            f"sigma {config['ruido_sigma']:.2f} V"
        ),
        "",
    ]
    for indice, fase in enumerate(diagnostico["fases"], start=1):
        linhas.append(
            f"{indice:02d}. {fase['nome']}\n"
            f"    entrada: {fase['entrada']}\n"
            f"    saida:   {fase['saida']}\n"
            f"    delta:   {fase['delta']}\n"
            f"    nota:    {fase['detalhe']}"
        )
    return "\n".join(linhas)


def quadro_bits_para_texto(quadro):
    if not quadro:
        return "sem bits"
    if quadro.get("tipo") == "nota":
        return quadro.get("texto", "")

    linhas = [
        f"{quadro.get('rotulo', 'bits')} ({quadro.get('medida', '')})",
        "p = carga original | + = bit adicionado pelo protocolo | . = outro",
    ]
    grupos = quadro.get("grupos", [])
    if not grupos:
        linhas.append("(sem bits)")
        return "\n".join(linhas)

    bits = []
    marcas = []
    for grupo in grupos:
        grupo_bits = grupo.get("bits", "")
        grupo_add = grupo.get("added", "")
        grupo_payload = grupo.get("payload", "")
        bits.append(grupo_bits)
        marcas.append("".join(
            "+" if grupo_add[i:i + 1] == "1"
            else ("p" if grupo_payload[i:i + 1] == "1" else ".")
            for i in range(len(grupo_bits))
        ))

    linhas.append("bits : " + " ".join(bits))
    linhas.append("marca: " + " ".join(marcas))
    omitidos = quadro.get("omitidos_bits", 0)
    if omitidos:
        linhas.append(f"... {omitidos} bits omitidos na visualização")
    return "\n".join(linhas)


def formatar_bits_por_fase(diagnostico):
    linhas = ["BITS POR FASE", ""]
    for indice, fase in enumerate(diagnostico["fases"], start=1):
        linhas.append(f"{indice:02d}. {fase['nome']}")
        linhas.append(quadro_bits_para_texto(fase.get("quadro")))
        linhas.append("")
    return "\n".join(linhas).rstrip()


def formatar_relatorio_quadros(resultado, config):
    linhas = ["RELATÓRIO DOS QUADROS RECEBIDOS"]
    for quadro in resultado["rx_relatorio_quadros"]:
        linha = (
            f"Quadro {quadro['quadro']}: "
            f"EDC {'OK' if quadro['edc_ok'] else 'ERRO DETECTADO'}"
        )
        if config["correcao"] == "hamming":
            linha += f", {quadro['corrigidos']} bit(s) corrigido(s)"
        if quadro["erro_duplo"]:
            linha += ", ERRO DUPLO detectado"
        linhas.append(linha)
    if len(linhas) == 1:
        linhas.append("(nenhum quadro recuperado)")
    return "\n".join(linhas)


def amostrar_para_grafico(sinal, limite=MAX_AMOSTRAS_GRAFICO):
    if not sinal:
        return []
    if len(sinal) <= limite:
        return list(sinal)
    passo = len(sinal) / limite
    return [sinal[int(i * passo)] for i in range(limite)]


def limites_series(series):
    valores = []
    for _, sinal in series:
        valores.extend(amostrar_para_grafico(sinal))
    if not valores:
        return -1.0, 1.0
    minimo = min(valores)
    maximo = max(valores)
    if minimo == maximo:
        folga = 1.0 if minimo == 0 else abs(minimo) * 0.25
        return minimo - folga, maximo + folga
    folga = (maximo - minimo) * 0.12
    return minimo - folga, maximo + folga


def formatar_volts(valor):
    return f"{valor:.2f} V"


if BACKEND == "gtk":

    class GraficoSinal(Gtk.DrawingArea):
        def __init__(self):
            super().__init__()
            self.series = []
            self.set_size_request(-1, 285)
            self.connect("draw", self.ao_desenhar)

        def set_series(self, series):
            self.series = series
            self.queue_draw()

        def ao_desenhar(self, _widget, cr):
            largura = max(1, self.get_allocated_width())
            altura = max(1, self.get_allocated_height())
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.paint()

            if not self.series:
                self.desenhar_texto(cr, 16, 28, "sem sinal para exibir", 0.35)
                return False

            topo = 26
            margem_baixo = 22
            espaco = 22
            altura_bloco = (altura - topo - margem_baixo - espaco) / len(self.series)
            minimo, maximo = limites_series(self.series)
            faixa = maximo - minimo or 1.0

            for indice, (titulo, sinal) in enumerate(self.series):
                y0 = topo + indice * (altura_bloco + espaco)
                self.desenhar_bloco(cr, titulo, sinal, 14, y0, largura - 28,
                                    altura_bloco, minimo, faixa)
            return False

        def desenhar_bloco(self, cr, titulo, sinal, x, y, largura, altura,
                           minimo, faixa):
            amostras = amostrar_para_grafico(sinal)
            self.desenhar_texto(cr, x, y - 7, titulo, 0.08, tamanho=11)

            cr.set_line_width(1)
            cr.set_source_rgb(0.89, 0.92, 0.96)
            for k in range(4):
                yy = y + altura * k / 3
                cr.move_to(x, yy)
                cr.line_to(x + largura, yy)
                cr.stroke()

            zero_y = y + altura - ((0 - minimo) / faixa) * altura
            if y <= zero_y <= y + altura:
                cr.set_source_rgb(0.78, 0.82, 0.88)
                cr.move_to(x, zero_y)
                cr.line_to(x + largura, zero_y)
                cr.stroke()

            self.desenhar_texto(cr, x + largura - 64, y + 11,
                                formatar_volts(minimo + faixa), 0.35,
                                tamanho=9)
            self.desenhar_texto(cr, x + largura - 64, y + altura - 4,
                                formatar_volts(minimo), 0.35, tamanho=9)

            if len(amostras) < 2:
                self.desenhar_texto(cr, x + 8, y + altura / 2,
                                    "sem amostras", 0.35)
                return

            cr.set_source_rgb(0.06, 0.46, 0.43)
            cr.set_line_width(1.35)
            for idx, valor in enumerate(amostras):
                xx = x + largura * idx / (len(amostras) - 1)
                yy = y + altura - ((valor - minimo) / faixa) * altura
                if idx == 0:
                    cr.move_to(xx, yy)
                else:
                    cr.line_to(xx, yy)
            cr.stroke()

        @staticmethod
        def desenhar_texto(cr, x, y, texto, cinza, tamanho=10):
            cr.set_source_rgb(cinza, cinza, cinza + 0.04)
            cr.select_font_face("Sans")
            cr.set_font_size(tamanho)
            cr.move_to(x, y)
            cr.show_text(texto)

    class JanelaSimulador(Gtk.Window):
        """janela principal do simulador em gtk 3."""

        def __init__(self):
            super().__init__(title="Simulador TR1 - Camadas Física e de Enlace")
            self._dimensionar_para_tela()
            self.set_position(Gtk.WindowPosition.CENTER)
            self.connect("destroy", self.ao_fechar)
            self.continuo_id = None
            self.contador_continuo = 0
            self.metricas = {}
            self.linhas_fases = []
            self.textos_bits = {}
            self.graficos = {}
            self.aplicar_tema_claro()

            fundo = Gtk.EventBox()
            fundo.set_visible_window(True)
            fundo.get_style_context().add_class("app-root")
            self.add(fundo)

            raiz = Gtk.Grid(column_spacing=16)
            raiz.set_border_width(16)
            raiz.set_hexpand(True)
            raiz.set_vexpand(True)
            raiz.set_halign(Gtk.Align.FILL)
            raiz.set_valign(Gtk.Align.FILL)
            raiz.get_style_context().add_class("app-root")
            fundo.add(raiz)

            painel_config = self.montar_painel_config()
            painel_config.set_hexpand(True)

            config_scroll = Gtk.ScrolledWindow()
            config_scroll.get_style_context().add_class("results-scroll")
            config_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            config_scroll.set_min_content_width(340)
            config_scroll.set_shadow_type(Gtk.ShadowType.NONE)
            config_scroll.set_can_focus(False)
            config_scroll.add(painel_config)
            config_scroll.set_hexpand(False)
            config_scroll.set_vexpand(True)
            config_scroll.set_halign(Gtk.Align.START)

            painel_resultados = self.montar_painel_resultados()
            painel_resultados.set_hexpand(True)
            painel_resultados.set_vexpand(True)

            raiz.attach(config_scroll, 0, 0, 1, 1)
            raiz.attach(painel_resultados, 1, 0, 1, 1)
            self.inicializar_resultados()

        def _dimensionar_para_tela(self):
            """ajusta a janela à área útil do monitor para caber em qualquer
            resolução (inclusive telas pequenas de notebook)."""
            largura, altura = 1320, 880
            try:
                display = Gdk.Display.get_default()
                monitor = display.get_primary_monitor() or display.get_monitor(0)
                area = monitor.get_workarea()
                largura = max(960, min(largura, area.width - 48))
                altura = max(620, min(altura, area.height - 56))
            except Exception:
                pass
            self.set_default_size(largura, altura)
            # garante um mínimo utilizável sem travar o redimensionamento.
            geo = Gdk.Geometry()
            geo.min_width, geo.min_height = 900, 600
            self.set_geometry_hints(None, geo, Gdk.WindowHints.MIN_SIZE)

        def _ajustar_janela_nativa(self):
            """no macOS força a janela (NSWindow) para aparência clara e fundo
            opaco, eliminando a "borda preta"/barra escura do backend Quartz.
            é no-op em outras plataformas ou se o PyObjC não estiver presente."""
            try:
                from AppKit import NSApplication, NSAppearance, NSColor
            except Exception:
                return False
            try:
                aqua = NSAppearance.appearanceNamed_("NSAppearanceNameAqua")
                fundo = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                    0.925, 0.937, 0.961, 1.0)  # #eceff5, igual ao fundo da app
                for ns in NSApplication.sharedApplication().windows():
                    if aqua is not None:
                        ns.setAppearance_(aqua)
                    ns.setOpaque_(True)
                    ns.setBackgroundColor_(fundo)
                    ns.setTitlebarAppearsTransparent_(False)
            except Exception:
                pass
            return False

        @staticmethod
        def aplicar_tema_claro():
            # força preferência por tema claro para os widgets usarem sempre a
            # variante clara; a barra de título nativa é clareada via PyObjC.
            ajustes = Gtk.Settings.get_default()
            if ajustes is not None:
                ajustes.set_property("gtk-application-prefer-dark-theme", False)

            css = b"""
            * {
                font-family: "Inter", "Cantarell", "Segoe UI", sans-serif;
                font-size: 14px;
                text-shadow: none;
                -gtk-icon-shadow: none;
                transition: none;
                outline: none;
            }
            window, .app-root, .main-panel, scrolledwindow, viewport {
                background: #eceff5;
                color: #0f172a;
            }
            scrolledwindow, scrolledwindow:focus, viewport, viewport:focus,
            stack, stack:focus, grid, grid:focus, box, box:focus {
                border: 0;
                outline: none;
                box-shadow: none;
            }
            scrolledwindow.frame, scrolledwindow.frame:focus,
            .frame, .frame:focus {
                border: 0;
                border-style: none;
                outline: none;
                box-shadow: none;
            }
            scrolledwindow undershoot,
            scrolledwindow overshoot,
            scrolledwindow junction,
            scrolledwindow scrollbar {
                background: transparent;
                background-image: none;
                border: 0;
                box-shadow: none;
            }
            /* mantemos a decoracao nativa do macOS (sem CSD, que no Quartz
               cria uma caixa preta em volta da janela). a barra de titulo e
               clareada via PyObjC em `_ajustar_janela_nativa`. */
            window, window.background {
                background-color: #eceff5;
            }
            label { color: #0f172a; }

            /* ---- campos de entrada ---- */
            entry {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                min-height: 44px;
                padding: 6px 14px;
                font-size: 15px;
                font-weight: 500;
                caret-color: #2563eb;
            }
            entry:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
            }
            entry selection {
                background: #2563eb;
                color: #ffffff;
            }
            entry image { color: #94a3b8; }
            spinbutton {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                min-height: 44px;
                padding: 0 4px;
                font-size: 15px;
                font-weight: 600;
            }
            spinbutton:focus-within {
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
            }
            spinbutton entry {
                border: 0;
                box-shadow: none;
                background: transparent;
                min-height: 36px;
                padding: 0 6px;
                font-size: 15px;
                font-weight: 600;
            }
            spinbutton button {
                background: #eef2f7;
                color: #1e293b;
                border: 0;
                border-radius: 8px;
                margin: 4px 3px;
                min-width: 34px;
                min-height: 34px;
            }
            spinbutton button:hover { background: #dbe3ef; }
            spinbutton button:active { background: #cbd5e1; }

            /* ---- combos / dropdowns ---- */
            combobox > box > button {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                min-height: 44px;
                padding: 6px 14px;
                box-shadow: none;
                font-size: 15px;
                font-weight: 600;
            }
            combobox > box > button:hover {
                border-color: #94a3b8;
                background: #f8fafc;
            }
            combobox > box > button:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
            }
            combobox cellview, combobox button label { color: #0f172a; }
            combobox arrow {
                color: #64748b;
                min-width: 18px;
                min-height: 18px;
            }
            combobox window.background,
            menu, .menu, popover, popover.background {
                background: #ffffff;
                color: #0f172a;
                border: 1px solid #dbe3ef;
                border-radius: 12px;
                padding: 6px;
                box-shadow: 0 14px 34px rgba(15, 23, 42, 0.20);
            }
            menuitem, .menu menuitem, modelbutton {
                border-radius: 8px;
                padding: 9px 12px;
                color: #0f172a;
            }
            menuitem label, modelbutton label, popover label { color: #0f172a; }
            menuitem:hover, menuitem:selected,
            combobox menuitem:hover, modelbutton:hover {
                background: #eff6ff;
                color: #1d4ed8;
            }
            menuitem:hover label, menuitem:selected label { color: #1d4ed8; }

            /* ---- botoes de acao ---- */
            button { border-radius: 11px; }
            button.primary, button.secondary {
                min-height: 46px;
                font-weight: 800;
            }
            button.primary {
                background: #2563eb;
                color: #ffffff;
                border: 1px solid #1d4ed8;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.30);
            }
            button.primary:hover { background: #1d4ed8; }
            button.primary label { color: #ffffff; }
            button.secondary {
                background: #ffffff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
            }
            button.secondary label { color: #1d4ed8; }
            button.secondary:hover { background: #eff6ff; }
            button.secondary:checked {
                background: #dc2626;
                border-color: #b91c1c;
                box-shadow: 0 4px 12px rgba(220, 38, 38, 0.30);
            }
            button.secondary:checked label { color: #ffffff; }

            /* ---- cartoes ---- */
            .sidebar, .card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            }
            .metric-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            }
            .title {
                font-size: 22px;
                font-weight: 800;
                color: #0f172a;
            }
            .subtitle {
                color: #64748b;
                font-size: 13px;
            }
            .field-label {
                font-weight: 700;
                font-size: 13px;
                color: #334155;
            }
            .sidebar-section {
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
                color: #94a3b8;
                margin-top: 10px;
                margin-bottom: 2px;
            }
            .section-title {
                font-size: 18px;
                font-weight: 900;
                color: #0f172a;
            }
            .section-hint {
                color: #64748b;
                font-size: 12px;
            }
            .mode-panel {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                color: #475569;
            }
            .mode-panel label { color: #475569; }

            /* ---- metricas ---- */
            .metric-label {
                color: #94a3b8;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.6px;
            }
            .metric-value {
                color: #0f172a;
                font-size: 22px;
                font-weight: 900;
            }
            .metric-ok { color: #047857; }
            .metric-warn { color: #b45309; }
            .metric-error { color: #b91c1c; }

            /* ---- tabela de fases ---- */
            .phase-table {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            .phase-head {
                background: #f1f5f9;
                border-bottom: 2px solid #e2e8f0;
                border-radius: 12px 12px 0 0;
            }
            .phase-row { background: #ffffff; border-bottom: 1px solid #eef2f7; }
            .phase-row-alt { background: #f8fafc; }
            .phase-row:hover { background: #eff6ff; }
            .phase-number {
                color: #1d4ed8;
                font-size: 13px;
                font-weight: 900;
            }
            .phase-name {
                color: #0f172a;
                font-size: 14px;
                font-weight: 800;
            }
            .phase-caption {
                color: #475569;
                font-size: 12px;
                font-weight: 800;
            }
            .phase-cell {
                color: #334155;
                font-size: 13px;
            }
            .phase-delta {
                color: #047857;
                font-size: 13px;
                font-weight: 900;
            }
            .phase-zero {
                color: #94a3b8;
                font-size: 13px;
                font-weight: 700;
            }
            .results-scroll {
                background: #eceff5;
                border: 0;
                box-shadow: none;
            }
            stackswitcher {
                background: transparent;
                padding: 0;
            }
            stackswitcher button {
                min-height: 36px;
                padding: 6px 14px;
                border-radius: 10px;
                background: #ffffff;
                color: #1e293b;
                border: 1px solid #dbe3ef;
                font-weight: 800;
            }
            stackswitcher button:checked {
                background: #2563eb;
                color: #ffffff;
                border-color: #1d4ed8;
            }
            stackswitcher button:checked label { color: #ffffff; }
            textview, textview text {
                background: #ffffff;
                color: #0f172a;
                font-family: "SF Mono", "Cascadia Mono", "Consolas", monospace;
                font-size: 12px;
            }
            .bits-box {
                background: #ffffff;
                border: 1px solid #dbe3ef;
                border-radius: 10px;
            }
            .bits-title {
                color: #0f172a;
                font-size: 14px;
                font-weight: 900;
            }
            .bits-hint {
                color: #64748b;
                font-size: 12px;
            }
            """
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

        @staticmethod
        def ao_fechar(*_args):
            if Gtk.main_level() > 0:
                Gtk.main_quit()

        @staticmethod
        def adicionar_classes(widget, *classes):
            contexto = widget.get_style_context()
            for classe in classes:
                contexto.add_class(classe)

        @staticmethod
        def label(texto="", classe=None, xalign=0, wrap=False):
            label = Gtk.Label(label=texto, xalign=xalign)
            if wrap:
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            if classe:
                label.get_style_context().add_class(classe)
            return label

        def novo_card(self, classe="card"):
            cartao = Gtk.EventBox()
            cartao.get_style_context().add_class(classe)
            conteudo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            conteudo.set_border_width(12)
            cartao.add(conteudo)
            return cartao, conteudo

        # montagem da tela

        def montar_painel_config(self):
            cartao, caixa = self.novo_card("sidebar")
            cartao.set_size_request(320, -1)
            caixa.set_size_request(292, -1)

            titulo = self.label("Simulador TR1", "title")
            caixa.pack_start(titulo, False, False, 0)
            subtitulo = self.label(
                "Transmissão completa: aplicação, enlace, física e meio ruidoso.",
                "subtitle",
                wrap=True,
            )
            subtitulo.set_width_chars(26)
            subtitulo.set_max_width_chars(30)
            caixa.pack_start(subtitulo, False, False, 0)

            def adicionar(rotulo_texto, widget):
                grupo = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                grupo.pack_start(self.label(rotulo_texto, "field-label"), False, False, 0)
                grupo.pack_start(widget, False, True, 0)
                caixa.pack_start(grupo, False, True, 0)

            def secao(texto):
                rotulo = self.label(texto.upper(), "sidebar-section")
                caixa.pack_start(rotulo, False, False, 0)

            secao("Mensagem")
            self.entrada_texto = Gtk.Entry(text="Ola, TR1!")
            self.entrada_texto.set_width_chars(20)
            self.entrada_texto.set_hexpand(True)
            self.entrada_texto.set_placeholder_text("Digite a mensagem a transmitir")
            adicionar("Texto de entrada", self.entrada_texto)

            secao("Camada de enlace")
            self.spin_quadro = Gtk.SpinButton.new_with_range(1, 100, 1)
            self.spin_quadro.set_value(8)
            self.spin_quadro.set_size_request(260, 44)
            adicionar("Tamanho máximo do quadro", self.spin_quadro)

            self.combo_enq = self.novo_combo(OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento", self.combo_enq)

            self.combo_det = self.novo_combo(OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros", self.combo_det)

            self.combo_cor = self.novo_combo(OPCOES_CORRECAO, 1)
            adicionar("Correção de erros", self.combo_cor)

            secao("Camada física")
            self.combo_dig = self.novo_combo(OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital", self.combo_dig)

            self.combo_port = self.novo_combo(OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora", self.combo_port)

            secao("Meio e ruído")
            self.spin_media = Gtk.SpinButton.new_with_range(-50.0, 50.0, 0.1)
            self.spin_media.set_digits(2)
            self.spin_media.set_value(0.0)
            self.spin_media.set_size_request(260, 44)
            adicionar("Ruído — média (V)", self.spin_media)

            self.spin_sigma = Gtk.SpinButton.new_with_range(0.0, 50.0, 0.1)
            self.spin_sigma.set_digits(2)
            self.spin_sigma.set_value(0.10)
            self.spin_sigma.set_size_request(260, 44)
            adicionar("Ruído — desvio σ (V)", self.spin_sigma)

            secao("Execução")
            self.spin_intervalo = Gtk.SpinButton.new_with_range(250, 5000, 50)
            self.spin_intervalo.set_value(900)
            self.spin_intervalo.set_size_request(260, 44)
            adicionar("Intervalo contínuo (ms)", self.spin_intervalo)

            botoes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            self.botao_transmitir = Gtk.Button(label="Transmitir uma vez")
            self.botao_transmitir.get_style_context().add_class("primary")
            self.botao_transmitir.connect("clicked", self.ao_transmitir)
            botoes.pack_start(self.botao_transmitir, True, True, 0)

            self.botao_continuo = Gtk.ToggleButton(label="Iniciar contínua")
            self.botao_continuo.get_style_context().add_class("secondary")
            self.botao_continuo.connect("toggled", self.ao_alternar_continua)
            botoes.pack_start(self.botao_continuo, True, True, 0)
            caixa.pack_start(botoes, False, True, 4)

            self.lbl_modo = Gtk.Label(label="Modo manual", xalign=0)
            modo_box = Gtk.EventBox()
            modo_box.get_style_context().add_class("mode-panel")
            modo_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            modo_inner.set_border_width(8)
            modo_inner.pack_start(self.lbl_modo, False, False, 0)
            modo_box.add(modo_inner)
            caixa.pack_start(modo_box, False, True, 0)

            self.lbl_status = Gtk.Label(label="", xalign=0)
            self.lbl_status.set_line_wrap(True)
            self.lbl_status.set_max_width_chars(34)
            modo_inner.pack_start(self.lbl_status, False, False, 0)
            return cartao

        def novo_combo(self, opcoes, indice_padrao):
            combo = Gtk.ComboBoxText()
            for rotulo, _ in opcoes:
                combo.append_text(rotulo)
            combo.set_active(indice_padrao)
            combo.set_hexpand(True)
            combo.set_size_request(260, 44)
            combo._opcoes = opcoes
            return combo

        @staticmethod
        def valor_combo(combo):
            return combo._opcoes[combo.get_active()][1]

        def montar_painel_resultados(self):
            painel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            painel.get_style_context().add_class("main-panel")
            painel.set_border_width(4)
            painel.set_hexpand(True)
            painel.set_vexpand(True)
            painel.set_valign(Gtk.Align.FILL)

            painel.pack_start(self.montar_metricas(), False, True, 0)
            painel.pack_start(self.montar_paginas_resultados(), True, True, 0)
            self.rolagem_resultados = None
            return painel

        def montar_paginas_resultados(self):
            caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            caixa.set_hexpand(True)
            caixa.set_vexpand(True)

            self.stack_resultados = Gtk.Stack()
            self.stack_resultados.set_transition_type(
                Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.stack_resultados.set_hexpand(True)
            self.stack_resultados.set_vexpand(True)

            seletor = Gtk.StackSwitcher()
            seletor.set_stack(self.stack_resultados)
            seletor.set_halign(Gtk.Align.START)
            caixa.pack_start(seletor, False, False, 0)

            self.stack_resultados.add_titled(
                self.montar_tabela_diagnostico(), "processamento",
                "Processamento")
            self.stack_resultados.add_titled(
                self.montar_pagina_bits(), "bits", "Bits e quadros")
            self.stack_resultados.add_titled(
                self.montar_pagina_graficos(), "graficos", "Gráficos")

            caixa.pack_start(self.stack_resultados, True, True, 0)
            return caixa

        def montar_metricas(self):
            grade = Gtk.Grid(column_spacing=10, row_spacing=10)
            grade.set_column_homogeneous(True)
            grade.set_hexpand(True)
            itens = [
                ("bits_aplicacao", "Bits da aplicação"),
                ("bits_enlace", "Bits no enlace"),
                ("bits_adicionados", "Bits adicionados"),
                ("potencia_sinal", "Potência do sinal"),
                ("potencia_ruido", "Potência do ruído"),
                ("texto_recuperado", "Status da recepção"),
            ]
            for indice, (chave, rotulo) in enumerate(itens):
                cartao, conteudo = self.novo_card("metric-card")
                conteudo.pack_start(
                    self.label(rotulo.upper(), "metric-label"), False, False, 0)
                valor = self.label("-", "metric-value")
                valor.set_line_wrap(True)
                valor.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                conteudo.pack_start(valor, False, False, 0)
                self.metricas[chave] = valor
                coluna = indice % 2
                linha = indice // 2
                grade.attach(cartao, coluna, linha, 1, 1)
            return grade

        def montar_tabela_diagnostico(self):
            cartao, conteudo = self.novo_card("card")
            conteudo.pack_start(
                self.label("Detalhamento por fase", "section-title"),
                False, False, 0)

            self.lbl_resumo_fases = self.label(
                "Resumo da transmissão aparece aqui depois da primeira execução.",
                "section-hint",
                wrap=True,
            )
            conteudo.pack_start(self.lbl_resumo_fases, False, False, 0)

            tabela = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            tabela.get_style_context().add_class("phase-table")
            tabela.set_hexpand(True)
            tabela.pack_start(self.criar_cabecalho_fases(), False, False, 0)
            for indice in range(10):
                self.linhas_fases.append(
                    self.criar_linha_fase(tabela, indice + 1, indice % 2 == 1))
            conteudo.pack_start(tabela, False, True, 0)
            return cartao

        # cada coluna usa a mesma largura (em caracteres) no cabeçalho e nas
        # linhas, então tudo fica alinhado como uma tabela de verdade.
        def celula_fase(self, chars, classe, expandir=False):
            celula = self.label("-", classe, xalign=0, wrap=True)
            celula.set_valign(Gtk.Align.START)
            celula.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            celula.set_width_chars(chars)
            if expandir:
                celula.set_hexpand(True)
                celula.set_halign(Gtk.Align.FILL)
            else:
                celula.set_max_width_chars(chars)
            return celula

        def criar_cabecalho_fases(self):
            cabecalho = Gtk.EventBox()
            cabecalho.get_style_context().add_class("phase-head")
            linha = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                            spacing=COL_FASE_ESPACO)
            linha.set_border_width(10)
            cabecalho.add(linha)

            colunas = [
                ("Nº", COL_FASE_NUM, False),
                ("Fase", COL_FASE_NOME, False),
                ("Entrada", COL_FASE_ENTRADA, False),
                ("Processamento", 0, True),
                ("Saída", COL_FASE_SAIDA, False),
                ("Bits +", COL_FASE_BITS, False),
            ]
            for texto, chars, expandir in colunas:
                titulo = self.label(texto, "phase-caption")
                if expandir:
                    titulo.set_hexpand(True)
                    titulo.set_halign(Gtk.Align.FILL)
                else:
                    titulo.set_width_chars(chars)
                    titulo.set_max_width_chars(chars)
                linha.pack_start(titulo, expandir, expandir, 0)
            return cabecalho

        def criar_linha_fase(self, parent, numero, alternada):
            linha = Gtk.EventBox()
            contexto = linha.get_style_context()
            contexto.add_class("phase-row")
            if alternada:
                contexto.add_class("phase-row-alt")
            linha.set_hexpand(True)

            grade = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                            spacing=COL_FASE_ESPACO)
            grade.set_border_width(10)
            grade.set_hexpand(True)
            linha.add(grade)

            numero_label = self.celula_fase(COL_FASE_NUM, "phase-number")
            numero_label.set_text(f"{numero:02d}")
            grade.pack_start(numero_label, False, False, 0)

            nome = self.celula_fase(COL_FASE_NOME, "phase-name")
            grade.pack_start(nome, False, False, 0)

            entrada = self.celula_fase(COL_FASE_ENTRADA, "phase-cell")
            grade.pack_start(entrada, False, False, 0)

            detalhe = self.celula_fase(0, "phase-cell", expandir=True)
            grade.pack_start(detalhe, True, True, 0)

            saida = self.celula_fase(COL_FASE_SAIDA, "phase-cell")
            grade.pack_start(saida, False, False, 0)

            delta = self.celula_fase(COL_FASE_BITS, "phase-cell")
            grade.pack_start(delta, False, False, 0)

            parent.pack_start(linha, False, True, 0)
            return {
                "nome": nome,
                "entrada": entrada,
                "saida": saida,
                "delta": delta,
                "detalhe": detalhe,
            }

        def montar_pagina_bits(self):
            pagina = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            pagina.set_hexpand(True)
            pagina.set_vexpand(True)

            itens = [
                ("tx_app", "TX - aplicação",
                 "Texto convertido para bits UTF-8."),
                ("tx_enlace", "TX - enlace",
                 "Fluxo depois de EDC, Hamming e enquadramento."),
                ("rx_fisica", "RX - física",
                 "Bits demodulados a partir do sinal recebido."),
                ("rx_app", "RX - aplicação",
                 "Payload validado e reconstruído como texto."),
                ("quadros", "Quadros recebidos",
                 "Resultado do EDC e correções por Hamming."),
                ("fases_bits", "Bits por fase",
                 "p = payload original, + = bits adicionados pelo protocolo."),
            ]
            for chave, titulo, hint in itens:
                card = self.criar_cartao_texto_bits(chave, titulo, hint)
                pagina.pack_start(card, False, True, 0)

            return pagina

        def criar_cartao_texto_bits(self, chave, titulo, hint):
            cartao, conteudo = self.novo_card("card")
            conteudo.pack_start(self.label(titulo, "bits-title"), False, False, 0)
            conteudo.pack_start(self.label(hint, "bits-hint", wrap=True),
                                False, False, 0)

            texto = Gtk.TextView()
            texto.set_editable(False)
            texto.set_cursor_visible(False)
            texto.set_monospace(True)
            texto.set_wrap_mode(Gtk.WrapMode.CHAR)
            texto.get_style_context().add_class("bits-box")
            texto.set_size_request(-1, 170 if chave != "fases_bits" else 260)

            rolagem = Gtk.ScrolledWindow()
            rolagem.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            rolagem.set_shadow_type(Gtk.ShadowType.NONE)
            rolagem.add(texto)
            conteudo.pack_start(rolagem, True, True, 0)

            self.textos_bits[chave] = texto
            return cartao

        def montar_pagina_graficos(self):
            pagina = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            pagina.set_hexpand(True)
            pagina.set_vexpand(True)

            itens = [
                ("tx_banda_base", "1. Banda-base (Tx)",
                 "Codificação digital antes da portadora."),
                ("tx_transmitido", "2. Sinal enviado ao meio (Tx)",
                 "Portadora ou banda-base que sai do transmissor."),
                ("rx_recebido", "3. Sinal recebido com ruído (Rx)",
                 "Mesmo sinal após o canal gaussiano."),
                ("rx_banda_base", "4. Banda-base reconstruída (Rx)",
                 "Bits demodulados redesenhados para comparação."),
            ]

            for chave, titulo, hint in itens:
                card, grafico = self.criar_cartao_grafico(titulo, hint)
                self.graficos[chave] = grafico
                pagina.pack_start(card, False, True, 0)
            return pagina

        def criar_cartao_grafico(self, titulo, hint):
            cartao, conteudo = self.novo_card("card")
            conteudo.pack_start(self.label(titulo, "section-title"), False, False, 0)
            conteudo.pack_start(self.label(hint, "section-hint", wrap=True),
                                False, False, 0)

            grafico = GraficoSinal()
            grafico.set_size_request(-1, 230)
            conteudo.pack_start(grafico, True, True, 0)
            return cartao, grafico

        # lógica da simulação

        def inicializar_resultados(self):
            self.definir_banner(
                "aguardando transmissão",
                "ok",
            )
            self.lbl_resumo_fases.set_text(
                "Resumo da transmissão aparece aqui depois da primeira execução.")
            for valor in self.metricas.values():
                if valor is not self.metricas["texto_recuperado"]:
                    valor.set_text("-")
            for labels in self.linhas_fases:
                for label in labels.values():
                    label.set_text("-")
            for texto in self.textos_bits.values():
                texto.get_buffer().set_text("Clique em Transmitir uma vez.")
            for grafico in self.graficos.values():
                grafico.set_series([])

        def definir_banner(self, texto, estado):
            if "texto_recuperado" not in self.metricas:
                return
            valor = self.metricas["texto_recuperado"]
            valor.set_text(texto)
            contexto = valor.get_style_context()
            contexto.remove_class("metric-ok")
            contexto.remove_class("metric-warn")
            contexto.remove_class("metric-error")
            if estado == "erro":
                contexto.add_class("metric-error")
            elif estado == "warn":
                contexto.add_class("metric-warn")
            else:
                contexto.add_class("metric-ok")

        def atualizar_metricas(self, resultado, diagnostico, config, ok):
            self.metricas["bits_aplicacao"].set_text(
                str(diagnostico["bits_aplicacao"]))
            self.metricas["bits_enlace"].set_text(str(diagnostico["bits_enlace"]))
            self.metricas["bits_adicionados"].set_text(
                str(diagnostico["bits_adicionados"]))
            self.metricas["potencia_sinal"].set_text(
                f"{resultado['potencia_sinal_w']:.4f} W")
            self.metricas["potencia_ruido"].set_text(
                f"{resultado['potencia_ruido_w']:.4f} W")
            sufixo_continuo = (
                f" | contínua #{self.contador_continuo}"
                if self.botao_continuo.get_active() else "")
            self.definir_banner(
                (
                    "texto correto"
                    if ok else "com diferenças"
                ) + f" | σ {config['ruido_sigma']:.2f} V{sufixo_continuo}",
                "ok" if ok else "warn",
            )
            self.lbl_resumo_fases.set_text(
                f"Aplicação {plural_bits(diagnostico['bits_aplicacao'])} -> "
                f"enlace {plural_bits(diagnostico['bits_enlace'])}; "
                f"EDC +{plural_bits(diagnostico['bits_edc'])}, "
                f"Hamming +{plural_bits(diagnostico['bits_correcao'])}, "
                f"enquadramento +{plural_bits(diagnostico['bits_enquadramento'])}, "
                f"padding da portadora +{plural_bits(diagnostico['padding_portadora'])}.")

        def atualizar_tabela_diagnostico(self, diagnostico):
            for labels, fase in zip(self.linhas_fases, diagnostico["fases"]):
                labels["nome"].set_text(fase["nome"])
                labels["entrada"].set_text(fase["entrada"])
                labels["saida"].set_text(fase["saida"])
                labels["delta"].set_text(fase["delta"])
                labels["detalhe"].set_text(fase["detalhe"])

                contexto = labels["delta"].get_style_context()
                contexto.remove_class("phase-zero")
                contexto.remove_class("phase-delta")
                if fase["delta"] == "0 bits":
                    contexto.add_class("phase-zero")
                else:
                    contexto.add_class("phase-delta")

        def atualizar_bits(self, resultado, diagnostico, config):
            textos = {
                "tx_app": (
                    f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
                    f"BITS DA APLICAÇÃO ({len(resultado['tx_bits_aplicacao'])} bits):\n"
                    f"{bits_str(resultado['tx_bits_aplicacao'])}"
                ),
                "tx_enlace": (
                    f"BITS NO ENLACE ({len(resultado['tx_bits_enlace'])} bits):\n"
                    f"{bits_str(resultado['tx_bits_enlace'])}"
                ),
                "rx_fisica": (
                    f"BITS DEMODULADOS ({len(resultado['rx_bits_fisica'])} bits):\n"
                    f"{bits_str(resultado['rx_bits_fisica'])}"
                ),
                "rx_app": (
                    f"BITS DA APLICAÇÃO RX ({len(resultado['rx_bits_aplicacao'])} bits):\n"
                    f"{bits_str(resultado['rx_bits_aplicacao'])}\n\n"
                    f"TEXTO RECUPERADO:\n{resultado['rx_texto']}"
                ),
                "quadros": formatar_relatorio_quadros(resultado, config),
                "fases_bits": formatar_bits_por_fase(diagnostico),
            }
            for chave, texto in textos.items():
                self.textos_bits[chave].get_buffer().set_text(texto)

        def rolar_resultados_para_topo(self):
            if self.rolagem_resultados is None:
                return False
            ajuste = self.rolagem_resultados.get_vadjustment()
            ajuste.set_value(ajuste.get_lower())
            return False

        def ler_config(self):
            return {
                "texto": self.entrada_texto.get_text(),
                "tam_max_quadro": int(self.spin_quadro.get_value()),
                "enquadramento": self.valor_combo(self.combo_enq),
                "deteccao": self.valor_combo(self.combo_det),
                "correcao": self.valor_combo(self.combo_cor),
                "mod_digital": self.valor_combo(self.combo_dig),
                "mod_portadora": self.valor_combo(self.combo_port),
                "ruido_media": self.spin_media.get_value(),
                "ruido_sigma": self.spin_sigma.get_value(),
            }

        def ao_alternar_continua(self, botao):
            if botao.get_active():
                self.contador_continuo = 0
                botao.set_label("Parar contínua")
                self.lbl_modo.set_text("Modo contínuo")
                self.ao_tick_continuo()
                intervalo = int(self.spin_intervalo.get_value())
                self.continuo_id = GLib.timeout_add(intervalo, self.ao_tick_continuo)
            else:
                botao.set_label("Iniciar contínua")
                self.lbl_modo.set_text("Modo manual")
                if self.continuo_id is not None:
                    GLib.source_remove(self.continuo_id)
                    self.continuo_id = None

        def ao_tick_continuo(self):
            if not self.botao_continuo.get_active():
                self.continuo_id = None
                return False
            self.contador_continuo += 1
            self.ao_transmitir(None)
            return self.botao_continuo.get_active()

        def ao_transmitir(self, _botao=None):
            config = self.ler_config()
            if not config["texto"]:
                self.lbl_status.set_text("Digite um texto para transmitir.")
                self.definir_banner("Digite um texto para transmitir.", "erro")
                return
            try:
                resultado = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.set_text(f"Erro: {erro}")
                self.definir_banner(f"Erro: {erro}", "erro")
                return

            self.plotar(
                self.graficos["tx_banda_base"],
                ("Sinal banda-base (Tx)", resultado["tx_sinal_banda_base"]),
            )
            self.plotar(
                self.graficos["tx_transmitido"],
                ("Sinal transmitido ao meio (Tx)",
                 resultado["tx_sinal_transmitido"]),
            )
            self.plotar(
                self.graficos["rx_recebido"],
                ("Sinal recebido com ruído (Rx)", resultado["rx_sinal_recebido"]),
            )
            self.plotar(
                self.graficos["rx_banda_base"],
                ("Banda-base reconstruída (Rx)",
                 resultado["rx_sinal_banda_base"]),
            )

            diagnostico = diagnosticar_camadas(
                resultado["tx_bits_aplicacao"], resultado, config)
            self.atualizar_tabela_diagnostico(diagnostico)
            self.atualizar_bits(resultado, diagnostico, config)

            ok = (resultado["rx_texto"] == config["texto"])
            pot_sinal = resultado["potencia_sinal_w"]
            pot_ruido = resultado["potencia_ruido_w"]
            self.atualizar_metricas(resultado, diagnostico, config, ok)
            self.lbl_status.set_text(
                f"Potência do sinal: {pot_sinal:.3f} W | do ruído: {pot_ruido:.4f} W\n"
                f"Texto recuperado {'corretamente' if ok else 'com diferenças'}.")
            if not self.botao_continuo.get_active():
                GLib.idle_add(self.rolar_resultados_para_topo)

        @staticmethod
        def plotar(grafico, *series):
            grafico.set_series(list(series))

        def executar(self):
            self.show_all()
            self.present()
            # foca o campo de texto com o cursor no fim (sem o texto inteiro
            # selecionado em azul) para uma abertura mais limpa.
            self.entrada_texto.grab_focus()
            self.entrada_texto.set_position(-1)
            # clareia a barra de título nativa após a janela existir.
            self._ajustar_janela_nativa()
            GLib.idle_add(self._ajustar_janela_nativa)
            Gtk.main()


# implementação tkinter para fallback quando gtk não está disponível
else:

    COR_FUNDO = "#111827"
    COR_PAINEL = "#1f2937"
    COR_CAMPO = "#374151"
    COR_TEXTO = "#f9fafb"
    COR_TEXTO_SECUNDARIO = "#d1d5db"
    COR_BORDA = "#4b5563"
    COR_BOTAO = "#2563eb"
    COR_BOTAO_ATIVO = "#1d4ed8"
    COR_LINHA = "#60a5fa"

    class GraficoSinalTk(tk.Canvas):
        def __init__(self, parent):
            super().__init__(parent, bg=COR_PAINEL, highlightthickness=0,
                             height=285)
            self.series = []
            self.bind("<Configure>", lambda _evento: self.redesenhar())

        def set_series(self, series):
            self.series = series
            self.redesenhar()

        def redesenhar(self):
            self.delete("all")
            largura = max(1, self.winfo_width())
            altura = max(1, self.winfo_height())
            if not self.series:
                self.create_text(16, 24, text="sem sinal para exibir",
                                 anchor="w", fill=COR_TEXTO_SECUNDARIO)
                return

            topo = 26
            margem_baixo = 22
            espaco = 22
            altura_bloco = (altura - topo - margem_baixo - espaco) / len(self.series)
            minimo, maximo = limites_series(self.series)
            faixa = maximo - minimo or 1.0

            for indice, (titulo, sinal) in enumerate(self.series):
                y0 = topo + indice * (altura_bloco + espaco)
                self.desenhar_bloco(titulo, sinal, 14, y0, largura - 28,
                                    altura_bloco, minimo, faixa)

        def desenhar_bloco(self, titulo, sinal, x, y, largura, altura,
                           minimo, faixa):
            amostras = amostrar_para_grafico(sinal)
            self.create_text(x, y - 7, text=titulo, anchor="w",
                             fill=COR_TEXTO, font=("Arial", 9, "bold"))
            for k in range(4):
                yy = y + altura * k / 3
                self.create_line(x, yy, x + largura, yy, fill=COR_BORDA)

            zero_y = y + altura - ((0 - minimo) / faixa) * altura
            if y <= zero_y <= y + altura:
                self.create_line(x, zero_y, x + largura, zero_y,
                                 fill=COR_TEXTO_SECUNDARIO)

            self.create_text(x + largura - 64, y + 10,
                             text=formatar_volts(minimo + faixa), anchor="w",
                             fill=COR_TEXTO_SECUNDARIO, font=("Arial", 8))
            self.create_text(x + largura - 64, y + altura - 4,
                             text=formatar_volts(minimo), anchor="w",
                             fill=COR_TEXTO_SECUNDARIO, font=("Arial", 8))

            if len(amostras) < 2:
                self.create_text(x + 8, y + altura / 2, text="sem amostras",
                                 anchor="w", fill=COR_TEXTO_SECUNDARIO)
                return

            pontos = []
            for idx, valor in enumerate(amostras):
                xx = x + largura * idx / (len(amostras) - 1)
                yy = y + altura - ((valor - minimo) / faixa) * altura
                pontos.extend([xx, yy])
            self.create_line(*pontos, fill=COR_LINHA, width=2)

    class JanelaSimulador(tk.Tk):
        """janela principal do simulador em tkinter."""

        def __init__(self):
            super().__init__()
            self.title("Simulador TR1 - Camadas Física e de Enlace")
            self.geometry("1200x750")
            self.protocol("WM_DELETE_WINDOW", self.destroy)
            self.configure(bg=COR_FUNDO)
            self.configurar_tema()

            raiz = tk.Frame(self, bg=COR_FUNDO, padx=8, pady=8)
            raiz.pack(fill=tk.BOTH, expand=True)

            self.montar_painel_config(raiz)
            self.montar_painel_resultados(raiz)
            self.lbl_status.config(text="Pronto. Ajuste os parâmetros e clique em Transmitir.")
            self.set_texto(self.txt_tx, "Transmissor (Tx)\n\nClique em Transmitir para gerar bits e sinais.")
            self.set_texto(self.txt_rx, "Receptor (Rx)\n\nClique em Transmitir para recuperar a mensagem.")

        # montagem da tela

        def configurar_tema(self):
            """define defaults legíveis no tk em modo escuro."""
            self.option_add("*Background", COR_PAINEL)
            self.option_add("*Foreground", COR_TEXTO)
            self.option_add("*Entry.Background", COR_CAMPO)
            self.option_add("*Text.Background", COR_CAMPO)
            self.option_add("*selectBackground", COR_BOTAO)
            self.option_add("*selectForeground", COR_TEXTO)

        def montar_painel_config(self, parent):
            frame = tk.LabelFrame(parent, text="Configuração", bg=COR_PAINEL,
                                  fg=COR_TEXTO, padx=8, pady=8,
                                  highlightbackground=COR_BORDA,
                                  highlightcolor=COR_BORDA)
            frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

            linha = 0

            def adicionar(rotulo_texto, widget):
                nonlocal linha
                tk.Label(frame, text=rotulo_texto, anchor="w", bg=COR_PAINEL,
                         fg=COR_TEXTO).grid(
                    row=linha, column=0, sticky="w", padx=2, pady=3)
                widget.grid(row=linha, column=1, sticky="we", padx=2, pady=3)
                linha += 1

            self.entrada_texto = tk.Entry(frame, width=24, bg=COR_PAINEL,
                                          fg=COR_TEXTO,
                                          insertbackground=COR_TEXTO,
                                          highlightthickness=1,
                                          highlightbackground=COR_BORDA,
                                          highlightcolor=COR_LINHA)
            self.entrada_texto.insert(0, "Ola, TR1!")
            adicionar("Texto de entrada:", self.entrada_texto)

            self.spin_quadro = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                         fg=COR_TEXTO,
                                         insertbackground=COR_TEXTO,
                                         highlightthickness=1,
                                         highlightbackground=COR_BORDA,
                                         highlightcolor=COR_LINHA)
            self.spin_quadro.delete(0, tk.END)
            self.spin_quadro.insert(0, "8")
            adicionar("Tam. máx. de quadro (bytes):", self.spin_quadro)

            self.combo_enq = self.novo_combo(frame, OPCOES_ENQUADRAMENTO, 2)
            adicionar("Enquadramento:", self.combo_enq)

            self.combo_det = self.novo_combo(frame, OPCOES_DETECCAO, 3)
            adicionar("Detecção de erros:", self.combo_det)

            self.combo_cor = self.novo_combo(frame, OPCOES_CORRECAO, 1)
            adicionar("Correção de erros:", self.combo_cor)

            self.combo_dig = self.novo_combo(frame, OPCOES_MOD_DIGITAL, 0)
            adicionar("Modulação digital:", self.combo_dig)

            self.combo_port = self.novo_combo(frame, OPCOES_MOD_PORTADORA, 3)
            adicionar("Modulação por portadora:", self.combo_port)

            self.spin_media = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                       fg=COR_TEXTO,
                                       insertbackground=COR_TEXTO,
                                       highlightthickness=1,
                                       highlightbackground=COR_BORDA,
                                       highlightcolor=COR_LINHA)
            self.spin_media.delete(0, tk.END)
            self.spin_media.insert(0, "0.00")
            adicionar("Ruído - média x (V):", self.spin_media)

            self.spin_sigma = tk.Entry(frame, width=7, bg=COR_CAMPO,
                                       fg=COR_TEXTO,
                                       insertbackground=COR_TEXTO,
                                       highlightthickness=1,
                                       highlightbackground=COR_BORDA,
                                       highlightcolor=COR_LINHA)
            self.spin_sigma.delete(0, tk.END)
            self.spin_sigma.insert(0, "0.10")
            adicionar("Ruído - desvio σ (V):", self.spin_sigma)

            tk.Button(frame, text="Transmitir", command=self.ao_transmitir,
                      bg=COR_BOTAO, fg=COR_TEXTO,
                      activebackground=COR_BOTAO_ATIVO,
                      activeforeground=COR_TEXTO,
                      relief=tk.FLAT).grid(
                row=linha, column=0, columnspan=2, sticky="we", pady=10)
            linha += 1

            self.lbl_status = tk.Label(
                frame, text="", wraplength=220, justify="left", anchor="nw",
                bg=COR_PAINEL, fg=COR_TEXTO)
            self.lbl_status.grid(row=linha, column=0, columnspan=2, sticky="w")

        def novo_combo(self, parent, opcoes, indice_padrao):
            valores = [r for r, _ in opcoes]
            var = tk.StringVar(parent)
            var.set(valores[indice_padrao])
            combo = tk.OptionMenu(parent, var, *valores)
            combo.config(width=22, anchor="w", bg=COR_CAMPO, fg=COR_TEXTO,
                         activebackground=COR_BOTAO,
                         activeforeground=COR_TEXTO,
                         highlightthickness=1,
                         highlightbackground=COR_BORDA,
                         relief=tk.FLAT)
            combo["menu"].config(bg=COR_CAMPO, fg=COR_TEXTO,
                                 activebackground=COR_BOTAO,
                                 activeforeground=COR_TEXTO)
            combo._var = var
            combo._valor_por_rotulo = {rotulo: valor for rotulo, valor in opcoes}
            return combo

        @staticmethod
        def valor_combo(combo):
            return combo._valor_por_rotulo[combo._var.get()]

        def montar_painel_resultados(self, parent):
            painel = tk.Frame(parent, bg=COR_FUNDO)
            painel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tab_tx = tk.LabelFrame(painel, text="Transmissor (Tx)",
                                   bg=COR_PAINEL, fg=COR_TEXTO, padx=6, pady=6)
            tab_tx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
            self.txt_tx, self.grafico_tx = self.criarmontar_aba(tab_tx)

            tab_rx = tk.LabelFrame(painel, text="Receptor (Rx)",
                                   bg=COR_PAINEL, fg=COR_TEXTO, padx=6, pady=6)
            tab_rx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
            self.txt_rx, self.grafico_rx = self.criarmontar_aba(tab_rx)

        def criarmontar_aba(self, parent):
            txt_frame = tk.Frame(parent, bg=COR_PAINEL)
            txt_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = tk.Scrollbar(txt_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            txt = tk.Text(txt_frame, wrap=tk.CHAR, font=("Courier", 9),
                          yscrollcommand=scrollbar.set, height=13,
                          state=tk.DISABLED, bg=COR_CAMPO, fg=COR_TEXTO,
                          insertbackground=COR_TEXTO,
                          relief=tk.SOLID, borderwidth=1)
            txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=txt.yview)

            grafico = GraficoSinalTk(parent)
            grafico.pack(fill=tk.BOTH, expand=True)

            return txt, grafico

        # lógica da simulação

        def ler_config(self):
            return {
                "texto": self.entrada_texto.get(),
                "tam_max_quadro": int(self.spin_quadro.get()),
                "enquadramento": self.valor_combo(self.combo_enq),
                "deteccao": self.valor_combo(self.combo_det),
                "correcao": self.valor_combo(self.combo_cor),
                "mod_digital": self.valor_combo(self.combo_dig),
                "mod_portadora": self.valor_combo(self.combo_port),
                "ruido_media": float(self.spin_media.get()),
                "ruido_sigma": float(self.spin_sigma.get()),
            }

        def ao_transmitir(self):
            config = self.ler_config()
            if not config["texto"]:
                self.lbl_status.config(text="Digite um texto para transmitir.")
                return
            try:
                resultado = simulador.executar_simulacao(config)
            except ValueError as erro:
                self.lbl_status.config(text=f"Erro: {erro}")
                return

            texto_tx = (
                f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(resultado['tx_bits_aplicacao'])} bits):\n"
                f"{bits_str(resultado['tx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE BITS - ENLACE/quadros ({len(resultado['tx_bits_enlace'])} bits):\n"
                f"{bits_str(resultado['tx_bits_enlace'])}\n"
            )
            self.set_texto(self.txt_tx, texto_tx)
            self.plotar(
                self.grafico_tx,
                ("Sinal banda-base (Tx)", resultado["tx_sinal_banda_base"]),
                ("Sinal transmitido ao meio (Tx)", resultado["tx_sinal_transmitido"]),
            )

            linhas_quadros = "\n".join(
                f"  Quadro {q['quadro']}: "
                f"EDC {'OK' if q['edc_ok'] else 'ERRO DETECTADO'}"
                + (f", {q['corrigidos']} bit(s) corrigido(s) por Hamming"
                   if config["correcao"] == "hamming" else "")
                + (", ERRO DUPLO detectado" if q["erro_duplo"] else "")
                for q in resultado["rx_relatorio_quadros"]) or "  (nenhum quadro recuperado)"
            texto_rx = (
                f"SAÍDA DE BITS - FÍSICA/demodulados "
                f"({len(resultado['rx_bits_fisica'])} bits):\n"
                f"{bits_str(resultado['rx_bits_fisica'])}\n\n"
                f"RELATÓRIO DOS QUADROS (enlace):\n{linhas_quadros}\n\n"
                f"SAÍDA DE BITS - APLICAÇÃO ({len(resultado['rx_bits_aplicacao'])} bits):\n"
                f"{bits_str(resultado['rx_bits_aplicacao'])}\n\n"
                f"SAÍDA DE TEXTO:\n{resultado['rx_texto']}\n"
            )
            self.set_texto(self.txt_rx, texto_rx)
            self.plotar(
                self.grafico_rx,
                ("Sinal recebido com ruído (Rx)", resultado["rx_sinal_recebido"]),
                ("Banda-base reconstruído (Rx)", resultado["rx_sinal_banda_base"]),
            )

            ok = (resultado["rx_texto"] == config["texto"])
            pot_sinal = resultado["potencia_sinal_w"]
            pot_ruido = resultado["potencia_ruido_w"]
            self.lbl_status.config(
                text=(f"Potência do sinal: {pot_sinal:.3f} W | do ruído: {pot_ruido:.4f} W\n"
                      f"Texto recuperado {'CORRETAMENTE' if ok else 'COM DIFERENÇAS'}."))

        @staticmethod
        def set_texto(widget, conteudo):
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.insert(tk.END, conteudo)
            widget.config(state=tk.DISABLED)

        @staticmethod
        def plotar(grafico, *series):
            grafico.set_series(list(series))

        def executar(self):
            self.mainloop()

"""
Simulador.py — Rotina principal. TX e RX em threads separadas.
Orquestra: enquadramento → EDC → modulação → canal → demodulação → verificação.
"""

import threading
import queue
import numpy as np

import CamadaFisica as CF
import CamadaEnlace as CE
import InterfaceGUI as GUI


# ─── Fila de comunicação entre TX e RX ────────────────────────────────────────

_fila_canal: queue.Queue = queue.Queue()


# ─── Transmissor (TX) ──────────────────────────────────────────────────────────

def transmissor(dados: bytes, config: dict,
                resultado_tx: list) -> None:
    """
    Executa em thread separada.
    Enquadra, aplica EDC, modula e coloca sinal no canal.
    Armazena (sinal_tx, quadros) em resultado_tx[0].
    """
    tamanho = config["tamanho_quad"]

    # 1. Enquadramento
    enquad = config["enquadramento"]
    if enquad == "Contagem de caracteres":
        quadros = CE.enquadrar_contagem(dados, tamanho)
        payload_bytes = b"".join(quadros)
    elif enquad == "Flags + inserção de bytes":
        quadros = CE.enquadrar_insercao_bytes(dados, tamanho)
        payload_bytes = b"".join(quadros)
    else:  # inserção de bits
        quadros_bits = CE.enquadrar_insercao_bits(dados, tamanho)
        # Serializa bits para bytes para modulação
        todos_bits = [b for q in quadros_bits for b in q]
        payload_bytes = CE._bits_para_bytes(todos_bits)
        quadros = quadros_bits  # mantém referência original

    # 2. Detecção / correção de erros
    edc = config["edc"]
    if edc == "Paridade par":
        payload_bytes = CE.paridade_par(payload_bytes)
    elif edc == "Checksum":
        payload_bytes = CE.checksum(payload_bytes)
    elif edc == "CRC-32":
        payload_bytes = CE.crc32(payload_bytes)
    else:  # Hamming
        bits = CE._bytes_para_bits(payload_bytes)
        bits_cod = CE.hamming_codificar(bits)
        payload_bytes = CE._bits_para_bytes(bits_cod)

    # 3. Modulação
    bits = CE._bytes_para_bits(payload_bytes)
    mod = config["mod_analog"]
    if mod == "ASK":
        sinal = CF.ask(bits)
    elif mod == "FSK":
        sinal = CF.fsk(bits)
    elif mod == "PSK":
        sinal = CF.psk(bits)
    elif mod == "QPSK":
        sinal = CF.qpsk(bits)
    elif mod == "16-QAM":
        sinal = CF.qam16(bits)
    else:
        # Banda-base como fallback
        mod_digital = config["mod_digital"]
        if mod_digital == "Manchester":
            sinal = CF.manchester(bits)
        elif mod_digital == "Bipolar":
            sinal = CF.bipolar(bits)
        else:
            sinal = CF.nrz_polar(bits)

    resultado_tx.append(sinal)
    _fila_canal.put((sinal, config))


# ─── Receptor (RX) ────────────────────────────────────────────────────────────

def receptor(resultado_rx: list) -> None:
    """
    Executa em thread separada.
    Recupera sinal do canal, adiciona ruído, demodula e verifica EDC.
    Armazena (sinal_canal, sinal_rx, mensagem) em resultado_rx[0].
    """
    sinal_tx, config = _fila_canal.get()

    # 4. Canal com ruído gaussiano (em V)
    sigma = config["ruido_sigma"]
    sinal_canal = CF.adicionar_ruido(sinal_tx, sigma)

    # 5. Demodulação
    mod = config["mod_analog"]
    if mod == "ASK":
        bits_rx = CF.demodular_ask(sinal_canal)
    else:
        bits_rx = CF.demodular_nrz_polar(sinal_canal)

    payload_bytes = CE._bits_para_bytes(bits_rx)

    # 6. Verificação / correção de erros
    edc = config["edc"]
    if edc == "Paridade par":
        valido = CE.verificar_paridade_par(payload_bytes)
        payload_bytes = payload_bytes[:-1]  # remove byte de paridade
    elif edc == "Checksum":
        valido = CE.verificar_checksum(payload_bytes)
        payload_bytes = payload_bytes[:-2]
    elif edc == "CRC-32":
        valido = CE.verificar_crc32(payload_bytes)
        payload_bytes = payload_bytes[:-4]
    else:  # Hamming
        bits_cod = CE._bytes_para_bits(payload_bytes)
        bits_dec, pos_erro = CE.hamming_decodificar(bits_cod)
        valido = pos_erro == 0
        payload_bytes = CE._bits_para_bytes(bits_dec)

    # 7. Desenquadramento
    enquad = config["enquadramento"]
    try:
        if enquad == "Contagem de caracteres":
            quadros = _partir_quadros_contagem(payload_bytes)
            dados_rx = CE.desenquadrar_contagem(quadros)
        elif enquad == "Flags + inserção de bytes":
            quadros = _partir_quadros_flags(payload_bytes)
            dados_rx = CE.desenquadrar_insercao_bytes(quadros)
        else:
            bits = CE._bytes_para_bits(payload_bytes)
            quadros_bits = _partir_quadros_bits(bits)
            dados_rx = CE.desenquadrar_insercao_bits(quadros_bits)
    except Exception:
        dados_rx = b""

    # Sinal RX reconstruído apenas para visualização
    bits_vis = CE._bytes_para_bits(payload_bytes)
    sinal_rx = CF.nrz_polar(bits_vis)

    mensagem_rx = dados_rx.decode("utf-8", errors="replace")
    resultado_rx.append((sinal_canal, sinal_rx, mensagem_rx, valido))


# ─── Helpers de desenquadramento ──────────────────────────────────────────────

def _partir_quadros_contagem(dados: bytes) -> list[bytes]:
    """Divide stream de bytes em quadros pela contagem."""
    quadros = []
    i = 0
    while i < len(dados):
        tamanho = dados[i]
        quadros.append(dados[i:i + tamanho])
        i += tamanho
    return quadros


def _partir_quadros_flags(dados: bytes) -> list[bytes]:
    """Divide stream em quadros delimitados por FLAG_BYTE."""
    partes = dados.split(CE.FLAG_BYTE)
    return [CE.FLAG_BYTE + p + CE.FLAG_BYTE
            for p in partes if p]


def _partir_quadros_bits(bits: list[int]) -> list[list[int]]:
    """Divide stream de bits em quadros delimitados por FLAG_BITS."""
    quadros = []
    flag = CE.FLAG_BITS
    n = len(flag)
    i = 0
    while i <= len(bits) - n:
        if bits[i:i+n] == flag:
            j = i + n
            while j <= len(bits) - n:
                if bits[j:j+n] == flag:
                    quadros.append(flag + bits[i+n:j] + flag)
                    i = j
                    break
                j += 1
        i += 1
    return quadros


# ─── Pipeline principal ───────────────────────────────────────────────────────

def transmitir(config: dict):
    """
    Chamado pela GUI. Executa TX e RX em threads e retorna os sinais.
    Retorna: (sinal_tx, sinal_canal, sinal_rx, mensagem_rx)
    """
    dados = config["mensagem"].encode("utf-8")

    resultado_tx: list = []
    resultado_rx: list = []

    t_tx = threading.Thread(target=transmissor, args=(dados, config, resultado_tx))
    t_rx = threading.Thread(target=receptor, args=(resultado_rx,))

    t_tx.start()
    t_rx.start()
    t_tx.join()
    t_rx.join()

    sinal_tx = resultado_tx[0]
    sinal_canal, sinal_rx, mensagem_rx, _ = resultado_rx[0]

    return sinal_tx, sinal_canal, sinal_rx, mensagem_rx


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    GUI.iniciar(transmitir)

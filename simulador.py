# -*- coding: utf-8 -*-
"""
SIMULADOR (rotina principal)
============================
Orquestra todas as camadas para simular uma transmissão completa

Executar `python3 simulador.py` abre a interface gráfica. A função
executar_simulacao() também pode ser usada isoladamente (ex.: testes).
"""

import threading
import queue

import camada_aplicacao
import camada_enlace
import camada_fisica
import meio_comunicacao


CONFIG_PADRAO = {
    "texto": "O hexa vem",
    "tam_max_quadro": 8,        # bytes de dados da aplicação por quadro
    "enquadramento": "bits",    # contagem | bytes | bits
    "deteccao": "crc",          # nenhum | paridade | checksum | crc
    "correcao": "hamming",      # nenhum | hamming
    "mod_digital": "nrz",       # nrz | manchester | bipolar
    "mod_portadora": "qpsk",    # nenhuma | ask | fsk | qpsk | 16qam
    "ruido_media": 0.0,         # média do ruído gaussiano, em volts
    "ruido_sigma": 0.1,         # desvio padrão do ruído, em volts
}


def _rotina_tx(config, meio, resultados):
    """THREAD TRANSMISSORA: desce a pilha de protocolos.

    Cada etapa intermediária é guardada em `resultados` para que a GUI
    possa exibir a saída de bits/sinal de cada camada (como pede o
    diagrama de interface do enunciado).
    """

    # camada de aplicação: texto -> bits
    bits_app = camada_aplicacao.texto_para_bits(config["texto"])
    resultados["tx_bits_aplicacao"] = bits_app

    # camada de enlace: edc + hamming + enquadramento
    bits_enlace = camada_enlace.transmitir(bits_app, config)
    resultados["tx_bits_enlace"] = bits_enlace

    # camada física: primeiro gera o sinal banda-base
    sinal_banda_base = camada_fisica.modular_digital(
        bits_enlace, config["mod_digital"])
    resultados["tx_sinal_banda_base"] = sinal_banda_base

    # se houver portadora, esse passa a ser o sinal enviado ao meio
    if config["mod_portadora"] != "nenhuma":
        sinal_tx = camada_fisica.modular_portadora(
            bits_enlace, config["mod_portadora"])
    else:
        sinal_tx = sinal_banda_base
    resultados["tx_sinal_transmitido"] = sinal_tx

    # entrega o sinal ao meio de comunicação pela fila
    meio.put(sinal_tx)


def _rotina_rx(config, meio, resultados):
    """THREAD RECEPTORA: sobe a pilha de protocolos (caminho inverso)."""
    
    sinal_rx = meio.get()
    resultados["rx_sinal_recebido"] = sinal_rx

    # camada física: recupera os bits do sinal recebido
    if config["mod_portadora"] != "nenhuma":
        bits_rx = camada_fisica.demodular_portadora(
            sinal_rx, config["mod_portadora"])
        
        # reconstrói o banda-base para mostrar o estágio intermediário na gui
        resultados["rx_sinal_banda_base"] = camada_fisica.modular_digital(
            bits_rx, config["mod_digital"])
        
    else:
        # sem portadora, o receptor demodula o banda-base ruidoso direto
        resultados["rx_sinal_banda_base"] = sinal_rx
        bits_rx = camada_fisica.demodular_digital(
            sinal_rx, config["mod_digital"])
    resultados["rx_bits_fisica"] = bits_rx

    # camada de enlace: desenquadra, corrige e verifica
    bits_app, relatorio = camada_enlace.receber(bits_rx, config)
    resultados["rx_bits_aplicacao"] = bits_app
    resultados["rx_relatorio_quadros"] = relatorio

    # camada de aplicação: bits -> texto
    resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)


def executar_simulacao(config):
    """Executa uma simulação completa e devolve um dicionário com todas as
    saídas intermediárias (bits e sinais de cada camada, TX e RX)."""
    
    resultados = {}
    fila_tx, fila_rx = queue.Queue(), queue.Queue()

    th_tx = threading.Thread(target=_rotina_tx, args=(config, fila_tx, resultados))
    th_rx = threading.Thread(target=_rotina_rx, args=(config, fila_rx, resultados))

    th_tx.start()
    th_rx.start()

    # canal: soma ruído ao sinal limpo e entrega ao receptor
    sinal_limpo = fila_tx.get()
    sinal_ruidoso = meio_comunicacao.transmitir(
        sinal_limpo, config["ruido_media"], config["ruido_sigma"])
    fila_rx.put(sinal_ruidoso)

    th_tx.join()
    th_rx.join()

    # métricas usadas na interface e no relatório
    p_sinal = meio_comunicacao.potencia_media(sinal_limpo)
    ruido = [r - s for r, s in zip(sinal_ruidoso, sinal_limpo)]
    p_ruido = meio_comunicacao.potencia_media(ruido)
    resultados["potencia_sinal_w"] = p_sinal
    resultados["potencia_ruido_w"] = p_ruido
    return resultados


if __name__ == "__main__":
    from interface_gui import JanelaSimulador
    JanelaSimulador().executar()

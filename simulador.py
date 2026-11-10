# -*- coding: utf-8 -*-
#Simulador

import threading
import queue

import camada_aplicacao
import camada_enlace
import camada_fisica
import meio_comunicacao


CONFIG_PADRAO = {
    "texto": "Que seu dia seja um ótimo dia!",
    "tam_max_quadro": 8,        
    "enquadramento": "bits",    
    "deteccao": "crc",          # nenhum | paridade | checksum | crc
    "correcao": "hamming",      # nenhum | hamming
    "bits_hamming": 7,          # bits de dados por bloco do Hamming (7 = (11,7))
    "mod_digital": "nrz",       # nrz | manchester | bipolar
    "mod_portadora": "8psk",    # nenhuma | ask | fsk | 8psk | 32qam
    "ruido_media": 0.0,         
    "ruido_sigma": 0.1,         
}


def _rotina_tx(config, meio, resultados):
    # aplicação: texto -> bits
    bits_app = camada_aplicacao.texto_para_bits(config["texto"])
    resultados["tx_bits_aplicacao"] = bits_app

    # enlace: quadros com EDC, Hamming e enquadramento
    bits_enlace = camada_enlace.transmitir(bits_app, config)
    resultados["tx_bits_enlace"] = bits_enlace

    # física, 1º estágio: banda-base
    sinal_banda_base = camada_fisica.modular_digital(bits_enlace, config["mod_digital"])
    resultados["tx_sinal_banda_base"] = sinal_banda_base

    # física, 2º estágio (opcional): com portadora, é ela que vai para o meio
    if config["mod_portadora"] == "nenhuma":
        sinal_tx = sinal_banda_base
    else:
        sinal_tx = camada_fisica.modular_portadora(bits_enlace, config["mod_portadora"])
    resultados["tx_sinal_transmitido"] = sinal_tx

    meio.put(sinal_tx)


def _rotina_rx(config, meio, resultados):
    sinal_rx = meio.get()               # bloqueia até o canal entregar o sinal
    if sinal_rx is None:
        return
    
    resultados["rx_sinal_recebido"] = sinal_rx

    # física: sinal -> bits
    if config["mod_portadora"] == "nenhuma":
        bits_rx = camada_fisica.demodular_digital(sinal_rx, config["mod_digital"])
        resultados["rx_sinal_banda_base"] = sinal_rx
    else:
        bits_rx = camada_fisica.demodular_portadora(sinal_rx, config["mod_portadora"])
        # Remodula os bits só para a GUI mostrar o estágio banda-base do receptor
        resultados["rx_sinal_banda_base"] = camada_fisica.modular_digital(
            bits_rx, config["mod_digital"])
    resultados["rx_bits_fisica"] = bits_rx

    # enlace: desenquadra, corrige e verifica
    bits_app, relatorio = camada_enlace.receber(bits_rx, config)
    resultados["rx_bits_aplicacao"] = bits_app
    resultados["rx_relatorio_quadros"] = relatorio

    # aplicação: bits -> texto
    resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)


def _executar_thread(rotina, config, fila, resultados, erros):
    """
    Roda a rotina guardando a exceção em `erros` (join() não a propaga).
    Se o transmissor falhar, manda None ao canal para o receptor não esperar.
    """
    try:
        rotina(config, fila, resultados)
    except Exception as erro:
        erros.append(erro)
        if rotina is _rotina_tx:
            fila.put(None)


def executar_simulacao(config):
    """
    A thread principal faz o papel do canal: pega o sinal do TX, aplica o
    ruído e entrega ao RX. Se alguma thread falhar, o erro é relançado aqui.
    """
    resultados = {}
    erros = []
    fila_tx = queue.Queue()            
    fila_rx = queue.Queue()            

    thread_tx = threading.Thread(target=_executar_thread,args=(_rotina_tx, config, fila_tx, resultados, erros))
    thread_rx = threading.Thread(target=_executar_thread,args=(_rotina_rx, config, fila_rx, resultados, erros))
    
    thread_tx.start()
    thread_rx.start()  # o RX já começa esperando o sinal

    #recebe o sinal limpo e entrega o sinal ruidoso ao RX
    sinal_limpo = fila_tx.get()
    if sinal_limpo is None:             # o TX falhou: libera o RX e segue
        fila_rx.put(None)
    else:
        sinal_ruidoso = meio_comunicacao.transmitir(sinal_limpo, config["ruido_media"], config["ruido_sigma"])
        fila_rx.put(sinal_ruidoso)

    thread_tx.join()
    thread_rx.join()

    if erros:
        raise erros[0]

    ruido = []
    for recebida, enviada in zip(sinal_ruidoso, sinal_limpo): #O zip junta duas listas posição por posição
        ruido.append(recebida - enviada)

    resultados["potencia_sinal_w"] = meio_comunicacao.potencia_media(sinal_limpo)
    resultados["potencia_ruido_w"] = meio_comunicacao.potencia_media(ruido)

    return resultados


if __name__ == "__main__":
    from interface_gui import JanelaSimulador
    JanelaSimulador().executar()

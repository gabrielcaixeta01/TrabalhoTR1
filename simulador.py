# -*- coding: utf-8 -*-
"""
SIMULADOR (rotina principal)
============================
Orquestra todas as camadas para simular uma transmissão completa,
seguindo o diagrama do enunciado:

  THREAD TX                       MEIO                    THREAD RX
  ---------                       ----                    ---------
  texto                                                       texto
    | aplicação (texto->bits)                  (bits->texto) aplicação
  bits                                                        bits
    | enlace (EDC/Hamming + enquadramento)   (inverso) enlace |
  quadros (bits)                                    quadros (bits)
    | física (banda-base -> portadora)      (demod/decod) física
  sinal (V) ----> [ + ruído gaussiano n(x, sigma) ] ----> sinal (V)

O enunciado pede "Programa/Thread TX" e "Programa/Thread RX" separados:
aqui o TX e o RX rodam em threading.Thread distintas e se comunicam
exclusivamente por uma queue.Queue, que faz o papel do meio físico.

Executar `python3 simulador.py` abre a interface gráfica. A função
executar_simulacao() também pode ser usada isoladamente (ex.: testes).
"""

import threading
import queue

import camada_aplicacao
import camada_enlace
import camada_fisica
import meio_comunicacao


# Configuração padrão (a GUI sobrescreve estes valores).
CONFIG_PADRAO = {
    "texto": "Ola, TR1!",
    "tam_max_quadro": 8,        # bytes de dados da aplicação por quadro
    "enquadramento": "bits",    # contagem | bytes | bits
    "deteccao": "crc",          # nenhum | paridade | checksum | crc
    "correcao": "hamming",      # nenhum | hamming
    "mod_digital": "nrz",       # nrz | manchester | bipolar
    "mod_portadora": "qpsk",    # nenhuma | ask | fsk | qpsk | 16qam
    "ruido_media": 0.0,         # média (x) do ruído gaussiano, em Volts
    "ruido_sigma": 0.1,         # desvio padrão (sigma) do ruído, em Volts
}


def _rotina_tx(config, meio, resultados):
    """THREAD TRANSMISSORA: desce a pilha de protocolos.

    Cada etapa intermediária é guardada em `resultados` para que a GUI
    possa exibir a saída de bits/sinal de cada camada (como pede o
    diagrama de interface do enunciado).
    """
    # --- Camada de aplicação: texto -> bits -------------------------------
    bits_app = camada_aplicacao.texto_para_bits(config["texto"])
    resultados["tx_bits_aplicacao"] = bits_app

    # --- Camada de enlace: EDC + (Hamming) + enquadramento ----------------
    bits_enlace = camada_enlace.transmitir(bits_app, config)
    resultados["tx_bits_enlace"] = bits_enlace

    # --- Camada física ------------------------------------------------------
    # 1º estágio: codificação banda-base (sempre gerada, para visualização
    # e porque é o sinal transmitido quando não há portadora).
    sinal_banda_base = camada_fisica.modular_digital(
        bits_enlace, config["mod_digital"])
    resultados["tx_sinal_banda_base"] = sinal_banda_base

    # 2º estágio: modulação por portadora (opcional). Quando habilitada,
    # é o sinal modulado que efetivamente trafega pelo meio.
    if config["mod_portadora"] != "nenhuma":
        sinal_tx = camada_fisica.modular_portadora(
            bits_enlace, config["mod_portadora"])
    else:
        sinal_tx = sinal_banda_base
    resultados["tx_sinal_transmitido"] = sinal_tx

    # Entrega o sinal ao meio de comunicação (a fila conecta as threads).
    meio.put(sinal_tx)


def _rotina_rx(config, meio, resultados):
    """THREAD RECEPTORA: sobe a pilha de protocolos (caminho inverso)."""
    # Recebe do meio o sinal JÁ RUIDOSO (o ruído é somado no canal,
    # entre as duas threads - ver executar_simulacao).
    sinal_rx = meio.get()
    resultados["rx_sinal_recebido"] = sinal_rx

    # --- Camada física: recupera os bits ----------------------------------
    if config["mod_portadora"] != "nenhuma":
        # Demodula a portadora (correlação coerente) -> bits.
        bits_rx = camada_fisica.demodular_portadora(
            sinal_rx, config["mod_portadora"])
        # Reconstrói o sinal banda-base a partir dos bits demodulados,
        # apenas para exibição do estágio intermediário na GUI.
        resultados["rx_sinal_banda_base"] = camada_fisica.modular_digital(
            bits_rx, config["mod_digital"])
    else:
        # Sem portadora: decodifica o banda-base ruidoso diretamente.
        resultados["rx_sinal_banda_base"] = sinal_rx
        bits_rx = camada_fisica.demodular_digital(
            sinal_rx, config["mod_digital"])
    resultados["rx_bits_fisica"] = bits_rx

    # --- Camada de enlace: desenquadra, corrige e verifica ----------------
    bits_app, relatorio = camada_enlace.receber(bits_rx, config)
    resultados["rx_bits_aplicacao"] = bits_app
    resultados["rx_relatorio_quadros"] = relatorio

    # --- Camada de aplicação: bits -> texto --------------------------------
    resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)


def executar_simulacao(config):
    """Executa uma simulação completa e devolve um dicionário com TODAS as
    saídas intermediárias (bits e sinais de cada camada, TX e RX).

    O meio de comunicação é modelado por duas filas:
      TX --fila_tx--> [canal: soma ruído gaussiano] --fila_rx--> RX
    """
    resultados = {}
    fila_tx, fila_rx = queue.Queue(), queue.Queue()

    th_tx = threading.Thread(target=_rotina_tx,
                             args=(config, fila_tx, resultados))
    th_rx = threading.Thread(target=_rotina_rx,
                             args=(config, fila_rx, resultados))
    th_tx.start()
    th_rx.start()

    # CANAL: pega o sinal limpo do TX, soma o ruído n(x, sigma) e entrega
    # ao RX. É o único ponto de contato entre as duas threads.
    sinal_limpo = fila_tx.get()
    sinal_ruidoso = meio_comunicacao.transmitir(
        sinal_limpo, config["ruido_media"], config["ruido_sigma"])
    fila_rx.put(sinal_ruidoso)

    th_tx.join()
    th_rx.join()

    # Métricas extras para a GUI/relatório: potências e SNR.
    p_sinal = meio_comunicacao.potencia_media(sinal_limpo)
    ruido = [r - s for r, s in zip(sinal_ruidoso, sinal_limpo)]
    p_ruido = meio_comunicacao.potencia_media(ruido)
    resultados["potencia_sinal_w"] = p_sinal
    resultados["potencia_ruido_w"] = p_ruido
    return resultados


if __name__ == "__main__":
    # A interface gráfica é importada só aqui para que os módulos das
    # camadas possam ser testados em máquinas sem GTK instalado.
    from interface_gui import JanelaSimulador
    JanelaSimulador().executar()
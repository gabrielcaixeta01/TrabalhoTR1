# -*- coding: utf-8 -*-
"""
SIMULADOR (rotina principal)
============================
Orquestra todas as camadas para simular uma transmissão completa, seguindo a
Figura 1 do enunciado ("Diagrama de desenvolvimento"):

      Programa/Thread TX                                Programa/Thread RX
  aplicação -> enlace -> física  --> MEIO (+ ruído) --> física -> enlace -> aplicação

O enunciado pede para DIFERENCIAR transmissor e receptor: cada um roda em sua
própria thread (_rotina_tx e _rotina_rx) e o único ponto de contato entre eles
é o MEIO DE COMUNICAÇÃO, ligado por filas (queue.Queue).

Executar `python3 simulador.py` abre a interface gráfica. A função
executar_simulacao() também pode ser usada sozinha (é o que testes.py faz).

Este módulo é o "colante" do projeto: ele só CHAMA funções das outras camadas,
não implementa protocolo nenhum. Por isso é a última peça a ser integrada.
"""

import threading
import queue

import camada_aplicacao
import camada_enlace
import camada_fisica
import meio_comunicacao


# Configuração padrão = o que a GUI mostra ao abrir. Chaves e valores aceitos:
CONFIG_PADRAO = {
    "texto": "Ola, TR1!",
    "tam_max_quadro": 8,        # bytes de dados da aplicação por quadro
    "enquadramento": "bits",    # contagem | entrelacamento | bytes | bits
    "deteccao": "crc",          # nenhum | paridade | checksum | crc
    "correcao": "hamming",      # nenhum | hamming
    "mod_digital": "nrz",       # nrz | manchester | bipolar
    "mod_portadora": "8psk",    # nenhuma | ask | fsk | 8psk | 32qam
    "ruido_media": 0.0,         # média (x) do ruído gaussiano, em Volts
    "ruido_sigma": 0.1,         # desvio padrão (sigma) do ruído, em Volts
}


def _rotina_tx(config, meio, resultados):
    """THREAD TRANSMISSORA: desce a pilha de protocolos.

    ENTRADA
        config     : dict como CONFIG_PADRAO
        meio       : queue.Queue por onde o sinal sai (meio.put(sinal))
        resultados : dict compartilhado; guardamos cada etapa intermediária
                     para a GUI exibir a "saída de bits/sinal" de cada
                     camada, como no diagrama do enunciado.

    PASSOS (e as chaves de `resultados` que cada um deve preencher)
        1. APLICAÇÃO : texto_para_bits(config["texto"])
                       -> resultados["tx_bits_aplicacao"]
        2. ENLACE    : camada_enlace.transmitir(bits_app, config)
                       -> resultados["tx_bits_enlace"]
        3. FÍSICA, 1º estágio (banda-base): modular_digital(bits_enlace,
                       config["mod_digital"])
                       -> resultados["tx_sinal_banda_base"]
        4. FÍSICA, 2º estágio (portadora, opcional): se mod_portadora != "nenhuma"
                       o sinal que trafega é modular_portadora(bits_enlace, tipo);
                       senão é o próprio banda-base.
                       -> resultados["tx_sinal_transmitido"]
        5. Entregue o sinal ao meio:  meio.put(sinal_tx)
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("simulador._rotina_tx")


def _rotina_rx(config, meio, resultados):
    """THREAD RECEPTORA: sobe a pilha de protocolos (caminho inverso).

    PASSOS (chaves de `resultados` a preencher)
        1. sinal_rx = meio.get()  (BLOQUEIA até o canal entregar o sinal)
                       -> resultados["rx_sinal_recebido"]
        2. FÍSICA:
           - com portadora: demodular_portadora(sinal_rx, tipo) -> bits_rx.
             Para exibir o estágio banda-base na GUI, remodule bits_rx com
             modular_digital -> resultados["rx_sinal_banda_base"].
           - sem portadora: demodular_digital(sinal_rx, mod_digital) -> bits_rx
             e resultados["rx_sinal_banda_base"] = sinal_rx.
           -> resultados["rx_bits_fisica"] = bits_rx
        3. ENLACE    : camada_enlace.receber(bits_rx, config)
                       -> resultados["rx_bits_aplicacao"], ["rx_relatorio_quadros"]
        4. APLICAÇÃO : bits_para_texto(bits_app) -> resultados["rx_texto"]
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("simulador._rotina_rx")


def executar_simulacao(config):
    """Executa uma simulação completa e devolve o dict `resultados` com todas
    as saídas intermediárias (bits e sinais de cada camada, TX e RX).

    COMO FAZER
        1. Crie `resultados = {}` e duas filas: fila_tx (TX -> canal) e
           fila_rx (canal -> RX), ambas queue.Queue().
        2. Crie as duas threads (threading.Thread(target=..., args=(config,
           fila, resultados))) e inicie ambas com .start(). O RX começa
           bloqueado esperando o sinal.
        3. FAÇA O PAPEL DO CANAL na thread principal:
               sinal_limpo    = fila_tx.get()
               sinal_ruidoso  = meio_comunicacao.transmitir(sinal_limpo,
                                    config["ruido_media"], config["ruido_sigma"])
               fila_rx.put(sinal_ruidoso)
        4. Aguarde o fim das threads com .join().
        5. Métricas para a GUI: ruido = sinal_ruidoso - sinal_limpo (amostra a
           amostra); calcule potencia_media do sinal e do ruído e guarde em
           resultados["potencia_sinal_w"] e resultados["potencia_ruido_w"].
        6. Devolva resultados.

    ARMADILHA: se uma thread levantar exceção (ex.: ValueError do enlace), o
    join() não propaga o erro e a GUI ficaria esperando para sempre. Pense em
    como capturar a exceção na thread e relançá-la na principal.
    """
    # TODO: implementar conforme os passos acima.
    raise NotImplementedError("simulador.executar_simulacao")


if __name__ == "__main__":
    from interface_gui import JanelaSimulador
    JanelaSimulador().executar()

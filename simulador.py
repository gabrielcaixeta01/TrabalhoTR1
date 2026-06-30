"""
rotina principal do simulador.

`executar_simulacao` monta o caminho tx -> meio -> rx e devolve os sinais,
bits e métricas usados pela interface e pelos testes.
"""

import threading
import queue

import camada_aplicacao
import camada_enlace
import camada_fisica
import meio_comunicacao


CONFIG_PADRAO = {
    "texto": "O Hexa vem!",
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
    """desce a pilha de protocolos no transmissor."""

    # aplicação: texto vira bits puros, antes de qualquer quadro ou sinal.
    bits_app = camada_aplicacao.texto_para_bits(config["texto"])
    resultados["tx_bits_aplicacao"] = bits_app

    # enlace: quebra em quadros, coloca edc, hamming e enquadramento.
    bits_enlace = camada_enlace.transmitir(bits_app, config)
    resultados["tx_bits_enlace"] = bits_enlace

    # física banda-base: transforma os bits de enlace em amostras de tensão.
    sinal_banda_base = camada_fisica.modular_digital(
        bits_enlace, config["mod_digital"])
    resultados["tx_sinal_banda_base"] = sinal_banda_base

    # se tiver portadora, o sinal transmitido é a modulação ask/fsk/qpsk/qam.
    # se não tiver, manda direto o sinal banda-base.
    if config["mod_portadora"] != "nenhuma":
        sinal_tx = camada_fisica.modular_portadora(
            bits_enlace, config["mod_portadora"])
    else:
        sinal_tx = sinal_banda_base
    resultados["tx_sinal_transmitido"] = sinal_tx

    # coloca o sinal pronto na fila que representa a saída do transmissor.
    meio.put(sinal_tx)


def _rotina_rx(config, meio, resultados):
    """sobe a pilha de protocolos no receptor."""
    # recebe da fila o sinal que já passou pelo meio ruidoso.
    sinal_rx = meio.get()
    resultados["rx_sinal_recebido"] = sinal_rx

    # se foi usado portadora, demodula a portadora direto para bits.
    # depois gera uma versão banda-base só para visualização na interface.
    if config["mod_portadora"] != "nenhuma":
        bits_rx = camada_fisica.demodular_portadora(
            sinal_rx, config["mod_portadora"])
        resultados["rx_sinal_banda_base"] = camada_fisica.modular_digital(
            bits_rx, config["mod_digital"])
    else:
        # sem portadora, o proprio sinal recebido é o banda-base.
        resultados["rx_sinal_banda_base"] = sinal_rx
        bits_rx = camada_fisica.demodular_digital(
            sinal_rx, config["mod_digital"])
    resultados["rx_bits_fisica"] = bits_rx

    # enlace receptor: desenquadra, corrige/verifica erro e devolve bits de app.
    bits_app, relatorio = camada_enlace.receber(bits_rx, config)
    resultados["rx_bits_aplicacao"] = bits_app
    resultados["rx_relatorio_quadros"] = relatorio

    # aplicação receptor: remonta bytes e decodifica como utf-8.
    resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)


def executar_simulacao(config):
    """executa uma transmissão completa e retorna os dados intermediários."""
    resultados = {}
    # fila_tx leva tx -> meio. fila_rx leva meio -> rx.
    # elas deixam o codigo parecendo uma comunicação entre blocos separados.
    fila_tx, fila_rx = queue.Queue(), queue.Queue()

    th_tx = threading.Thread(target=_rotina_tx, args=(config, fila_tx, resultados))
    th_rx = threading.Thread(target=_rotina_rx, args=(config, fila_rx, resultados))

    # inicia transmissor e receptor. o receptor fica esperando algo na fila_rx.
    th_tx.start()
    th_rx.start()

    # o simulador pega o sinal limpo que saiu do tx, passa pelo meio,
    # e entrega o sinal ruidoso para o rx.
    sinal_limpo = fila_tx.get()
    sinal_ruidoso = meio_comunicacao.transmitir(
        sinal_limpo, config["ruido_media"], config["ruido_sigma"])
    fila_rx.put(sinal_ruidoso)

    # espera as duas rotinas terminarem antes de calcular métricas.
    th_tx.join()
    th_rx.join()

    # calcula potência do sinal e do ruido separado.
    # ruido = sinal recebido - sinal limpo, amostra por amostra.
    p_sinal = meio_comunicacao.potencia_media(sinal_limpo)
    ruido = [r - s for r, s in zip(sinal_ruidoso, sinal_limpo)]
    p_ruido = meio_comunicacao.potencia_media(ruido)
    resultados["potencia_sinal_w"] = p_sinal
    resultados["potencia_ruido_w"] = p_ruido
    return resultados


if __name__ == "__main__":
    from interface_gui import JanelaSimulador
    JanelaSimulador().executar()

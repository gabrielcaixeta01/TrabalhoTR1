"""API em snake_case para as modulações da camada física."""

from __future__ import annotations

import CamadaFisica as _legacy


SAMPLE_RATE = _legacy.SAMPLE_RATE
CARRIER_FREQ = _legacy.CARRIER_FREQ


def transmitir_ruido(sinal, desvio: float):
    return _legacy.adicionar_ruido(sinal, desvio)


def modular_nrz_polar(bits, amplitude: float = 1.0):
    return _legacy.nrz_polar(bits, amplitude)


def modular_manchester(bits, amplitude: float = 1.0):
    return _legacy.manchester(bits, amplitude)


def modular_bipolar(bits, amplitude: float = 1.0):
    return _legacy.bipolar(bits, amplitude)


def modular_ask(bits, amplitude: float = 1.0):
    return _legacy.ask(bits, amplitude)


def modular_fsk(bits, amplitude: float = 1.0, freq0: float = 5.0, freq1: float = 15.0):
    return _legacy.fsk(bits, amplitude, freq0, freq1)


def modular_psk(bits, amplitude: float = 1.0):
    return _legacy.psk(bits, amplitude)


def modular_qpsk(bits, amplitude: float = 1.0):
    return _legacy.qpsk(bits, amplitude)


def modular_16qam(bits, amplitude: float = 1.0):
    return _legacy.qam16(bits, amplitude)


def demodular_nrz_polar(sinal):
    return _legacy.demodular_nrz_polar(sinal)


def demodular_manchester(sinal):
    return _legacy.demodular_manchester(sinal)


def demodular_bipolar(sinal):
    return _legacy.demodular_bipolar(sinal)


def demodular_ask(sinal):
    return _legacy.demodular_ask(sinal)


def demodular_fsk(sinal, amplitude: float = 1.0, freq0: float = 5.0, freq1: float = 15.0):
    return _legacy.demodular_fsk(sinal, amplitude, freq0, freq1)


def demodular_psk(sinal):
    return _legacy.demodular_psk(sinal)


def demodular_qpsk(sinal):
    return _legacy.demodular_qpsk(sinal)


def demodular_16qam(sinal, amplitude: float = 1.0):
    return _legacy.demodular_qam16(sinal, amplitude)
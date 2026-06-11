"""Canal de comunicação com ruído gaussiano."""

from __future__ import annotations

import numpy as np

import camada_fisica as CF


def transmitir(sinal, media: float = 0.0, sigma: float = 0.0):
    """Soma ruído gaussiano ao sinal e aplica um offset opcional."""
    sinal_array = np.asarray(sinal, dtype=float)
    if media:
        sinal_array = sinal_array + media
    return CF.transmitir_ruido(sinal_array, sigma)
"""
CamadaFisica.py — Modulações digitais (banda-base) e analógicas (portadora).
Sinais representados em Volts. Ruído gaussiano somado ao canal.
"""

import numpy as np


# ─── Parâmetros globais ────────────────────────────────────────────────────────

SAMPLE_RATE = 1000  # amostras por bit
CARRIER_FREQ = 10   # Hz — frequência da portadora


# ─── Canal com ruído gaussiano ─────────────────────────────────────────────────

def adicionar_ruido(sinal: np.ndarray, desvio: float) -> np.ndarray:
    """Soma ruído gaussiano n(0, desvio) ao sinal em V."""
    ruido = np.random.normal(0, desvio, len(sinal))
    return sinal + ruido


# ─── Banda-base ────────────────────────────────────────────────────────────────

def nrz_polar(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """NRZ-Polar: bit 1 → +A V, bit 0 → -A V."""
    sinal = []
    for bit in bits:
        valor = amplitude if bit == 1 else -amplitude
        sinal.extend([valor] * SAMPLE_RATE)
    return np.array(sinal)


def manchester(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """Manchester: bit 1 → transição -A→+A, bit 0 → transição +A→-A."""
    sinal = []
    metade = SAMPLE_RATE // 2
    for bit in bits:
        if bit == 1:
            sinal.extend([-amplitude] * metade + [amplitude] * metade)
        else:
            sinal.extend([amplitude] * metade + [-amplitude] * metade)
    return np.array(sinal)


def bipolar(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """Bipolar (AMI): bit 0 → 0 V, bit 1 → alterna +A/-A V."""
    sinal = []
    polaridade = 1
    for bit in bits:
        if bit == 0:
            sinal.extend([0.0] * SAMPLE_RATE)
        else:
            sinal.extend([polaridade * amplitude] * SAMPLE_RATE)
            polaridade *= -1
    return np.array(sinal)


# ─── Por portadora ─────────────────────────────────────────────────────────────

def _portadora(n_amostras: int) -> np.ndarray:
    """Gera vetor de tempo para a portadora."""
    t = np.linspace(0, n_amostras / SAMPLE_RATE, n_amostras, endpoint=False)
    return 2 * np.pi * CARRIER_FREQ * t


def ask(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """ASK: bit 1 → A·cos(2πft), bit 0 → 0 V."""
    sinal = []
    for bit in bits:
        t = _portadora(SAMPLE_RATE)
        amp = amplitude if bit == 1 else 0.0
        sinal.extend(amp * np.cos(t))
    return np.array(sinal)


def fsk(bits: list[int], amplitude: float = 1.0,
        freq0: float = 5.0, freq1: float = 15.0) -> np.ndarray:
    """FSK: bit 1 → freq1, bit 0 → freq0."""
    sinal = []
    for bit in bits:
        freq = freq1 if bit == 1 else freq0
        t = np.linspace(0, 1 / SAMPLE_RATE * SAMPLE_RATE,
                        SAMPLE_RATE, endpoint=False)
        sinal.extend(amplitude * np.cos(2 * np.pi * freq * t))
    return np.array(sinal)


def psk(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """BPSK: bit 1 → fase 0, bit 0 → fase π."""
    sinal = []
    for bit in bits:
        t = _portadora(SAMPLE_RATE)
        fase = 0 if bit == 1 else np.pi
        sinal.extend(amplitude * np.cos(t + fase))
    return np.array(sinal)


def qpsk(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """QPSK: pares de bits → 4 fases (0, π/2, π, 3π/2)."""
    fases = {(1, 1): 0, (1, 0): np.pi / 2,
             (0, 0): np.pi, (0, 1): 3 * np.pi / 2}
    sinal = []
    # Garante número par de bits
    if len(bits) % 2:
        bits = bits + [0]
    for i in range(0, len(bits), 2):
        par = (bits[i], bits[i + 1])
        t = _portadora(SAMPLE_RATE)
        sinal.extend(amplitude * np.cos(t + fases[par]))
    return np.array(sinal)


def qam16(bits: list[int], amplitude: float = 1.0) -> np.ndarray:
    """16-QAM: grupos de 4 bits → constelação 4x4."""
    # Mapeamento Gray para coordenadas I/Q
    mapa = {
        (0,0,0,0): (-3,-3), (0,0,0,1): (-3,-1), (0,0,1,1): (-3,1), (0,0,1,0): (-3,3),
        (0,1,0,0): (-1,-3), (0,1,0,1): (-1,-1), (0,1,1,1): (-1,1), (0,1,1,0): (-1,3),
        (1,1,0,0): ( 1,-3), (1,1,0,1): ( 1,-1), (1,1,1,1): ( 1,1), (1,1,1,0): ( 1,3),
        (1,0,0,0): ( 3,-3), (1,0,0,1): ( 3,-1), (1,0,1,1): ( 3,1), (1,0,1,0): ( 3,3),
    }
    # Completa bits para múltiplo de 4
    while len(bits) % 4:
        bits = bits + [0]
    sinal = []
    norm = amplitude / 3.0  # normaliza para amplitude máxima
    for i in range(0, len(bits), 4):
        grupo = tuple(bits[i:i+4])
        I, Q = mapa[grupo]
        t = _portadora(SAMPLE_RATE)
        componente = norm * (I * np.cos(t) - Q * np.sin(t))
        sinal.extend(componente)
    return np.array(sinal)


# ─── Demodulação (receptor) ────────────────────────────────────────────────────

def demodular_nrz_polar(sinal: np.ndarray) -> list[int]:
    """Decisor por limiar 0 V."""
    bits = []
    for i in range(0, len(sinal), SAMPLE_RATE):
        media = np.mean(sinal[i:i + SAMPLE_RATE])
        bits.append(1 if media >= 0 else 0)
    return bits


def demodular_ask(sinal: np.ndarray) -> list[int]:
    """Envelope detector simplificado."""
    bits = []
    for i in range(0, len(sinal), SAMPLE_RATE):
        energia = np.mean(np.abs(sinal[i:i + SAMPLE_RATE]))
        bits.append(1 if energia > 0.25 else 0)
    return bits

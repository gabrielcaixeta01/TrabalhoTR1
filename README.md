# Simulador TR1 — Camadas Física e de Enlace

Simulador em Python 3 com interface gráfica GTK 3. Um chat de texto é transmitido por um canal ruidoso
(ruído gaussiano em Volts) entre um transmissor (thread TX) e um receptor (thread RX).

**Integrantes:** Gabriel Caixeta Romero · Henrique Martins Fortes · Pedro Henrique Mantovani Conti

## Funcionalidades

| Camada | Implementado |
|---|---|
| Aplicação | texto ↔ bits (UTF-8) |
| Enlace — enquadramento | contagem de caracteres, entrelaçamento de bits, byte stuffing, bit stuffing |
| Enlace — detecção | paridade par, checksum, CRC-32 |
| Enlace — correção | código de Hamming (m configurável; padrão (11,7)) |
| Física — banda-base | NRZ-Polar, Manchester, Bipolar |
| Física — portadora | ASK, FSK, 8PSK, 32-QAM |
| Meio | sinal em Volts + ruído gaussiano n(média, σ) |

Nenhum protocolo vem de biblioteca externa: CRC, Hamming, checksum e modulações são implementados à mão.

## Estrutura

```
simulador.py          # ponto de entrada: threads TX → meio → RX
camada_aplicacao.py   # texto ↔ bits
camada_enlace.py      # enquadramento, detecção e correção de erros
camada_fisica.py      # modulação banda-base e por portadora
meio_comunicacao.py   # canal com ruído gaussiano
interface_gui.py      # interface GTK 3 + gráficos matplotlib
testes.py             # testes de ida e volta (sem GTK)
requirements.txt      # dependências Python (matplotlib)
```

## Instalação e execução

```bash
# Linux (Debian/Ubuntu): dependências do GTK
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Ambiente virtual (--system-site-packages para enxergar o GTK)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt

python3 simulador.py  # abre a interface gráfica
python3 testes.py     # roda os testes (não precisa de GTK)
```

## Fluxo

```
TX:  texto → bits → [EDC → Hamming] → enquadramento → banda-base → portadora → sinal (V)
                             ↓ fila_tx ↓
MEIO:                 sinal + ruído n(x, σ)
                             ↓ fila_rx ↓
RX:  sinal → demodulação → desenquadramento → [Hamming → EDC] → bits → texto
```

## Convenções

- Bits: `list[int]` com 0/1, MSB primeiro. Sinal: `list[float]` em Volts.
- Configuração da simulação (`simulador.CONFIG_PADRAO`): `texto`, `tam_max_quadro`, `enquadramento`
  (`contagem` · `entrelacamento` · `bytes` · `bits`), `deteccao` (`nenhum` · `paridade` · `checksum` · `crc`),
  `correcao` (`nenhum` · `hamming`), `bits_hamming`, `mod_digital` (`nrz` · `manchester` · `bipolar`),
  `mod_portadora` (`nenhuma` · `ask` · `fsk` · `8psk` · `32qam`), `ruido_media`, `ruido_sigma`.

# Simulador TR1 — Camadas Física e de Enlace (UnB)

Trabalho final de **Teleinformática e Redes 1** (prof. Marcelo Antonio Marotta): simulador das camadas
física e de enlace, em Python 3 com interface gráfica GTK 3. Um chat de texto é transmitido por um
canal ruidoso (ruído gaussiano em Volts) entre um transmissor (thread TX) e um receptor (thread RX).

**Integrantes:** Gabriel Caixeta Romero · Henrique Martins Fortes · Pedro Henrique Mantovani Conti

> **Estado do repositório:** este é o **esqueleto** do trabalho. A estrutura, as assinaturas, a GUI e os
> testes estão prontos; o corpo dos protocolos está como `TODO`, com docstrings explicando objetivo,
> passos, fórmulas e dicas. Ordem de implementação e checklist: [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md).

**Restrição do enunciado:** nenhum protocolo (CRC, Hamming, checksum, modulações) pode vir de biblioteca
externa — tudo é implementado à mão (ex.: proibido `zlib` para o CRC). Só é permitido o `random` padrão
para gerar o ruído.

---

## 1. O que precisa ser implementado

| Camada | Itens exigidos |
|---|---|
| Meio de comunicação | sinal em Volts + ruído AWGN n(x, σ) configurável |
| Física (banda-base) | NRZ-Polar, Manchester, Bipolar |
| Física (portadora) | ASK, FSK, **8PSK**, **32-QAM** |
| Enlace — enquadramento | contagem de caracteres, **entrelaçamento de bits**, byte stuffing, bit stuffing |
| Enlace — detecção | bit de paridade par, checksum, CRC-32 (IEEE 802) |
| Enlace — correção | código de Hamming (11,7) |
| Aplicação | chat: texto → bits (Tx) e bits → texto (Rx) |
| Interface | GUI em GTK com configuração geral e saídas de Tx e Rx |

---

## 2. Estrutura de arquivos

```
TrabalhoTR1/
├── simulador.py          # Ponto de entrada: threads TX → meio → RX
├── camada_aplicacao.py   # Texto ↔ bits (UTF-8)
├── camada_enlace.py      # Enquadramento, detecção e correção de erros
├── camada_fisica.py      # Modulação banda-base e por portadora
├── meio_comunicacao.py   # Canal: sinal em Volts + ruído gaussiano
├── interface_gui.py      # GUI GTK 3 + gráficos matplotlib (pronta)
├── testes.py             # Testes de ida e volta (sem GTK)
├── CLAUDE.md             # Contexto do projeto para o Claude Code
├── requirements.txt      # Dependências Python (matplotlib)
├── docs/
│   ├── DESENVOLVIMENTO.md  # O que implementar, em ordem, e checklist do enunciado
│   ├── DECISOES.md         # Decisões de projeto e justificativas (insumo do relatório)
│   ├── enunciado/          # PDF do professor
│   └── referencias/        # Resumos dos slides (NotebookLM) com slide de origem
└── estudos/              # Material de estudo teórico por camada (+ código de referência)
```

Mapeamento com a Figura 1 do enunciado: `CamadaFisica` = `camada_fisica.py`, `CamadaEnlace` =
`camada_enlace.py`, `InterfaceGUI` = `interface_gui.py`, `Simulador` = `simulador.py`.

---

## 3. Instalação e execução

```bash
# Linux (Debian/Ubuntu) — dependências do GTK
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
# Fedora/RHEL: sudo dnf install python3-gobject python3-cairo gobject-introspection

# Ambiente virtual (precisa de --system-site-packages para enxergar o GTK)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt   # matplotlib

python3 testes.py     # roda os testes (não precisa de GTK)
python3 simulador.py  # abre a interface gráfica
```

---

## 4. Convenções de dados (valem para todos os módulos)

| Dado | Representação |
|---|---|
| Bits | `list[int]` com valores 0/1, **MSB primeiro** |
| Sinal | `list[float]` em **Volts** |
| Texto | UTF-8 → bits via `camada_aplicacao` |
| Quadro/payload | lista de bits alinhada em bytes |

Constantes globais da física (em `camada_fisica.py`): `V = 1.0` (amplitude de referência),
`AMOSTRAS_POR_BIT = 100`, `AMOSTRAS_POR_SIMBOLO = 100`, `CICLOS_PORTADORA = 4`, `CICLOS_FSK = (2, 4)`.

Configuração da simulação (`simulador.CONFIG_PADRAO`):

| Chave | Valores |
|---|---|
| `texto` | string digitada |
| `tam_max_quadro` | bytes de dados por quadro |
| `enquadramento` | `contagem` · `entrelacamento` · `bytes` · `bits` |
| `deteccao` | `nenhum` · `paridade` · `checksum` · `crc` |
| `correcao` | `nenhum` · `hamming` |
| `mod_digital` | `nrz` · `manchester` · `bipolar` |
| `mod_portadora` | `nenhuma` · `ask` · `fsk` · `8psk` · `32qam` |
| `ruido_media`, `ruido_sigma` | Volts |

---

## 5. Fluxo completo

```
TX:  texto → bits → [EDC → Hamming] → enquadramento → banda-base → portadora → sinal (V)
                             ↓ fila_tx ↓
MEIO:                 sinal + ruído n(x, σ)
                             ↓ fila_rx ↓
RX:  sinal → demodulação → desenquadramento → [Hamming → EDC] → bits → texto
```

Ordem no TX: o EDC é calculado sobre os dados e o Hamming protege dados **+ EDC**; só depois os blocos
são enquadrados. O RX desfaz exatamente na ordem inversa.

---

## 6. Testes

```bash
python3 testes.py
```

Cada teste imprime `[PASS]`, `[FAIL]` (bug) ou `[TODO]` (função ainda não implementada). Cobertura: meio,
aplicação, 4 enquadramentos (e casos críticos de stuffing e padding), 3 EDCs (e CRC com rajada de 32 bits), Hamming (sem erro, 1 erro em cada posição), constelações, todas as modulações com e sem
ruído e a simulação completa (4 enquadramentos × 5 opções de portadora). Meta: **zero `TODO` e zero `FAIL`**.

---

## 7. Problemas comuns

| Erro | Causa | Solução |
|---|---|---|
| `No module named 'gi'` | PyGObject não instalado | `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0` |
| `No module named 'matplotlib'` | matplotlib não instalado | `pip install matplotlib` |
| `NotImplementedError` ao abrir a GUI | protocolos ainda não implementados | normal no esqueleto; implemente as funções |
| `ValueError: Quadro final excede 255 bytes` | contagem de caracteres com quadro grande | reduzir o tamanho máximo de quadro |
| `Gtk-WARNING: cannot open display` | sem display gráfico (SSH) | `ssh -X ...` ou rodar só `python3 testes.py` |

---

## 8. Material de estudo

A pasta [estudos/](estudos/) traz a teoria por camada (com a seção "pontos que o professor gosta de
cobrar" no fim de cada arquivo): `01` portadora · `02` enquadramento · `03` detecção · `04` correção ·
`05` pipeline e meio. Os trechos de código ali são exemplos de estudo; a implementação final é do grupo.

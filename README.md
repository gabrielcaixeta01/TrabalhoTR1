# Simulador TR1 — Camadas Física e de Enlace (UnB)

Simulador educacional das camadas física e de enlace de uma rede de computadores, implementado em Python 3 com interface gráfica GTK 3. Simula a transmissão completa de texto entre um transmissor (Thread TX) e um receptor (Thread RX) por um canal ruidoso (ruído gaussiano AWGN em Volts).

**Restrição importante:** nenhum algoritmo central (CRC, Hamming, checksum, modulações) usa biblioteca externa — tudo foi implementado manualmente, bit a bit.

**Integrantes:** Gabriel Caixeta Romero, Gustavo Henrique Andrade Cavalcanti, Fernando Augusto Hortencio.

---

## 1. Estrutura de arquivos

```
TrabalhoTR1/
├── simulador.py              # Ponto de entrada: orquestra TX → meio → RX (threads)
├── camada_aplicacao.py       # Texto ↔ bits (UTF-8)
├── camada_enlace.py          # Enquadramento, detecção e correção de erros
├── camada_fisica.py          # Modulação digital (banda-base) e por portadora
├── meio_comunicacao.py       # Canal: sinal em Volts + ruído gaussiano n(x, σ)
├── interface_gui.py          # GUI GTK 3 com gráficos matplotlib embutidos
├── testes.py                 # Suite de testes de ida-e-volta (roda sem GTK)
├── gerar_imagens_relatorio.py  # Gera os gráficos do relatório
├── main.tex                  # Relatório LaTeX
└── estudos/                  # Material de estudo por módulo
```

---

## 2. Instalação e execução

### Dependências do sistema (GTK — Linux)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

> Em Fedora/RHEL: `sudo dnf install python3-gobject python3-cairo gobject-introspection`

### Dependências Python

```bash
# Com ambiente virtual (recomendado — precisa de --system-site-packages para o GTK)
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install matplotlib

# Ou diretamente, sem ambiente virtual
pip install matplotlib
```

### Executar

```bash
python3 simulador.py    # abre a interface gráfica GTK
python3 testes.py       # roda os testes sem precisar de GTK
```

---

## 3. Dependências

| Dependência | Uso | Como instalar |
|---|---|---|
| `PyGObject` (gi) | Interface gráfica GTK 3 | `apt install python3-gi ...` |
| `matplotlib` | Gráficos dos sinais na GUI | `pip install matplotlib` (única dep. pip) |
| `math`, `random`, `threading`, `queue` | Modulações, ruído, threads | stdlib Python |

> **Numpy não é necessário.** Nenhum arquivo importa numpy.

---

## 4. Convenções de dados

| Dado | Representação |
|---|---|
| Bits | `list[int]` com valores 0/1 |
| Sinal | `list[float]` em **Volts** |
| Texto | UTF-8 → bits via `camada_aplicacao` |

Constantes globais (em `camada_fisica.py`):
- `V = 1.0` — amplitude de referência (V)
- `AMOSTRAS_POR_BIT = 100`, `AMOSTRAS_POR_SIMBOLO = 100`
- `CICLOS_PORTADORA = 4`, `CICLOS_FSK = (2, 4)`

---

## 5. Módulos

### `camada_aplicacao.py`
| Função | O que faz |
|---|---|
| `texto_para_bits(texto)` | UTF-8 → lista de bits (MSB primeiro) |
| `bits_para_texto(bits)` | Inverso; usa `errors="replace"` para bits corrompidos |

### `camada_enlace.py`

**Enquadramento** — cada TX recebe lista de payloads (bits alinhados em bytes) e devolve o fluxo de bits; RX faz o inverso:
| TX | RX |
|---|---|
| `enquadrar_contagem(payloads)` | `desenquadrar_contagem(bits)` |
| `enquadrar_bytes(payloads)` — FLAG `0x7E` + byte stuffing com ESC `0x7D` | `desenquadrar_bytes(bits)` |
| `enquadrar_bits(payloads)` — FLAG `01111110` + bit stuffing (após cinco 1s, insere 0) | `desenquadrar_bits(bits)` |

**Detecção de erros:**
| TX | RX |
|---|---|
| `adicionar_paridade_par(bits)` | `verificar_paridade_par(bits) → (payload, ok)` |
| `adicionar_checksum(bits)` — complemento de 1, 16 bits | `verificar_checksum(bits) → (payload, ok)` |
| `adicionar_crc32(bits)` — polinômio IEEE 802, sem zlib | `verificar_crc32(bits) → (payload, ok)` |

**Correção de erros** — Hamming(8,4) SECDED (4 bits → 8 bits):
| TX | RX |
|---|---|
| `codificar_hamming(bits)` | `decodificar_hamming(bits) → (dados, n_corrigidos, erro_duplo)` |

### `camada_fisica.py`

**Banda-base:**
| Modulação | Regra |
|---|---|
| `modular_nrz_polar` | 1 → +V, 0 → −V |
| `modular_manchester` | Convenção Tanenbaum: 1 → alto→baixo, 0 → baixo→alto no meio do bit |
| `modular_bipolar` | 0 → 0 V; 1 → alterna +V/−V (AMI) |

**Portadora** (representação I/Q: `s(t) = I·cos − Q·sen`):
| Modulação | Bits/símbolo | Parâmetro variado |
|---|---|---|
| `modular_ask` | 1 | Amplitude (on-off keying) |
| `modular_fsk` | 1 | Frequência (2 ou 4 ciclos/símbolo) |
| `modular_qpsk` | 2 | Fase — 4 pontos com mapeamento Gray |
| `modular_16qam` | 4 | Amplitude + fase — grade 4×4, Gray nos dois eixos |

Demodulação por correlação coerente + decisão de mínima distância na constelação.

### `meio_comunicacao.py`
| Função | O que faz |
|---|---|
| `transmitir(sinal, media, sigma)` | Soma ruído gaussiano `N(media, sigma)` amostra a amostra |
| `potencia_media(sinal)` | Retorna `P = média(v²)` em Watts (carga 1 Ω) |

### `simulador.py`
Conecta tudo em duas threads com filas `queue.Queue`:
```
TX:  texto → bits → [EDC + Hamming] → enquadramento → banda-base → portadora → sinal (V)
                          ↓ fila_tx ↓
MEIO: sinal + ruído N(x, σ)
                          ↓ fila_rx ↓
RX:  sinal → demodulação → desenquadramento → [Hamming + EDC] → bits → texto
```

---

## 6. Testes

```bash
python3 testes.py
```

Cobertura: aplicação (UTF-8), 3 enquadramentos + casos críticos, 3 EDCs + CRC de `"123456789" == 0xCBF43926`, Hamming (ida-e-volta, 1 erro, erro duplo), todas as modulações com e sem ruído, simulação completa (3 enquadramentos × 5 portadoras).

Estado atual: **todos os testes passam.**

---

## 7. Problemas comuns

| Erro | Causa | Solução |
|---|---|---|
| `No module named 'gi'` | PyGObject não instalado | `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0` |
| `No module named 'matplotlib'` | matplotlib não instalado | `pip install matplotlib` (ver seção 2) |
| `ValueError: Quadro final excede 255 bytes` | Quadro + EDC + Hamming > 255 bytes | Reduzir "Tam. máx. de quadro" na GUI (ex.: 8 ou 16 bytes) com enquadramento por contagem |
| `Gtk-WARNING: cannot open display` | Sem display gráfico (SSH sem X11) | `ssh -X ...` ou rodar só `python3 testes.py` |
| Texto recuperado "COM DIFERENÇAS" | Ruído alto demais | Reduzir σ na GUI ou usar modulação mais robusta (ex.: NRZ-Polar) |

---

## 8. Critérios de avaliação

| Critério | Onde é atendido |
|---|---|
| Relatório (+2) | `main.tex` / PDF gerado |
| Código compila e executa (+2) | Testar em Linux — o trabalho é corrigido em Linux |
| Saídas corretas (+3) | `testes.py` — ida-e-volta + casos conhecidos |
| Conceitos de TR1 (+3) | Algoritmos manuais, threads TX/RX, ruído em Volts |
| Legibilidade (−10) | Comentários, separação por módulo conforme o enunciado |
| Plágio (−10) | Desenvolvimento independente do grupo |

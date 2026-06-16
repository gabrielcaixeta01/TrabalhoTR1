# Simulador de Camada Física e de Enlace — TR1 (UnB)

Simulador das camadas física e de enlace de uma rede de computadores, implementando enquadramento, detecção/correção de erros, modulação banda-base e modulação por portadora, com transmissão por um meio de comunicação ruidoso (ruído gaussiano em Volts) e interface gráfica em GTK.

**Linguagem:** Python 3 + PyGObject (GTK 3)
**Restrição importante:** nenhum algoritmo central (CRC, Hamming, checksum, modulações) usa biblioteca externa pronta — tudo foi implementado manualmente. Matplotlib é usado apenas para plotar os sinais na interface gráfica.

**Integrantes:** Gabriel Caixeta Romero, Gustavo Henrique Andrade Cavalcanti, Fernando Augusto Hortencio.

---

## 1. Estrutura de arquivos

```
simulador-tr1/
├── README.md
├── requirements.txt          # matplotlib
├── simulador.py              # Rotina principal: orquestra TX → meio → RX (threads)
├── camada_aplicacao.py       # Texto ↔ bits (codificador/decodificador)
├── camada_enlace.py          # Enquadramento, detecção e correção de erros
├── camada_fisica.py          # Modulação digital (banda-base) e por portadora
├── meio_comunicacao.py       # Canal: sinal em Volts + ruído gaussiano n(x, σ)
├── interface_gui.py          # GUI em GTK 3 (entrada, configuração e gráficos)
├── testes.py                 # Suite de testes de ida-e-volta (roda sem GTK)
└── relatorio/                # Relatório em PDF (mínimo 3 páginas)
```

> O enunciado exige explicitamente os arquivos `CamadaFisica`, `CamadaEnlace`, `InterfaceGUI` e `Simulador`. A estrutura acima respeita isso (em snake_case, padrão Python); se o professor cobrar o nome literal, basta renomear os arquivos — o conteúdo é o mesmo.

---

## 2. Convenções de dados (decisões de projeto)

Definir isso **antes** de codar evita retrabalho:

| Dado | Representação |
|---|---|
| Bits | `list[int]` com valores 0/1 (ex.: `[1, 0, 1, 1]`) |
| Bytes/quadros | também como lista de bits (múltiplos de 8) |
| Sinal banda-base / modulado | `list[float]` em **Volts** (ex.: ±1.0 V), com `AMOSTRAS_POR_BIT` amostras por bit (ex.: 100) |
| Texto | UTF-8 → bits via `camada_aplicacao` |

Constantes globais (definidas em um único lugar, no topo de `camada_fisica.py`):
- `V = 1.0` — amplitude de referência em Volts
- `AMOSTRAS_POR_BIT = 100` — resolução do sinal banda-base
- `AMOSTRAS_POR_SIMBOLO = 100` — resolução de cada símbolo da portadora
- `CICLOS_PORTADORA = 4` — ciclos de portadora por símbolo (ASK/QPSK/16-QAM)
- `CICLOS_FSK = (2, 4)` — frequências (em ciclos/símbolo) do FSK para bit 0 e bit 1

---

## 3. Detalhamento dos módulos

### 3.1 `camada_aplicacao.py`
Camada de aplicação do diagrama do enunciado.

| Função | O que faz |
|---|---|
| `texto_para_bits(texto: str) -> list[int]` | Codifica o texto em UTF-8 e expande cada byte em 8 bits (MSB primeiro) |
| `bits_para_texto(bits: list[int]) -> str` | Operação inversa; agrupa de 8 em 8 e decodifica UTF-8 (com tratamento de erro para bits corrompidos) |

### 3.2 `camada_enlace.py`
Tudo da camada de enlace, dividido em três blocos. Cada protocolo tem a função de **TX** e a de **RX** (inversa).

**Enquadramento** (cada função TX recebe uma **lista de payloads** — listas de bits
alinhadas em bytes — e devolve o fluxo único de bits; a RX faz o inverso):
| TX | RX |
|---|---|
| `enquadrar_contagem(payloads)` | `desenquadrar_contagem(bits)` |
| `enquadrar_bytes(payloads)` — FLAG + byte stuffing com ESC | `desenquadrar_bytes(bits)` |
| `enquadrar_bits(payloads)` — FLAG `01111110` + bit stuffing (após cinco 1s, insere 0) | `desenquadrar_bits(bits)` |

A divisão da mensagem em blocos de `tam_max_quadro` bytes acontece em
`transmitir(bits, config)`, que monta a lista de payloads e chama o enquadrador escolhido.

Decisões documentadas no relatório:
- FLAG = `01111110` (0x7E), ESC = `01111101` (0x7D), como no HDLC/PPP.
- Na contagem de caracteres, o primeiro byte do quadro guarda o tamanho do payload em
  bytes (limite de 255 bytes por quadro, validado em `transmitir()`).
- `tam_max_quadro` vem da GUI ("Tamanho máximo de quadro" no diagrama).

**Detecção de erros** (aplicada ao payload de cada quadro, antes do enquadramento no TX e depois do desenquadramento no RX):
| TX | RX |
|---|---|
| `adicionar_paridade_par(bits)` | `verificar_paridade_par(bits) -> (payload, ok)` |
| `adicionar_checksum(bits)` — soma em complemento de 1, 16 bits (como em aula) | `verificar_checksum(bits) -> (payload, ok)` |
| `adicionar_crc32(bits)` — polinômio IEEE 802 `0x04C11DB7`, **implementado bit a bit, sem zlib** | `verificar_crc32(bits) -> (payload, ok)` |

**Correção de erros** — Hamming(8,4) estendido (SECDED): cada 4 bits de dados viram
8 bits (1 byte → 2 bytes), com p1/p2/p4 nas posições potência de 2 e uma paridade
geral `p0` que permite detectar erro duplo:
| TX | RX |
|---|---|
| `codificar_hamming(bits)` | `decodificar_hamming(bits) -> (dados, n_corrigidos, erro_duplo)` — calcula a síndrome, corrige 1 bit errado por bloco e sinaliza erro duplo |

### 3.3 `camada_fisica.py`

**Modulação digital (banda-base)** — bits → sinal em Volts:
| Modulação | Regra |
|---|---|
| `modular_nrz_polar(bits)` | 1 → +V, 0 → −V durante todo o bit |
| `modular_manchester(bits)` | Convenção Tanenbaum/G.E. Thomas (XOR com clock subindo): bit 1 → transição alto→baixo no meio do bit; bit 0 → baixo→alto |
| `modular_bipolar(bits)` | 0 → 0 V; 1 → alterna entre +V e −V (AMI) |

E os decodificadores correspondentes: `demodular_nrz_polar(sinal)`, `demodular_manchester(sinal)`, `demodular_bipolar(sinal)`. Como há ruído, a decisão é por **limiar sobre a média das amostras** de cada bit (ex.: NRZ: média > 0 → 1).

**Modulação por portadora** — bits → sinal `A·cos(2πft + φ)`:
| Modulação | Bits/símbolo | Parâmetro variado |
|---|---|---|
| `modular_ask(bits)` | 1 | Amplitude / on-off keying (1 → portadora com amplitude V, 0 → 0 V) |
| `modular_fsk(bits)` | 1 | Frequência (f1 para 0, f2 para 1) |
| `modular_qpsk(bits)` | 2 | Fase (45°, 135°, 225°, 315° — codificação Gray) |
| `modular_16qam(bits)` | 4 | Amplitude + fase (constelação 4×4, Gray nos dois eixos) |

Demoduladores: por **correlação** com as portadoras de referência (detecção coerente) — multiplicar pelo cosseno/seno de referência, integrar por símbolo e decidir pelo ponto da constelação mais próximo. É a parte matematicamente mais delicada do trabalho.

### 3.4 `meio_comunicacao.py`
| Função | O que faz |
|---|---|
| `transmitir(sinal, media, sigma)` | Soma a cada amostra um ruído gaussiano `n(x, σ)` via `random.gauss`, conforme exigido no enunciado. `media` e `sigma` vêm da GUI |

### 3.5 `interface_gui.py` (GTK 3, **não pode ser terminal**)
Janela com:
- **Configuração geral:** entrada de texto; tamanho máximo de quadro; tipo de enquadramento; tipo de detecção; tipo de correção; tipo de modulação digital; tipo de modulação por portadora; parâmetros do ruído (média x e desvio σ) — os campos do diagrama do enunciado. O tamanho do EDC é automático conforme a técnica escolhida (paridade 1 byte, checksum 2 bytes, CRC 4 bytes).
- **Painel TX:** texto de entrada, bits após cada etapa (aplicação → enlace → física) e gráfico do sinal modulado (matplotlib embutido no GTK via `FigureCanvas`).
- **Painel RX:** sinal recebido (com ruído), bits após demodulação, quadros decodificados, erros detectados/corrigidos e texto final.

### 3.6 `simulador.py`
Rotina principal. Conecta tudo:

```
TX (thread/programa):  texto → bits → [Hamming/EDC] → enquadramento
                       → banda-base → portadora → sinal (V)
                              │
                       meio_comunicacao (+ ruído gaussiano)
                              │
RX (thread/programa):  sinal → demodulação → decodificação banda-base
                       → desenquadramento → verificação/correção → bits → texto
```

O diagrama do enunciado pede **Programa/Thread TX e RX separados** — usar `threading.Thread` para TX e RX, com o "meio" como fila/buffer compartilhado, deixa isso explícito e rende pontos em "Conceitos de TR1".

---

## 4. Testes e validação

A corretude é verificada por `testes.py`, que roda **sem GTK** e segue a estratégia de
ida-e-volta: aplicar a operação de TX e a de RX em sequência e conferir que a saída é
idêntica à entrada (sem ruído), além de casos com valores conhecidos e erros injetados.

Cobertura da suite:
- **Aplicação:** `texto → bits → texto` (inclui acentos UTF-8).
- **Enquadramento:** os 3 tipos + casos críticos (payload só de 1s no bit stuffing;
  FLAG/ESC no byte stuffing).
- **Detecção:** paridade, checksum e CRC (aceita payload íntegro / detecta 1 bit
  invertido) + CRC-32 de `"123456789"` == `0xCBF43926`.
- **Correção:** Hamming (ida-e-volta, corrige 1 bit, detecta erro duplo).
- **Física:** todas as modulações banda-base e por portadora, com e sem ruído.
- **Simulação completa:** 3 enquadramentos × 5 opções de portadora, conferindo o texto.

```bash
python testes.py    # imprime PASS/FAIL por caso e o resultado geral
```

Estado atual: **todos os testes passam.**

---

## 5. Como executar

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0   # GTK no Linux
pip install matplotlib
python3 simulador.py

# Ambiente local deste checkout:
source .venv/bin/activate
python simulador.py
python testes.py
```
---

## 6. Mapeamento com os critérios de avaliação

| Critério | Onde é atendido |
|---|---|
| Relatório (+2) | `relatorio/` |
| Código compila e executa (+2) | testar sempre no Linux (o trabalho será corrigido em Linux) |
| Saídas corretas (+3) | testes de ida e volta por fase + casos conhecidos (CRC de `"123456789"`, etc.) |
| Conceitos de TR1 (+3) | implementação manual de tudo, threads TX/RX, ruído em Volts |
| Legibilidade (−10) | comentários, indentação, sem duplicação, separação por arquivo conforme o enunciado |
| Plágio (−10) | desenvolvimento independente do grupo |

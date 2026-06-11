# Simulador de Camada Física e de Enlace — TR1 (UnB)

Simulador das camadas física e de enlace de uma rede de computadores, implementando enquadramento, detecção/correção de erros, modulação banda-base e modulação por portadora, com transmissão por um meio de comunicação ruidoso (ruído gaussiano em Volts) e interface gráfica em GTK.

**Linguagem:** Python 3 + PyGObject (GTK 3)
**Restrição importante:** nenhum algoritmo central (CRC, Hamming, checksum, modulações) pode usar biblioteca externa pronta — tudo implementado manualmente. NumPy/Matplotlib são usados apenas como apoio numérico e para plotar os sinais (não implementam nenhum protocolo).

---

## 1. Estrutura de arquivos

```
simulador-tr1/
├── README.md
├── requirements.txt          # PyGObject, numpy, matplotlib
├── simulador.py              # Rotina principal: orquestra TX → meio → RX
├── camada_aplicacao.py       # Texto ↔ bits (codificador/decodificador)
├── camada_enlace.py          # Enquadramento, detecção e correção de erros
├── camada_fisica.py          # Modulação digital (banda-base) e por portadora
├── meio_comunicacao.py       # Canal: sinal em Volts + ruído gaussiano n(x, σ)
├── interface_gui.py          # GUI em GTK 3 (entrada, configuração e gráficos)
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

Constantes globais (definidas em um único lugar, ex.: topo de `camada_fisica.py`):
- `V = 1.0` — amplitude de referência em Volts
- `AMOSTRAS_POR_BIT = 100`
- `FREQ_PORTADORA = 4` (ciclos por símbolo, valor didático para visualização)

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

**Enquadramento** (recebe os bits da aplicação, devolve quadros):
| TX | RX |
|---|---|
| `enquadrar_contagem(bits, tam_max_quadro)` | `desenquadrar_contagem(bits)` |
| `enquadrar_bytes(bits, tam_max_quadro)` — FLAG + byte stuffing com ESC | `desenquadrar_bytes(bits)` |
| `enquadrar_bits(bits, tam_max_quadro)` — FLAG `01111110` + bit stuffing (após cinco 1s, insere 0) | `desenquadrar_bits(bits)` |

Decisões a documentar no relatório:
- FLAG = `01111110` (0x7E), ESC = `01111101` (0x7D), como no HDLC/PPP.
- Na contagem de caracteres, o primeiro byte do quadro guarda o tamanho do payload em bytes.
- `tam_max_quadro` vem da GUI ("Tamanho máximo de quadro" no diagrama).

**Detecção de erros** (aplicada ao payload de cada quadro, antes do enquadramento no TX e depois do desenquadramento no RX):
| TX | RX |
|---|---|
| `adicionar_paridade_par(bits)` | `verificar_paridade_par(bits) -> (payload, ok)` |
| `adicionar_checksum(bits)` — soma em complemento de 1, 16 bits (como em aula) | `verificar_checksum(bits) -> (payload, ok)` |
| `adicionar_crc32(bits)` — polinômio IEEE 802 `0x04C11DB7`, **implementado bit a bit, sem zlib** | `verificar_crc32(bits) -> (payload, ok)` |

**Correção de erros:**
| TX | RX |
|---|---|
| `codificar_hamming(bits)` — Hamming com bits de paridade nas posições potência de 2 | `decodificar_hamming(bits) -> (payload, posicao_corrigida)` — calcula a síndrome e corrige 1 bit errado por bloco |

### 3.3 `camada_fisica.py`

**Modulação digital (banda-base)** — bits → sinal em Volts:
| Modulação | Regra |
|---|---|
| `modular_nrz_polar(bits)` | 1 → +V, 0 → −V durante todo o bit |
| `modular_manchester(bits)` | bit XOR clock: 1 → transição alto→baixo no meio do bit (ou baixo→alto, conforme convenção dos slides — **conferir nos slides!**) |
| `modular_bipolar(bits)` | 0 → 0 V; 1 → alterna entre +V e −V (AMI) |

E os decodificadores correspondentes: `demodular_nrz_polar(sinal)`, `demodular_manchester(sinal)`, `demodular_bipolar(sinal)`. Como há ruído, a decisão é por **limiar sobre a média das amostras** de cada bit (ex.: NRZ: média > 0 → 1).

**Modulação por portadora** — bits → sinal `A·cos(2πft + φ)`:
| Modulação | Bits/símbolo | Parâmetro variado |
|---|---|---|
| `modular_ask(bits)` | 1 | Amplitude (1 → A, 0 → 0 ou A/2) |
| `modular_fsk(bits)` | 1 | Frequência (f1 para 0, f2 para 1) |
| `modular_qpsk(bits)` | 2 | Fase (45°, 135°, 225°, 315° — codificação Gray) |
| `modular_16qam(bits)` | 4 | Amplitude + fase (constelação 4×4, Gray nos dois eixos) |

Demoduladores: por **correlação** com as portadoras de referência (detecção coerente) — multiplicar pelo cosseno/seno de referência, integrar por símbolo e decidir pelo ponto da constelação mais próximo. É a parte matematicamente mais delicada do trabalho.

### 3.4 `meio_comunicacao.py`
| Função | O que faz |
|---|---|
| `transmitir(sinal, media, sigma)` | Soma a cada amostra um ruído gaussiano `n(x, σ)` (via `random.gauss` ou `numpy.random.normal`), conforme exigido no enunciado. `media` e `sigma` vêm da GUI |

### 3.5 `interface_gui.py` (GTK 3, **não pode ser terminal**)
Janela com:
- **Configuração geral:** entrada de texto; tamanho máximo de quadro; tamanho do EDC; tipo de enquadramento; tipo de detecção/correção; tipo de modulação digital; tipo de modulação por portadora; parâmetros do ruído (x e σ) — exatamente os campos do diagrama do enunciado.
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

## 4. Ordem de implementação recomendada

A ordem abaixo permite testar cada etapa isoladamente (sempre teste TX → RX sem ruído primeiro: a saída tem que ser idêntica à entrada).

**Fase 0 — Esqueleto (1 dia)**
1. Criar todos os arquivos com as assinaturas das funções (stubs) e as constantes globais.
2. `camada_aplicacao.py` completo + teste de ida e volta (`texto → bits → texto`).

**Fase 1 — Banda-base (a parte mais visual)**
3. NRZ-Polar (modulação + demodulação) — é a mais simples e serve de gabarito para as outras.
4. Manchester e Bipolar.
5. Teste: `bits → sinal → bits` sem ruído, depois com ruído pequeno (σ = 0.1).

**Fase 2 — Enquadramento**
6. Contagem de caracteres.
7. FLAGs + inserção de bytes.
8. FLAGs + inserção de bits (cuidado com o stuffing na borda do quadro — caso clássico de off-by-one).

**Fase 3 — Detecção de erros**
9. Paridade par (trivial, valida a arquitetura EDC).
10. Checksum (complemento de 1).
11. CRC-32 bit a bit (testar contra valores conhecidos: o CRC-32 de `"123456789"` em ASCII é `0xCBF43926`).

**Fase 4 — Correção**
12. Hamming: codificação, síndrome e correção. Teste forçando a inversão de 1 bit manualmente e conferindo a correção.

**Fase 5 — Portadora (a parte mais difícil)**
13. ASK e FSK (1 bit/símbolo, demodulação simples).
14. QPSK (2 bits/símbolo, demodulação I/Q por correlação).
15. 16-QAM (4 bits/símbolo, decisão pelo ponto mais próximo da constelação).

**Fase 6 — Integração**
16. `meio_comunicacao.py` com ruído gaussiano.
17. `simulador.py` com threads TX/RX encadeando o pipeline completo.

**Fase 7 — GUI e relatório**
18. GUI GTK com todos os seletores e gráficos (deixar por último: a lógica já estará testada).
19. Relatório (capa, introdução, implementação com diagramas, divisão de tarefas dos membros, conclusão).

---

## 5. Como executar

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0   # GTK no Linux
pip install numpy matplotlib
python3 simulador.py
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
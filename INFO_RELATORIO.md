# Briefing para o Relatório — Simulador TR1 (Camadas Física e de Enlace)

> **Propósito deste arquivo:** reunir TODAS as informações técnicas e de contexto do
> projeto para que o relatório final (PDF, mín. 3 páginas) seja redigido a partir daqui.
> Cada seção abaixo já está alinhada à estrutura exigida pelo enunciado
> (Capa, Introdução, Implementação, Membros, Conclusão) e ao checklist de requisitos.
> **Status de cobertura: 100% dos itens obrigatórios do enunciado estão implementados.**

---

## 0. Identificação (para a CAPA)

- **Nome do simulador:** Simulador TR1 — Camadas Física e de Enlace
- **Disciplina:** Teleinformática e Redes 1 (TR1)
- **Professor:** Marcelo Antonio Marotta
- **Instituição:** Universidade de Brasília (UnB)
- **Tipo:** Trabalho Final
- **Linguagem/stack:** Python 3 + PyGObject (GTK 3); matplotlib só para plotar sinais
- **Integrantes:**
  - Gabriel Caixeta Romero
  - Gustavo Henrique Andrade Cavalcanti
  - Fernando Augusto Hortencio

---

## 1. Introdução (problema + visão geral)

**Problema:** simular a transmissão de uma mensagem de texto entre dois nós de rede,
exercitando as **camadas física e de enlace** — enquadramento, detecção e correção de
erros, modulação banda-base e modulação por portadora — através de um **meio ruidoso**
modelado eletricamente (amostras em Volts + ruído gaussiano).

**Visão geral do funcionamento:** o usuário digita um texto e escolhe, na GUI, os
protocolos de cada camada e os parâmetros de ruído. O simulador então:
1. converte o texto em bits (aplicação);
2. monta quadros com EDC/Hamming e enquadramento (enlace);
3. transforma os bits em sinal elétrico banda-base e, opcionalmente, modulado em
   portadora (física);
4. propaga o sinal pelo meio, somando ruído gaussiano amostra a amostra;
5. percorre o caminho inverso no receptor e exibe, em abas TX/RX, os bits e sinais
   de cada camada, além do texto recuperado e métricas (potências, SNR, erros).

**Diferencial pedido pelo enunciado (TX vs RX):** transmissor e receptor rodam em
**threads separadas** que se comunicam **exclusivamente por filas** (`queue.Queue`),
que fazem o papel do meio físico. O ruído é somado no "canal", entre as duas threads.

---

## 2. Arquitetura e mapeamento de arquivos

O enunciado exige os arquivos `CamadaFisica`, `CamadaEnlace`, `InterfaceGUI` e
`Simulador`. O projeto os entrega em snake_case (padrão Python), com módulos auxiliares:

| Arquivo | Papel | Requisito do enunciado |
|---|---|---|
| `simulador.py` | Rotina principal: orquestra TX → meio → RX em threads | `Simulador` |
| `camada_fisica.py` | Modulação digital (banda-base) e por portadora | `CamadaFisica` |
| `camada_enlace.py` | Enquadramento, detecção e correção de erros | `CamadaEnlace` |
| `interface_gui.py` | GUI em GTK 3 (entrada, config, gráficos) | `InterfaceGUI` |
| `camada_aplicacao.py` | Texto ↔ bits (codificador/decodificador) | apoio |
| `meio_comunicacao.py` | Canal: sinal em Volts + ruído gaussiano n(x, σ) | apoio (meio) |
| `testes.py` | Suite de testes de ida-e-volta (TX→RX sem ruído == entrada) | validação |

### Diagrama de pilha (TX → MEIO → RX) — para reproduzir no relatório

```
  THREAD TX                       MEIO                    THREAD RX
  ---------                       ----                    ---------
  texto                                                       texto
    | aplicação (texto->bits)                  (bits->texto) aplicação
  bits                                                        bits
    | enlace (EDC/Hamming + enquadramento)   (inverso) enlace |
  quadros (bits)                                    quadros (bits)
    | física (banda-base -> portadora)      (demod/decod) física
  sinal (V) ----> [ + ruído gaussiano n(x, sigma) ] ----> sinal (V)
```

A comunicação entre threads usa duas filas: `TX --fila_tx--> [canal soma ruído] --fila_rx--> RX`.

---

## 3. Cobertura do checklist (requisito → onde está implementado)

### 3.1 Camada Física — Modulação Digital (banda-base) ✅
| Requisito | Função (modular / demodular) | Convenção adotada |
|---|---|---|
| NRZ-Polar | `modular_nrz_polar` / `demodular_nrz_polar` | bit 1 → +V; bit 0 → −V. Decisão por **média** das amostras |
| Manchester | `modular_manchester` / `demodular_manchester` | Convenção **Tanenbaum/G.E. Thomas** (XOR com clock subindo): bit 0 = baixo→alto, bit 1 = alto→baixo. Decisão compara média da 1ª vs 2ª metade |
| Bipolar (AMI) | `modular_bipolar` / `demodular_bipolar` | bit 0 → 0 V; bit 1 → alterna +V/−V (elimina DC). Decisão por **\|média\| > V/2** |

### 3.2 Camada Física — Modulação por Portadora ✅
Representação comum I/Q: `s(t) = I·cos(2πft) − Q·sen(2πft)`; demodulação **coerente**
por correlação (produto interno) + escolha do **ponto de constelação mais próximo**.

| Requisito | Função | Detalhe |
|---|---|---|
| ASK | `modular_ask` / `demodular_ask` | On-off keying: bit 1 → portadora amplitude V; bit 0 → 0 V. Limiar V/2 sobre \|amplitude\| medida |
| FSK | `modular_fsk` / `demodular_fsk` | Duas frequências ortogonais (2 e 4 ciclos/símbolo). Decisão por **energia** em cada frequência |
| QPSK | `modular_qpsk` / `demodular_qpsk` | 2 bits/símbolo, **mapeamento Gray** (vizinhos diferem em 1 bit) |
| 16-QAM | `modular_16qam` / `demodular_16qam` | 4 bits/símbolo; níveis Gray {−3,−1,+1,+3}·(V/3) em I e Q; decisão por eixo |

Parâmetros globais (em `camada_fisica.py`): `V=1.0`, `AMOSTRAS_POR_BIT=100`,
`AMOSTRAS_POR_SIMBOLO=100`, `CICLOS_PORTADORA=4`, `CICLOS_FSK=(2,4)`.
Helpers reaproveitados: `_onda`, `_correlacionar`, `_pad`, `_bits_do_ponto_mais_proximo`.

### 3.3 Camada de Enlace — Enquadramento ✅
| Requisito | Função (enquadrar / desenquadrar) | Detalhe |
|---|---|---|
| Contagem de caracteres | `enquadrar_contagem` / `desenquadrar_contagem` | 1 byte de cabeçalho = nº de bytes do payload (máx. 255, validado) |
| FLAGs + inserção de bytes | `enquadrar_bytes` / `desenquadrar_bytes` | FLAG=0x7E, ESC=0x7D (HDLC/PPP); byte stuffing com máquina de estados |
| FLAGs + inserção de bits | `enquadrar_bits` / `desenquadrar_bits` | Após **5 bits 1 consecutivos** insere um 0; FLAG=01111110 nunca aparece nos dados |

### 3.4 Camada de Enlace — Detecção de Erros ✅
**Nenhuma biblioteca externa** (proibição da `zlib` respeitada — tudo bit a bit).

| Requisito | Função (adicionar / verificar) | Detalhe |
|---|---|---|
| Bit de paridade par | `adicionar_paridade_par` / `verificar_paridade_par` | Anexa 1 byte (7 zeros + paridade) p/ manter alinhamento; detecta nº ímpar de bits invertidos |
| Checksum | `adicionar_checksum` / `verificar_checksum` | Soma em **complemento de 1** de palavras de 16 bits (end-around carry), igual ao checksum da Internet; verificação deve dar 0xFFFF |
| CRC-32 (IEEE 802) | `adicionar_crc32` / `verificar_crc32` (`_calcular_crc32`) | Polinômio IEEE 802 0x04C11DB7 na forma refletida 0xEDB88320, init 0xFFFFFFFF, XOR final. **Validado:** CRC32("123456789") == 0xCBF43926 |

### 3.5 Camada de Enlace — Correção de Erros ✅
| Requisito | Função | Detalhe |
|---|---|---|
| Hamming | `codificar_hamming` / `decodificar_hamming` | **Hamming(8,4) estendido (SECDED)**: 4 bits → 8 bits; corrige 1 erro e detecta 2 erros por bloco; usa síndrome + paridade geral p0 |

### 3.6 Interface Gráfica ✅
- GTK 3 (não é terminal), conforme exigido. `interface_gui.py` → classe `JanelaSimulador`.
- Painel esquerdo: configuração geral (texto, tam. máx. de quadro, combos de
  enquadramento/detecção/correção/mod. digital/mod. portadora, ruído x e σ).
- Painel direito: abas **Transmissor** e **Receptor** com bits de cada camada,
  texto recuperado, relatório por quadro (EDC OK/erro, bits corrigidos, erro duplo)
  e gráficos dos sinais (matplotlib embutido no GTK).
- Diferenciação **TX vs RX** explícita nas duas abas.

---

## 4. Fluxo detalhado dos pipelines (para a seção Implementação)

### Transmissor — `camada_enlace.transmitir(bits, config)`
1. Divide os bits da aplicação em blocos de `tam_max_quadro` bytes.
2. Cada bloco recebe o **EDC** ao final (paridade/checksum/CRC).
3. Se Hamming ativo, o bloco (payload+EDC) é codificado — **dobra** de tamanho.
4. Cada bloco vira um quadro segundo o enquadramento escolhido.
5. Quadros concatenados em um único fluxo de bits.

Depois (`simulador._rotina_tx`): bits → `modular_digital` (banda-base) e, se houver
portadora, → `modular_portadora` (sinal efetivamente transmitido ao meio).

### Receptor — caminho inverso
`simulador._rotina_rx`: recebe sinal ruidoso → demodula portadora (ou banda-base) →
`camada_enlace.receber`: desenquadra → corrige (Hamming) → verifica EDC → bits →
`camada_aplicacao.bits_para_texto`.

### Meio — `meio_comunicacao.transmitir(sinal, media, sigma)`
Soma `random.gauss(media, sigma)` a cada amostra (AWGN). Canal ideal quando
media=σ=0. `potencia_media` calcula P = média de v² (W sobre 1 Ω) para SNR.

---

## 5. Decisões de projeto (detalhes omissos do enunciado — exigido no relatório)

1. **Alinhamento em bytes dos EDCs:** paridade→1 byte, checksum→2 bytes, CRC→4 bytes,
   para compatibilizar com enquadramentos que operam sobre bytes.
2. **Hamming(8,4) estendido (SECDED)** em vez do (7,4) puro: mantém alinhamento em
   bytes (1→2 bytes) e permite detectar erro duplo.
3. **Ordem TX:** EDC primeiro, Hamming depois — assim o Hamming protege também os bits
   de detecção. No RX, a ordem se inverte (corrige antes de verificar EDC).
4. **Padding da portadora:** QPSK/16-QAM completam com zeros até fechar símbolo
   inteiro; o desenquadramento descarta o excedente (byte 0x00 / FLAGs).
5. **Convenção Manchester:** Tanenbaum/G.E. Thomas (documentada explicitamente).
6. **Demodulação robusta a ruído:** banda-base por média; portadora por correlação
   coerente + mínima distância na constelação (Gray minimiza bits errados).
7. **CRC validável:** forma refletida padrão (Ethernet) para conferir contra o vetor
   de teste conhecido 0xCBF43926.
8. **Limite da contagem de caracteres:** quadro final ≤ 255 bytes, validado em
   `transmitir()` (lança `ValueError` exibido na GUI).
9. **Decodificação de texto tolerante:** `bits_para_texto` usa `errors="replace"`
   (caractere `�`) para não derrubar o programa quando o ruído corrompe bytes.
10. **Desacoplamento da GUI:** GTK importado só dentro do `__main__`/GUI, permitindo
    rodar `testes.py` e os módulos em máquinas sem GTK.

---

## 6. Validação / resultados (para a seção Resultado)

`testes.py` cobre, por ida-e-volta (saída == entrada):
- aplicação (texto↔bits, inclui acentos UTF-8);
- os 3 enquadramentos + casos críticos (payload só de 1s no bit stuffing; FLAG/ESC no
  byte stuffing);
- os 3 EDCs (aceita íntegro / detecta 1 bit invertido) + CRC-32 contra 0xCBF43926;
- Hamming (ida-e-volta, corrige 1 bit, detecta erro duplo);
- todas as modulações banda-base e por portadora, com e sem ruído;
- **simulação completa** combinando 3 enquadramentos × 5 opções de portadora.

**Resultado atual: "TODOS OS TESTES PASSARAM".** (Citar no relatório como evidência de
corretude — útil para o critério "Resultado +3" e "Conceitos de TR1 +3".)

> Nota de manutenção: `simulador.py` teve seu conteúdo restaurado (um commit havia
> sobrescrito o módulo por um shim); após restauração `python testes.py` passa 100%.

---

## 7. Como executar (para apêndice/execução)

```bash
source .venv/bin/activate
python simulador.py     # abre a GUI GTK
python testes.py        # roda a suite (sem GTK)
```
Dependências Linux da GUI: `python3-gi python3-gi-cairo gir1.2-gtk-3.0` + `matplotlib`.

---

## 8. Sugestão de divisão por membro (seção Membros — AJUSTAR com o grupo)

> ⚠️ Os papéis abaixo são uma sugestão a partir do escopo; **confirmar/editar** com os
> integrantes antes de finalizar o PDF.
- **Gabriel Caixeta Romero:** camada de enlace (enquadramentos, EDC, Hamming) e testes.
- **Gustavo Henrique Andrade Cavalcanti:** camada física (modulações digital e portadora) e meio.
- **Fernando Augusto Hortencio:** interface GTK, integração do simulador (threads) e relatório.

---

## 9. Conclusão (tópicos sugeridos)

- Todos os protocolos exigidos foram implementados **sem bibliotecas externas** nos
  algoritmos centrais (CRC, Hamming, checksum, modulações).
- Principais dificuldades: demodulação robusta a ruído (correlação coerente e mínima
  distância); manter **alinhamento em bytes** entre EDC/Hamming/enquadramento;
  padding das modulações multibit (QPSK/16-QAM); convenção de Manchester.
- Arquitetura TX/RX em threads + filas reproduz fielmente o diagrama do enunciado e
  isola o meio (ruído) como ponto único de contato.

---

## 10. Checklist de entrega (status)

- [x] Camada física: NRZ-Polar, Manchester, Bipolar
- [x] Camada física: ASK, FSK, QPSK, 16-QAM
- [x] Enquadramento: contagem, FLAGs+bytes, FLAGs+bits
- [x] Detecção: paridade par, checksum, CRC-32 (sem zlib)
- [x] Correção: Hamming
- [x] GUI em GTK (não-terminal), diferencia TX/RX
- [x] Simulador com rotina principal e meio com ruído gaussiano em Volts
- [x] Testes de ida-e-volta passando
- [ ] **Relatório PDF (mín. 3 páginas) — A GERAR a partir deste arquivo**
- [ ] Compactar relatório + código em .zip e submeter no Moodle

# Desenvolvimento — Simulador TR1

O que precisa ser feito, **em ordem de implementação**. Cada item aponta o arquivo, as funções e o
material de estudo (pasta `estudos/`, na raiz do repositório). Todas as funções do esqueleto já têm docstring com objetivo, passos, fórmulas e
dicas: comecem lendo a docstring antes de escrever código.

**Como acompanhar o progresso:** `python3 testes.py` mostra `[TODO]` (falta implementar), `[PASS]` e
`[FAIL]` (bug). A meta é zerar `TODO` e `FAIL`.

```
 aplicação ─► enlace ─► física ─► MEIO (+ruído) ─► física ─► enlace ─► aplicação
   Tx          Tx        Tx                          Rx        Rx         Rx
```

---

## Etapa 1 — Base (destrava o resto)

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 1 | Conversão texto ↔ bits (UTF-8, MSB primeiro): `texto_para_bits`, `bits_para_texto` | `camada_aplicacao.py` | 05 |
| 2 | Utilitários de bits: `bits_para_bytes`, `bytes_para_bits` (usados por quase todo o enlace) | `camada_enlace.py` | 02 |
| 3 | Canal: ruído gaussiano n(x, σ) somado a cada amostra (`transmitir`) e potência média (`potencia_media`) | `meio_comunicacao.py` | 05 |

## Etapa 2 — Camada física: banda-base

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 4 | NRZ-Polar: modulador e demodulador (decisão pela média das amostras) | `camada_fisica.py` | 01 |
| 5 | Manchester: modulador e demodulador (comparar as duas metades do bit) | `camada_fisica.py` | 01 |
| 6 | Bipolar: modulador e demodulador (alternância de polaridade; decisão pelo módulo) | `camada_fisica.py` | 01 |

## Etapa 3 — Camada física: portadora

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 7 | Auxiliares: `onda` (gera símbolo a partir de I/Q), `correlacionar` (recupera I/Q), `pad`, `bits_do_ponto_mais_proximo` | `camada_fisica.py` | 01 |
| 8 | ASK: modulador e demodulador (limiar V/2 sobre a amplitude) | `camada_fisica.py` | 01 |
| 9 | FSK: modulador e demodulador (energia em duas frequências) | `camada_fisica.py` | 01 |
| 10 | 8PSK: preencher `MAPA_8PSK` (Gray) e implementar modulador e demodulador | `camada_fisica.py` | 01 |
| 11 | 32-QAM: preencher `MAPA_32QAM` (cruz 6×6 sem cantos) e implementar modulador e demodulador | `camada_fisica.py` | 01 |

## Etapa 4 — Camada de enlace: detecção de erros

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 12 | Bit de paridade par: `adicionar_paridade_par`, `verificar_paridade_par` | `camada_enlace.py` | 03 |
| 13 | Checksum: `soma_complemento1`, `bits_para_palavras16`, `adicionar_checksum`, `verificar_checksum` | `camada_enlace.py` | 03 |
| 14 | CRC-32 (IEEE 802), sem `zlib`, pela divisão módulo 2 dos slides: `resto_mod2`, `calcular_crc32`, `adicionar_crc32`, `verificar_crc32` | `camada_enlace.py` | 03 |

## Etapa 5 — Camada de enlace: enquadramento

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 15 | Contagem de caracteres (a contagem inclui o byte de cabeçalho): `enquadrar_contagem`, `desenquadrar_contagem` | `camada_enlace.py` | 02 |
| 16 | Inserção de bytes (byte stuffing): `enquadrar_bytes`, `desenquadrar_bytes` | `camada_enlace.py` | 02 |
| 17 | Inserção de bits (bit stuffing): `enquadrar_bits`, `desenquadrar_bits` | `camada_enlace.py` | 02 |
| 18 | Entrelaçamento por matriz (paridade por coluna, transmissão por linhas): `paridade_colunas`, `entrelacar`, `desentrelacar`, `enquadrar_entrelacamento`, `desenquadrar_entrelacamento` | `camada_enlace.py` | 02 |

Todos os desenquadradores precisam **ignorar o padding de zeros** que 8PSK/32-QAM acrescentam no fim.

## Etapa 6 — Camada de enlace: correção de erros e orquestração

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 19 | Hamming (11,7) dos slides, com síndrome: `codificar_hamming`, `decodificar_hamming` (completar com zeros até múltiplo de 7 e de 8) | `camada_enlace.py` | 04 |
| 20 | Pipeline do enlace: `transmitir` (divide → EDC → Hamming → enquadra) e `receber` (ordem inversa, com relatório por quadro) | `camada_enlace.py` | 02, 03, 04, 05 |

## Etapa 7 — Integração

| # | O que fazer | Onde | Estudo |
|---|---|---|---|
| 21 | Threads TX e RX ligadas pelo canal: `_rotina_tx`, `_rotina_rx`, `executar_simulacao` (cuidar da exceção dentro de thread) | `simulador.py` | 05 |
| 22 | Rodar a suíte completa (`testes.py`) e corrigir o que falhar | todos | — |
| 23 | Rodar a interface (`python3 simulador.py`), que já vem pronta, e testar todas as combinações | `interface_gui.py` | — |

## Etapa 8 — Experimentos e relatório

| # | O que fazer |
|---|---|
| 24 | Experimentos para o relatório: sinais banda-base e portadora, constelações com ruído, variação de σ, comparação com/sem Hamming, comparação entre EDCs |
| 25 | Relatório PDF (mínimo 3 páginas): **capa** (nome do simulador + membros), **introdução** (problema + visão geral), **implementação** (diagramas, funcionamento dos protocolos, procedimentos, decisões), **membros** (atividade de cada um), **conclusão** (comentários e dificuldades) |
| 26 | Revisão final do código (comentários, indentação, sem funções duplicadas/redundantes/inalcançáveis) e empacotamento em `.zip` para o Moodle |

---

## Decisões de projeto

O enunciado e os slides deixam vários detalhes em aberto (convenção do Manchester, rotulagem do 32-QAM, N do
entrelaçamento, tamanho da palavra do checksum, polinômio e variante do CRC, FLAG/ESC, padding do Hamming,
tratamento de quadro com EDC inválido...). Todos já foram decididos e justificados em
[DECISOES.md](DECISOES.md), que também é o insumo da seção "decisões tomadas" do relatório. Leiam o arquivo
antes de implementar e, se o grupo quiser mudar algo, atualizem-no junto com o código.

Único ponto a conferir: a **convenção do Manchester** (os dois resumos dos slides se contradizem). O
`DECISOES.md` explica como trocar.

---

## Todos precisam dominar tudo

O professor pode perguntar sobre qualquer trecho a qualquer membro (enunciado, seção 5). Sugestões:

- Ler **todos** os arquivos de `estudos/` (cada um termina com "pontos que o professor gosta de cobrar").
- Revisão cruzada: quem revisa um módulo tenta explicá-lo em voz alta; o que não conseguir explicar vira pergunta.
- Ensaio: explicar o caminho completo de uma mensagem (texto → sinal → texto), função por função.

---

## Checklist do enunciado

**Meio de comunicação**
- [ ] Sinal em Volts (ou Watts)
- [ ] Ruído gaussiano n(x, σ), com x e σ configuráveis

**Camada física**
- [ ] NRZ-Polar · [ ] Manchester · [ ] Bipolar
- [ ] ASK · [ ] FSK · [ ] 8PSK · [ ] 32-QAM

**Camada de enlace**
- [ ] Contagem de caracteres · [ ] Entrelaçamento de bits · [ ] Byte stuffing · [ ] Bit stuffing
- [ ] Paridade par · [ ] Checksum · [ ] CRC-32 (IEEE 802)
- [ ] Hamming
- [ ] Nenhuma biblioteca externa implementando protocolo (ex.: zlib para CRC)

**Aplicação e interface**
- [ ] Chat de texto: entrada no Tx, saída legível no Rx
- [ ] GUI em GTK (não é terminal) com configuração geral e saídas de Tx e Rx
- [ ] Threads/programas distintos para transmissor e receptor

**Entrega (.zip no Moodle)**
- [ ] Relatório PDF com capa, introdução, implementação, membros e conclusão
- [ ] Código: `CamadaFisica`, `CamadaEnlace`, `InterfaceGUI`, `Simulador`
- [ ] Código legível: comentários, indentação, sem funções duplicadas/redundantes/inalcançáveis
- [ ] Prazo conforme o Moodle (−1 ponto por dia de atraso)
- [ ] Desenvolvimento independente do grupo (verificador automático de plágio)

**Pontuação (resumo do enunciado):** relatório +2 · compila e executa +2 · saídas corretas +3 ·
conceitos de TR1 implementados +3 · legibilidade/modularização até −10.

# Detalhes dos slides (respostas do NotebookLM)

> Respostas do NotebookLM às perguntas que o resumo `docs/referencias/referencia-slides.md` não cobria. Cada item cita
> o arquivo e o slide de origem. "**Não consta nos slides**" = o NotebookLM não achou a informação;
> nesses casos a decisão é do grupo (e deve ir para o relatório).
>
> Texto reorganizado a partir do que o NotebookLM devolveu (as marcas de citação foram removidas). A linha
> de paridade do exemplo 7×7 veio truncada ("1 0 ...") e foi **calculada por nós**.

---

## 1. Entrelaçamento de bits (enquadramento)

Fonte: `TR1_09_key.pdf`, slides 23 e 24.

- **Algoritmo:** os dados são formatados em uma **matriz retangular de bits**. A paridade é calculada
  **por coluna** e colocada na **última linha**.
- **Ordem de transmissão:** linhas de cima para baixo, e dentro de cada linha da esquerda para a direita.
  A última linha enviada é a de paridade das colunas.
- **Exemplo (slide 24):** matriz de dados 7×7 (mais a linha de paridade, 8 linhas no total):

| Linha | Bits |
|---|---|
| 1 | 1 0 0 1 1 1 0 |
| 2 | 1 1 0 0 1 0 1 |
| 3 | 1 1 1 0 1 0 0 |
| 4 | 1 1 1 0 1 1 1 |
| 5 | 1 1 0 1 1 1 1 |
| 6 | 1 1 1 0 0 1 0 |
| 7 | 1 1 0 1 0 1 1 |
| 8 (paridade das colunas, calculada por nós) | 1 0 1 1 1 1 0 |

- **Valores de M e N:** no exemplo, 7 linhas de dados × 7 colunas. **Como escolher N: não consta.**
- **Paridade:** só por coluna. Se a matriz corrige erro sem outro código: **não consta** (aparece na
  seção de *detecção* de erros).
- **Início/fim do quadro entrelaçado e padding: não consta.**
- **Relação com Hamming e detecção:** classificado como uma forma de checksum / bits de verificação para
  espalhar erros em rajada. A integração com Hamming em um mesmo algoritmo **não consta** (tópicos separados).

## 2. Modulação por portadora

Fonte: `CF - 12 - BPSK, QPSK, 8PSK.pdf` (slides 3, 5, 6, 8, 9), `CF - 13 - Modulação mista.pdf` (slides 3, 4, 9),
`CF - 11 - Modulação e Demodulação.pdf` (slides 5 a 8).

- **8PSK:** 3 bits por símbolo (tribit); fases de 45° em 45°. Mapeamento Gray (slides 5 e 9):

| Fase | Tribit |
|---|---|
| 0° | 000 |
| 45° | 001 |
| 90° | 011 |
| 135° | 010 |
| 180° | 110 |
| 225° | 111 |
| 270° | 101 |
| 315° | 100 |

  Tabela numérica com I e Q do 8PSK: **não consta** (só existe para o 16-QAM).
- **32-QAM:** o diagrama do slide 4 mostra uma constelação retangular/em cruz recortada, com distância
  mínima d_min = 0,337. **Níveis numéricos de I/Q e tabela de rotulagem dos 5 bits: não consta.**
- **ASK:** bit 1 com amplitude A na frequência f; bit 0 com amplitude 0 (On-Off Keying). Exemplo de
  MATLAB: `A*sin(2*pi*f*j/100)` para o bit 1 e 0 para o bit 0.
- **FSK:** duas frequências f1 e f2 com a mesma amplitude A. Exemplo: `A*sin(2*pi*f1*j/100)` para o bit 1
  e `A*sin(2*pi*f2*j/100)` para o bit 0. **Fórmulas de demodulação: não constam.**
- **Convenção I/Q:** `I(t) = x(t)·cos(ωc t)`, `Q(t) = −y(t)·sen(ωc t)`, `s(t) = x(t)cos(ωc t) − y(t)sen(ωc t)`.
- **QPSK:** 45° → 11 · 135° → 10 · 225° → 00 · 315° → 01.

## 3. Enquadramento

Fonte: `TR1_08_key.pdf`, slides 28 a 37.

- **Contagem de caracteres:** cabeçalho de **1 byte** e a contagem **inclui o próprio byte de cabeçalho**.
  Exemplo: para enviar 2 bytes de dados, o cabeçalho vale **3**.
- **Byte stuffing:** inserir ESC antes de qualquer FLAG presente nos dados e antes de qualquer ESC nos
  dados; o receptor remove o ESC e trata o byte seguinte como dado. **Valores hexadecimais de FLAG e ESC
  não constam** (só os nomes).
- **Bit stuffing:** FLAG = `01111110`. Após **cinco 1s** consecutivos nos dados o transmissor insere um `0`;
  o receptor, ao ver cinco 1s seguidos de um 0, remove esse 0.

## 4. Detecção de erros

Fonte: `TR1_09_key.pdf`, slides 18, 19, 23, 25, 30 a 33.

- **Checksum:** é o complemento da soma dos blocos; o receptor soma tudo (dados + checksum) e, se der zero,
  não há erro. **Tamanho da palavra, tipo de soma (complemento de 1) e exemplo numérico: não constam.**
- **CRC:** divisão polinomial **módulo 2 pura** (XOR sem transporte): anexar k zeros (k = grau de G),
  dividir por G(x), o resto de k bits é o CRC e substitui os zeros; o receptor divide o quadro recebido e
  resto ≠ 0 indica erro. Exemplos com G(x) = x⁴ + x + 1 (10011). **Polinômio do CRC-32, valor inicial,
  XOR final e reflexão de bits: não constam.**
- **Paridade:** aparece por caractere/byte (slides 18 e 19) e por coluna no entrelaçamento (slide 23).

## 5. Correção de erros (Hamming)

Fonte: `TR1_09_key.pdf`, slides 38 e 39.

- Código de **Hamming (11,7)**. Posições 1, 2, 4, 8 = paridades (P1, P2, P4, P8); posições 3, 5, 6, 7, 9, 10,
  11 = dados (M3, M5, M6, M7, M9, M10, M11). Paridade par:
  - P1 = M3 ⊕ M5 ⊕ M7 ⊕ M9 ⊕ M11
  - P2 = M3 ⊕ M6 ⊕ M7 ⊕ M10 ⊕ M11
  - P4 = M5 ⊕ M6 ⊕ M7
  - P8 = M9 ⊕ M10 ⊕ M11
- **Paridade geral (SECDED) e payload não múltiplo do bloco: não constam.**

## 6. Banda-base

Fonte: `CF - 10 - Canal banda base.pdf`, slides 3, 4, 6 a 9 e 11.

- **Manchester (slide 8):** transição **alto→baixo para o bit 1** e **baixo→alto para o bit 0** (XOR entre
  dados e clock).

  > ⚠️ **Conflito:** o primeiro resumo (`docs/referencias/referencia-slides.md`) diz o contrário (1 = baixo→alto, "IEEE
  > 802.3"). Conferir o slide 8 do `CF - 10` com os próprios olhos e fixar uma convenção.
- **Bipolar/AMI (slide 9):** bit 0 = 0 V; os bits 1 alternam entre +V e −V.
- **NRZI (slide 7):** bit 1 causa transição; bit 0 mantém o nível.
- **NRZ Polar:** +V para 1 e −V para 0. **NRZ Unipolar:** +V para 1 e 0 V para 0.
- **Decisão do receptor:** amostragem no instante central do bit, comparando com um nível de referência
  (padrão de olho).

## 7. Canal e ruído

Fonte: `CF - 5 - Capacidade do Canal.pdf` (slides 6, 7), `CF - 5.1` (slides 6 a 10), `CF - 13` (slide 9).

- SNR = S/N (potência do sinal / potência do ruído). Shannon: C = B·log₂(1 + SNR).
- Modelagem do ruído gaussiano (média e desvio padrão): **não consta** (vem do enunciado).
- Probabilidade de erro: só em gráficos de log BER × Eb/N0 (QPSK, 8-PSK, 16-PSK, 16-QAM, 64-QAM; CF-13, slide 9).

## 8. Outras convenções

- **Nyquist:** C = 2·B·log₂N; taxa de bits R = m·Rs, com m = log₂N bits por símbolo (CF-5, slide 13).
- **MAC (`TR1_012.pdf`, slide 13):** premissas de canal compartilhado (tráfego independente, canal único,
  colisões observáveis, tempo contínuo ou segmentado, detecção de portadora). Fora do escopo do trabalho.

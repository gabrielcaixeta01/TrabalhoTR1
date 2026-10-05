# Especificação Técnica de Implementação: Teleinformática e Redes
> **Documento de Referência para Claude Code / Sistemas de Comunicação**
> **Origem:** Compilação dos Slides da Disciplina de Teleinformática e Redes / Comunicação de Dados (UnB)
>
> *Resumo gerado pelo NotebookLM a partir dos slides do prof. Marotta e salvo aqui como fonte de verdade
> teórica do projeto, junto com o enunciado. É um resumo: não cobre tudo (ex.: não traz ASK, FSK, 32-QAM,
> contagem de caracteres nem byte/bit stuffing). Texto original abaixo, sem edições.*

---

## 1. Camada Física: Codificação de Linha (Banda Base)

A transmissão em banda base não utiliza portadora e mapeia a sequência binária de dados em níveis contínuos ou transições de tensão elétrica.

### 1.1 Esquemas de Codificação
* **NRZ Polar (Non-Return-to-Zero Polar)**:
  * `1` $\rightarrow +V$
  * `0` $\rightarrow -V$
  * **Largura de Banda Mínima**: $B/2 \text{ Hz}$ para taxa de bit de $B \text{ bits/s}$.
  * **Desvantagem**: Perda de sincronismo e drift de nível CC em sequências longas de bits idênticos.

* **NRZ Unipolar**:
  * `1` $\rightarrow +V$
  * `0` $\rightarrow 0\text{V}$

* **NRZI (NRZ-Inverted / NRZ-M / NRZ-S)**:
  * `1` $\rightarrow$ **Transição** no início del intervalo de bit.
  * `0` $\rightarrow$ **Sem transição** (mantém o nível anterior).
  * **Uso**: Facilita a recuperação de clock em sequências de `1`s.

* **Manchester (IEEE 802.3)** *(CORREÇÃO: a convenção deste item está invertida; pelo slide 8 do CF-10 o bit 1 desce, alto→baixo, e o bit 0 sobe. Ver `referencia-slides-detalhes.md`.)*:
  * Operação: $S(t) = \text{Data}(t) \oplus \text{Clock}(t)$
  * Transição garantida no centro do bit:
    * `1` $\rightarrow$ Transição de Baixo ($-V$) para Alto ($+V$).
    * `0` $\rightarrow$ Transição de Alto ($+V$) para Baixo ($-V$).
  * **Vantagem**: Auto-sincronização permanente e componente CC nula.
  * **Desvantagem**: Dobra a largura de banda necessária em relação ao NRZ.

* **AMI / Bipolar (Alternate Mark Inversion / Pseudo-Ternário)**:
  * `0` $\rightarrow 0\text{V}$
  * `1` $\rightarrow$ Alterna consecutivamente entre $+V$ e $-V$.
  * **Vantagem**: Componente de Corrente Contínua (CC) estritamente nula e capacidade de detecção de erros simples (violação de bipolaridade).

* **RZ Bipolar (Return-to-Zero)**:
  * `1` $\rightarrow$ Pulso positivo $+V$ na primeira metade do tempo de bit ($T_b/2$), retornando a $0\text{V}$ na segunda metade.
  * `0` $\rightarrow$ Pulso negativo $-V$ na primeira metade ($T_b/2$), retornando a $0\text{V}$.

---

### 1.2 Padrão de Olho (Eye Diagram)
Ferramenta de diagnóstico obtida pela sobreposição de episódios de forma de onda em osciloscópio:
* **Abertura Vertical**: Margem contra o ruído ($\Delta n$).
* **Abertura Horizontal**: Intervalo de tempo sobre o qual a amostragem pode ocorrer sem erro de ISI (Intersymbol Interference).
* **Cruzamento de Níveis**: Sensibilidade ao Jitter de fase ($\Delta t$).
* **Sensibilidade de Amostragem**: Instante ideal de amostragem coincide com o centro da abertura máxima do olho.

---

## 2. Modulação em Banda Passante & Estrutura Quadrartura

### 2.1 Mapeamento e Agrupamento de Bits
O fluxo serial $R \text{ bits/s}$ é dividido por um conversor Serial-Paralelo em blocos de $m = \log_2 N$ bits, gerando símbolos transmitidos a uma taxa $R_s = R/m \text{ bauds}$:
* **BPSK ($m=1$)**: 1 bit/símbolo ($R_s = R$).
* **QPSK / 4-QAM ($m=2$)**: 2 bits/símbolo (Dibits) ($R_s = R/2$).
* **8PSK ($m=3$)**: 3 bits/símbolo (Tribits) ($R_s = R/3$).
* **16-QAM ($m=4$)**: 4 bits/símbolo (Quadribits) ($R_s = R/4$).

---

### 2.2 Estrutura do Modulador I/Q (Quadratura)
O sinal modulado é sintetizado como:
$$s(t) = I(t) \cdot \cos(\omega_c t) - Q(t) \cdot \sin(\omega_c t)$$
onde $I(t)$ é a componente Em Fase e $Q(t)$ é a componente Em Quadratura.

---

### 2.3 Mapeamento de Gray (Bit Labeling)
Para minimizar a Taxa de Erros de Bit (BER), símbolos adjacentes na constelação diferem por **exatamente 1 bit**.

#### QPSK (4-PSK / 4-QAM)
| Dibit | Fase ($\theta$) | Coordenada $I$ | Coordenada $Q$ |
| :---: | :---: | :---: | :---: |
| **11** | $45^\circ$ ($\pi/4$) | $+1/\sqrt{2}$ | $+1/\sqrt{2}$ |
| **10** | $135^\circ$ ($3\pi/4$) | $-1/\sqrt{2}$ | $+1/\sqrt{2}$ |
| **00** | $225^\circ$ ($5\pi/4$) | $-1/\sqrt{2}$ | $-1/\sqrt{2}$ |
| **01** | $315^\circ$ ($7\pi/4$) | $+1/\sqrt{2}$ | $-1/\sqrt{2}$ |

#### 16-QAM (Tabela Exata dos Quadribits)
Coordenadas discretas no plano complexo: $I, Q \in \left\{ \pm \frac{1}{3\sqrt{2}}, \pm \frac{1}{\sqrt{2}} \right\}$.

| Quadribit | Coordenada $Q$ | Coordenada $I$ | Amplitude ($A_j$) | Fase ($\theta_i$) |
| :---: | :---: | :---: | :---: | :---: |
| **0000** | $-1/3\sqrt{2}$ | $-1/3\sqrt{2}$ | $0,33$ | $225^\circ$ |
| **0001** | $-1/\sqrt{2}$ | $-1/3\sqrt{2}$ | $0,75$ | $255^\circ$ |
| **0010** | $-1/3\sqrt{2}$ | $-1/\sqrt{2}$ | $0,75$ | $195^\circ$ |
| **0011** | $-1/\sqrt{2}$ | $+1/\sqrt{2}$ | $1,00$ | $225^\circ$ |
| **0100** | $+1/3\sqrt{2}$ | $-1/3\sqrt{2}$ | $0,33$ | $135^\circ$ |
| **0101** | $+1/\sqrt{2}$ | $-1/3\sqrt{2}$ | $0,75$ | $105^\circ$ |
| **0110** | $+1/3\sqrt{2}$ | $-1/\sqrt{2}$ | $0,75$ | $165^\circ$ |
| **0111** | $-1/\sqrt{2}$ | $-1/\sqrt{2}$ | $1,00$ | $135^\circ$ |
| **1000** | $-1/3\sqrt{2}$ | $+1/3\sqrt{2}$ | $0,33$ | $315^\circ$ |
| **1001** | $-1/\sqrt{2}$ | $+1/3\sqrt{2}$ | $0,75$ | $285^\circ$ |
| **1010** | $-1/3\sqrt{2}$ | $+1/\sqrt{2}$ | $0,75$ | $345^\circ$ |
| **1011** | $+1/\sqrt{2}$ | $+1/3\sqrt{2}$ | $0,75$ | $75^\circ$ |
| **1100** | $+1/3\sqrt{2}$ | $+1/3\sqrt{2}$ | $0,33$ | $45^\circ$ |
| **1101** | $+1/\sqrt{2}$ | $+1/3\sqrt{2}$ | $0,75$ | $75^\circ$ |
| **1110** | $+1/3\sqrt{2}$ | $+1/\sqrt{2}$ | $0,75$ | $15^\circ$ |
| **1111** | $+1/\sqrt{2}$ | $+1/\sqrt{2}$ | $1,00$ | $45^\circ$ |

---

## 3. Teoremas de Capacidade do Canal

1. **Teorema de Nyquist (Canal Ideal sem Ruído)**:
   $$C = 2 \cdot B \cdot \log_2 M \quad \text{(bits/s)}$$
   * $B$: Largura de banda do canal (Hz).
   * $M$: Número de níveis discretos de sinalização (símbolos).

2. **Teorema de Shannon (Canal Ruidoso AWGN)**:
   $$C = B \cdot \log_2 (1 + \text{SNR}) \quad \text{(bits/s)}$$
   * $\text{SNR} = \frac{S}{N}$ (em escala linear, onde $\text{SNR}_{\text{linear}} = 10^{\text{SNR}_{\text{dB}}/10}$).

---

## 4. Camada de Enlace: Detecção e Correção de Erros

### 4.1 Bit de Paridade
* **Paridade Par**: Adiciona bit $P$ tal que a soma $\sum b_i + P \equiv 0 \pmod 2$.
* **Paridade Ímpar**: Adiciona bit $P$ tal que a soma $\sum b_i + P \equiv 1 \pmod 2$.
* Detecta qualquer número ímpar de erros em um bloco.

---

### 4.2 Entrelaçamento (Interleaving) para Tratar Erros em Rajada (Burst Errors)
O entrelaçamento por matriz rearranja a ordem de transmissão dos bits para transformar uma rajada contínua de erros no canal em erros individuais isolados em múltiplos blocos/palavras de código.

#### Algoritmo de Implementação (Matriz $M \times N$):
1. **Formatação**: Arrumar os dados em uma matriz de $M$ linhas e $N$ colunas.
2. **Cálculo de Redundância**: Calcular 1 bit de paridade **por coluna** (a última linha $M+1$ contém os $N$ bits de paridade das colunas).
3. **Transmissão (Escrita por Linhas)**: Transmitir a matriz **linha por linha**, da esquerda para a direita, de cima para baixo (Linha 1, Linha 2, ..., Linha $M+1$).
4. **Recepção (Leitura/Reconstrução)**: Reconstruir a matriz $M \times (N)$ preenchendo-a linha por linha na ordem de chegada.
5. **Decodificação**: Recalcular a paridade de cada **coluna**.
   * *Efeito*: Uma rajada de erro contínua de tamanho até $N$ bits no canal atinge no máximo **1 bit por coluna** da matriz, permitindo a detecção/correção simples por coluna.

---

### 4.3 Checksum
* Adiciona no final da mensagem o complemento da soma dos blocos de dados.
* O receptor soma toda a palavra de código recebida (dados + checksum). Se o resultado final for zero (ou complementado igual a zero), a mensagem é aceita.

---

### 4.4 Código de Redundância Cíclica (CRC / Código Polinomial)

Baseado em aritmética polinomial Módulo 2 (operações XOR sem vai-um/empréstimo).

#### Regras do Polinômio Gerador $G(x)$:
* Polinômio de grau $k$. O divisor tem $k+1$ bits.
* Os bits mais significativo (MSB) e menos significativo (LSB) de $G(x)$ devem ser obrigatoriamente iguais a `1`.

#### Algoritmo do Transmissor:
1. Dada a mensagem binária $M(x)$ de $m$ bits e o gerador $G(x)$ de $k+1$ bits.
2. Deslocar $M(x)$ em $k$ posições para a esquerda (anexar $k$ zeros ao final dos dados): $M'(x) = M(x) \cdot x^k$.
3. Realizar a divisão polinomial Módulo 2 de $M'(x)$ por $G(x)$.
4. O resto da divisão $R(x)$ (com $k$ bits) é o valor do CRC.
5. Transmitir o quadro final: $T(x) = M'(x) \oplus R(x)$ (dados seguidos pelo CRC).

#### Algoritmo do Receptor:
1. Receber o quadro $T'(x)$.
2. Dividir $T'(x)$ por $G(x)$ em Módulo 2.
3. Se Resto $= 0 \rightarrow$ Quadro sem erros detectados.
4. Se Resto $\neq 0 \rightarrow$ Erro detectado (quadro descartado).

---

### 4.5 Código de Hamming (11, 7) - Correção de Erro Individual (FEC)

O código de Hamming adiciona $r$ bits de paridade a $m$ bits de dados, ocupando posições que são **potências de 2** ($1, 2, 4, 8, \dots$).

#### Estrutura do Vetor (11, 7):
| Pos | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bit** | **P1** | **P2** | M3 | **P4** | M5 | M6 | M7 | **P8** | M9 | M10 | M11 |

#### Regras para Cálculo de Paridade (Par):
A posição binária de cada bit determina quais bits de paridade o cobrem:
* **P1** (Posição 0001): Cobre bits cuja posição binária possui bit 0 ativo (1, 3, 5, 7, 9, 11).
  $$P1 = M3 \oplus M5 \oplus M7 \oplus M9 \oplus M11$$
* **P2** (Posição 0010): Cobre bits cuja posição binária possui bit 1 ativo (2, 3, 6, 7, 10, 11).
  $$P2 = M3 \oplus M6 \oplus M7 \oplus M10 \oplus M11$$
* **P4** (Posição 0100): Cobre bits cuja posição binária possui bit 2 ativo (4, 5, 6, 7).
  $$P4 = M5 \oplus M6 \oplus M7$$
* **P8** (Posição 1000): Cobre bits cuja posição binária possui bit 3 ativo (8, 9, 10, 11).
  $$P8 = M9 \oplus M10 \oplus M11$$

#### Algoritmo do Receptor (Síndrome de Erro):
1. Calcule os bits de verificação $s_1, s_2, s_4, s_8$ incluindo o próprio bit de paridade recebido:
   * $s_1 = P1 \oplus M3 \oplus M5 \oplus M7 \oplus M9 \oplus M11$
   * $s_2 = P2 \oplus M3 \oplus M6 \oplus M7 \oplus M10 \oplus M11$
   * $s_4 = P4 \oplus M5 \oplus M6 \oplus M7$
   * $s_8 = P8 \oplus M9 \oplus M10 \oplus M11$
2. Monte a Síndrome $S = (s_8 s_4 s_2 s_1)_2$.
3. **Decisão**:
   * Se $S = 0 \rightarrow$ Nenhum erro detectado.
   * Se $S > 0 \rightarrow$ O valor decimal de $S$ indica a **posição exata do bit corrompido** (1 a 11). Inverta o bit nessa posição para corrigir!

---

## 5. Subcamada MAC e Protocolos de Controle de Acesso ao Meio

### 5.1 Protocolos de Janela Deslizante (Sliding Window)
* **Stop-and-Wait**: Janela do emissor $= 1$, janela do receptor $= 1$. Aguarda ACK antes do próximo envio.
* **Go-Back-N**: Janela do emissor $W > 1$, janela do receptor $= 1$. Se ocorrer erro em um quadro, todos os quadros a partir dele são descartados pelo receptor e retransmitidos pelo emissor após timeout.
* **Retransmissão Seletiva (Selective Repeat)**: Janela do emissor $W > 1$, janela do receptor $W > 1$. Armazena quadros fora de ordem em buffer e retransmite individualmente apenas o quadro solicitado via NAK/timeout.
* **Piggybacking**: Técnica Full-Duplex que anexa a confirmação (ACK) no cabeçalho dos quadros de dados enviados no sentido oposto.

---

### 5.2 Algoritmos de Acesso Múltiplo (CSMA)

* **CSMA 1-Persistente**:
  * Escuta o canal. Se **livre**, transmite imediatamente ($\text{probabilidade } p=1$).
  * Se **ocupado**, continua escutando continuamente até ficar livre e transmite.

* **CSMA Não-Persistente**:
  * Escuta o canal. Se **livre**, transmite.
  * Se **ocupado**, aguarda um intervalo de tempo aleatório (backoff) antes de testar o canal novamente.

* **CSMA p-Persistente (Canais Slotted)**:
  * Escuta o canal. Se **livre**, transmite com probabilidade $p$, ou adia para o próximo slot com probabilidade $q = 1-p$.
  * Se **ocupado**, aguarda o próximo slot e repete a verificação.

* **CSMA/CD (Collision Detection - Base do IEEE 802.3 Ethernet)**:
  1. A estação monitora/escuta o meio físico **enquanto** realiza a transmissão.
  2. Se o sinal lido no cabo difere do sinal transmitido, uma **colisão** é detectada.
  3. A estação interrompe imediatamente a transmissão do quadro para economizar largura de banda e envia um sinal de *Jam*.
  4. Executa o algoritmo de recuo exponencial aleatório (Binary Exponential Backoff) antes de tentar retransmitir.

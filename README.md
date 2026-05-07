# Simulador TR1 — Camada Física e Camada de Enlace

Simulador educacional das camadas física e de enlace de um sistema de comunicação digital, desenvolvido como trabalho prático da disciplina de Redes de Telecomunicações 1 (TR1).

---

## Sumário

1. [O que o simulador faz](#o-que-o-simulador-faz)
2. [Como executar](#como-executar)
3. [Estrutura dos arquivos](#estrutura-dos-arquivos)
4. [Como funciona: visão geral](#como-funciona-visão-geral)
5. [Camada de Enlace](#camada-de-enlace)
   - [Enquadramento](#enquadramento)
   - [Detecção de erros](#detecção-de-erros)
   - [Correção de erros](#correção-de-erros)
6. [Camada Física](#camada-física)
   - [Modulações digitais (banda-base)](#modulações-digitais-banda-base)
   - [Modulações analógicas (por portadora)](#modulações-analógicas-por-portadora)
7. [Canal com ruído gaussiano](#canal-com-ruído-gaussiano)
8. [Interface gráfica](#interface-gráfica)
9. [Dependências](#dependências)

---

## O que o simulador faz

Imagine que você quer enviar a mensagem `"Hello TR1"` de um computador para outro. Na vida real, essa mensagem passa por várias etapas antes de virar um sinal elétrico no cabo (ou onda no ar). Este simulador reproduz essas etapas:

```
Mensagem em texto
      ↓
[Camada de Enlace] — divide em quadros e protege contra erros
      ↓
[Camada Física] — converte bits em sinal elétrico (Volts)
      ↓
[Canal] — adiciona ruído gaussiano ao sinal
      ↓
[Camada Física RX] — recupera os bits do sinal ruidoso
      ↓
[Camada de Enlace RX] — verifica/corrige erros e remonta a mensagem
      ↓
Mensagem recebida
```

O transmissor (TX) e o receptor (RX) rodam em **threads separadas**, simulando dois equipamentos independentes que se comunicam pelo canal.

---

## Como executar

### Pré-requisitos

- Python 3.10+
- Conda (recomendado) ou pip

### Instalação das dependências

```bash
conda install -c conda-forge pygobject gtk3 numpy matplotlib
```

### Executar o simulador

```bash
cd TrabalhoTR1
python Simulador.py
```

> No macOS, se a janela não aparecer, tente:
> ```bash
> GDK_BACKEND=quartz python Simulador.py
> ```

---

## Estrutura dos arquivos

```
TrabalhoTR1/
├── Simulador.py       Rotina principal — orquestra TX e RX em threads
├── CamadaFisica.py    Modulações e canal com ruído
├── CamadaEnlace.py    Enquadramento, detecção e correção de erros
├── InterfaceGUI.py    Interface gráfica GTK com gráficos de forma de onda
└── README.md          Este documento
```

Cada arquivo tem uma responsabilidade bem definida — nenhuma função de enquadramento fica em `CamadaFisica.py`, por exemplo. Isso segue o princípio de **modularização**.

---

## Como funciona: visão geral

O `Simulador.py` é o maestro. Quando você clica em **Transmitir** na interface, ele:

1. Pega a mensagem digitada e converte para bytes (`"Hello TR1"` → sequência de números de 0 a 255)
2. Passa para a thread do **Transmissor (TX)**:
   - Divide os bytes em quadros (enquadramento)
   - Acrescenta informação de detecção ou correção de erros (EDC)
   - Modula os bits em forma de onda elétrica (Volts)
   - Coloca o sinal numa fila (simulando o canal)
3. A thread do **Receptor (RX)** pega o sinal da fila:
   - Adiciona ruído gaussiano (simulando interferências reais)
   - Demodula o sinal de volta para bits
   - Verifica ou corrige os erros
   - Desenquadra e recupera a mensagem original
4. Os três sinais (TX, canal, RX) são exibidos como gráficos na interface

---

## Camada de Enlace

### Enquadramento

Antes de transmitir, os dados são divididos em **quadros** — pequenos pacotes com tamanho controlado. Isso facilita a detecção de onde começa e termina cada mensagem. Existem três técnicas disponíveis:

---

#### Contagem de caracteres

O primeiro byte de cada quadro diz quantos bytes o quadro tem no total (incluindo ele mesmo).

```
Exemplo com tamanho máximo de 4 bytes:
Dados: "ABCDE"  →  [5|A B C D] [2|E]
                    ↑ conta 5    ↑ conta 2
```

**Problema:** se esse byte inicial sofrer erro, todo o quadro fica desalinhado. Por isso existe a próxima técnica.

---

#### Flags + inserção de bytes (byte stuffing)

Cada quadro começa e termina com um byte especial chamado **flag** (`0x7E`). Se o próprio conteúdo da mensagem contiver o valor `0x7E`, um byte de escape (`0x7D`) é inserido antes, e o byte original é modificado com XOR `0x20`.

```
Flag = 0x7E,  Escape = 0x7D

Dado original:  [0x7E] → transmitido como: [0x7D][0x5E]
Dado original:  [0x7D] → transmitido como: [0x7D][0x5D]
Quadro final:   0x7E | ...payload stuffed... | 0x7E
```

O receptor reverte o processo ao receber.

---

#### Flags + inserção de bits (bit stuffing)

Funciona no nível dos bits. A flag é a sequência `01111110`. Para garantir que essa sequência nunca apareça nos dados, após **5 bits `1` consecutivos** no payload, um bit `0` é inserido automaticamente pelo transmissor. O receptor remove esses bits `0` inseridos.

```
Payload original:  0 1 1 1 1 1 1 0
Após stuffing:     0 1 1 1 1 1 [0] 1 0   ← bit 0 inserido após 5 uns
```

---

### Detecção de erros

Depois de enquadrar, o transmissor acrescenta uma assinatura matemática aos dados. Se durante o caminho algum bit for corrompido pelo ruído, essa assinatura não vai bater no receptor — sinalizando erro.

---

#### Bit de paridade par

O bit de paridade garante que o número total de bits `1` nos dados seja **par**. É a técnica mais simples, mas só detecta erros em números ímpares de bits corrompidos.

```
Dados:   1 0 1 1 0  → 3 bits 1 (ímpar) → paridade = 1
Enviado: 1 0 1 1 0 | 1
Receptor conta os 1s: se resultado for ímpar, houve erro.
```

---

#### Checksum

Soma todos os bytes do quadro como palavras de 16 bits em complemento de 1, e acrescenta o complemento dessa soma no final. No receptor, a soma de tudo (incluindo o checksum) deve dar `0xFFFF`.

```
Dados (simplificado): 0x4500 + 0x0034 + ... = soma
Checksum = complemento de 1 da soma
Receptor: soma + checksum = 0xFFFF → sem erro
```

É o mesmo mecanismo usado nos protocolos TCP/IP.

---

#### CRC-32 (IEEE 802)

O método mais robusto para detecção. Trata os dados como um grande número binário e faz uma **divisão polinomial** usando o polinômio padrão IEEE 802 (`0xEDB88320`). O resto dessa divisão (4 bytes) é anexado ao quadro.

```
CRC = resto de (dados ÷ polinômio)
Receptor refaz a divisão — se o resto ≠ 0, houve erro.
```

Detecta todos os erros em rajada de até 32 bits. É usado em Ethernet, ZIP, PNG, entre outros.

---

### Correção de erros

#### Código de Hamming

Diferente dos anteriores, o Hamming não só **detecta** o erro — ele **localiza e corrige** um bit errado automaticamente.

Funciona inserindo bits de paridade em posições específicas (potências de 2: 1, 2, 4, 8, …). Cada bit de paridade cobre um subconjunto dos bits de dados. Se um bit for corrompido, a combinação de paridades que falhou aponta exatamente a posição do erro.

```
Exemplo com 4 bits de dados (D):
Posições:  1   2   3   4   5   6   7
Conteúdo: [P1][P2][D1][P4][D2][D3][D4]

P1 cobre posições 1,3,5,7
P2 cobre posições 2,3,6,7
P4 cobre posições 4,5,6,7

Se P1 e P2 falham mas P4 não → erro na posição 1+2 = 3 → corrige o bit 3
```

---

## Camada Física

### Modulações digitais (banda-base)

Representam bits diretamente como níveis de tensão, sem portadora.

---

#### NRZ-Polar (Non-Return to Zero Polar)

O mais simples. Bit `1` = tensão positiva (+A Volts), bit `0` = tensão negativa (−A Volts). A tensão não retorna a zero entre bits.

```
Bits:   1    0    1    1    0
       ___       ___  ___
+1V   |   |     |   ||   |
      |   |     |   ||   |
 0V   |   |     |   ||   |
      |   |_____|   ||   |___
-1V
```

**Problema:** longas sequências de 0s ou 1s não geram transições, dificultando a sincronização.

---

#### Manchester

Cada bit é representado por uma **transição no meio do período**:
- Bit `1` → transição de −A para +A
- Bit `0` → transição de +A para −A

```
Bits:   1         0         1
       _____             _____
+1V   |     |           |     |
      |     |           |     |
 0V   |     |           |     |
      |     |_____|     |     |
-1V               |_____|
```

Sempre tem transição → facilita sincronização. Usado na Ethernet clássica (10BASE-T).

---

#### Bipolar (AMI — Alternate Mark Inversion)

- Bit `0` → 0 Volts
- Bit `1` → alterna entre +A e −A a cada ocorrência

```
Bits:   0    1    0    1    1    0
       0V   _    0V        _    0V
            |              |
           +1V
                      -1V
```

Garante que a média DC do sinal seja zero — importante para alguns meios de transmissão.

---

### Modulações analógicas (por portadora)

Usam uma onda senoidal de alta frequência (portadora) e **variam alguma característica** dela para representar os bits.

A portadora tem a forma: `A · cos(2πft + φ)`

Onde:
- `A` = amplitude (Volts)
- `f` = frequência (Hz)
- `φ` = fase (graus)

---

#### ASK (Amplitude Shift Keying)

Varia a **amplitude**:
- Bit `1` → portadora com amplitude A
- Bit `0` → portadora com amplitude 0 (silêncio)

```
Bit 1: ~~~~~~~~~~~   Bit 0: (silêncio)
```

Simples, mas sensível a ruído (que afeta diretamente a amplitude).

---

#### FSK (Frequency Shift Keying)

Varia a **frequência**:
- Bit `1` → frequência alta (ex: 15 Hz)
- Bit `0` → frequência baixa (ex: 5 Hz)

```
Bit 1: ~~~~~~  (ondas mais juntas)
Bit 0: ~~~     (ondas mais espaçadas)
```

Mais resistente a ruído que ASK. Usado em modems antigos e rádio FM de dados.

---

#### PSK (Phase Shift Keying) / BPSK

Varia a **fase**:
- Bit `1` → fase 0° (cos normal)
- Bit `0` → fase 180° (cos invertido)

```
Bit 1:  /\/\/\    Bit 0:  \/\/\/
```

---

#### QPSK (Quadrature Phase Shift Keying)

Varia a fase em 4 valores (0°, 90°, 180°, 270°), codificando **2 bits por símbolo**.

| Bits | Fase |
|------|------|
| 11   | 0°   |
| 10   | 90°  |
| 00   | 180° |
| 01   | 270° |

Dobra a eficiência espectral em relação ao BPSK. Muito usado em Wi-Fi e 4G.

---

#### 16-QAM (Quadrature Amplitude Modulation)

Combina variação de amplitude **e** fase, criando uma constelação de 16 pontos. Cada símbolo representa **4 bits**.

```
Constelação 16-QAM (coordenadas I/Q):

Q
↑
3  ·  ·  ·  ·
1  ·  ·  ·  ·
-1 ·  ·  ·  ·
-3 ·  ·  ·  ·
   -3 -1  1  3 → I
```

Alta eficiência espectral, mas requer boa relação sinal-ruído. Usado em Wi-Fi 802.11n/ac e cabo.

---

## Canal com ruído gaussiano

O canal é modelado como um **AWGN (Additive White Gaussian Noise)** — o modelo de ruído mais usado em telecomunicações.

O sinal recebido é:

```
r(t) = s(t) + n(t)
```

Onde:
- `s(t)` = sinal transmitido (em Volts)
- `n(t)` = ruído gaussiano com média 0 e desvio padrão σ (em Volts)

O parâmetro **σ (sigma)** é configurável na interface. Quanto maior o σ, mais ruído e mais provável é ocorrer erro de bit.

```
σ = 0.0 → sem ruído (canal ideal)
σ = 0.1 → ruído leve
σ = 0.5 → ruído moderado
σ = 1.0 → ruído severo (muitos erros)
```

---

## Interface gráfica

A interface é construída com **GTK3** (via PyGObject) e os gráficos com **matplotlib** embutido na janela GTK.

### Painel esquerdo — Configurações

| Campo | Descrição |
|-------|-----------|
| Mensagem | Texto a ser transmitido |
| Tamanho máx. do quadro | Máximo de bytes por quadro antes de fragmentar |
| Tamanho EDC | Tamanho do código de detecção (referência informativa) |
| Enquadramento | Técnica usada para delimitar os quadros |
| Detecção/Correção | Algoritmo de proteção contra erros |
| Modulação digital | Modulação banda-base (NRZ-Polar, Manchester, Bipolar) |
| Modulação analógica | Modulação por portadora (ASK, FSK, PSK, QPSK, 16-QAM) |
| Ruído σ (V) | Intensidade do ruído gaussiano no canal |

### Painel direito — Gráficos

Após clicar em **Transmitir**, três formas de onda são exibidas:

1. **Sinal Transmitido (TX)** — forma de onda gerada pelo transmissor (em Volts)
2. **Sinal no Canal** — o mesmo sinal após adição do ruído gaussiano
3. **Sinal Recebido (RX)** — sinal após demodulação no receptor

### Status

Abaixo das configurações aparece o resultado:
- `RX: "Hello TR1" ✓ (sem erros)` — mensagem recebida corretamente
- `RX: "H?llo TR1" ✗ (erro detectado)` — erro detectado pelo EDC

---

## Dependências

| Biblioteca | Uso |
|-----------|-----|
| `numpy` | Geração e processamento de sinais (arrays de Volts) |
| `matplotlib` | Renderização dos gráficos de forma de onda |
| `PyGObject` + `gtk3` | Interface gráfica GTK3 |
| `threading` | TX e RX em threads separadas |
| `queue` | Comunicação entre thread TX e thread RX |
| `struct` | Empacotamento de bytes para checksum e CRC |

Instalação via conda (recomendado):
```bash
conda install -c conda-forge pygobject gtk3 numpy matplotlib
```

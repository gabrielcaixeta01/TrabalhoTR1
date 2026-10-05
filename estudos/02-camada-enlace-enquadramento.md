# Camada de Enlace — Enquadramento (Framing)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides de enlace do prof. Marotta + enunciado (seção 1.3).
> Mapeado no código: `camada_enlace.py`, seção "[1/3] ENQUADRAMENTO".
>
> **Nota:** as seções 0 a 8 explicam o que cada técnica é e para que serve; a seção 9 traz o código de
> referência testado. Detalhes confirmados nos slides: `docs/referencias/referencia-slides-detalhes.md`.

---

## 0. O problema: por que enquadrar?

A camada física entrega ao receptor um **fluxo contínuo de bits**, sem "espaços". Mas a camada de
enlace precisa trabalhar com **quadros** (frames) — pedaços com começo e fim bem definidos, para poder
aplicar detecção de erro, confirmar recebimento etc.

**Enquadrar** = marcar onde cada quadro começa e termina dentro do fluxo de bits.
O desafio é: como o receptor sabe onde um quadro acaba, se os dados podem conter **qualquer**
sequência de bits — inclusive uma que pareça um delimitador?

Quatro técnicas resolvem isso (todas exigidas no trabalho):

1. **Contagem de caracteres** — diz no cabeçalho quantos bytes vêm.
2. **Entrelaçamento de bits** — intercala os bits de vários quadros (seção 8).
3. **FLAGs + inserção de bytes** (byte stuffing) — delimitadores + escape de bytes.
4. **FLAGs + inserção de bits** (bit stuffing) — delimitadores + escape de bits.

> No projeto, cada função de TX recebe uma **lista de payloads** (cada um já alinhado em bytes) e
> devolve o **fluxo único de bits**. A função de RX faz o inverso. A divisão da mensagem em blocos de
> `tam_max_quadro` bytes acontece antes, em `transmitir()` (ver arquivo 05).

---

## 1. Contagem de caracteres (character count)

**Ideia:** o primeiro campo do quadro é um **cabeçalho** que diz quantos bytes de dados vêm a seguir.
O receptor lê esse número e sabe exatamente quantos bytes consumir antes do próximo quadro.

```
┌────────┬──────────────────────┐
│ 1 byte │  payload (N bytes)   │
│ = N+1  │                      │
└────────┴──────────────────────┘
```

**Vantagem:** simples, sem overhead de escape.
**Desvantagem clássica (cai em prova):** se o **byte de contagem for corrompido** pelo ruído, o
receptor conta o número errado de bytes e **perde o sincronismo de TODOS os quadros seguintes** —
não há como se recuperar. Por isso, na prática, raramente é usada sozinha.

### No projeto

Pelos slides (`TR1_08`, 28-30) o cabeçalho tem **1 byte** e a contagem **inclui o próprio byte de
cabeçalho**: para enviar 2 bytes de dados, o cabeçalho vale **3**. Como o cabeçalho tem **8 bits**, o quadro
inteiro (cabeçalho + payload) tem no máximo **255 bytes**, ou seja, até 254 bytes de payload — limite
validado em `transmitir()` (lança `ValueError` se o quadro final, já com EDC e Hamming, passar disso).

No desenquadramento há um detalhe ligado à camada física: 8PSK e 32-QAM completam o fim do fluxo com
**zeros de enchimento** para fechar símbolos inteiros (ver arquivo 01). Um quadro real nunca tem 0 bytes,
então um cabeçalho `0x00` sinaliza "acabaram os quadros, o resto é enchimento" e o receptor para de ler.
Todo protocolo de enquadramento precisa ignorar esse lixo final sem inventar quadros.

---

## 2. FLAGs + inserção de bytes (byte stuffing)

**Ideia:** delimitar cada quadro com um byte especial, a **FLAG** (`0x7E = 01111110`, padrão HDLC/PPP).
O receptor sabe que o quadro vai de uma FLAG até a próxima.

```
┌──────┬──────────────────────┬──────┐
│ FLAG │  payload (escapado)  │ FLAG │
│ 0x7E │                      │ 0x7E │
└──────┴──────────────────────┴──────┘
```

**Problema:** e se o byte `0x7E` aparecer **dentro dos dados**? O receptor pensaria que o quadro acabou.
**Solução — escape (stuffing):** define-se um byte de escape **ESC** (`0x7D`). Sempre que um byte de
dado for igual à FLAG **ou** ao ESC, insere-se um ESC **antes** dele. Assim:

- `0x7E` nos dados vira `0x7D 0x7E` → o receptor vê o ESC e sabe que o `0x7E` seguinte é dado, não delimitador.
- `0x7D` nos dados vira `0x7D 0x7D` → idem (precisa escapar o próprio escape, senão dava ambiguidade).

### No projeto — transmissor

Abre o quadro com uma FLAG, percorre o payload byte a byte inserindo um ESC antes de cada byte que seja
FLAG ou ESC, e fecha com outra FLAG. Exemplo: dados `41 7E 42` viram `7E 41 7D 7E 42 7E`.

### No projeto — receptor (máquina de estados)

A leitura é uma **máquina de estados** com duas informações de controle: "estou dentro de um quadro?" e
"o byte anterior foi um ESC?". Os três estados implícitos: **fora de quadro** (procurando FLAG de abertura), **dentro normal**
(lendo dados, atento a ESC e FLAG), e **dentro escapado** (o byte atual é dado literal, seja ele FLAG ou ESC).

**Vantagem:** sincronismo se recupera (basta achar a próxima FLAG).
**Desvantagem:** overhead variável — no pior caso (payload cheio de FLAGs/ESCs) o quadro quase **dobra**.

> **Cai em prova:** por que escapar também o ESC? Porque, sem isso, ao ver um ESC o receptor não saberia
> se ele é "escape de verdade" ou um byte de dado igual a `0x7D`. Escapar o ESC remove a ambiguidade.

---

## 3. FLAGs + inserção de bits (bit stuffing)

**Ideia:** o delimitador é o **padrão de bits** `01111110` (= `0x7E`, a mesma FLAG, mas agora pensada
bit a bit). O truque é garantir que esse padrão **nunca apareça dentro dos dados** — não escapando
bytes, mas **bits**.

**Regra de stuffing:** ao transmitir, sempre que aparecerem **cinco bits `1` consecutivos** nos dados,
insere-se um `0` logo depois. Como a FLAG tem **seis** `1`s seguidos (`0111111​0`), e os dados nunca
terão mais de cinco `1`s seguidos depois do stuffing, o padrão da FLAG fica reservado só para o delimitador.

```
TX:  ...0 1 1 1 1 1 [insere 0] 1...      (cinco 1s -> mete um 0)
RX:  ...0 1 1 1 1 1 [remove 0] 1...      (depois de cinco 1s, descarta o 0 seguinte)
```

### No projeto — transmissor

Percorre os bits do payload contando quantos `1`s seguidos já passaram; ao chegar a cinco, insere um `0`
e zera a contagem. Coloca a FLAG `01111110` antes e depois.

### No projeto — receptor

Procura uma FLAG de abertura deslizando uma janela de 8 bits, depois a FLAG de fechamento. Entre as duas
refaz a contagem de `1`s seguidos: depois de cinco, o próximo bit (um `0`) foi inserido pelo transmissor
e é descartado. Cada trecho vira um payload; a busca continua depois da FLAG de fechamento.

**Vantagem sobre byte stuffing:** funciona em **nível de bit**, então não depende de alinhamento em
bytes nem de tabela de caracteres — é o que o HDLC real usa.
**Overhead:** no pior caso (payload só de `1`s) insere-se 1 bit a cada 5 → ~20% de aumento. É justamente
o caso crítico que o `testes.py` cobre (`[[1]*40]`).

> **Cai em prova:** por que cinco 1s e não seis? Porque a FLAG é `0111111​0` (seis 1s). Cortando em cinco,
> garante-se que jamais se formem seis 1s seguidos nos dados, então a FLAG nunca é "imitada".

---

## 4. Quadro comparativo (cola de prova)

| Técnica | Como delimita | Overhead | Falha característica | Recupera sincronismo? |
|---|---|---|---|---|
| Contagem de caracteres | nº de bytes no cabeçalho | mínimo (1 byte) | 1 byte de contagem corrompido bagunça **todos** os quadros seguintes | ❌ não |
| FLAGs + byte stuffing | FLAG 0x7E + escape de bytes | variável (dobra no pior caso) | precisa de alinhamento em bytes | ✅ sim (acha próxima FLAG) |
| FLAGs + bit stuffing | padrão 01111110 + insere 0 após cinco 1s | ~20% no pior caso | — (mais robusta) | ✅ sim |

---

## 5. Onde isso entra no pipeline do trabalho

No transmissor (`transmitir`, arquivo 05), o enquadramento é a **última etapa** antes da física:

```
bits da aplicação → [divide em blocos] → [+ EDC] → [+ Hamming] → [ENQUADRA] → física
```

No receptor (`receber`), é a **primeira**:

```
física → [DESENQUADRA] → [Hamming corrige] → [EDC verifica] → bits da aplicação
```

A escolha (`contagem` | `entrelacamento` | `bytes` | `bits`) vem do combo "Tipo de enquadramento" da GUI.

---

## 6. Como testar e visualizar

### Teste automático (`testes.py`)
Para cada protocolo, enquadrar uma lista de payloads e desenquadrar deve devolver **exatamente** a mesma
lista. Os casos críticos são payload só de `1`s (força o bit stuffing), payload com `0x7E`/`0x7D`
(força o byte stuffing), quadros de tamanhos diferentes e zeros extras no fim do fluxo (padding).

### Experimento manual (recomendo, é muito didático)
Enquadre uma mensagem curta com cada técnica e imprima o fluxo de bits: dá para **ver** a FLAG, o
cabeçalho de contagem e os bits/bytes inseridos. Depois inverta um bit no meio do fluxo e observe o que
cada técnica recupera.

### Na GUI
1. Escolha cada tipo de enquadramento e observe, na aba **Transmissor**, os bits da camada de enlace
   ficarem **maiores** que os da aplicação (overhead de FLAGs / stuffing / cabeçalho).
2. Com **contagem**, se você forçar ruído alto sem correção, repare como o erro "vaza" para os quadros
   seguintes (perda de sincronismo) — exatamente a desvantagem teórica.
3. Compare o tamanho do fluxo entre `bytes` e `bits` para o mesmo texto: dá pra ver o overhead de cada um.

---

## 7. Pontos que o professor gosta de cobrar

1. **Desvantagem da contagem de caracteres**: corrupção do contador desincroniza tudo.
2. **Por que escapar o próprio ESC** no byte stuffing (ambiguidade).
3. **Por que cinco 1s** no bit stuffing (a FLAG tem seis 1s).
4. **FLAG = 0x7E = 01111110** e ESC = 0x7D (origem HDLC/PPP).
5. Bit stuffing é **independente de alinhamento de byte**; byte stuffing não.
6. Cálculo de **overhead no pior caso** de cada técnica.
7. **Por que o entrelaçamento por matriz ajuda contra rajadas** (no máximo 1 bit errado por coluna) e o que ele não faz.
8. Na contagem de caracteres, a contagem **inclui** o byte de cabeçalho (2 bytes de dados -> valor 3).

---

## 8. Entrelaçamento de bits (interleaving) — o 4º protocolo do enunciado

> Fonte: slides `TR1_09`, 23-24 (ver `docs/referencias/referencia-slides-detalhes.md`).

**Problema:** o canal real erra em **rajadas** (vários bits seguidos errados). Uma paridade simples sobre
o quadro inteiro não percebe um erro par, e uma rajada pode destruir um bloco inteiro.

**Algoritmo dos slides:**

1. Arrumar os dados em uma **matriz** de M linhas × N colunas.
2. Calcular **1 bit de paridade por coluna** e colocá-lo numa linha extra (a linha M+1).
3. Transmitir **linha por linha**, de cima para baixo e da esquerda para a direita; a última linha enviada
   é a de paridade.
4. O receptor remonta a matriz preenchendo linha a linha, **recalcula a paridade de cada coluna** e compara.

```
dados (M x N)            paridade por coluna
1 0 0 1 1 1 0
1 1 0 0 1 0 1
...  (7 linhas)    ->    1 0 1 1 1 1 0     (exemplo 7x7 do slide 24)
```

**Por que ajuda contra rajadas:** como as linhas são enviadas em sequência, uma rajada de até N bits
seguidos atinge **no máximo 1 bit por coluna**. Cada coluna tem então no máximo um erro, que a paridade da
coluna consegue **detectar** (sinalizando qual coluna está ruim).

**Limites (cai em prova):** a paridade por coluna só detecta número ímpar de erros por coluna; com um erro por
coluna ela localiza a coluna, mas não a linha. Os slides apresentam isso na seção de *detecção* e **não
dizem** como escolher N, como delimitar o quadro nem como tratar padding.

**Decisões do grupo (documentar no relatório):** o código de referência usa N = 8 (cada linha é um byte, a
linha de paridade é 1 byte e o quadro continua alinhado em bytes) e delimita o quadro pela contagem de
caracteres. Como a transmissão é por linhas, a ordem dos bits não muda; o que se ganha é a paridade por coluna.
Se o grupo preferir um entrelaçamento "de verdade" (transmitir por colunas, ou intercalar vários quadros), é
uma extensão que precisa ser justificada no relatório.

**Para testar:** o exemplo 7×7 do slide 24 deve gerar a linha de paridade `1011110`; inverter um bit de uma
coluna deve fazer `desentrelacar` apontar essa coluna; e o padding de zeros no fim do fluxo não pode virar
quadro (cabeçalho 0).

---

## 9. Código de referência — `camada_enlace.py` (enquadramento)

> Código **testado** (ida e volta, com e sem ruído, e a simulação completa), no mesmo formato das
> assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha antes de
> colar; o professor pergunta.


### Utilitários de bits

```python
# ------------------------------ utilitários -------------------------------
def bits_para_bytes(bits):
    """Lista de bits (múltiplo de 8) -> lista de inteiros 0..255."""
    resultado = []
    for i in range(0, len(bits), 8):
        byte = 0
        for b in bits[i:i + 8]:
            byte = (byte << 1) | b
        resultado.append(byte)
    return resultado


def bytes_para_bits(lista_bytes):
    """Lista de inteiros 0..255 -> bits, MSB primeiro."""
    bits = []
    for byte in lista_bytes:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits
```


### Contagem de caracteres

Pelos slides (`TR1_08`, 28-30) o cabeçalho tem 1 byte e a contagem **inclui o próprio cabeçalho**: 2 bytes de dados -> cabeçalho vale 3. Por isso o payload máximo é de 254 bytes.

```python
# ------------------------- contagem de caracteres -------------------------
def enquadrar_contagem(payloads):
    """Quadro = [contagem (1 byte)] + payload. A contagem INCLUI o próprio
    byte de cabeçalho (slides): 2 bytes de dados -> cabeçalho vale 3."""
    fluxo = []
    for payload in payloads:
        fluxo += bytes_para_bits([len(payload) // 8 + 1]) + payload
    return fluxo


def desenquadrar_contagem(bits):
    payloads, pos = [], 0
    while pos + 8 <= len(bits):
        contagem = bits_para_bytes(bits[pos:pos + 8])[0]
        pos += 8
        if contagem == 0:                   # padding da modulação: acabou
            break
        fim = pos + (contagem - 1) * 8      # a contagem inclui o cabeçalho
        if fim > len(bits):                 # quadro truncado
            break
        payloads.append(bits[pos:fim])
        pos = fim
    return payloads
```


### Inserção de bytes (byte stuffing)

```python
# -*- coding: utf-8 -*-
FLAG_BYTE = 0x7E
ESC_BYTE = 0x7D
# ------------------- FLAGs com inserção de bytes (stuffing) ---------------
def enquadrar_bytes(payloads):
    """Quadro = FLAG + payload (com ESC antes de FLAG/ESC) + FLAG."""
    fluxo = []
    for payload in payloads:
        quadro = [FLAG_BYTE]
        for byte in bits_para_bytes(payload):
            if byte in (FLAG_BYTE, ESC_BYTE):
                quadro.append(ESC_BYTE)
            quadro.append(byte)
        quadro.append(FLAG_BYTE)
        fluxo += bytes_para_bits(quadro)
    return fluxo


def desenquadrar_bytes(bits):
    payloads = []
    dentro, escapado, atual = False, False, []
    for byte in bits_para_bytes(bits[:len(bits) // 8 * 8]):
        if not dentro:
            if byte == FLAG_BYTE:
                dentro, atual = True, []
        elif escapado:
            atual.append(byte)
            escapado = False
        elif byte == ESC_BYTE:
            escapado = True
        elif byte == FLAG_BYTE:
            if atual:
                payloads.append(bytes_para_bits(atual))
            dentro = False
        else:
            atual.append(byte)
    return payloads
```


### Inserção de bits (bit stuffing)

```python
FLAG_BITS = [0, 1, 1, 1, 1, 1, 1, 0]
# -------------------- FLAGs com inserção de bits (stuffing) ---------------
def enquadrar_bits(payloads):
    """Quadro = FLAG + payload (0 após cinco 1s) + FLAG."""
    fluxo = []
    for payload in payloads:
        trem, uns = [], 0
        for bit in payload:
            trem.append(bit)
            uns = uns + 1 if bit == 1 else 0
            if uns == 5:
                trem.append(0)
                uns = 0
        fluxo += FLAG_BITS + trem + FLAG_BITS
    return fluxo


def desenquadrar_bits(bits):
    payloads, i, n = [], 0, len(bits)
    while i + 8 <= n:
        if bits[i:i + 8] != FLAG_BITS:
            i += 1
            continue
        j = i + 8                                   # procura a FLAG de fechamento
        while j + 8 <= n and bits[j:j + 8] != FLAG_BITS:
            j += 1
        if j + 8 > n:
            break
        payload, uns = [], 0
        for bit in bits[i + 8:j]:
            if uns == 5:                            # este é o 0 inserido: descarta
                uns = 0
                continue
            payload.append(bit)
            uns = uns + 1 if bit == 1 else 0
        if payload:
            payloads.append(payload)
        i = j + 8
    return payloads
```


### Entrelaçamento por matriz (slides `TR1_09`, 23-24)

Algoritmo dos slides: dados em matriz, paridade par **por coluna** na última linha, transmissão linha a linha (cima para baixo, esquerda para a direita). Vetor de teste: o exemplo 7x7 do slide 24 tem linha de paridade `1011110`. **Decisão de projeto** (`docs/DECISOES.md`; não consta nos slides): `n_colunas = 8` (cada linha é um byte, então a linha de paridade é 1 byte e o quadro continua alinhado em bytes) e delimitação do quadro pela contagem de caracteres. Como a transmissão é por linhas, a ordem dos bits não muda; o ganho é a paridade por coluna.

```python
# ---------------- entrelaçamento por matriz (slides, seção 4.2) -----------
def paridade_colunas(bits, n_colunas):
    """Paridade par de cada coluna de uma matriz de linhas de `n_colunas` bits."""
    paridades = [0] * n_colunas
    for k, bit in enumerate(bits):
        paridades[k % n_colunas] ^= bit
    return paridades


def entrelacar(bits, n_colunas):
    """Matriz M x N + linha de paridade por coluna, transmitida linha a linha."""
    if len(bits) % n_colunas != 0:
        raise ValueError("o nº de bits precisa ser múltiplo de n_colunas")
    return bits + paridade_colunas(bits, n_colunas)


def desentrelacar(bits, n_colunas):
    """Reconstrói a matriz e confere a paridade. Devolve (dados, colunas_com_erro)."""
    dados, recebida = bits[:-n_colunas], bits[-n_colunas:]
    calculada = paridade_colunas(dados, n_colunas)
    colunas_com_erro = [c for c in range(n_colunas) if calculada[c] != recebida[c]]
    return dados, colunas_com_erro


def enquadrar_entrelacamento(payloads, n_colunas=8):
    """Cada payload vira uma matriz (linhas de n_colunas bits) com a linha de
    paridade das colunas; o quadro é delimitado pela contagem de caracteres."""
    return enquadrar_contagem([entrelacar(p, n_colunas) for p in payloads])


def desenquadrar_entrelacamento(bits, n_colunas=8):
    """Inverso: desenquadra pela contagem e remove a linha de paridade das colunas."""
    return [desentrelacar(q, n_colunas)[0] for q in desenquadrar_contagem(bits)]
```


# Camada de Enlace — Enquadramento (Framing)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides de enlace do prof. Marotta + enunciado (seção 1.3).
> Mapeado no código: `camada_enlace.py`, seção "1) ENQUADRAMENTO".

---

## 0. O problema: por que enquadrar?

A camada física entrega ao receptor um **fluxo contínuo de bits**, sem "espaços". Mas a camada de
enlace precisa trabalhar com **quadros** (frames) — pedaços com começo e fim bem definidos, para poder
aplicar detecção de erro, confirmar recebimento etc.

**Enquadrar** = marcar onde cada quadro começa e termina dentro do fluxo de bits.
O desafio é: como o receptor sabe onde um quadro acaba, se os dados podem conter **qualquer**
sequência de bits — inclusive uma que pareça um delimitador?

Três técnicas resolvem isso (todas exigidas no trabalho):

1. **Contagem de caracteres** — diz no cabeçalho quantos bytes vêm.
2. **FLAGs + inserção de bytes** (byte stuffing) — delimitadores + escape de bytes.
3. **FLAGs + inserção de bits** (bit stuffing) — delimitadores + escape de bits.

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
│  = N   │                      │
└────────┴──────────────────────┘
```

**Vantagem:** simples, sem overhead de escape.
**Desvantagem clássica (cai em prova):** se o **byte de contagem for corrompido** pelo ruído, o
receptor conta o número errado de bytes e **perde o sincronismo de TODOS os quadros seguintes** —
não há como se recuperar. Por isso, na prática, raramente é usada sozinha.

### No projeto

```python
def enquadrar_contagem(payloads):
    for payload in payloads:
        n_bytes = len(payload) // 8
        fluxo += _bytes_para_bits([n_bytes])   # cabeçalho = nº de bytes
        fluxo += payload
```

Como o cabeçalho tem **8 bits**, o payload máximo por quadro é **255 bytes** — limite validado em
`transmitir()` (lança `ValueError` se o quadro final, já com EDC e Hamming, passar disso).

No desenquadramento há um detalhe esperto ligado à camada física:

```python
def desenquadrar_contagem(bits):
    while pos + 8 <= len(bits):
        n_bytes = _bits_para_bytes(bits[pos:pos+8])[0]
        pos += 8
        if n_bytes == 0:
            break   # byte 0x00 = padding do QPSK/16-QAM, não é quadro real
        ...
```

O `n_bytes == 0` serve para parar no **padding de zeros** que QPSK/16-QAM acrescentam para fechar
símbolos inteiros (ver arquivo 01). Um quadro real nunca tem 0 bytes, então um cabeçalho 0x00 sinaliza
"acabaram os quadros, o resto é enchimento".

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

```python
def enquadrar_bytes(payloads):
    for payload in payloads:
        quadro = [FLAG_BYTE]                    # abre
        for byte in _bits_para_bytes(payload):
            if byte in (FLAG_BYTE, ESC_BYTE):   # byte "perigoso"?
                quadro.append(ESC_BYTE)         # insere escape antes
            quadro.append(byte)
        quadro.append(FLAG_BYTE)                # fecha
```

### No projeto — receptor (máquina de estados)

A leitura é uma **máquina de estados** com duas flags de controle (`dentro`, `escapado`):

```python
def desenquadrar_bytes(bits):
    dentro, escapado, atual = False, False, []
    for byte in bytes_fluxo:
        if not dentro:
            if byte == FLAG_BYTE:   # achou início de quadro
                dentro, atual = True, []
            continue
        if escapado:                # byte logo após ESC = dado literal
            atual.append(byte); escapado = False
        elif byte == ESC_BYTE:
            escapado = True          # próximo byte é literal
        elif byte == FLAG_BYTE:      # FLAG de fechamento
            if atual: payloads.append(_bytes_para_bits(atual))
            dentro = False
        else:
            atual.append(byte)
```

Os três estados implícitos: **fora de quadro** (procurando FLAG de abertura), **dentro normal**
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

```python
def enquadrar_bits(payloads):
    for payload in payloads:
        stuffed, uns = [], 0
        for bit in payload:
            stuffed.append(bit)
            uns = uns + 1 if bit == 1 else 0    # conta 1s consecutivos
            if uns == 5:
                stuffed.append(0)               # insere o 0 de stuffing
                uns = 0
        fluxo += FLAG_BITS + stuffed + FLAG_BITS
```

### No projeto — receptor

```python
def desenquadrar_bits(bits):
    # acha FLAG de abertura, acha FLAG de fechamento, e no meio:
    payload, uns, k = [], 0, i + 8
    while k < j:
        bit = bits[k]
        if uns == 5:        # este 0 foi inserido pelo stuffing -> descarta
            uns = 0
        else:
            payload.append(bit)
            uns = uns + 1 if bit == 1 else 0
        k += 1
```

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

A escolha (`contagem` | `bytes` | `bits`) vem do combo "Tipo de enquadramento" da GUI.

---

## 6. Como testar e visualizar

### Teste automático (`testes.py`)
```python
payloads = [_bits_aleatorios(7) for _ in range(3)]
for tipo in ("contagem", "bytes", "bits"):
    fluxo = enlace._ENQUADRAR[tipo](payloads)
    assert enlace._DESENQUADRAR[tipo](fluxo) == payloads   # ida e volta

# casos críticos:
enlace.desenquadrar_bits(enlace.enquadrar_bits([[1]*40])) == [[1]*40]      # bit stuffing só de 1s
# byte stuffing com FLAG/ESC dentro do payload:
p = [enlace._bytes_para_bits([0x7E, 0x7D, 0x41, 0x7E])]
enlace.desenquadrar_bytes(enlace.enquadrar_bytes(p)) == p
```

### Experimento manual (recomendo, é muito didático)
```python
import camada_enlace as e

# byte stuffing: veja o ESC aparecer
p = [e._bytes_para_bits([0x7E, 0x41])]          # payload começa com a própria FLAG
fluxo = e.enquadrar_bytes(p)
print(e._bits_para_bytes(fluxo))                # observe: 7E 7D 7E 41 7E (ESC inserido!)

# bit stuffing: veja o 0 inserido
p = [[1,1,1,1,1,1,1,1]]                          # oito 1s
fluxo = e.enquadrar_bits(p)
print(fluxo)                                     # FLAG + 1 1 1 1 1 [0] 1 1 1 [0] + FLAG
```

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
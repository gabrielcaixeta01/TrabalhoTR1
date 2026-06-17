# Camada de Enlace — Detecção de Erros (Paridade, Checksum, CRC-32)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides de enlace do prof. Marotta + enunciado (seção 1.4).
> Mapeado no código: `camada_enlace.py`, seção "2) DETECÇÃO DE ERROS".

---

## 0. A ideia geral: EDC

O ruído do canal pode inverter bits. **Detecção de erros** acrescenta ao quadro um campo redundante
calculado a partir dos dados — o **EDC** (*Error Detecting Code*). No receptor, recalcula-se o EDC
sobre os dados recebidos e compara-se com o EDC recebido: se não baterem, **houve erro**.

> Detecção ≠ correção. Aqui só sabemos *que* errou, não *onde*. A correção (Hamming) é o arquivo 04.

As três técnicas exigidas, em ordem crescente de robustez:

| Técnica | Tamanho do EDC | Detecta |
|---|---|---|
| Bit de paridade par | 1 bit (1 byte alinhado) | nº **ímpar** de bits errados |
| Checksum (complemento de 1) | 16 bits (2 bytes) | a maioria dos erros, alguns escapam |
| CRC-32 | 32 bits (4 bytes) | praticamente todos os erros de rajada |

> **Decisão de projeto importante:** todos os EDCs geram saída **alinhada em bytes**, porque os
> enquadramentos de contagem e de bytes operam sobre bytes. Por isso a paridade vira **1 byte inteiro**
> (7 zeros + 1 bit de paridade), não 1 bit solto. Tabela `TAMANHO_EDC` no código:
> `{"nenhum":0, "paridade":1, "checksum":2, "crc":4}` (em bytes).

No projeto, no TX as funções `adicionar_*` **anexam** o EDC ao final do payload; no RX as `verificar_*`
devolvem `(payload_sem_edc, ok)`.

---

## 1. Bit de paridade par

**Ideia:** escolher 1 bit extra de modo que o número total de `1`s (dados + paridade) seja **par**.

- Se os dados têm um número par de 1s → bit de paridade = 0.
- Se ímpar → bit de paridade = 1 (para "fechar" em par).

No receptor, conta-se o total de 1s. Se for **ímpar**, houve erro.

**Limitação central (cai em prova):** detecta apenas um número **ímpar** de bits invertidos.
Se **dois** bits virarem (ou qualquer número par), a paridade volta a fechar e o erro passa
**despercebido**. É a detecção mais fraca.

### No projeto

```python
def adicionar_paridade_par(bits):
    paridade = sum(bits) % 2            # 1 se nº de 1s for ímpar
    return bits + [0]*7 + [paridade]    # 1 byte: 7 zeros + paridade (alinhamento)

def verificar_paridade_par(bits):
    ok = (sum(bits) % 2) == 0           # soma de TODOS os bits deve ser par
    return bits[:-8], ok                # remove o byte de paridade
```

Repare: como os 7 zeros não mudam a contagem de 1s, somar o byte inteiro no RX equivale a checar a
paridade do conjunto. O `% 2` é a forma aritmética do XOR de todos os bits.

---

## 2. Checksum (soma em complemento de 1, 16 bits)

É o **checksum da Internet** (mesmo usado em TCP/IP/UDP), feito exatamente como apresentado em aula.

**Ideia:**
1. Quebrar os dados em **palavras de 16 bits**.
2. Somá-las em **aritmética de complemento de 1**: sempre que a soma estoura 16 bits, o "vai-um"
   (carry) é **somado de volta** no resultado (*end-around carry*).
3. O checksum é o **complemento de 1** (inversão de todos os bits) dessa soma.

No receptor, soma-se tudo (dados + checksum) do mesmo jeito; o resultado deve dar **`0xFFFF`**
(todos os bits 1), porque o checksum é justamente o que "falta" para a soma saturar.

### No projeto

```python
def _soma_complemento1(palavras):
    soma = 0
    for p in palavras:
        soma += p
        soma = (soma & 0xFFFF) + (soma >> 16)   # reincorpora o carry (end-around)
    return soma

def adicionar_checksum(bits):
    soma = _soma_complemento1(_bits_para_palavras16(bits))
    checksum = (~soma) & 0xFFFF                  # complemento de 1
    return bits + _bytes_para_bits([checksum >> 8, checksum & 0xFF])

def verificar_checksum(bits):
    payload = bits[:-16]
    total = _soma_complemento1(_bits_para_palavras16(payload) +
                               _bits_para_palavras16(bits[-16:]))
    return payload, total == 0xFFFF              # deve saturar em 0xFFFF
```

**Mais forte que paridade**, porque considera o valor posicional dos bits (uma soma, não só contagem
de paridade). **Mas ainda falha** em alguns padrões — por exemplo, erros que se cancelam na soma
(um bit que some de valor X e outro que ganha X na posição complementar). Por isso o CRC é preferido
para detecção séria.

> **Cai em prova:** por que end-around carry? A aritmética de complemento de 1 não tem "estouro
> perdido": o carry do bit mais alto retorna ao bit mais baixo. Isso torna a soma comutativa/associativa
> independentemente da ordem das palavras, e é o que faz a verificação fechar em `0xFFFF`.

---

## 3. CRC-32 (IEEE 802)

A técnica de detecção mais robusta do trabalho. Baseada em **divisão polinomial em GF(2)**
(aritmética módulo 2, onde soma = subtração = XOR).

**Ideia conceitual:**
- Os bits da mensagem são vistos como os coeficientes de um **polinômio** `M(x)`.
- Define-se um **polinômio gerador** `G(x)` (para CRC-32 IEEE 802: grau 32, `0x04C11DB7`).
- Anexa-se 32 zeros à mensagem e divide-se por `G(x)` em GF(2). O **resto** dessa divisão é o CRC.
- Transmite-se `mensagem + CRC`. No receptor, divide-se tudo por `G(x)`: **resto 0 → sem erro**;
  resto ≠ 0 → erro detectado. (No projeto recalcula-se e compara, que é equivalente.)

**Por que é tão bom:** um gerador de grau 32 bem escolhido detecta: todos os erros de 1 e 2 bits,
qualquer número ímpar de erros, **todas as rajadas de até 32 bits**, e a esmagadora maioria das
rajadas maiores (probabilidade de passar ≈ `2⁻³²`). É por isso que é o padrão de Ethernet.

### No projeto (implementação refletida, bit a bit, **sem zlib**)

```python
_POLI_CRC32_REFLETIDO = 0xEDB88320   # forma refletida do 0x04C11DB7

def _calcular_crc32(bits):
    crc = 0xFFFFFFFF                  # registrador inicial (padrão)
    for i in range(0, len(bits), 8):
        for bit in reversed(bits[i:i+8]):    # processa LSB->MSB de cada byte
            if (crc ^ bit) & 1:
                crc = (crc >> 1) ^ _POLI_CRC32_REFLETIDO   # "subtrai" o gerador
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF           # XOR final (padrão)
```

Detalhes que o relatório menciona como decisões:
- Usa-se a **forma refletida** `0xEDB88320` com `init = 0xFFFFFFFF` e XOR final — exatamente o CRC-32
  padrão (Ethernet/zlib). A vantagem é poder **validar** contra um vetor conhecido.
- **Validação:** `CRC32("123456789") == 0xCBF43926`. (Confirmei rodando o código: bate certinho.)
- A divisão é feita **bit a bit** (sem tabela, sem `zlib`), respeitando a proibição do enunciado de
  importar bibliotecas externas para os algoritmos centrais.

```python
def verificar_crc32(bits):
    payload = bits[:-32]
    recebido = 0
    for b in bits[-32:]:
        recebido = (recebido << 1) | b
    return payload, _calcular_crc32(payload) == recebido
```

> **Cai em prova:** "GF(2)" significa aritmética módulo 2 → somar e subtrair são ambos **XOR**, sem
> vai-um. A "divisão" do CRC é uma sequência de XORs com o gerador. Não confunda com soma aritmética
> (que é o caso do checksum, onde o carry importa).

---

## 4. Quadro comparativo (cola de prova)

| Aspecto | Paridade par | Checksum (compl. 1) | CRC-32 |
|---|---|---|---|
| Tamanho do EDC | 1 bit (1 byte) | 16 bits (2 bytes) | 32 bits (4 bytes) |
| Operação base | XOR / contagem de 1s | soma com end-around carry | divisão polinomial em GF(2) |
| Detecta nº ímpar de erros | ✅ | ✅ | ✅ |
| Detecta nº par de erros | ❌ | parcial | ✅ (quase sempre) |
| Detecta rajadas | fraco | médio | ✅ até 32 bits sempre |
| Verificação no RX | soma total par | soma total = 0xFFFF | resto da divisão = 0 |
| Custo | baixíssimo | baixo | maior (mas barato com tabela) |

**Regra de bolso:** paridade = didática / detecção mínima; checksum = barato e razoável (Internet);
CRC = padrão industrial para enlace (Ethernet/Wi-Fi/HDLC).

---

## 5. Onde entra no pipeline e ordem em relação ao Hamming

Detalhe **importante** e que cai em prova — a ordem no TX (`transmitir`, arquivo 05):

```
payload → [1º: adiciona EDC] → [2º: codifica Hamming] → [3º: enquadra]
```

O **EDC vai primeiro, o Hamming depois**. Assim o Hamming protege **também** os bits do EDC.
No RX a ordem se inverte naturalmente:

```
desenquadra → [Hamming corrige] → [verifica EDC] → payload
```

Ou seja: o Hamming corrige o que puder, e **depois** o EDC confere se o que sobrou está íntegro.
Faz sentido: primeiro conserta, depois audita.

---

## 6. Como testar e visualizar

### Teste automático (`testes.py`)
```python
for tipo in ("paridade", "checksum", "crc"):
    com_edc = enlace._ADICIONAR_EDC[tipo](dados)
    payload, valido = enlace._VERIFICAR_EDC[tipo](com_edc)
    assert valido and payload == dados           # payload íntegro passa
    corrompido = com_edc[:]; corrompido[3] ^= 1  # inverte 1 bit
    _, valido = enlace._VERIFICAR_EDC[tipo](corrompido)
    assert not valido                            # detecta o erro

# CRC contra valor conhecido:
assert enlace._calcular_crc32(app.texto_para_bits("123456789")) == 0xCBF43926
```

### Experimento manual (mostra a limitação da paridade)
```python
import camada_enlace as e
dados = [1,0,1,1,0,0,1,0]

# paridade NÃO detecta 2 bits invertidos:
com = e.adicionar_paridade_par(dados)
com[0] ^= 1; com[1] ^= 1                 # inverte DOIS bits
print(e.verificar_paridade_par(com))     # (payload, True)  <- erro passou!

# CRC detecta o mesmo caso:
com = e.adicionar_crc32(dados)
com[0] ^= 1; com[1] ^= 1
print(e.verificar_crc32(com))            # (payload, False) <- pegou
```

### Na GUI
1. Escolha um EDC, ponha ruído moderado **sem** Hamming, e veja na aba **Receptor** o relatório por
   quadro indicando `EDC OK` ou erro detectado.
2. Repita com paridade vs CRC no mesmo nível de ruído: o CRC pega erros que a paridade deixa passar.
3. O tamanho dos bits da camada de enlace cresce conforme o EDC escolhido (1 / 2 / 4 bytes por quadro).

---

## 7. Pontos que o professor gosta de cobrar

1. **Limitação da paridade**: só detecta nº ímpar de erros (2 bits passam).
2. **Checksum**: soma em complemento de 1, **end-around carry**, verificação fecha em `0xFFFF`.
3. **CRC = divisão polinomial em GF(2)** (soma = XOR); resto 0 no RX = sem erro.
4. **CRC detecta toda rajada até o grau do gerador** (32 bits aqui).
5. Vetor de teste **`CRC32("123456789") = 0xCBF43926`** (prova de corretude).
6. **Ordem EDC → Hamming** no TX e por quê (Hamming protege o EDC também).
7. Diferença entre **detecção** (estas técnicas) e **correção** (Hamming).
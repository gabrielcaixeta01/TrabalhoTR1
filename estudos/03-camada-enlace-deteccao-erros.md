# Camada de Enlace — Detecção de Erros (Paridade, Checksum, CRC-32)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides de enlace do prof. Marotta + enunciado (seção 1.3).
> Mapeado no código: `camada_enlace.py`, seção "[2/3] DETECÇÃO DE ERROS".

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

O transmissor soma os bits do payload módulo 2 (o `% 2` é a forma aritmética do XOR de todos os bits) e
anexa um byte com 7 zeros e o bit de paridade. O receptor refaz a conta sobre payload + byte.

Repare: como os 7 zeros não mudam a contagem de 1s, somar o byte inteiro no RX equivale a checar a
paridade do conjunto.

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

O payload é dividido em palavras de 16 bits (completando com zeros se preciso), somado em complemento de
1, invertido e anexado em 2 bytes. Em Python o `~` produz número negativo, então é preciso mascarar com
`0xFFFF` para ficar com 16 bits. O receptor soma payload + checksum e confere se deu `0xFFFF`.

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

### No projeto (divisão módulo 2 pura, bit a bit, **sem zlib**)

É o algoritmo dos slides (`TR1_09`, 30-33): anexar k = 32 zeros à mensagem, dividir por G(x) em módulo 2 e
tomar o resto de 32 bits como CRC, que é anexado ao quadro (4 bytes). O receptor divide o quadro inteiro
(dados + CRC) por G(x): **resto 0 = sem erro**.

Implementação típica: um registrador de 32 bits; para cada bit da entrada (inclusive os 32 zeros) faz-se
"desloca e traz o próximo bit", e se o bit de grau 32 ficou ligado aplica-se XOR com G(x).

Detalhes que o relatório menciona como decisões:
- O gerador é o do padrão IEEE 802 (33 bits, `0x104C11DB7`). Os slides só mostram exemplos com polinômios
  pequenos (`x⁴ + x + 1`), então o polinômio do CRC-32 vem do enunciado.
- Os slides **não** falam de valor inicial, XOR final nem reflexão de bits. Por isso o CRC "puro" **não**
  dá o valor `0xCBF43926` para `"123456789"`. Esse valor é do CRC-32 padrão refletido (Ethernet/zlib), que
  o código de referência traz como variante opcional para validar o algoritmo contra um valor conhecido.
- A divisão é feita **bit a bit**, respeitando a proibição do enunciado de usar bibliotecas externas.

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
Para cada técnica: anexar o EDC e verificar deve aceitar o payload íntegro; inverter **um** bit deve ser
detectado. Para o CRC, também vale inverter uma rajada de até 32 bits (deve ser sempre detectada) e, se o
grupo mantiver a variante padrão, conferir `CRC32("123456789") = 0xCBF43926`.

### Experimento manual (mostra a limitação da paridade)
Anexe paridade a um payload e inverta **dois** bits: a verificação continua dando "ok" (erro passa
despercebido). Repita com checksum e CRC e compare.

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
5. Procedimento do CRC nos slides (anexar k zeros, dividir módulo 2, receptor com resto 0). O vetor `0xCBF43926` vale só para o CRC-32 padrão refletido.
6. **Ordem EDC → Hamming** no TX e por quê (Hamming protege o EDC também).
7. Diferença entre **detecção** (estas técnicas) e **correção** (Hamming).

---

## 9. Código de referência — `camada_enlace.py` (detecção de erros)

> Código **testado** (ida e volta, com e sem ruído, e a simulação completa), no mesmo formato das
> assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha antes de
> colar; o professor pergunta.


### Bit de paridade par

```python
# ------------------------------ paridade par ------------------------------
def adicionar_paridade_par(bits):
    """Anexa 1 byte: 7 zeros + bit de paridade par."""
    return bits + [0] * 7 + [sum(bits) % 2]


def verificar_paridade_par(bits):
    if len(bits) < 8:
        return bits, False
    return bits[:-8], sum(bits) % 2 == 0
```


### Checksum (complemento de 1, palavras de 16 bits)

O tamanho da palavra (16 bits) é decisão do grupo; o resumo dos slides não o especifica.

```python
# -------------------------------- checksum --------------------------------
def soma_complemento1(palavras):
    """Soma de 16 bits em complemento de 1 (end-around carry)."""
    soma = 0
    for palavra in palavras:
        soma += palavra
        soma = (soma & 0xFFFF) + (soma >> 16)
    return soma


def bits_para_palavras16(bits):
    """Bits -> palavras de 16 bits (completa com zeros à direita)."""
    bits = bits + [0] * ((-len(bits)) % 16)
    return [(b[0] << 8) | b[1] for b in
            (bits_para_bytes(bits[i:i + 16]) for i in range(0, len(bits), 16))]


def adicionar_checksum(bits):
    soma = soma_complemento1(bits_para_palavras16(bits))
    checksum = ~soma & 0xFFFF
    return bits + bytes_para_bits([checksum >> 8, checksum & 0xFF])


def verificar_checksum(bits):
    if len(bits) < 16:
        return bits, False
    payload = bits[:-16]
    total = soma_complemento1(bits_para_palavras16(payload)
                              + bits_para_palavras16(bits[-16:]))
    return payload, total == 0xFFFF
```


### CRC-32 como nos slides (divisão módulo 2 pura)

Segue o algoritmo do resumo: anexar 32 zeros, dividir módulo 2 por G(x), o resto é o CRC; o receptor divide o quadro inteiro e espera resto 0. Não usa valor inicial nem XOR final, então **não** dá o valor `0xCBF43926` para `"123456789"`.

```python
# ---------------------------------- CRC-32 --------------------------------
GERADOR_CRC32 = 0x104C11DB7        # x^32 + x^26 + ... + x + 1 (33 bits)


def resto_mod2(bits):
    """Resto da divisão polinomial módulo 2 de `bits` por GERADOR_CRC32."""
    resto = 0
    for bit in bits:
        resto = (resto << 1) | bit             # "traz" o próximo bit
        if resto >> 32:                        # grau 32 ligado: subtrai (XOR) G
            resto ^= GERADOR_CRC32
    return resto


def calcular_crc32(bits):
    """CRC = resto de M(x) * x^32 por G(x) (anexa 32 zeros à mensagem)."""
    return resto_mod2(bits + [0] * 32)


def adicionar_crc32(bits):
    crc = calcular_crc32(bits)
    return bits + bytes_para_bits([(crc >> s) & 0xFF for s in (24, 16, 8, 0)])


def verificar_crc32(bits):
    """Receptor: dividir o quadro inteiro por G; resto 0 -> sem erro."""
    if len(bits) < 32:
        return bits, False
    return bits[:-32], resto_mod2(bits) == 0
```


### CRC-32 padrão refletido (alternativa validável)

Variante usada em Ethernet/zlib. `calcular_crc32_padrao` de `"123456789"` dá `0xCBF43926`, o que permite conferir a implementação contra um valor conhecido.

```python
POLI_CRC32_REFLETIDO = 0xEDB88320


def calcular_crc32_padrao(bits):
    """Variante refletida (Ethernet/zlib): CRC32('123456789') = 0xCBF43926."""
    crc = 0xFFFFFFFF
    for i in range(0, len(bits), 8):
        for bit in reversed(bits[i:i + 8]):     # LSB do byte primeiro
            if (crc ^ bit) & 1:
                crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF
```


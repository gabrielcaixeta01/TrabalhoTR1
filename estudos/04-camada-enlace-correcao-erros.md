# Camada de Enlace — Correção de Erros (Hamming)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides `TR1_09` (38-39), que usam o **Hamming (11,7)**, e enunciado (seção 1.3).
> No projeto o Hamming é **generalizado**: o número de bits de dados por bloco (m) é configurável e o (11,7) é o caso m = 7.
> Mapeado no código: `camada_enlace.py`, seção "3) Correção de erros: Hamming".

---

## 0. Detecção vs Correção

As técnicas do arquivo 03 só **detectam** erro — descobrem *que* algo mudou, e aí seria preciso pedir
retransmissão. O **Hamming** vai além: ele **corrige** o erro no próprio receptor (FEC — *Forward
Error Correction*), descobrindo *qual* bit virou e invertendo de volta. Não precisa retransmitir.

O preço: **mais redundância**. No Hamming (11,7), 7 bits de dados viram 11 (overhead de 4/7 ≈ 57%). Com blocos maiores o
overhead cai: no (31,26) são 5 bits de paridade para 26 de dados (≈ 19%).

---

## 1. A ideia: bits de paridade que "se cruzam"

Hamming posiciona **bits de paridade** em posições estratégicas, cada um cobrindo um subconjunto
diferente dos bits. Quando um bit vira, ele "estraga" exatamente o conjunto de paridades que o
cobrem — e essa **combinação de paridades quebradas é o endereço binário** da posição que errou.

As paridades ficam nas posições **potência de 2** (1, 2, 4, 8), porque assim cada posição do bloco é coberta
por uma combinação única delas (o índice em binário diz quais paridades a cobrem).

---

## 2. Hamming (11,7) — o dos slides

7 bits de dados + 4 de paridade = 11 bits por bloco (slide 38):

```
posição:   1    2    3    4    5    6    7    8    9    10   11
conteúdo:  P1   P2   M3   P4   M5   M6   M7   P8   M9   M10  M11
```

Paridade **par**. Cada paridade cobre as posições cujo índice em binário tem aquele bit ligado:

| Paridade | Cobre as posições | Equação |
|---|---|---|
| P1 (bit 0) | 1, 3, 5, 7, 9, 11 | P1 = M3 ⊕ M5 ⊕ M7 ⊕ M9 ⊕ M11 |
| P2 (bit 1) | 2, 3, 6, 7, 10, 11 | P2 = M3 ⊕ M6 ⊕ M7 ⊕ M10 ⊕ M11 |
| P4 (bit 2) | 4, 5, 6, 7 | P4 = M5 ⊕ M6 ⊕ M7 |
| P8 (bit 3) | 8, 9, 10, 11 | P8 = M9 ⊕ M10 ⊕ M11 |

(⊕ = XOR = soma módulo 2.)

### Decodificação: a síndrome

O receptor recalcula as quatro verificações **incluindo o próprio bit de paridade recebido**:
`s1 = P1 ⊕ M3 ⊕ M5 ⊕ M7 ⊕ M9 ⊕ M11` e analogamente `s2`, `s4`, `s8`. A **síndrome** é o número binário
`S = (s8 s4 s2 s1)`:

- `S = 0` → nenhum erro detectado;
- `S > 0` → o valor decimal de `S` é a **posição exata do bit errado** (1 a 11): basta invertê-lo.

Exemplo: `S = 0101 = 5` → o bit da posição 5 (M5) virou.

### O que este Hamming NÃO faz

Os slides **não** mostram bit de paridade geral (SECDED). Logo:
- corrige **1 erro por bloco**;
- com **2 erros** no mesmo bloco, a síndrome aponta uma posição errada e o decodificador "corrige" o bit
  errado, **sem perceber**. Só dá para suspeitar quando `S > 11` (posição inexistente, 12 a 15).

### Generalização: Hamming (m + r, m)

O (11,7) é só um caso. Para **m** bits de dados, precisamos de **r** bits de paridade tais que a síndrome (r bits)
consiga apontar qualquer das `n = m + r` posições, ou "nenhum erro":

```
2^r ≥ m + r + 1      (menor r que satisfaz)
```

| m (dados) | r (paridade) | Código (n, m) |
|---|---|---|
| 4 | 3 | (7, 4) |
| 7 | 4 | (11, 7) — o dos slides |
| 11 | 4 | (15, 11) |
| 26 | 5 | (31, 26) |
| 57 | 6 | (63, 57) |

A regra de posições é a mesma: paridades nas potências de 2 (1, 2, 4, 8, 16, ...), dados nas demais, e a paridade
p cobre toda posição que tem o bit p ligado no binário. O que muda é só o tamanho do bloco. No projeto, m vem da
GUI (`bits_hamming`, padrão 7).

---

## 3. No projeto — codificação

O payload (já alinhado em bytes e com o EDC anexado) é processado em blocos de **m bits de dados**. Para cada
bloco: coloca-se cada dado na sua posição de dados, calcula-se cada paridade como o XOR das posições que ela
cobre e monta-se o bloco de `m + r` bits.

**Problema de alinhamento (decisão do grupo):** os slides não dizem o que fazer quando o número de bits não é
múltiplo de m, nem como encaixar blocos de `m + r` bits em quadros de bytes (a contagem e o byte stuffing
trabalham em bytes). A solução: anexar um **bit 1 de fim** aos dados e completar com zeros até múltiplo de m,
e depois completar a saída com zeros até múltiplo de 8. O bit 1 de fim marca onde os dados terminam; assim o
receptor sabe quanto enchimento tirar para **qualquer** m (cortar só "até múltiplo de 8" não funcionaria com m
grande, porque o enchimento pode passar de 8 bits).

## 4. No projeto — decodificação

Para cada bloco completo de `m + r` bits: calcula-se a síndrome, inverte-se o bit apontado quando `0 < S ≤ n`,
conta-se a correção e extraem-se os m bits de dados. Trabalhe sobre uma **cópia** do bloco para não alterar a
entrada. No fim descartam-se o enchimento: os zeros do final e o bit 1 de fim.

**O que o teste deve provar:** injetando 1 erro em **cada posição** de um bloco, o decodificador recupera os
dados originais em todas (vale para qualquer m, não só 7).

---

## 5. Capacidade de correção — a régua de Hamming (cai em prova)

A capacidade vem da **distância de Hamming mínima** `d` do código (menor nº de bits que diferem entre
dois códigos válidos):

- Para **detectar** até `t` erros: `d ≥ t + 1`.
- Para **corrigir** até `t` erros: `d ≥ 2t + 1`.

O Hamming (11,7) tem `d = 3` → corrige 1 (`2·1+1=3`) **ou** detecta 2 (`2+1=3`), não os dois juntos. Para
corrigir 1 **e** detectar 2 é preciso `d = 4`: é o que o bit de paridade geral do Hamming *estendido*
(SECDED) proporciona. Os slides não o usam; ele aparece aqui só como contraste para a prova.

---

## 6. Onde entra no pipeline

Ordem no TX (`transmitir`, arquivo 05) — o Hamming vem **depois** do EDC:

```
payload → [+ EDC] → [codifica Hamming: 7 bits viram 11] → [enquadra]
```

No RX (`receber`):

```
desenquadra → [decodifica Hamming: corrige] → [verifica EDC] → payload
```

O relatório por quadro guarda `corrigidos` (quantos bits o Hamming consertou) e um indicador de erro
incorrigível — a GUI mostra isso na aba do receptor.

> Por isso o EDC ainda é útil mesmo com Hamming: como o (11,7) não percebe erro duplo, é o EDC (CRC, por
> exemplo) que flagra que o resultado final está corrompido.

---

## 7. Como testar e visualizar

### Teste automático (`testes.py`)
Codificar e decodificar sem erro devolve os dados originais; inverter 1 bit é corrigido (contador de
corrigidos = 1).

### Experimento manual (ver a síndrome funcionando)
Codifique 7 bits, inverta cada uma das 11 posições (uma por vez) e imprima a síndrome: ela é a posição
invertida. Depois inverta duas posições e veja que o decodificador "corrige" o bit errado sem avisar.

### Na GUI
1. Ative **correção = hamming**, escolha um EDC e ponha **ruído moderado**.
2. Na aba **Receptor**, o relatório por quadro mostra **bits corrigidos** > 0 — o Hamming consertando
   o ruído em tempo real.
3. Aumente o σ: em certo ponto aparecem blocos com 2 erros que o Hamming não conserta; o EDC acusa e o texto
   começa a sair com `�`.
4. Compare **com e sem Hamming** no mesmo ruído: com Hamming o texto sobrevive a σ maiores.

---

## 8. Pontos que o professor gosta de cobrar

1. **Paridades nas posições potência de 2** e por quê (cada posição coberta por combinação única).
2. **Síndrome = endereço binário** do bit errado.
3. **Corrige 1 erro; não detecta 2** no (11,7). Só o Hamming estendido (SECDED, com paridade geral) corrige 1 e detecta 2.
4. Régua: **detectar `t` → d ≥ t+1**; **corrigir `t` → d ≥ 2t+1**; (11,7) tem d=3, estendido d=4.
5. Diferença **FEC (Hamming)** × retransmissão (ARQ, baseada em detecção).
6. **Ordem EDC → Hamming** no TX e o motivo (Hamming protege o EDC; EDC pega o que o Hamming não corrige).
7. Custo da correção: no (11,7), 7 bits viram 11 (≈ 57% de overhead); blocos maiores gastam menos paridade, mas um
   erro duplo no mesmo bloco fica mais provável. Mais o enchimento para fechar em bytes.
8. Por que o Hamming do projeto **não é fixo**: m é configurável e r sai de `2^r ≥ m + r + 1`.

---

## 9. Código de referência — `camada_enlace.py` (Hamming)

> Código **testado** (ida e volta, 1 erro em cada posição para vários m, e a simulação completa), no mesmo
> formato das assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha
> antes de colar; o professor pergunta.

Hamming (m + r, m) com m configurável (padrão 7, que é o (11,7) dos slides). Corrige 1 erro por bloco mas não
detecta erro duplo: uma síndrome acima de n aponta uma posição inexistente e é sinalizada como incorrigível.

```python
# ------------------------------- Hamming (m + r, m) ------------------------
BITS_HAMMING_PADRAO = 7


def bits_de_paridade(m):
    """Menor r tal que 2^r >= m + r + 1."""
    r = 1
    while 2 ** r < m + r + 1:
        r += 1
    return r


def posicoes_hamming(m):
    """Devolve (n, posicoes_paridade, posicoes_dados) de um bloco com m bits de dados."""
    r = bits_de_paridade(m)
    n = m + r
    posicoes_paridade = [2 ** k for k in range(r)]          # 1, 2, 4, 8, ...
    posicoes_dados = [p for p in range(1, n + 1) if p not in posicoes_paridade]
    return n, posicoes_paridade, posicoes_dados


def codificar_hamming(bits, m=BITS_HAMMING_PADRAO):
    """Blocos de m bits de dados viram m + r; saída completada para múltiplo de 8."""
    n, posicoes_paridade, posicoes_dados = posicoes_hamming(m)
    bits = bits + [1]                                       # bit 1 de fim
    bits = bits + [0] * (-len(bits) % m)
    saida = []
    for inicio in range(0, len(bits), m):
        bloco = [0] * (n + 1)                               # posições 1 a n
        for pos, dado in zip(posicoes_dados, bits[inicio:inicio + m]):
            bloco[pos] = dado
        for p in posicoes_paridade:
            for pos in range(1, n + 1):
                if pos & p and pos != p:                    # posições cobertas por p
                    bloco[p] ^= bloco[pos]
        saida += bloco[1:]
    return saida + [0] * (-len(saida) % 8)


def decodificar_hamming(bits, m=BITS_HAMMING_PADRAO):
    """Corrige 1 erro por bloco. Devolve (dados, n_corrigidos, erro_incorrigivel)."""
    n, posicoes_paridade, posicoes_dados = posicoes_hamming(m)
    dados = []
    n_corrigidos = 0
    erro_incorrigivel = False
    for inicio in range(0, len(bits) // n * n, n):          # só blocos completos
        bloco = [0] + bits[inicio:inicio + n]
        sindrome = 0
        for p in posicoes_paridade:
            soma = 0
            for pos in range(1, n + 1):
                if pos & p:                                 # inclui a própria paridade
                    soma ^= bloco[pos]
            if soma:
                sindrome += p                               # síndrome em binário
        if 0 < sindrome <= n:
            bloco[sindrome] ^= 1                            # a síndrome é a posição do erro
            n_corrigidos += 1
        elif sindrome > n:
            erro_incorrigivel = True                        # aponta posição inexistente
        dados += [bloco[pos] for pos in posicoes_dados]
    while dados and dados[-1] == 0:                         # tira o enchimento...
        dados.pop()
    if dados:
        dados.pop()                                         # ...e o 1 de fim
    return dados, n_corrigidos, erro_incorrigivel
```

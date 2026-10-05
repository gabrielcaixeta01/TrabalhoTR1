# Camada de Enlace — Correção de Erros (Hamming)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides `TR1_09` (38-39), que usam o **Hamming (11,7)**, e enunciado (seção 1.3).
> Mapeado no código: `camada_enlace.py`, seção "[3/3] CORREÇÃO DE ERROS - HAMMING".

---

## 0. Detecção vs Correção

As técnicas do arquivo 03 só **detectam** erro — descobrem *que* algo mudou, e aí seria preciso pedir
retransmissão. O **Hamming** vai além: ele **corrige** o erro no próprio receptor (FEC — *Forward
Error Correction*), descobrindo *qual* bit virou e invertendo de volta. Não precisa retransmitir.

O preço: **mais redundância**. No Hamming (11,7) do projeto, 7 bits de dados viram 11 (overhead de 4/7 ≈ 57%).

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

---

## 3. No projeto — codificação

O payload (já alinhado em bytes e com o EDC anexado) é processado em blocos de **7 bits de dados**. Para cada
bloco: coloca-se cada dado na sua posição (3, 5, 6, 7, 9, 10, 11), calcula-se cada paridade como o XOR das
posições que ela cobre e monta-se o bloco de 11 bits.

**Problema de alinhamento (decisão do grupo):** os slides não dizem o que fazer quando o número de bits não é
múltiplo de 7, nem como encaixar blocos de 11 bits em quadros de bytes (a contagem e o byte stuffing
trabalham em bytes). A solução do código de referência: completar o último bloco de dados com zeros até 7 e
completar a saída com zeros até um múltiplo de 8.

## 4. No projeto — decodificação

Para cada bloco de 11 bits: calcula-se a síndrome, inverte-se o bit apontado quando `0 < S ≤ 11`, conta-se a
correção e extraem-se os 7 bits de dados. Trabalhe sobre uma **cópia** do bloco para não alterar a entrada.
No fim descartam-se os bits de enchimento (a quantidade de dados volta a ser múltiplo de 8).

**O que o teste deve provar:** injetando 1 erro em **cada uma das 11 posições** de um bloco, o decodificador
recupera os dados originais em todas.

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
7. Custo da correção: 7 bits viram 11 (≈ 57% de overhead), mais o enchimento para fechar em bytes.

---

## 9. Código de referência — `camada_enlace.py` (Hamming)

> Código **testado** (ida e volta, com e sem ruído, e a simulação completa), no mesmo formato das
> assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha antes de
> colar; o professor pergunta.

Implementa o **Hamming(11,7)** do resumo dos slides (7 bits de dados, 4 de paridade em 1, 2, 4 e 8). Diferente do (8,4) estendido discutido nas seções anteriores, ele **corrige 1 erro por bloco mas não detecta erro duplo**: uma síndrome acima de 11 aponta uma posição inexistente e é sinalizada como incorrigível. Como 11 bits não fecham em bytes, a saída é completada com zeros até um múltiplo de 8 e o decodificador descarta o excedente.

### Hamming(11,7)

```python
# ------------------------------ Hamming (11,7) -----------------------------
POSICOES_DADOS = [3, 5, 6, 7, 9, 10, 11]          # as demais (1, 2, 4, 8) são paridades
COBERTURA = {1: [3, 5, 7, 9, 11], 2: [3, 6, 7, 10, 11],
             4: [5, 6, 7], 8: [9, 10, 11]}


def codificar_hamming(bits):
    """Blocos de 7 bits de dados viram 11 bits; saída completada para múltiplo de 8."""
    bits = bits + [0] * ((-len(bits)) % 7)
    saida = []
    for i in range(0, len(bits), 7):
        bloco = [0] * 12                          # índices 1..11 (0 não é usado)
        for pos, dado in zip(POSICOES_DADOS, bits[i:i + 7]):
            bloco[pos] = dado
        for p, cobertos in COBERTURA.items():
            for pos in cobertos:
                bloco[p] ^= bloco[pos]            # paridade par do grupo
        saida += bloco[1:]
    return saida + [0] * ((-len(saida)) % 8)


def decodificar_hamming(bits):
    """Corrige 1 erro por bloco. Devolve (dados, n_corrigidos, erro_incorrigivel)."""
    dados, corrigidos, incorrigivel = [], 0, False
    for i in range(0, len(bits) // 11 * 11, 11):
        bloco = [0] + bits[i:i + 11]
        sindrome = 0
        for p, cobertos in COBERTURA.items():
            s = bloco[p]
            for pos in cobertos:
                s ^= bloco[pos]
            if s:
                sindrome += p                     # s8 s4 s2 s1 em binário
        if 0 < sindrome <= 11:
            bloco[sindrome] ^= 1                  # a síndrome é a posição errada
            corrigidos += 1
        elif sindrome > 11:
            incorrigivel = True                   # aponta posição inexistente
        dados += [bloco[pos] for pos in POSICOES_DADOS]
    return dados[:len(dados) // 8 * 8], corrigidos, incorrigivel
```


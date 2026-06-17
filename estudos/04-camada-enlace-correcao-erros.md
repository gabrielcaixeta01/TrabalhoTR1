# Camada de Enlace — Correção de Erros (Hamming)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides de enlace do prof. Marotta + enunciado (seção 1.5).
> Mapeado no código: `camada_enlace.py`, seção "3) CORREÇÃO DE ERROS - HAMMING(8,4) estendido".

---

## 0. Detecção vs Correção

As técnicas do arquivo 03 só **detectam** erro — descobrem *que* algo mudou, e aí seria preciso pedir
retransmissão. O **Hamming** vai além: ele **corrige** o erro no próprio receptor (FEC — *Forward
Error Correction*), descobrindo *qual* bit virou e invertendo de volta. Não precisa retransmitir.

O preço: **mais redundância**. O Hamming(8,4) do projeto dobra o tamanho dos dados (4 bits viram 8).

---

## 1. A ideia: bits de paridade que "se cruzam"

Hamming posiciona **bits de paridade** em posições estratégicas, cada um cobrindo um subconjunto
diferente dos bits. Quando um bit vira, ele "estraga" exatamente o conjunto de paridades que o
cobrem — e essa **combinação de paridades quebradas é o endereço binário** da posição que errou.

O Hamming clássico é o **(7,4)**: 4 bits de dados + 3 de paridade = 7 bits. As paridades ficam nas
posições potência de 2 (1, 2, 4), porque assim cada posição do bloco é coberta por uma combinação
única delas:

```
posição:   1    2    3    4    5    6    7
conteúdo:  p1   p2   d1   p4   d2   d3   d4

p1 (pos 1) cobre posições com bit 0 do índice = 1,3,5,7
p2 (pos 2) cobre posições com bit 1 do índice = 2,3,6,7
p4 (pos 4) cobre posições com bit 2 do índice = 4,5,6,7
```

A leitura das três paridades no RX forma a **síndrome** `s = s4 s2 s1` (em binário). Se a síndrome é
`000`, não houve erro. Se é, por exemplo, `101 = 5`, o **bit da posição 5** virou — basta invertê-lo.
É isso que dá a correção de **1 bit**.

---

## 2. Hamming(8,4) estendido — SECDED (o que o projeto usa)

O (7,4) puro **corrige 1 erro**, mas não distingue 1 erro de 2 erros (com 2 erros a síndrome aponta
uma posição errada e ele "corrige" estragando ainda mais). A solução é o **Hamming estendido**:
acrescenta-se **um bit de paridade geral `p0`** sobre todo o bloco, virando **8 bits**.

Isso é o **SECDED** — *Single Error Correction, Double Error Detection*: **corrige 1 erro e detecta
(sem corrigir) 2 erros** por bloco. Bônus: 8 bits = 1 byte cheio, mantendo o alinhamento que o resto
da camada usa (4 bits de dados → 1 byte de código; 1 byte de dados → 2 bytes de código).

Layout do bloco no projeto:

```
posição:   1    2    3    4    5    6    7    8
conteúdo:  p1   p2   d1   p4   d2   d3   d4   p0
                                              ↑ paridade geral dos 7 primeiros
```

### Como a combinação (síndrome, paridade geral) decide

| Síndrome | Paridade geral p0 | Diagnóstico | Ação |
|---|---|---|---|
| 0 | ok (par) | sem erro | nada |
| ≠ 0 | quebrada (ímpar) | **1 erro** nos bits 1–7 | corrige na posição da síndrome |
| 0 | quebrada (ímpar) | erro só no próprio p0 | dados intactos (conta como corrigido) |
| ≠ 0 | ok (par) | **2 erros** (duplo) | detecta, **não corrige** |

A lógica do último caso: dois erros mexem na síndrome (que aponta algo ≠ 0) mas **não** mudam a
paridade geral (porque dois bits invertidos mantêm a paridade par). Essa contradição —
"a síndrome diz que errou, mas a paridade geral diz que está par" — é a **assinatura do erro duplo**.

---

## 3. No projeto — codificação

```python
def codificar_hamming(bits):
    for i in range(0, len(bits), 4):            # 4 bits de dados por vez
        d1, d2, d3, d4 = bits[i:i+4]
        p1 = (d1 + d2 + d4) % 2                 # cobre posições 1,3,5,7
        p2 = (d1 + d3 + d4) % 2                 # cobre posições 2,3,6,7
        p4 = (d2 + d3 + d4) % 2                 # cobre posições 4,5,6,7
        bloco = [p1, p2, d1, p4, d2, d3, d4]
        p0 = sum(bloco) % 2                      # paridade geral (o "estendido")
        saida += bloco + [p0]
```

Cada `% 2` é a paridade par (XOR) do grupo. As fórmulas de `p1/p2/p4` saem direto da tabela de
cobertura da seção 1 (quais posições de dados caem em cada grupo).

## 4. No projeto — decodificação

```python
def decodificar_hamming(bits):
    for i in range(0, len(bits) - 7, 8):
        b = bits[i:i+8][:]                       # cópia (vamos poder corrigir)
        s1 = (b[0] + b[2] + b[4] + b[6]) % 2     # recalcula paridade pos 1,3,5,7
        s2 = (b[1] + b[2] + b[5] + b[6]) % 2     # pos 2,3,6,7
        s4 = (b[3] + b[4] + b[5] + b[6]) % 2     # pos 4,5,6,7
        sindrome = s4*4 + s2*2 + s1              # posição do bit errado (1-7)
        par_geral = sum(b) % 2                   # 0 se paridade geral ok
        if sindrome != 0 and par_geral == 1:     # ERRO SIMPLES
            b[sindrome - 1] ^= 1                  # corrige na posição apontada
            corrigidos += 1
        elif sindrome == 0 and par_geral == 1:   # erro só no p0
            corrigidos += 1
        elif sindrome != 0 and par_geral == 0:   # ERRO DUPLO
            erro_duplo = True
        dados += [b[2], b[4], b[5], b[6]]         # extrai d1 d2 d3 d4
    return dados, corrigidos, erro_duplo
```

Note que a síndrome inclui o **próprio bit de paridade** no recálculo (`s1` usa `b[0]=p1`, etc.).
Por isso, se só o `p1` virou, a síndrome aponta a posição 1 (o próprio p1) — e corrigir o p1 é
inofensivo porque ele não é dado. A extração final `[b[2], b[4], b[5], b[6]]` pega exatamente as
posições 3,5,6,7 (os d1,d2,d3,d4).

**Verifiquei empiricamente** (rodei o código): injetando 1 erro em **cada uma das 8 posições**, o
decodificador recupera os 4 bits originais nas 8 vezes; injetando 2 erros no mesmo bloco, ele sinaliza
`erro_duplo = True` sem corromper silenciosamente. Comportamento SECDED correto.

---

## 5. Capacidade de correção — a régua de Hamming (cai em prova)

A capacidade vem da **distância de Hamming mínima** `d` do código (menor nº de bits que diferem entre
dois códigos válidos):

- Para **detectar** até `t` erros: `d ≥ t + 1`.
- Para **corrigir** até `t` erros: `d ≥ 2t + 1`.

O Hamming(7,4) tem `d = 3` → corrige 1 (`2·1+1=3`) **ou** detecta 2 (`2+1=3`), não os dois juntos.
O Hamming(8,4) estendido tem `d = 4` → consegue **corrigir 1 e detectar 2 simultaneamente** (SECDED).
É exatamente o salto que o `p0` proporciona.

---

## 6. Onde entra no pipeline

Ordem no TX (`transmitir`, arquivo 05) — o Hamming vem **depois** do EDC:

```
payload → [+ EDC] → [codifica Hamming: dobra de tamanho] → [enquadra]
```

No RX (`receber`):

```
desenquadra → [decodifica Hamming: corrige/detecta] → [verifica EDC] → payload
```

O relatório por quadro guarda `corrigidos` (quantos bits o Hamming consertou) e `erro_duplo` (se
algum bloco teve erro duplo) — a GUI mostra isso na aba do receptor.

> Por isso o EDC ainda é útil mesmo com Hamming: se o ruído estourar a capacidade do Hamming
> (≥ 2 erros por bloco), o EDC ainda flagra que o resultado final está corrompido.

---

## 7. Como testar e visualizar

### Teste automático (`testes.py`)
```python
dados = _bits_aleatorios(6)
cod = enlace.codificar_hamming(dados)
dec, n, duplo = enlace.decodificar_hamming(cod)
assert dec == dados and n == 0 and not duplo     # ida e volta limpa

cod_err = cod[:]; cod_err[5] ^= 1                 # 1 erro
dec, n, _ = enlace.decodificar_hamming(cod_err)
assert dec == dados and n == 1                    # corrigiu

cod_err[6] ^= 1                                   # 2º erro no mesmo bloco
_, _, duplo = enlace.decodificar_hamming(cod_err)
assert duplo                                      # detectou erro duplo
```

### Experimento manual (ver a síndrome funcionando)
```python
import camada_enlace as e
dados = [1,0,1,1]
cod = e.codificar_hamming(dados)        # ex.: [0,1,1,0,0,1,1,0]
print("código:", cod)

for pos in range(8):                     # injeta erro em cada posição
    c = cod[:]; c[pos] ^= 1
    dec, n, dup = e.decodificar_hamming(c)
    print(f"erro na pos {pos+1}: recuperou {dec}  (corrigidos={n}, duplo={dup})")
# todas as 8 linhas devem recuperar [1,0,1,1]
```

### Na GUI
1. Ative **correção = hamming**, escolha um EDC e ponha **ruído moderado**.
2. Na aba **Receptor**, o relatório por quadro mostra **bits corrigidos** > 0 — o Hamming consertando
   o ruído em tempo real.
3. Aumente o σ: em certo ponto aparecem **erros duplos** e o texto começa a sair com `�`, mostrando o
   limite SECDED (corrige 1, detecta 2, mas não corrige 2).
4. Compare **com e sem Hamming** no mesmo ruído: com Hamming o texto sobrevive a σ bem maiores.

---

## 8. Pontos que o professor gosta de cobrar

1. **Paridades nas posições potência de 2** e por quê (cada posição coberta por combinação única).
2. **Síndrome = endereço binário** do bit errado.
3. **SECDED**: o bit extra `p0` permite **corrigir 1 e detectar 2**; a assinatura do erro duplo é
   "síndrome ≠ 0 mas paridade geral par".
4. Régua: **detectar `t` → d ≥ t+1**; **corrigir `t` → d ≥ 2t+1**; (7,4) tem d=3, estendido d=4.
5. Diferença **FEC (Hamming)** × retransmissão (ARQ, baseada em detecção).
6. **Ordem EDC → Hamming** no TX e o motivo (Hamming protege o EDC; EDC pega o que o Hamming não corrige).
7. Hamming(8,4) **dobra** o payload (overhead de 100%) — o custo da correção.
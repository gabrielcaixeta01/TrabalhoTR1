# Camada Física — Modulação por Portadora (ASK, FSK, 8PSK, 32-QAM)

> Material de estudo (prova + revisão do projeto TR1).
> Base: slides do prof. Marotta — CF-11 (Modulação e Demodulação), CF-12 (BPSK/QPSK/8PSK), CF-13 (Modulação Mista/QAM).
> Mapeado no código: `camada_fisica.py`, seção "2) MODULAÇÃO POR PORTADORA".

---

## 0. Por que existe modulação por portadora?

A modulação **banda-base** (NRZ, Manchester, Bipolar) põe os bits direto como níveis de tensão.
Isso funciona em fio curto, mas tem dois problemas: ocupa as **baixas frequências** (perto de 0 Hz) e
não dá para colocar vários sinais no mesmo meio sem se atrapalharem.

A modulação **por portadora** (ou *banda passante*) resolve isso pegando uma onda senoidal de
frequência fixa `fc` — a **portadora** — e deixando os bits modificarem **um dos três parâmetros** dela:

| Parâmetro da senoide `e(t) = Vp·sen(ωt + θ)` | Técnica | Sigla |
|---|---|---|
| Amplitude `Vp` | chaveamento de amplitude | **ASK** |
| Frequência `ω = 2πf` | chaveamento de frequência | **FSK** |
| Fase `θ` | chaveamento de fase | **PSK** |
| Amplitude **e** fase juntas | mista (quadratura + amplitude) | **QAM** |

Isso é literalmente o que o slide CF-11 chama de "Processo de Modulação Discreta": substituir
`Vp`, `ω` ou `θ` pela função discreta do fluxo de bits `I(t)`.

---

## 1. A grande ideia unificadora: representação I/Q

Esta é a parte que destrava **tudo** o resto. Todos os slides de portadora (CF-12 em diante) usam
um **diagrama vetorial** com duas bases ortogonais:

- eixo horizontal: `cos(ωc·t)` → componente **I** (*In-phase*, "em fase")
- eixo vertical: `sen(ωc·t)` → componente **Q** (*Quadrature*, "em quadratura", defasada 90°)

Qualquer símbolo modulado pode ser escrito como uma soma dessas duas ondas:

```
s(t) = I·cos(ωc·t) − Q·sen(ωc·t)
```

Ou seja: **escolher um par de números (I, Q) é escolher uma amplitude e uma fase** ao mesmo tempo,
porque em coordenadas polares:

- amplitude `A = √(I² + Q²)`  (distância à origem)
- fase `θ = atan2(Q, I)`  (ângulo)

O conjunto de todos os pontos `(I, Q)` válidos de uma modulação é a sua **constelação**.
Modular = pegar bits, escolher o ponto `(I, Q)` correspondente, gerar a onda.
Demodular = receber a onda, descobrir qual `(I, Q)` foi enviado, voltar aos bits.

> **Cai em prova:** ASK, FSK, PSK e QAM são todos *casos particulares* de mexer em `(I, Q)`.
> PSK move o ponto num **círculo** (amplitude constante, só a fase muda). QAM usa uma **grade**
> (amplitude e fase mudam). ASK liga/desliga a amplitude. FSK é o único que troca a *frequência*
> (foge um pouco do plano I/Q de uma única portadora).

### No projeto

Toda a seção de portadora do `camada_fisica.py` é construída em cima de duas funções auxiliares que
implementam exatamente a fórmula acima:

`onda(i, q, ciclos)` é o **modulador genérico**: gera as amostras de um símbolo somando `I·cos − Q·sen`
ao longo de `AMOSTRAS_POR_SIMBOLO` instantes. Compare-o (compare com o "Modulador genérico PSK" das págs. 11-20 do CF-12:
conversor serial→paralelo, associação de fase ao símbolo, canais I e Q, gerador de portadora
`cos ωc·t` / `−sen ωc·t`, e o somador `S(t) = I(t) + Q(t)`).

`correlacionar(simbolo, ciclos)` é o **demodulador genérico** (detecção coerente): projeta o sinal
recebido sobre `cos` e `−sen` de referência para recuperar `(I, Q)`, com `I = (2/N)·Σ s[n]·cos(ωn)` e
`Q = −(2/N)·Σ s[n]·sen(ωn)`.

**Por que funciona:** `cos` e `sen` são ortogonais ao longo de um número inteiro de ciclos —
`soma( cos(ωt)·sen(ωt) ) = 0` para ciclos completos. Por isso multiplicar por `cos` só "enxerga" I
e multiplicar por `sen` só "enxerga" Q: cada eixo fica isolado. O fator `2/N` é a normalização
que devolve a amplitude original (`soma( cos²(ωt) ) = N/2` para ciclos completos, logo `2/N · N/2 = 1`).
É por isso que `CICLOS_PORTADORA = 4` precisa ser **inteiro**: garante ciclos completos por símbolo
e mantém a ortogonalidade.

---

## 2. ASK — Amplitude Shift Keying

**Ideia (CF-11, pág. 8):** o bit liga ou desliga a portadora.

- bit 1 → portadora com amplitude `V`
- bit 0 → nada (0 V) — por isso também se chama **OOK**, *On-Off Keying*

1 bit por símbolo. É a técnica **mais simples e a mais suscetível a ruído** (o slide diz isso
explicitamente): qualquer ruído que aumente a amplitude do "0" ou diminua a do "1" causa erro.

Demodulação: `correlacionar` devolve `(I, Q)`; a amplitude do símbolo é `√(I² + Q²)` — a distância
do ponto à origem no plano I/Q. Compara com o **limiar V/2** (meio do caminho entre 0 e V).

**Constelação:** dois pontos no eixo I → `(0,0)` e `(V,0)`.

---

## 3. FSK — Frequency Shift Keying

**Ideia (CF-11, pág. 10):** a amplitude é sempre a mesma; o que muda é a **frequência**.

- bit 0 → frequência `f0`
- bit 1 → frequência `f1`

1 bit por símbolo. **Mais tolerante a ruído que ASK** (o ruído teria que falsear a frequência
inteira, não só a amplitude), mas tem **baixa eficiência espectral** porque usa duas faixas de frequência.

> No slide o exemplo é `f1 = 2·fc` (o "1" usa o dobro da frequência do "0"). No projeto usamos
> `CICLOS_FSK = (2, 4)`: 2 ciclos/símbolo para o bit 0, 4 ciclos/símbolo para o bit 1.
> O importante é que sejam **inteiras e distintas** → portadoras ortogonais dentro do símbolo.

Demodulação **não-coerente por energia**: correlaciona o símbolo com cada uma das duas frequências
e mede a energia `√(I² + Q²)` em cada uma — a frequência com mais energia é a que foi transmitida.

> **FSK é o único que não cabe no plano I/Q de uma só portadora**, justamente porque a frequência muda.
> Por isso a demodulação dele compara energia em duas frequências em vez de ler um ponto da constelação.

---

## 4. PSK — Phase Shift Keying e o 8PSK

**Ideia (CF-11 pág. 12; CF-12 inteiro):** amplitude e frequência constantes; o bit muda a **fase**.
É a técnica **mais adotada** em comunicação de dados: maior eficiência espectral e maior tolerância a
ruído que ASK/FSK.

### BPSK e QPSK — a escadinha conceitual

- **BPSK:** 1 bit por símbolo, 2 fases (0° e 180°) → pontos `(+A, 0)` e `(−A, 0)`. Os dois pontos ficam
  o mais longe possível um do outro, por isso é o mais robusto.
- **QPSK:** 2 bits por símbolo (*dibit*), 4 fases (45°, 135°, 225°, 315°). Dobra a taxa do BPSK na
  mesma banda. (CF-12, pág. 8.)

O enunciado **não pede** BPSK nem QPSK; eles servem de degrau para entender o 8PSK.

### 8PSK — o que o trabalho pede

**3 bits por símbolo** (*tribit*), **8 fases** igualmente espaçadas no círculo, a cada **45°**:
0°, 45°, 90°, 135°, 180°, 225°, 270°, 315° (CF-12, págs. 40-41).

Como todos os pontos ficam no mesmo círculo de raio `V`, a amplitude é constante (característica do PSK):

```
fase_k = k · 45°          (k = 0..7)
(I, Q) = ( V·cos(fase_k) , V·sen(fase_k) )
```

**Codificação de Gray (essencial — CF-12, págs. 28-31):** os tribits são atribuídos às fases de modo
que **vizinhos no círculo diferem em apenas 1 bit**. Se o ruído empurrar o ponto recebido para o
símbolo vizinho, erra-se **só 1 bit** em vez de até 3. Sequência Gray de 3 bits em ordem de fase:

| k | fase | tribit (Gray) |
|---|---|---|
| 0 | 0°   | 000 |
| 1 | 45°  | 001 |
| 2 | 90°  | 011 |
| 3 | 135° | 010 |
| 4 | 180° | 110 |
| 5 | 225° | 111 |
| 6 | 270° | 101 |
| 7 | 315° | 100 |

Repare que subir de `k` para `k+1` muda **um bit de cada vez** (e de `k=7` de volta a `k=0` também:
`100 → 000`). Isso é Gray.

**Modulação:** agrupar os bits de 3 em 3 (completando com zeros se sobrar, *padding*), buscar o
`(I, Q)` do tribit na tabela e gerar um símbolo da portadora com `s(t) = I·cos − Q·sen`.

**Demodulação:** correlacionar o símbolo recebido para obter `(I, Q)` medidos e escolher o **ponto da
constelação mais próximo** (decisão de mínima distância, `(I_ref−I)² + (Q_ref−Q)²` mínimo). Com ruído
`(I, Q)` não cai exato num ponto; o "arredondamento" para o vizinho mais perto é o que dá robustez.

> **Trade-off central do PSK (CF-12):** mais fases → pontos mais próximos no círculo → menos tolerância
> a ruído. A distância entre pontos vizinhos no 8PSK é `2·V·sen(22,5°) ≈ 0,77·V`, contra `√2·V ≈ 1,41·V`
> no QPSK. Esta frase cai em prova.

---

## 5. 32-QAM — Quadrature Amplitude Modulation

**Ideia (CF-13):** combinar variação de **fase E amplitude**. Em vez de pontos só num círculo (PSK), a
constelação vira uma **grade** → mais pontos com vizinhos mais afastados do que num círculo.
O slide CF-13 (pág. 3) quantifica para o 16-QAM: tolera ~0,81 dB mais ruído gaussiano que 16-PSK.

### A constelação do 32-QAM

**32 pontos = 5 bits por símbolo** (2⁵ = 32). Uma grade quadrada com 32 pontos não existe
(√32 não é inteiro), então usa-se a **constelação em cruz**: grade **6×6 = 36 pontos** com os **4
cantos removidos** → 36 − 4 = **32** pontos.

Níveis em cada eixo: `{−5, −3, −1, +1, +3, +5}`, multiplicados por uma escala. Os cantos
`(±5, ±5)` são os pontos de **maior energia**; removê-los reduz a potência de pico e média. Se a
escala for `V/5`, o maior `|I|` ou `|Q|` vale exatamente `V`.

```
         Q
   .  x  x  x  x  .       x = ponto da constelação
   x  x  x  x  x  x       . = canto removido (±5, ±5)
   x  x  x  x  x  x   I
   x  x  x  x  x  x
   x  x  x  x  x  x
   .  x  x  x  x  .
```

### Rotulagem dos 5 bits (decisão de projeto)

Os slides não trazem os níveis nem a rotulagem (só o desenho da cruz). O ideal seria Gray (vizinhos diferem
em 1 bit), mas **na cruz um Gray perfeito não existe**. A escolha do projeto (registrada em
`docs/DECISOES.md`) é um Gray "quase perfeito":

- **2 bits de quadrante**, em Gray ao redor da origem: `(+,+)=00`, `(−,+)=01`, `(−,−)=11`, `(+,−)=10`;
- **3 bits de posição** dentro do quadrante. Cada quadrante tem 8 pontos (3×3 níveis menos o canto) que
  formam um ciclo de vizinhos; rotulam-se ao longo do ciclo com o Gray de 3 bits do 8PSK
  (`000, 001, 011, 010, 110, 111, 101, 100`).

Como a posição só depende de `(|I|, |Q|)`, dois pontos vizinhos de quadrantes diferentes diferem apenas nos
bits de quadrante (1 bit). Resultado: dos 52 pares de pontos vizinhos, **48 diferem em 1 bit e 4 em 3 bits**.
Mesmo assim, o erro mais provável (ruído empurra para o vizinho) quase sempre custa 1 bit só.

O que **não pode faltar** em qualquer mapeamento: os 32 rótulos devem ser **distintos** (um-para-um);
senão o receptor não consegue inverter o mapeamento.

### Demodulação

Diferente do 16-QAM, **não** dá para decidir I e Q separadamente: a cruz **não é um produto
cartesiano** (faltam os cantos), então um `(I, Q)` medido poderia cair na região de um canto removido
e a decisão por eixo devolveria um ponto que não existe. Use a **mínima distância sobre os 32 pontos**.

> **Custo do 32-QAM:** 5 bits/símbolo é muita informação por símbolo, mas a distância mínima entre
> pontos é de `2·(V/5) = 0,4·V`, bem menor que no 8PSK (≈ `0,77·V`). Ele só funciona bem com ruído
> baixo — e isso é exatamente o trade-off bits/símbolo × robustez que o professor gosta de cobrar.

---

## 6. Quadro-resumo (cola de prova)

| Modulação | Bits/símbolo | O que varia | Constelação | Robustez a ruído | Eficiência espectral |
|---|---|---|---|---|---|
| ASK | 1 | amplitude (on/off) | 2 pts no eixo I | pior | baixa |
| FSK | 1 | frequência | 2 frequências | média | pior (usa 2 faixas) |
| BPSK | 1 | fase (0°/180°) | 2 pts opostos | ótima | média |
| QPSK | 2 | fase (4 ângulos) | 4 pts no círculo | boa | boa |
| **8PSK** (pedido) | 3 | fase (8 ângulos) | 8 pts no círculo | cai vs QPSK | melhor |
| **32-QAM** (pedido) | 5 | amplitude + fase | cruz (6×6 sem cantos) | a menor das quatro | a maior |

**Trade-off geral:** mais bits/símbolo → mais dados na mesma banda, mas pontos mais próximos →
mais sensível a ruído. QAM ameniza isso usando grade em vez de círculo.

---

## 7. Como testar e visualizar no projeto

### Teste automático (sem GUI)
`python3 testes.py` roda a ida-e-volta de **todas** as portadoras (`ask`, `fsk`, `8psk`, `32qam`), com e
sem ruído (`[:len(bits)]` ignora o padding final), e confere que `MAPA_8PSK` tem 8 pontos no raio `V`
e `MAPA_32QAM` tem 32 pontos distintos. Procure as linhas `portadora '8psk' ...` etc.

### Experimento rápido no terminal (recomendo fazer e olhar os números)
Depois de implementar, module um fluxo com um símbolo de cada fase do 8PSK (8 símbolos = 24 bits = 800
amostras) e demodule: devem voltar os mesmos bits. Depois fatie o sinal em janelas de
`AMOSTRAS_POR_SIMBOLO` e chame `correlacionar` em cada uma: os pares `(I, Q)` caem sobre o círculo de
raio `V`, nos ângulos múltiplos de 45°. Repita com 32-QAM e confira os 32 pontos da cruz.

### Na GUI
1. Digite um texto curto, escolha **mod. portadora = 8PSK** (ou ASK/FSK/32-QAM).
2. Aba **Transmissor**: veja o gráfico do sinal modulado (a portadora "trocando de fase/amplitude").
3. Aumente o **σ** do ruído aos poucos e observe na aba **Receptor**: o sinal recebido fica "borrado"
   e, passando da capacidade de decisão, o texto recuperado começa a sair com `�`.
4. Compare a robustez: com o mesmo σ, **ASK** erra antes de **8PSK**; **32-QAM** (5 bits/símbolo, pontos
   mais próximos) costuma errar antes que o 8PSK. Isso reproduz o trade-off do quadro-resumo — e dá
   um ótimo gráfico para o relatório.

### Como ligar o teste à teoria
- O par `(I, Q)` que `correlacionar` devolve **é** a coordenada do ponto na constelação dos slides.
- Sem ruído, o ponto cai exato em cima do símbolo; com ruído, ele se desloca, e a decisão de mínima
  distância "arredonda" para o símbolo certo — até o ruído ser grande demais e arredondar para o
  vizinho (= bit errado).

---

## 8. Pontos que o professor gosta de cobrar

1. **Diferença I/Q e o porquê de cos/−sen serem ortogonais** (base da detecção coerente).
2. **Gray code**: por que reduz a taxa de erro de *bit* (não de *símbolo*) — vizinho errado = 1 bit só.
3. **Trade-off bits/símbolo × distância × ruído** (8PSK vs QPSK; 32-QAM vs 8PSK).
4. **ASK é a mais sensível a ruído; PSK a mais usada**; FSK mais robusta que ASK mas gasta banda.
5. **Por que a constelação do 32-QAM é em cruz** e por que a decisão não pode ser feita por eixo.
6. Diferença entre **demodulação coerente** (correlação com portadora de referência — ASK/PSK/QAM no
   projeto) e **não-coerente por energia** (FSK no projeto).

---

## 9. Código de referência — `camada_fisica.py`

> Código **testado** (ida e volta, com e sem ruído, e a simulação completa), no mesmo formato das
> assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha antes de
> colar; o professor pergunta.

Os parâmetros globais (`V`, `AMOSTRAS_POR_BIT`...) são os do esqueleto.

### Banda-base: NRZ-Polar, Manchester (IEEE 802.3) e Bipolar (AMI)

Manchester segue o slide 8 do `CF - 10` (dado XOR clock): bit 1 = alto→baixo, bit 0 = baixo→alto. **Conferir no slide:** o primeiro resumo diz o contrário (ver `referencia-slides-detalhes.md`).

```python
# ------------------------------ banda-base --------------------------------
def modular_nrz_polar(bits):
    """1 -> +V, 0 -> -V durante todo o bit."""
    sinal = []
    for bit in bits:
        nivel = V if bit == 1 else -V
        sinal += [nivel] * AMOSTRAS_POR_BIT
    return sinal


def demodular_nrz_polar(sinal):
    """Média das amostras do bit: > 0 -> 1."""
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        bits.append(1 if media > 0 else 0)
    return bits


def modular_manchester(bits):
    """Slides CF-10 (dado XOR clock): 1 = alto->baixo, 0 = baixo->alto."""
    metade = AMOSTRAS_POR_BIT // 2
    resto = AMOSTRAS_POR_BIT - metade
    sinal = []
    for bit in bits:
        if bit == 1:
            sinal += [V] * metade + [-V] * resto
        else:
            sinal += [-V] * metade + [V] * resto
    return sinal


def demodular_manchester(sinal):
    """Compara a média das duas metades: 1ª maior que a 2ª -> bit 1."""
    metade = AMOSTRAS_POR_BIT // 2
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        m1 = sum(sinal[k:k + metade]) / metade
        m2 = sum(sinal[k + metade:k + AMOSTRAS_POR_BIT]) / (AMOSTRAS_POR_BIT - metade)
        bits.append(1 if m1 > m2 else 0)
    return bits


def modular_bipolar(bits):
    """AMI: 0 -> 0 V; cada 1 alterna entre +V e -V."""
    sinal = []
    polaridade = V
    for bit in bits:
        if bit == 0:
            sinal += [0.0] * AMOSTRAS_POR_BIT
        else:
            sinal += [polaridade] * AMOSTRAS_POR_BIT
            polaridade = -polaridade
    return sinal


def demodular_bipolar(sinal):
    """|média| > V/2 -> 1 (em qualquer polaridade)."""
    bits = []
    for k in range(0, len(sinal) - AMOSTRAS_POR_BIT + 1, AMOSTRAS_POR_BIT):
        media = sum(sinal[k:k + AMOSTRAS_POR_BIT]) / AMOSTRAS_POR_BIT
        bits.append(1 if abs(media) > V / 2 else 0)
    return bits
```


### Auxiliares da portadora (I/Q, correlação, padding, mínima distância)

`_modular_por_constelacao` e `_demodular_por_constelacao` evitam repetir o mesmo laço em 8PSK e 32-QAM.

```python
# ------------------------ auxiliares de portadora -------------------------
def onda(i, q, ciclos):
    """Um símbolo: s[n] = I*cos(2*pi*ciclos*n/N) - Q*sen(2*pi*ciclos*n/N)."""
    N = AMOSTRAS_POR_SIMBOLO
    amostras = []
    for n in range(N):
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
    return amostras


def correlacionar(simbolo, ciclos):
    """Inverso de onda(): recupera (I, Q) por correlação com cos e -sen."""
    N = len(simbolo)
    soma_cos = 0.0
    soma_sen = 0.0
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / N
        soma_cos += amostra * math.cos(angulo)
        soma_sen += amostra * math.sin(angulo)
    return 2 / N * soma_cos, -2 / N * soma_sen


def pad(bits, tamanho):
    """Completa com zeros até um múltiplo de `tamanho`."""
    resto = len(bits) % tamanho
    if resto == 0:
        return bits
    return bits + [0] * (tamanho - resto)


def bits_do_ponto_mais_proximo(i, q, constelacao):
    """Decisão de mínima distância sobre {bits: (I_ref, Q_ref)}."""
    melhor_bits, menor_dist = None, None
    for bits_simbolo, (i_ref, q_ref) in constelacao.items():
        dist = (i_ref - i) ** 2 + (q_ref - q) ** 2     # sem raiz: só comparamos
        if menor_dist is None or dist < menor_dist:
            menor_dist, melhor_bits = dist, bits_simbolo
    return list(melhor_bits)


def _modular_por_constelacao(bits, bits_por_simbolo, constelacao):
    """Agrupa os bits, busca (I, Q) na constelação e gera os símbolos."""
    bits = pad(bits, bits_por_simbolo)
    sinal = []
    for k in range(0, len(bits), bits_por_simbolo):
        i, q = constelacao[tuple(bits[k:k + bits_por_simbolo])]
        sinal += onda(i, q, CICLOS_PORTADORA)
    return sinal


def _demodular_por_constelacao(sinal, constelacao):
    """Correlaciona cada símbolo e decide pelo ponto mais próximo."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits += bits_do_ponto_mais_proximo(i, q, constelacao)
    return bits
```


### ASK e FSK

```python
# --------------------------------- ASK ------------------------------------
def modular_ask(bits):
    """1 -> portadora com amplitude V; 0 -> 0 V."""
    sinal = []
    for bit in bits:
        sinal += onda(V if bit == 1 else 0.0, 0.0, CICLOS_PORTADORA)
    return sinal


def demodular_ask(sinal):
    """Amplitude = hypot(I, Q) comparada a V/2."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        i, q = correlacionar(sinal[k:k + N], CICLOS_PORTADORA)
        bits.append(1 if math.hypot(i, q) > V / 2 else 0)
    return bits


# --------------------------------- FSK ------------------------------------
def modular_fsk(bits):
    """0 -> CICLOS_FSK[0] ciclos/símbolo; 1 -> CICLOS_FSK[1]."""
    sinal = []
    for bit in bits:
        sinal += onda(V, 0.0, CICLOS_FSK[bit])
    return sinal


def demodular_fsk(sinal):
    """Escolhe a frequência com mais energia (detecção não-coerente)."""
    bits = []
    N = AMOSTRAS_POR_SIMBOLO
    for k in range(0, len(sinal) - N + 1, N):
        simbolo = sinal[k:k + N]
        e0 = math.hypot(*correlacionar(simbolo, CICLOS_FSK[0]))
        e1 = math.hypot(*correlacionar(simbolo, CICLOS_FSK[1]))
        bits.append(1 if e1 > e0 else 0)
    return bits
```


### 8PSK (Gray, 3 bits por símbolo)

A sequência Gray (000, 001, 011, 010, 110, 111, 101, 100 a cada 45°) é a dos slides `CF - 12` (5 e 9). As coordenadas (I, Q) não constam nos slides: usamos raio V.

```python
# --------------------------------- 8PSK -----------------------------------
GRAY_3_BITS = [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0),
               (1, 1, 0), (1, 1, 1), (1, 0, 1), (1, 0, 0)]     # em ordem de fase
MAPA_8PSK = {rotulo: (V * math.cos(math.radians(45 * k)),
                      V * math.sin(math.radians(45 * k)))
             for k, rotulo in enumerate(GRAY_3_BITS)}


def modular_8psk(bits):
    """3 bits por símbolo, 8 fases de 45 graus no círculo de raio V."""
    return _modular_por_constelacao(bits, 3, MAPA_8PSK)


def demodular_8psk(sinal):
    return _demodular_por_constelacao(sinal, MAPA_8PSK)
```


### 32-QAM (constelação em cruz, 5 bits por símbolo)

Os slides (`CF - 13`, slide 4) mostram só o desenho da cruz; níveis de I/Q e rotulagem **não constam**. **Decisão de projeto** (`docs/DECISOES.md`): níveis ±1, ±3, ±5 vezes V/5, sem os cantos; rótulo de 5 bits = 2 bits de quadrante (Gray) + 3 bits de posição (Gray ao longo do ciclo de 8 pontos de cada quadrante). Gray perfeito não existe na cruz: dos 52 pares de vizinhos, 48 diferem em 1 bit e 4 em 3 bits.

```python
# -------------------------------- 32-QAM ----------------------------------
# Cruz: grade 6x6 de níveis {-5,-3,-1,1,3,5} sem os 4 cantos (36 - 4 = 32).
# Rotulagem "Gray quase perfeito" de 5 bits = 2 bits de QUADRANTE + 3 bits de
# POSIÇÃO dentro do quadrante:
#   - quadrante em Gray ao redor da origem: (+,+)=00, (-,+)=01, (-,-)=11, (+,-)=10;
#   - cada quadrante tem 8 pontos (3x3 menos o canto); eles formam um CICLO de
#     vizinhos e recebem os rótulos Gray de 3 bits ao longo desse ciclo.
# A posição só depende de (|I|, |Q|), então dois pontos vizinhos de quadrantes
# diferentes diferem só nos bits de quadrante (1 bit). Gray perfeito é
# impossível na cruz: alguns vizinhos dentro do quadrante diferem em mais bits.
ESCALA_QAM = V / 5
CICLO_QUADRANTE = [(1, 1), (3, 1), (5, 1), (5, 3), (3, 3), (3, 5), (1, 5), (1, 3)]
QUADRANTES = {(1, 1): (0, 0), (-1, 1): (0, 1), (-1, -1): (1, 1), (1, -1): (1, 0)}
MAPA_32QAM = {}
for (sinal_i, sinal_q), bits_quadrante in QUADRANTES.items():
    for posicao, (abs_i, abs_q) in enumerate(CICLO_QUADRANTE):
        gray_3 = GRAY_3_BITS[posicao]                  # 000,001,011,010,110,111,101,100
        MAPA_32QAM[bits_quadrante + gray_3] = (sinal_i * abs_i * ESCALA_QAM,
                                               sinal_q * abs_q * ESCALA_QAM)


def modular_32qam(bits):
    """5 bits por símbolo sobre a constelação em cruz."""
    return _modular_por_constelacao(bits, 5, MAPA_32QAM)


def demodular_32qam(sinal):
    return _demodular_por_constelacao(sinal, MAPA_32QAM)
```


### Despacho (interface única usada pelo simulador e pela GUI)

```python
# -------------------------------- despacho --------------------------------
MODULACOES_DIGITAIS = {"nrz": (modular_nrz_polar, demodular_nrz_polar),
                       "manchester": (modular_manchester, demodular_manchester),
                       "bipolar": (modular_bipolar, demodular_bipolar)}
MODULACOES_PORTADORA = {"ask": (modular_ask, demodular_ask),
                        "fsk": (modular_fsk, demodular_fsk),
                        "8psk": (modular_8psk, demodular_8psk),
                        "32qam": (modular_32qam, demodular_32qam)}


def modular_digital(bits, tipo):
    return MODULACOES_DIGITAIS[tipo][0](bits)


def demodular_digital(sinal, tipo):
    return MODULACOES_DIGITAIS[tipo][1](sinal)


def modular_portadora(bits, tipo):
    if tipo == "nenhuma":
        return None
    return MODULACOES_PORTADORA[tipo][0](bits)


def demodular_portadora(sinal, tipo):
    return MODULACOES_PORTADORA[tipo][1](sinal)
```


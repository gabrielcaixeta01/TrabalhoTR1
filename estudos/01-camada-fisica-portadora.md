# Camada Física — Modulação por Portadora (ASK, FSK, PSK/QPSK, 16-QAM)

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

```python
def onda(i, q, ciclos):
    # fórmula: s(t) = I·cos(2π·f·t) − Q·sen(2π·f·t)
    # i e q são as coordenadas do ponto na constelação escolhido pelos bits
    N = AMOSTRAS_POR_SIMBOLO
    for n in range(N):
        # n vai de 0 a N-1; n/N é a fração do símbolo percorrida (0 a ~1)
        # multiplicar por ciclos converte para "quantos ciclos completos já foram"
        # multiplicar por 2π converte para radianos → ângulo da portadora nessa amostra
        angulo = 2 * math.pi * ciclos * n / N
        # aplica a fórmula I/Q: I escala o cosseno, Q escala o seno (com sinal negativo)
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
```

`onda` é o **modulador genérico** (compare com o "Modulador genérico PSK" das págs. 11-20 do CF-12:
conversor serial→paralelo, associação de fase ao símbolo, canais I e Q, gerador de portadora
`cos ωc·t` / `−sen ωc·t`, e o somador `S(t) = I(t) + Q(t)`).

`correlacionar` é o **demodulador genérico** (detecção coerente): projeta o sinal recebido sobre
`cos` e `−sen` de referência para recuperar `(I, Q)`:

```python
def correlacionar(simbolo, ciclos):
    N = len(simbolo)
    soma_cos = 0.0
    soma_sen = 0.0
    # enumerate dá (n, amostra): n é o índice, amostra é o valor em Volts
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / N
        # produto ponto a ponto: multiplica o sinal recebido pela portadora de referência
        # somar todos os produtos é o "produto interno" (correlação / integral discreta)
        soma_cos += amostra * math.cos(angulo)   # projeta sobre o eixo I
        soma_sen += amostra * math.sin(angulo)   # projeta sobre o eixo Q
    # 2/N normaliza: sem isso a soma cresceria com N e não voltaria à amplitude original
    i =  2/N * soma_cos
    q = -2/N * soma_sen   # sinal negativo porque a fórmula usa −Q·sen (ver onda())
    return i, q
```

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

```python
def modular_ask(bits):
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, CICLOS_PORTADORA)   # I=V, Q=0 → portadora ligada
        else:
            sinal += onda(0.0, 0.0, CICLOS_PORTADORA) # I=0, Q=0 → portadora desligada (silêncio)
```

Demodulação: `correlacionar` devolve `(I, Q)`; a amplitude do símbolo é `√(I² + Q²)` — a distância
do ponto à origem no plano I/Q. Compara com o **limiar V/2** (meio do caminho entre 0 e V):

```python
def demodular_ask(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
    # math.hypot(i, q) = √(i² + q²) = amplitude do símbolo recebido
    # se amplitude > V/2 → estava mais perto de V → bit 1
    # se amplitude ≤ V/2 → estava mais perto de 0 → bit 0
    if math.hypot(i, q) > V / 2:
        bits.append(1)
    else:
        bits.append(0)
```

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

```python
def modular_fsk(bits):
    f0, f1 = CICLOS_FSK   # ex: f0=2 ciclos/símbolo, f1=4 ciclos/símbolo
    for bit in bits:
        if bit == 1:
            sinal += onda(V, 0.0, f1)   # amplitude V, frequência alta (f1)
        else:
            sinal += onda(V, 0.0, f0)   # amplitude V, frequência baixa (f0)
```

Demodulação **não-coerente por energia**: correlaciona o símbolo com cada uma das duas frequências
e mede a energia `√(I² + Q²)` em cada uma — a frequência com mais energia é a que foi transmitida:

```python
def demodular_fsk(sinal):
    # correlacionar projeta o símbolo sobre a portadora de f0 e de f1 separadamente
    # math.hypot(*...) desempacota o par (i, q) e calcula √(i²+q²) = energia naquela frequência
    e0 = math.hypot(*correlacionar(simbolo, f0))   # quanta energia em f0?
    e1 = math.hypot(*correlacionar(simbolo, f1))   # quanta energia em f1?
    # a frequência com mais energia é a que foi transmitida
    if e1 > e0:
        bits.append(1)
    else:
        bits.append(0)
```

> **FSK é o único que não cabe no plano I/Q de uma só portadora**, justamente porque a frequência muda.
> Por isso a demodulação dele compara energia em duas frequências em vez de ler um ponto da constelação.

---

## 4. PSK — Phase Shift Keying e o QPSK

**Ideia (CF-11 pág. 12; CF-12 inteiro):** amplitude e frequência constantes; o bit muda a **fase**.
É a técnica **mais adotada** em comunicação de dados: maior eficiência espectral e maior tolerância a
ruído que ASK/FSK.

### BPSK (PSK binário) — base teórica

1 bit por símbolo, 2 fases:
- bit 0 → fase 0°  → ponto `(+A, 0)`
- bit 1 → fase 180° → ponto `(−A, 0)`

Os dois pontos ficam **o mais longe possível** um do outro no círculo (distância 2A), por isso o BPSK
é bem robusto. O projeto não implementa BPSK isolado, mas ele é o degrau conceitual para o QPSK.

### QPSK — Quadrature PSK (o que o trabalho pede)

**2 bits por símbolo** (um *dibit*), 4 fases igualmente espaçadas no círculo. Dobra a taxa de
transmissão em relação ao BPSK usando a mesma banda. As 4 fases (CF-12, pág. 8, "QPSK(1)"):
45°, 135°, 225°, 315°.

**Codificação de Gray (essencial — CF-12, pág. 28-31):** os dibits são atribuídos às fases de forma
que **vizinhos no círculo diferem em apenas 1 bit**. Assim, se o ruído empurrar o ponto recebido para
o símbolo vizinho, erra-se **só 1 bit** em vez de 2. O slide destaca isso:
"Se um dibit for detectado errado, refere-se a apenas um bit errado".

Constelação Gray do projeto (`MAPA_QPSK`), com `A = V/√2`:

| dibit | fase | (I, Q) |
|---|---|---|
| 00 | 45°  | (+A, +A) |
| 01 | 135° | (−A, +A) |
| 11 | 225° | (−A, −A) |
| 10 | 315° | (+A, −A) |

Repare que andar pelos vizinhos `00 → 01 → 11 → 10` muda **1 bit de cada vez** — isso é Gray.
Usar `A = V/√2` mantém a amplitude total `√(I²+Q²) = V` em todos os pontos (PSK = amplitude constante):
`√( (V/√2)² + (V/√2)² ) = √( V²/2 + V²/2 ) = √V² = V`.

```python
# A = V/√2 garante que todos os pontos fiquem no círculo de raio V:
# √(A² + A²) = √(2·A²) = A·√2 = (V/√2)·√2 = V ✓
A_QPSK = V / math.sqrt(2)
MAPA_QPSK = {(0,0): (A_QPSK, A_QPSK), (0,1): (-A_QPSK, A_QPSK),
              (1,1): (-A_QPSK, -A_QPSK), (1,0): (A_QPSK, -A_QPSK)}

def modular_qpsk(bits):
    bits = pad(bits, 2)           # garante número par de bits (QPSK lê 2 por vez)
    for k in range(0, len(bits), 2):
        # lê o dibit e busca o ponto (I, Q) correspondente na constelação
        i, q = MAPA_QPSK[(bits[k], bits[k+1])]
        sinal += onda(i, q, CICLOS_PORTADORA)
```

Demodulação: recupera `(I, Q)` por correlação e escolhe o **ponto da constelação mais próximo**
(decisão de mínima distância = menor `√((I_ref−I)² + (Q_ref−Q)²)`) — é o que dá robustez ao ruído:

```python
def demodular_qpsk(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
    # com ruído, (i, q) não cai exato num ponto; bits_do_ponto_mais_proximo
    # percorre a constelação e devolve o dibit do ponto geometricamente mais perto
    bits += bits_do_ponto_mais_proximo(i, q, MAPA_QPSK)
```

> **8PSK / 16PSK (CF-12 págs. 40-41):** mesma ideia com 8 ou 16 fases (3 ou 4 bits/símbolo). O slide
> avisa o trade-off central de PSK: **mais fases → pontos mais próximos no círculo → menos tolerância
> a ruído**. O trabalho não pede, mas a frase cai em prova.

---

## 5. 16-QAM — Quadrature Amplitude Modulation

**Ideia (CF-13):** combinar variação de **fase E amplitude**. Em vez de pontos só num círculo (PSK),
a constelação vira uma **grade 4×4 = 16 pontos** → **4 bits por símbolo** (*quadribit*).

A sacada do QAM sobre o PSK de mesma ordem: espalhar 16 pontos numa **grade** deixa os vizinhos mais
distantes do que espalhar 16 pontos num **círculo**. O slide CF-13 (pág. 3) quantifica:
**16-QAM tolera ~0,81 dB mais ruído gaussiano que 16-PSK**.

No projeto, os 4 bits são divididos: os 2 primeiros escolhem o nível de **I**, os 2 últimos o nível de
**Q**, ambos sobre os níveis Gray `{−3, −1, +1, +3}` escalados por `V/3`:

```python
# níveis inteiros {-3,-1,1,3} com código Gray: vizinhos diferem em 1 bit
# (00→-3, 01→-1, 11→+1, 10→+3): andar pelos vizinhos muda 1 bit por vez
NIVEIS_GRAY = {(0,0): -3, (0,1): -1, (1,1): 1, (1,0): 3}
# escala V/3 faz o nível máximo (3) virar exatamente V: 3 × (V/3) = V
ESCALA_QAM  = V / 3

def modular_16qam(bits):
    bits = pad(bits, 4)   # garante múltiplo de 4 (16-QAM lê 4 bits por vez)
    for k in range(0, len(bits), 4):
        # bits k,k+1 determinam o nível de I; bits k+2,k+3 determinam o nível de Q
        # cada nível é um dos 4 valores da grade: -3,-1,+1,+3 (escalados)
        i = NIVEIS_GRAY[(bits[k],   bits[k+1])] * ESCALA_QAM
        q = NIVEIS_GRAY[(bits[k+2], bits[k+3])] * ESCALA_QAM
        sinal += onda(i, q, CICLOS_PORTADORA)
```

Demodulação: como a constelação é um **produto cartesiano** (grade), os eixos I e Q são
independentes — decide-se cada um separadamente, escolhendo o nível `{−3,−1,1,3}·(V/3)` mais
próximo do valor medido:

```python
def demodular_16qam(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
    # decide o eixo I e o eixo Q separadamente (possível porque a grade é produto cartesiano)
    # cada chamada a decidir_nivel_gray devolve 2 bits (o par Gray do nível mais próximo)
    bits += decidir_nivel_gray(i) + decidir_nivel_gray(q)
```

> ⚠️ **Atenção à tabela do slide CF-13 (pág. 5).** A tabela "No./Quadribit/Q/I/Amplitude/Fase" tem
> inconsistências internas (algumas linhas listam amplitude/fase que não batem com o par (I,Q) ao lado,
> e há valores de I/Q repetidos com quadribits diferentes). **Não decore os valores numéricos daquela
> tabela.** O que vale e cai em prova é o **conceito**: 16-QAM = grade 4×4, 4 bits/símbolo, Gray em
> cada eixo, melhor que 16-PSK em ruído. O mapeamento Gray correto é o do código acima.

---

## 6. Quadro-resumo (cola de prova)

| Modulação | Bits/símbolo | O que varia | Constelação | Robustez a ruído | Eficiência espectral |
|---|---|---|---|---|---|
| ASK | 1 | amplitude (on/off) | 2 pts no eixo I | pior | baixa |
| FSK | 1 | frequência | 2 frequências | média | pior (usa 2 faixas) |
| BPSK | 1 | fase (0°/180°) | 2 pts opostos | ótima | média |
| QPSK | 2 | fase (4 ângulos) | 4 pts no círculo | boa | boa |
| 8PSK | 3 | fase (8 ângulos) | 8 pts no círculo | cai vs QPSK | melhor |
| 16-QAM | 4 | amplitude + fase | grade 4×4 | melhor que 16-PSK | alta |

**Trade-off geral:** mais bits/símbolo → mais dados na mesma banda, mas pontos mais próximos →
mais sensível a ruído. QAM ameniza isso usando grade em vez de círculo.

---

## 7. Como testar e visualizar no projeto

### Teste automático (sem GUI)
Em `testes.py`, o bloco "camada física" roda ida-e-volta de **todas** as portadoras, com e sem ruído:

```python
for tipo in fisica.MODULACOES_PORTADORA:           # ask, fsk, qpsk, 16qam
    sinal = fisica.modular_portadora(bits, tipo)
    demod = fisica.demodular_portadora(sinal, tipo)
    print(demod[:len(bits)] == bits)               # True — [:len(bits)] ignora o padding
    ruidoso = meio.transmitir(sinal, 0.0, 0.1)     # σ = 0.1
    print(fisica.demodular_portadora(ruidoso, tipo)[:len(bits)] == bits)   # True com ruído baixo
```

Rodar:
```bash
python3 testes.py        # procure as linhas "portadora 'qpsk' ..." etc.
```

### Experimento rápido no terminal (recomendo fazer e olhar os números)
```python
import camada_fisica as f
bits = [0,0, 0,1, 1,1, 1,0]          # um símbolo de cada fase em QPSK
sinal = f.modular_qpsk(bits)
print(len(sinal))                     # 4 símbolos × 100 amostras = 400
print(f.demodular_qpsk(sinal))        # deve devolver os mesmos bits

# inspecione a constelação que o receptor "vê":
from camada_fisica import correlacionar, AMOSTRAS_POR_SIMBOLO as N, CICLOS_PORTADORA as C
for k in range(0, len(sinal), N):
    print(correlacionar(sinal[k:k+N], C))   # imprime os pares (I,Q) ~ (±0.707, ±0.707)
```

### Na GUI
1. Digite um texto curto, escolha **mod. portadora = qpsk** (ou ask/fsk/16qam).
2. Aba **Transmissor**: veja o gráfico do sinal modulado (a portadora "trocando de fase/amplitude").
3. Aumente o **σ** do ruído aos poucos e observe na aba **Receptor**: o sinal recebido fica "borrado"
   e, passando da capacidade de decisão, o texto recuperado começa a sair com `�`.
4. Compare a robustez: com o mesmo σ, **ask** erra antes de **qpsk**; **16qam** (4 bits/símbolo, pontos
   mais próximos) costuma errar antes que qpsk. Isso reproduz na prática o trade-off do quadro-resumo.

### Como ligar o teste à teoria
- O par `(I, Q)` que `correlacionar` devolve **é** a coordenada do ponto na constelação dos slides.
- Sem ruído, o ponto cai exato em cima do símbolo; com ruído, ele se desloca, e a decisão de mínima
  distância (`bits_do_ponto_mais_proximo` / `decidir_nivel_gray`) "arredonda" para o símbolo certo —
  até o ruído ser grande demais e arredondar para o vizinho (= bit errado).

---

## 8. Pontos que o professor gosta de cobrar

1. **Diferença I/Q e o porquê de cos/−sen serem ortogonais** (base da detecção coerente).
2. **Gray code**: por que reduz a taxa de erro de *bit* (não de *símbolo*) — vizinho errado = 1 bit só.
3. **Trade-off bits/símbolo × distância × ruído** (a frase do 8PSK/16PSK e o 0,81 dB do 16-QAM).
4. **ASK é a mais sensível a ruído; PSK a mais usada**; FSK mais robusta que ASK mas gasta banda.
5. **16-QAM vs 16-PSK**: mesma quantidade de símbolos, mas a grade do QAM afasta mais os pontos.
6. Diferença entre **demodulação coerente** (correlação com portadora de referência — ASK/PSK/QAM no
   projeto) e **não-coerente por energia** (FSK no projeto).
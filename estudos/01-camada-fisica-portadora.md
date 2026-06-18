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
    # gera s(t) = I·cos(2π·f·t) − Q·sen(2π·f·t)
    for n in range(N):
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
```

`onda` é o **modulador genérico** (compare com o "Modulador genérico PSK" das págs. 11-20 do CF-12:
conversor serial→paralelo, associação de fase ao símbolo, canais I e Q, gerador de portadora
`cos ωc·t` / `−sen ωc·t`, e o somador `S(t) = I(t) + Q(t)`).

`correlacionar` é o **demodulador genérico** (detecção coerente): projeta o sinal recebido sobre
`cos` e `−sen` de referência para recuperar `(I, Q)`:

```python
def correlacionar(simbolo, ciclos):
    for n, amostra in enumerate(simbolo):
        angulo = 2 * math.pi * ciclos * n / N
        soma_cos += amostra * math.cos(angulo)
        soma_sen += amostra * math.sin(angulo)
    i =  2/N * soma_cos
    q = -2/N * soma_sen
    return i, q
```

**Por que funciona:** `cos` e `sen` são ortogonais ao longo de um número inteiro de ciclos.
Multiplicar o sinal recebido por `cos(ωc·t)` e somar (= produto interno / integral) "filtra" só a
componente I; o mesmo com `−sen` filtra Q. O fator `2/N` é a normalização que devolve a amplitude original.
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
        sinal += onda(V if bit == 1 else 0.0, 0.0, CICLOS_PORTADORA)  # I=V ou 0, Q=0
```

Demodulação: mede a amplitude `√(I²+Q²)` de cada símbolo e compara com o **limiar V/2**
(meio do caminho entre 0 e V):

```python
def demodular_ask(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
    bits.append(1 if math.hypot(i, q) > V/2 else 0)
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
    f0, f1 = CICLOS_FSK
    for bit in bits:
        sinal += onda(V, 0.0, f1 if bit == 1 else f0)  # mesma amplitude, frequência diferente
```

Demodulação **não-coerente por energia**: mede quanta energia o símbolo tem em `f0` e em `f1`,
escolhe a maior. Note que aqui `correlacionar` é chamado com cada uma das duas frequências:

```python
def demodular_fsk(sinal):
    e0 = math.hypot(*correlacionar(simbolo, f0))   # energia em f0
    e1 = math.hypot(*correlacionar(simbolo, f1))   # energia em f1
    bits.append(1 if e1 > e0 else 0)
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

Constelação Gray do projeto (`_MAPA_QPSK`), com `A = V/√2`:

| dibit | fase | (I, Q) |
|---|---|---|
| 00 | 45°  | (+A, +A) |
| 01 | 135° | (−A, +A) |
| 11 | 225° | (−A, −A) |
| 10 | 315° | (+A, −A) |

Repare que andar pelos vizinhos `00 → 01 → 11 → 10` muda **1 bit de cada vez** — isso é Gray.
Usar `A = V/√2` mantém a amplitude total `√(I²+Q²) = V` em todos os pontos (PSK = amplitude constante).

```python
_A_QPSK = V / math.sqrt(2)
_MAPA_QPSK = {(0,0): (_A,_A), (0,1): (-_A,_A), (1,1): (-_A,-_A), (1,0): (_A,-_A)}

def modular_qpsk(bits):
    bits = pad(bits, 2)                       # completa para nº par de bits
    for k in range(0, len(bits), 2):
        i, q = _MAPA_QPSK[(bits[k], bits[k+1])]
        sinal += onda(i, q, CICLOS_PORTADORA)
```

Demodulação: recupera `(I,Q)` por correlação e escolhe o **ponto da constelação mais próximo**
(decisão de mínima distância) — é o que dá robustez ao ruído:

```python
def demodular_qpsk(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
    bits += bits_do_ponto_mais_proximo(i, q, _MAPA_QPSK)
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
_NIVEIS_GRAY = {(0,0): -3, (0,1): -1, (1,1): 1, (1,0): 3}   # Gray: vizinhos diferem em 1 bit
_ESCALA_QAM  = V / 3                                         # nível máximo = ±V

def modular_16qam(bits):
    bits = pad(bits, 4)
    for k in range(0, len(bits), 4):
        i = _NIVEIS_GRAY[(bits[k],   bits[k+1])] * _ESCALA_QAM
        q = _NIVEIS_GRAY[(bits[k+2], bits[k+3])] * _ESCALA_QAM
        sinal += onda(i, q, CICLOS_PORTADORA)
```

Demodulação: como a constelação é um **produto cartesiano** (grade), pode-se decidir cada eixo
separadamente — escolhe o nível `{−3,−1,1,3}` mais próximo do I medido e do Q medido:

```python
def demodular_16qam(sinal):
    i, q = correlacionar(simbolo, CICLOS_PORTADORA)
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
    assert demod[:len(bits)] == bits               # [:len(bits)] ignora o padding
    ruidoso = meio.transmitir(sinal, 0.0, 0.1)     # σ = 0.1
    assert fisica.demodular_portadora(ruidoso, tipo)[:len(bits)] == bits
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
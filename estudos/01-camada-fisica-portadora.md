# Camada física - portadora

Este resumo acompanha `camada_fisica.py` e serve para revisar ASK, FSK, QPSK e 16-QAM antes da apresentação.

## ideia central

Na modulação por portadora, os bits escolhem uma onda senoidal. No projeto, quase tudo passa pela representação i/q:

```text
s(t) = i*cos(wt) - q*sin(wt)
```

O par `(i, q)` define amplitude e fase. Modular é escolher esse par a partir dos bits. Demodular é estimar `(i, q)` no receptor e voltar aos bits.

## funções principais

```python
def onda(i, q, ciclos):
    N = AMOSTRAS_POR_SIMBOLO
    amostras = []
    for n in range(N):
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
    return amostras
```

`onda` gera um símbolo. `ciclos` é a frequência medida em ciclos por símbolo.

```python
i = 2 / N * soma_cos
q = -2 / N * soma_sen
```

`correlacionar` mede quanto do sinal parece com cosseno e seno. Isso recupera as coordenadas aproximadas do símbolo recebido.

## ASK

ASK muda amplitude:

- bit 1: portadora com amplitude `V`;
- bit 0: amplitude `0`.

Defesa curta: é simples, mas ruído de amplitude pode confundir o receptor.

## FSK

FSK muda frequência:

- bit 0: `CICLOS_FSK[0]`;
- bit 1: `CICLOS_FSK[1]`.

O receptor compara a energia nas duas frequências e escolhe a maior.

## QPSK

QPSK transmite 2 bits por símbolo. O projeto usa mapeamento gray, então pontos vizinhos mudam só um bit.

```python
MAPA_QPSK = {
    (0, 0): (A_QPSK, A_QPSK),
    (0, 1): (-A_QPSK, A_QPSK),
    (1, 1): (-A_QPSK, -A_QPSK),
    (1, 0): (A_QPSK, -A_QPSK),
}
```

Defesa curta: QPSK aumenta taxa de bits por símbolo sem aproximar tanto os pontos quanto 16-QAM.

## 16-QAM

16-QAM transmite 4 bits por símbolo. Dois bits escolhem o eixo `i` e dois escolhem o eixo `q`.

```python
NIVEIS_GRAY = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
ESCALA_QAM = V / 3
```

Defesa curta: é mais eficiente, mas os pontos da constelação ficam mais próximos e o ruído causa erro com mais facilidade.

## padding

QPSK precisa de grupos de 2 bits. 16-QAM precisa de grupos de 4 bits. Quando faltam bits no último grupo, `pad` completa com zeros. Depois, o desenquadramento remove o excedente naturalmente.

## frase para apresentação

> A portadora transforma grupos de bits em pontos de constelação. O receptor usa correlação para estimar o ponto recebido e escolhe o ponto válido mais próximo.

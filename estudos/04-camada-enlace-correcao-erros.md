# Camada de enlace - hamming

Este resumo acompanha `camada_enlace.py` e cobre o hamming(8,4) estendido usado no projeto.

## detecção vs correção

Paridade, checksum e crc detectam erro, mas não indicam qual bit deve ser corrigido. Hamming adiciona paridades que permitem localizar erro simples.

## bloco hamming(8,4)

Cada 4 bits viram 8 bits:

```text
p1 p2 d1 p4 d2 d3 d4 p0
```

`p1`, `p2` e `p4` são as paridades de hamming. `p0` é a paridade geral.

## codificação

```python
p1 = (d1 + d2 + d4) % 2
p2 = (d1 + d3 + d4) % 2
p4 = (d2 + d3 + d4) % 2
bloco = [p1, p2, d1, p4, d2, d3, d4]
p0 = sum(bloco) % 2
```

## decodificação

```python
s1 = (bloco[0] + bloco[2] + bloco[4] + bloco[6]) % 2
s2 = (bloco[1] + bloco[2] + bloco[5] + bloco[6]) % 2
s4 = (bloco[3] + bloco[4] + bloco[5] + bloco[6]) % 2
sindrome = s4 * 4 + s2 * 2 + s1
par_geral = sum(bloco) % 2
```

## interpretação

| síndrome | paridade geral | resultado |
|---|---|---|
| 0 | par | sem erro |
| diferente de 0 | ímpar | erro simples, corrigível |
| 0 | ímpar | erro no `p0`, dados intactos |
| diferente de 0 | par | erro duplo, detectado e não corrigido |

## custo

O custo é alto: 4 bits de dados viram 8 bits. Em troca, o receptor corrige erro simples e detecta erro duplo.

## frase para apresentação

> A síndrome diz onde está o erro simples. A paridade geral impede que dois erros sejam confundidos com um erro simples corrigível.

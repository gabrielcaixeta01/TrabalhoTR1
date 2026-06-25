# Camada de enlace - enquadramento

Este resumo acompanha `camada_enlace.py` e cobre os três enquadramentos pedidos no enunciado.

## problema

A camada física entrega um fluxo contínuo de bits. A camada de enlace precisa separar esse fluxo em quadros. Enquadrar é marcar onde cada quadro começa e termina.

## contagem de caracteres

Formato:

```text
[1 byte com tamanho] [payload]
```

Código:

```python
n_bytes = len(payload) // 8
fluxo += bytes_para_bits([n_bytes])
fluxo += payload
```

Vantagem: simples e com pouco overhead.

Limitação: se o byte de contagem corromper, o receptor perde o alinhamento.

No projeto, o quadro final não pode passar de 255 bytes quando esse modo é usado, porque o tamanho cabe em apenas 1 byte.

## byte stuffing

Usa:

- `FLAG_BYTE = 0x7e`;
- `ESC_BYTE = 0x7d`.

Código:

```python
if byte in (FLAG_BYTE, ESC_BYTE):
    quadro.append(ESC_BYTE)
quadro.append(byte)
```

Defesa curta: se a flag ou o escape aparecerem como dado, o transmissor coloca `ESC` antes. O receptor entende que o próximo byte é dado literal.

## bit stuffing

Flag:

```text
01111110
```

Código:

```python
if uns == 5:
    trem.append(0)
    uns = 0
```

Defesa curta: depois de cinco bits 1 seguidos, o transmissor insere 0. Assim a sequência da flag não aparece dentro do payload.

## receptor

Cada modo tem uma função inversa:

- `desenquadrar_contagem`;
- `desenquadrar_bytes`;
- `desenquadrar_bits`.

O receptor devolve uma lista de payloads. Depois disso, `receber` aplica hamming e edc.

## frase para apresentação

> O enquadramento resolve o problema de fronteira dos quadros. Sem isso, o receptor teria apenas uma sequência contínua de bits sem saber onde cada mensagem começa ou termina.

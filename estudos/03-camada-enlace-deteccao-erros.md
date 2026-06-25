# Camada de enlace - detecção de erros

Este resumo acompanha `camada_enlace.py` e cobre paridade, checksum e crc-32.

## ideia central

Detecção de erros adiciona um campo redundante ao payload. No receptor, esse campo é verificado. Se não bater, algum bit foi alterado no caminho.

No código:

```python
ADICIONAR_EDC = {
    "nenhum": lambda b: b,
    "paridade": adicionar_paridade_par,
    "checksum": adicionar_checksum,
    "crc": adicionar_crc32,
}
```

## paridade par

Código:

```python
paridade = sum(bits) % 2
return bits + [0] * 7 + [paridade]
```

Defesa curta: a soma total de bits 1 precisa ser par. Detecta quantidade ímpar de erros, mas pode falhar com quantidade par.

No projeto, a paridade ocupa 1 byte para manter alinhamento com os enquadramentos por byte.

## checksum

Código:

```python
soma = soma_complemento1(bits_para_palavras16(bits))
checksum = (~soma) & 0xFFFF
```

Defesa curta: soma palavras de 16 bits em complemento de 1. No receptor, payload + checksum deve fechar em `0xffff`.

## crc-32

Código:

```python
for bit in reversed(byte):
    if (crc ^ bit) & 1:
        crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
    else:
        crc >>= 1
return crc ^ 0xFFFFFFFF
```

Defesa curta:

- implementado bit a bit;
- não usa `zlib`;
- usa o polinômio refletido `0xedb88320`;
- o vetor `123456789` gera `0xcbf43926`.

## ordem no transmissor

```text
payload -> edc -> hamming -> enquadramento
```

O edc vem antes do hamming para que a correção proteja também os bits de verificação.

## frase para apresentação

> Paridade é simples, checksum é intermediário e crc-32 é o detector mais forte do projeto, especialmente para erros em rajada.

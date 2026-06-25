# Pipeline completo e meio

Este resumo amarra `simulador.py`, `camada_aplicacao.py`, `camada_enlace.py`, `camada_fisica.py` e `meio_comunicacao.py`.

## fluxo completo

```text
texto -> bits -> enlace tx -> física tx -> meio -> física rx -> enlace rx -> texto
```

## aplicação

`camada_aplicacao.py` converte texto em bytes e bytes em bits:

```python
for byte in texto.encode("utf-8"):
    for i in range(7, -1, -1):
        bits.append((byte >> i) & 1)
```

No receptor, os bytes são reconstruídos e decodificados como texto.

## transmissor

`_rotina_tx` faz:

```text
texto -> bits da aplicação -> bits de enlace -> sinal banda-base -> sinal transmitido
```

Se há portadora, o sinal enviado ao meio é a portadora. Se não há, o sinal enviado é o banda-base.

## meio

O meio fica entre as filas tx e rx:

```python
sinal_limpo = fila_tx.get()
sinal_ruidoso = meio_comunicacao.transmitir(
    sinal_limpo, config["ruido_media"], config["ruido_sigma"])
fila_rx.put(sinal_ruidoso)
```

Código do ruído:

```python
return [amostra + random.gauss(media, sigma) for amostra in sinal]
```

`media` desloca o sinal. `sigma` controla a dispersão do ruído.

## receptor

`_rotina_rx` faz:

```text
sinal recebido -> bits físicos -> enlace recebe -> bits da aplicação -> texto
```

Se há portadora, o receptor demodula a portadora. Se não há, ele demodula diretamente o sinal banda-base ruidoso.

## métricas

Potência média:

```python
return sum(amostra * amostra for amostra in sinal) / len(sinal)
```

O simulador calcula potência do sinal e potência do ruído para exibir na interface.

## testes principais

`testes.py` valida:

- texto para bits e volta;
- enquadramentos;
- paridade, checksum e crc;
- hamming com erro simples e erro duplo;
- modulações com ruído controlado;
- simulação completa.

## frase para apresentação

> O simulador separa claramente tx, meio e rx: a thread transmissora gera o sinal, o meio soma ruído e a thread receptora reconstrói a mensagem.

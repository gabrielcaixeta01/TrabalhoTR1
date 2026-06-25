# Walkthrough do Simulador TR1

Este guia explica como a interface web se conecta ao codigo Python real, o
que cada camada faz por tras e como testar cada funcionalidade isoladamente.

## 1. Como rodar

Interface web local:

```bash
cd /Users/augustop/Github/TrabalhoTR1
/usr/bin/python3 simulador_web.py
```

Abra:

```text
http://127.0.0.1:8765
```

Suite completa de testes:

```bash
cd /Users/augustop/Github/TrabalhoTR1
/usr/bin/python3 testes.py
```

## 2. Ideia central do projeto

O fluxo completo e:

```text
texto -> bits -> quadros -> sinal eletrico -> canal com ruido -> sinal recebido -> bits -> texto
```

No transmissor, o projeto desce a pilha:

```text
Aplicacao -> Enlace -> Fisica -> Meio
```

No receptor, ele sobe a pilha:

```text
Meio -> Fisica -> Enlace -> Aplicacao
```

## 3. O que a interface web faz

A interface web nao reimplementa os algoritmos em JavaScript. Ela so coleta os
parametros na pagina, chama a API local `/api/simular` e mostra o resultado.

Trecho em `simulador_web.py`:

```python
def montar_resposta(payload):
    config = config_de_payload(payload)
    if not config["texto"]:
        raise ValueError("Digite um texto para transmitir.")

    resultado = simulador.executar_simulacao(config)
```

Ou seja: quem calcula CRC, Hamming, modulacao e ruido e o Python em
`simulador.py`, `camada_enlace.py`, `camada_fisica.py` e
`meio_comunicacao.py`.

## 4. O papel de cada controle da interface

| Controle | O que muda no codigo |
|---|---|
| Texto de entrada | Mensagem que vira bytes UTF-8 e depois bits |
| Tamanho maximo do quadro | Quantos bytes de aplicacao entram em cada quadro |
| Enquadramento | Como o receptor descobre onde cada quadro comeca e termina |
| Deteccao de erros | Redundancia anexada para detectar alteracao de bits |
| Correcao de erros | Hamming, usado para corrigir 1 erro por bloco |
| Modulacao digital | Como bits viram sinal banda-base |
| Modulacao por portadora | Como bits viram senoide modulada |
| Media do ruido | Deslocamento DC somado ao sinal |
| Slider de sigma do ruido | Intensidade aleatoria do ruido gaussiano |
| Intervalo continuo | Tempo entre simulacoes automaticas no modo continuo |
| Transmitir uma vez | Executa uma simulacao Python isolada |
| Iniciar continua | Repete a simulacao, gerando novo ruido a cada rodada |

## 5. Pipeline principal: `simulador.py`

O arquivo central e `simulador.py`. Ele cria uma thread TX, uma thread RX e usa
filas para representar o meio.

Trecho do transmissor:

```python
bits_app = camada_aplicacao.texto_para_bits(config["texto"])
bits_enlace = camada_enlace.transmitir(bits_app, config)
sinal_banda_base = camada_fisica.modular_digital(
    bits_enlace, config["mod_digital"])

if config["mod_portadora"] != "nenhuma":
    sinal_tx = camada_fisica.modular_portadora(
        bits_enlace, config["mod_portadora"])
else:
    sinal_tx = sinal_banda_base
```

Trecho do canal:

```python
sinal_limpo = fila_tx.get()
sinal_ruidoso = meio_comunicacao.transmitir(
    sinal_limpo, config["ruido_media"], config["ruido_sigma"])
fila_rx.put(sinal_ruidoso)
```

Trecho do receptor:

```python
bits_rx = camada_fisica.demodular_portadora(
    sinal_rx, config["mod_portadora"])
bits_app, relatorio = camada_enlace.receber(bits_rx, config)
resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)
```

## 6. Camada de aplicacao

Arquivo: `camada_aplicacao.py`.

Ela converte texto em bits e bits em texto. O texto e codificado em UTF-8.

Trecho:

```python
for byte in texto.encode("utf-8"):
    for i in range(7, -1, -1):
        bits.append((byte >> i) & 1)
```

Teste isolado:

```bash
/usr/bin/python3 - <<'PY'
import camada_aplicacao as app

bits = app.texto_para_bits("A")
print(bits)
print(app.bits_para_texto(bits))
PY
```

Saida esperada:

```text
[0, 1, 0, 0, 0, 0, 0, 1]
A
```

## 7. Camada de enlace

Arquivo: `camada_enlace.py`.

A camada de enlace faz tres coisas:

1. Enquadramento.
2. Deteccao de erros.
3. Correcao de erros.

### 7.1 Ordem no transmissor

Trecho:

```python
bloco = ADICIONAR_EDC[config["deteccao"]](bloco)
if config["correcao"] == "hamming":
    bloco = codificar_hamming(bloco)
payloads.append(bloco)
return ENQUADRAR[config["enquadramento"]](payloads)
```

Ordem:

```text
dados -> EDC -> Hamming -> enquadramento
```

O Hamming vem depois do EDC porque assim ele tambem protege os bits do
verificador.

### 7.2 Ordem no receptor

Trecho:

```python
payloads = DESENQUADRAR[config["enquadramento"]](bits)
if config["correcao"] == "hamming":
    payload, info["corrigidos"], info["erro_duplo"] = \
        decodificar_hamming(payload)
payload, info["edc_ok"] = VERIFICAR_EDC[config["deteccao"]](payload)
```

Ordem:

```text
desenquadramento -> Hamming -> EDC -> dados
```

## 8. Enquadramento

### Contagem de caracteres

Cada quadro comeca com 1 byte dizendo quantos bytes de payload vem depois.

Trecho:

```python
n_bytes = len(payload) // 8
fluxo += bytes_para_bits([n_bytes])
fluxo += payload
```

Vantagem: simples. Risco: se o byte de contagem corromper, o receptor perde o
alinhamento.

### Byte stuffing

Usa `FLAG = 0x7E` para delimitar quadros e `ESC = 0x7D` para escapar dados.

Trecho:

```python
if byte in (FLAG_BYTE, ESC_BYTE):
    quadro.append(ESC_BYTE)
quadro.append(byte)
```

Serve para impedir que um byte dos dados seja confundido com delimitador.

### Bit stuffing

Usa a flag `01111110`. Sempre que aparecem cinco bits `1` seguidos no payload,
o transmissor insere um `0`.

Trecho:

```python
if uns == 5:
    trem.append(0)
    uns = 0
```

Isso impede que a flag apareca dentro dos dados.

Teste dos tres enquadramentos:

```bash
/usr/bin/python3 - <<'PY'
import camada_enlace as e

payloads = [e.bytes_para_bits([0x7E, 0x7D, 0x41])]
for tipo in ("contagem", "bytes", "bits"):
    fluxo = e.ENQUADRAR[tipo](payloads)
    volta = e.DESENQUADRAR[tipo](fluxo)
    print(tipo, volta == payloads, len(fluxo), "bits")
PY
```

## 9. Deteccao de erros

### Paridade par

Adiciona um byte com 7 zeros e 1 bit de paridade. A soma total de bits `1`
precisa ser par.

Trecho:

```python
paridade = sum(bits) % 2
return bits + [0] * 7 + [paridade]
```

Detecta quantidade impar de erros. Pode falhar com quantidade par.

### Checksum

Soma palavras de 16 bits em complemento de 1. No receptor, payload + checksum
deve fechar em `0xFFFF`.

Trecho:

```python
soma = soma_complemento1(bits_para_palavras16(bits))
checksum = (~soma) & 0xFFFF
```

### CRC-32

Calcula o CRC-32 IEEE bit a bit, sem `zlib`.

Trecho:

```python
if (crc ^ bit) & 1:
    crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
else:
    crc >>= 1
```

Teste de deteccao:

```bash
/usr/bin/python3 - <<'PY'
import camada_aplicacao as app
import camada_enlace as e

dados = app.texto_para_bits("teste")
for tipo in ("paridade", "checksum", "crc"):
    pacote = e.ADICIONAR_EDC[tipo](dados)
    payload, ok = e.VERIFICAR_EDC[tipo](pacote)
    print(tipo, "integro:", ok and payload == dados)

    corrompido = pacote[:]
    corrompido[3] ^= 1
    _, ok = e.VERIFICAR_EDC[tipo](corrompido)
    print(tipo, "com erro detectado:", not ok)

print("CRC 123456789:", hex(e.calcular_crc32(app.texto_para_bits("123456789"))))
PY
```

O CRC conhecido deve sair:

```text
0xcbf43926
```

## 10. Correcao com Hamming

O projeto usa Hamming(8,4) estendido. Cada 4 bits de dados viram 8 bits:

```text
p1 p2 d1 p4 d2 d3 d4 p0
```

Ele corrige 1 erro por bloco e detecta erro duplo.

Trecho:

```python
sindrome = s4 * 4 + s2 * 2 + s1
par_geral = sum(bloco) % 2
if sindrome != 0 and par_geral == 1:
    bloco[sindrome - 1] ^= 1
```

Teste:

```bash
/usr/bin/python3 - <<'PY'
import camada_enlace as e

dados = [1, 0, 1, 1, 0, 1, 0, 0]
cod = e.codificar_hamming(dados)
print("codificado:", cod)

com_erro = cod[:]
com_erro[5] ^= 1
dec, corrigidos, duplo = e.decodificar_hamming(com_erro)
print("1 erro:", dec == dados, corrigidos, duplo)

com_erro[6] ^= 1
dec, corrigidos, duplo = e.decodificar_hamming(com_erro)
print("2 erros:", corrigidos, duplo)
PY
```

## 11. Camada fisica: banda-base

Arquivo: `camada_fisica.py`.

### NRZ-Polar

`1` vira `+V`, `0` vira `-V`.

Trecho:

```python
nivel = V if bit == 1 else -V
sinal += [nivel] * AMOSTRAS_POR_BIT
```

Demodulacao: media positiva vira `1`, media negativa vira `0`.

### Manchester

Sempre ha transicao no meio do bit:

```text
0: -V depois +V
1: +V depois -V
```

Demodulacao: compara a media da primeira metade com a segunda.

### Bipolar AMI

`0` vira `0 V`; cada `1` alterna `+V`, `-V`, `+V`, `-V`.

Teste banda-base:

```bash
/usr/bin/python3 - <<'PY'
import camada_fisica as f
import meio_comunicacao as m

bits = [1, 0, 1, 1, 0, 0, 1, 0]
for tipo in f.MODULACOES_DIGITAIS:
    sinal = f.modular_digital(bits, tipo)
    print(tipo, "sem ruido:", f.demodular_digital(sinal, tipo) == bits)

    ruidoso = m.transmitir(sinal, 0.0, 0.2)
    print(tipo, "com sigma=0.2:", f.demodular_digital(ruidoso, tipo) == bits)
PY
```

## 12. Camada fisica: portadora

As modulacoes por portadora usam a ideia I/Q:

```text
s(t) = I cos(2 pi f t) - Q sin(2 pi f t)
```

Trecho que gera uma onda:

```python
angulo = 2 * math.pi * ciclos * n / N
amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
```

Trecho que recupera I/Q:

```python
soma_cos += amostra * math.cos(angulo)
soma_sen += amostra * math.sin(angulo)
i = 2 / N * soma_cos
q = -2 / N * soma_sen
```

### ASK

Muda amplitude. `1` transmite portadora; `0` transmite quase nada.

### FSK

Muda frequencia. No projeto: 2 ciclos para `0`, 4 ciclos para `1`.

### QPSK

Usa 4 pontos de fase. Cada simbolo carrega 2 bits. Usa mapeamento Gray.

### 16-QAM

Usa grade 4x4. Cada simbolo carrega 4 bits. E mais eficiente, mas mais sensivel
a ruido porque os pontos ficam mais proximos.

Teste portadora:

```bash
/usr/bin/python3 - <<'PY'
import camada_fisica as f
import meio_comunicacao as m

bits = [1, 0, 1, 1, 0, 0, 1, 0]
for tipo in f.MODULACOES_PORTADORA:
    sinal = f.modular_portadora(bits, tipo)
    demod = f.demodular_portadora(sinal, tipo)
    print(tipo, "sem ruido:", demod[:len(bits)] == bits)

    ruidoso = m.transmitir(sinal, 0.0, 0.1)
    demod = f.demodular_portadora(ruidoso, tipo)
    print(tipo, "com sigma=0.1:", demod[:len(bits)] == bits)
PY
```

## 13. Meio de comunicacao e ruido

Arquivo: `meio_comunicacao.py`.

O canal soma ruido gaussiano independente em cada amostra:

```python
return [amostra + random.gauss(media, sigma) for amostra in sinal]
```

Se `sigma = 0` e `media = 0`, o canal e ideal.

```python
if sigma == 0 and media == 0:
    return list(sinal)
```

Potencia media:

```python
return sum(amostra * amostra for amostra in sinal) / len(sinal)
```

Interpretacao:

| Parametro | Efeito |
|---|---|
| `media` | desloca todas as amostras para cima/baixo |
| `sigma` | controla a dispersao aleatoria do ruido |
| potencia do ruido | cresce quando `sigma` cresce |

## 14. Como testar ruido na simulacao completa

Use este script para ver quando a transmissao comeca a falhar:

```bash
/usr/bin/python3 - <<'PY'
import random
import simulador

random.seed(7)
base = dict(
    simulador.CONFIG_PADRAO,
    texto="Ola, TR1!",
    enquadramento="bits",
    deteccao="crc",
    correcao="hamming",
    mod_digital="nrz",
    mod_portadora="qpsk",
)

for sigma in (0.0, 0.05, 0.10, 0.20, 0.40, 0.80):
    config = dict(base, ruido_media=0.0, ruido_sigma=sigma)
    r = simulador.executar_simulacao(config)
    quadros = r["rx_relatorio_quadros"]
    print("\nsigma =", sigma)
    print("texto:", repr(r["rx_texto"]))
    print("potencias:", round(r["potencia_sinal_w"], 4),
          round(r["potencia_ruido_w"], 4))
    print("quadros:", quadros)
PY
```

O comportamento esperado:

1. Com `sigma` baixo, o texto volta correto.
2. Com `sigma` medio, o Hamming pode corrigir alguns bits.
3. Com `sigma` alto, aparecem erros duplos, EDC falha ou o texto sai diferente.

## 15. Experimentos bons para a apresentacao

### Experimento seguro

Na interface:

```text
Enquadramento: FLAGs + insercao de bits
Deteccao: CRC-32
Correcao: Hamming
Modulacao digital: NRZ-Polar
Modulacao por portadora: QPSK
Ruido media: 0
Ruido sigma: 0.10
```

O texto deve ser recuperado corretamente.

### Mostrar efeito do ruido

Na interface, use o slider `Ruido - desvio sigma (V)` e repita com:

```text
sigma = 0.20
sigma = 0.40
sigma = 0.80
```

Para ver o ruido mudando em tempo real, clique em `Iniciar continua`.
Cada rodada chama novamente o Python, entao `random.gauss(media, sigma)` gera
novas amostras de ruido no canal.

Observe:

1. Potencia do ruido aumenta.
2. O grafico recebido fica mais deformado.
3. O relatorio dos quadros pode mostrar bits corrigidos por Hamming.
4. Em ruido alto, o texto recuperado pode sair com diferencas.

### Comparar modulacoes

Mantendo o mesmo texto e `sigma`, alterne:

```text
ASK -> FSK -> QPSK -> 16-QAM
```

O que defender:

1. ASK e sensivel a ruido de amplitude.
2. FSK separa os bits por frequencia.
3. QPSK carrega 2 bits por simbolo.
4. 16-QAM carrega 4 bits por simbolo, mas exige melhor SNR.

## 16. Como ler os resultados da interface

### Processamento por fase

A tabela `Processamento por fase` mostra, em texto normal, quanto cada etapa
recebeu, quanto entregou e quantos bits foram adicionados.

Exemplo com:

```text
Texto: teste
Enquadramento: Contagem de caracteres
Deteccao: Bit de paridade par
Correcao: Hamming
Portadora: QPSK
```

O diagnostico esperado e:

```text
Aplicacao: 5 bytes UTF-8 -> 40 bits
Deteccao: 40 bits -> 48 bits, adicionou 8 bits
Hamming: 48 bits -> 96 bits, adicionou 48 bits
Enquadramento: 96 bits -> 104 bits, adicionou 8 bits
QPSK: 104 bits -> 52 simbolos, 5200 amostras, adicionou 0 bits
```

Isso deixa claro que modulacao nao adiciona bits de informacao; ela muda a
representacao fisica. Quem adiciona redundancia no exemplo e a paridade, o
Hamming e o enquadramento.

### Transmissor (Tx)

Mostra:

1. Texto original.
2. Bits da aplicacao.
3. Bits de enlace depois de EDC, Hamming e enquadramento.
4. Sinal banda-base.
5. Sinal transmitido ao meio.

### Receptor (Rx)

Mostra:

1. Bits recuperados pela camada fisica.
2. Relatorio por quadro.
3. Bits finais da aplicacao.
4. Texto recuperado.
5. Sinal recebido com ruido.
6. Banda-base reconstruido.

## 17. Frases curtas para defesa

1. "A interface web e so visualizacao; a simulacao roda no Python."
2. "No TX, o enlace adiciona EDC, aplica Hamming e depois enquadra."
3. "No RX, a ordem e inversa: desenquadra, corrige com Hamming e verifica EDC."
4. "O ruido e AWGN: somamos uma amostra gaussiana a cada amostra do sinal."
5. "QPSK e 16-QAM usam I/Q; o receptor recupera I e Q por correlacao."
6. "Hamming(8,4) corrige erro simples e detecta erro duplo."
7. "CRC-32 e mais forte que paridade porque usa divisao polinomial em GF(2)."
8. "16-QAM carrega mais bits por simbolo, mas e mais sensivel a ruido."

# Pipeline Completo — Orquestração, Meio e Threads (visão de sistema)

> Material de estudo (prova + revisão do projeto TR1).
> Amarra os arquivos 01–04. Mapeado em: `simulador.py`, `camada_enlace.py`
> (`transmitir`/`receber`), `meio_comunicacao.py`, `camada_aplicacao.py`.

---

## 0. Para que serve este arquivo

Os arquivos 01–04 explicam cada protocolo isolado. Este mostra **como eles se encaixam** numa
transmissão completa de texto — que é a "visão geral do simulador" pedida na introdução do relatório
e o tipo de pergunta integradora que cai em prova ("descreva o caminho de uma mensagem do TX ao RX").

---

## 1. A pilha de camadas (modelo do enunciado)

O trabalho simula 3 camadas + o meio, espelhando o diagrama da Figura 1 do enunciado:

```
  APLICAÇÃO   texto ↔ bits                      (camada_aplicacao.py)
  ENLACE      enquadramento + EDC + Hamming      (camada_enlace.py)
  FÍSICA      banda-base + portadora             (camada_fisica.py)
  ─────────────────────────────────────────────
  MEIO        sinal em Volts + ruído gaussiano    (meio_comunicacao.py)
```

Cada camada tem um lado **TX** (desce a pilha) e um lado **RX** (sobe a pilha, caminho inverso).

---

## 2. O caminho de uma mensagem (TX → meio → RX)

```
  THREAD TX                        MEIO                      THREAD RX
  ─────────                        ────                      ─────────
  "Ola, TR1!"                                                "Ola, TR1!"
     │ aplicação: texto→bits                  bits→texto :aplicação │
  bits                                                          bits
     │ enlace.transmitir():                  enlace.receber(): │
     │   1. +EDC  2. +Hamming  3. enquadra    1. desenquadra    │
     │                                        2. Hamming corrige │
     │                                        3. verifica EDC    │
  quadros (bits)                                      quadros (bits)
     │ física: banda-base → portadora    demodula/decodifica :física │
  sinal (V) ──► [ + ruído gaussiano N(x,σ) ] ──► sinal (V) ruidoso
```

### Detalhe da camada de enlace no TX — `transmitir(bits, config)`

```python
def transmitir(bits, config):
    tam = config["tam_max_quadro"] * 8           # bloco em bits
    # valida limite de 255 bytes SE enquadramento = contagem
    ...
    payloads = []
    for i in range(0, len(bits), tam):           # 1. divide em blocos
        bloco = bits[i:i+tam]
        bloco = _ADICIONAR_EDC[config["deteccao"]](bloco)   # 2. +EDC
        if config["correcao"] == "hamming":
            bloco = codificar_hamming(bloco)                # 3. +Hamming (dobra)
        payloads.append(bloco)
    return _ENQUADRAR[config["enquadramento"]](payloads)    # 4. enquadra
```

**Ordem que cai em prova:** divide → EDC → Hamming → enquadra. O EDC antes do Hamming faz o Hamming
proteger também os bits de detecção.

### Detalhe da camada de enlace no RX — `receber(bits, config)`

```python
def receber(bits, config):
    payloads = _DESENQUADRAR[config["enquadramento"]](bits)   # 1. desenquadra
    for payload in payloads:
        if config["correcao"] == "hamming":
            payload, corrigidos, erro_duplo = decodificar_hamming(payload)  # 2. corrige
        payload, edc_ok = _VERIFICAR_EDC[config["deteccao"]](payload)       # 3. verifica
        bits_app += payload
        relatorio.append({...})    # por quadro: edc_ok, corrigidos, erro_duplo
    return bits_app, relatorio
```

A ordem inverte: desenquadra → Hamming corrige → EDC verifica. O `relatorio` (um dict por quadro)
alimenta a aba do receptor na GUI.

---

## 3. Aplicação — a fronteira texto ↔ bits

```python
def texto_para_bits(texto):
    for byte in texto.encode("utf-8"):       # UTF-8: acentos viram >1 byte
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)      # MSB primeiro

def bits_para_texto(bits):
    # agrupa de 8 em 8, remonta bytes, decodifica UTF-8
    return dados.decode("utf-8", errors="replace")   # bits corrompidos -> �
```

Convenção de **todo o simulador**: bits são `list[int]` de 0/1, MSB primeiro, sempre em múltiplos de 8.
O `errors="replace"` é o que faz um byte corrompido virar `�` em vez de derrubar o programa.

---

## 4. O meio — sinal elétrico + ruído gaussiano

O enunciado exige: sinal em **Volts/Watts** e ruído de uma **variável aleatória gaussiana n(x, σ)**.

```python
def transmitir(sinal, media, sigma):
    if sigma == 0 and media == 0:
        return list(sinal)                    # canal ideal
    return [a + random.gauss(media, sigma) for a in sinal]   # AWGN

def potencia_media(sinal):
    return sum(v*v for v in sinal) / len(sinal)   # P = média de v² (W em 1Ω)
```

- `media` (x): nível DC espúrio do canal (normalmente 0).
- `sigma` (σ): "intensidade" do ruído — quanto maior, mais o sinal chega distorcido.
- O ruído é **AWGN** (*Additive White Gaussian Noise*): somado **amostra a amostra**, independente.
- `potencia_media` permite calcular **SNR** (relação sinal-ruído) para a GUI/relatório.

> **Cai em prova:** ruído gaussiano é somado a cada amostra do sinal, não a cada bit. Por isso a
> resolução `AMOSTRAS_POR_BIT = 100` importa: o demodulador decide por **média** (banda-base) ou
> **correlação** (portadora) sobre as 100 amostras, e essa média/integração é o que "filtra" o ruído.

---

## 5. TX e RX como threads separadas — o "diferencial" do enunciado

O enunciado pede **"Programa/Thread TX"** e **"Programa/Thread RX"** separados. O projeto resolve com
`threading.Thread` + duas `queue.Queue` que fazem o papel do meio físico:

```python
def executar_simulacao(config):
    fila_tx, fila_rx = queue.Queue(), queue.Queue()
    th_tx = threading.Thread(target=_rotina_tx, args=(config, fila_tx, resultados))
    th_rx = threading.Thread(target=_rotina_rx, args=(config, fila_rx, resultados))
    th_tx.start(); th_rx.start()

    # CANAL: único ponto de contato entre as threads
    sinal_limpo = fila_tx.get()
    sinal_ruidoso = meio_comunicacao.transmitir(sinal_limpo,
                        config["ruido_media"], config["ruido_sigma"])
    fila_rx.put(sinal_ruidoso)

    th_tx.join(); th_rx.join()
    # métricas: potência do sinal, potência do ruído (para SNR)
```

A separação é didática e "rende pontos em Conceitos de TR1": o ruído é somado **entre** as duas
threads, isolando o meio como único ponto de contato — exatamente como no diagrama.

> Detalhe físico do RX: quando há portadora, o RX demodula a portadora para bits e **reconstrói** o
> banda-base só para exibição na GUI (`rx_sinal_banda_base`); a decodificação real vem da portadora.

---

## 6. Tabela mestra: requisito → arquivo → função

| Camada | Requisito | Arquivo | Função TX / RX |
|---|---|---|---|
| Aplicação | texto ↔ bits | `camada_aplicacao.py` | `texto_para_bits` / `bits_para_texto` |
| Enlace | contagem | `camada_enlace.py` | `enquadrar_contagem` / `desenquadrar_contagem` |
| Enlace | byte stuffing | `camada_enlace.py` | `enquadrar_bytes` / `desenquadrar_bytes` |
| Enlace | bit stuffing | `camada_enlace.py` | `enquadrar_bits` / `desenquadrar_bits` |
| Enlace | paridade | `camada_enlace.py` | `adicionar_paridade_par` / `verificar_paridade_par` |
| Enlace | checksum | `camada_enlace.py` | `adicionar_checksum` / `verificar_checksum` |
| Enlace | CRC-32 | `camada_enlace.py` | `adicionar_crc32` / `verificar_crc32` |
| Enlace | Hamming | `camada_enlace.py` | `codificar_hamming` / `decodificar_hamming` |
| Física | NRZ/Manchester/Bipolar | `camada_fisica.py` | `modular_digital` / `demodular_digital` |
| Física | ASK/FSK/QPSK/16-QAM | `camada_fisica.py` | `modular_portadora` / `demodular_portadora` |
| Meio | ruído AWGN | `meio_comunicacao.py` | `transmitir` / `potencia_media` |
| Simulador | orquestração TX/RX | `simulador.py` | `executar_simulacao`, `_rotina_tx`, `_rotina_rx` |

---

## 7. Como testar o sistema inteiro

### Suite completa (`testes.py`)
O bloco final faz **simulação ponta a ponta** combinando 3 enquadramentos × 5 opções de portadora,
conferindo que o texto recuperado == texto enviado:

```python
for enq in ("contagem", "bytes", "bits"):
    for port in ("nenhuma", "ask", "fsk", "qpsk", "16qam"):
        config = dict(simulador.CONFIG_PADRAO, texto=texto,
                      enquadramento=enq, mod_portadora=port, ruido_sigma=0.05)
        r = simulador.executar_simulacao(config)
        print(r["rx_texto"] == texto)   # True — texto recuperado sem erros
```

Rodar tudo:
```bash
python3 testes.py    # espera: "RESULTADO GERAL: TODOS OS TESTES PASSARAM"
```
(`random.seed(42)` torna os resultados reprodutíveis em qualquer máquina.)

### Simulação manual no terminal (sem GUI)
```python
import simulador
config = dict(simulador.CONFIG_PADRAO,
              texto="Teste de ponta a ponta!",
              enquadramento="bits", deteccao="crc", correcao="hamming",
              mod_portadora="qpsk", ruido_sigma=0.1)
r = simulador.executar_simulacao(config)
print("Texto RX:", r["rx_texto"])
print("Potência sinal (W):", r["potencia_sinal_w"])
print("Potência ruído (W):", r["potencia_ruido_w"])
for q in r["rx_relatorio_quadros"]:
    print(q)     # edc_ok, corrigidos, erro_duplo por quadro
```

### Na GUI (visão integrada)
1. Configure todas as camadas e o ruído, clique **Transmitir**.
2. Aba **Transmissor**: bits após cada etapa (aplicação → enlace → física) e o gráfico do sinal.
3. Aba **Receptor**: sinal ruidoso recebido, bits demodulados, relatório por quadro e texto final.
4. Suba o σ gradualmente e observe a cadeia de defesa: primeiro o **Hamming** corrige (relatório mostra
   bits corrigidos), depois o **EDC** acusa erro quando o Hamming satura, por fim o texto sai com `�`.

---

## 8. Roteiro de revisão para a prova (ordem sugerida)

1. **Aplicação**: convenção texto↔bits (UTF-8, MSB primeiro).
2. **Enlace – enquadramento** (arquivo 02): 3 técnicas, vantagens/limitações.
3. **Enlace – detecção** (arquivo 03): paridade < checksum < CRC, e por quê.
4. **Enlace – correção** (arquivo 04): Hamming SECDED, síndrome, régua de distância.
5. **Física – banda-base**: NRZ/Manchester/Bipolar (você já domina).
6. **Física – portadora** (arquivo 01): I/Q, ASK/FSK/PSK/QAM, Gray, trade-offs.
7. **Meio**: AWGN, SNR, ruído por amostra.
8. **Integração**: ordem TX (EDC→Hamming→enquadra) e RX (inverso); threads + filas como meio.
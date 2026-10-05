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

1. Valida o tamanho (na contagem de caracteres o quadro final precisa caber em 255 bytes).
2. Divide a mensagem em blocos de `tam_max_quadro` bytes.
3. Para cada bloco: anexa o EDC e, se habilitado, codifica com Hamming.
4. Enquadra todos os blocos segundo o protocolo escolhido.

**Ordem que cai em prova:** divide → EDC → Hamming → enquadra. O EDC antes do Hamming faz o Hamming
proteger também os bits de detecção.

### Detalhe da camada de enlace no RX — `receber(bits, config)`

A ordem inverte: desenquadra → Hamming corrige → EDC verifica. O `relatorio` (um dict por quadro)
alimenta a aba do receptor na GUI.

---

## 3. Aplicação — a fronteira texto ↔ bits

Convenção de **todo o simulador**: bits são `list[int]` de 0/1, MSB primeiro, sempre em múltiplos de 8.
O `errors="replace"` é o que faz um byte corrompido virar `�` em vez de derrubar o programa.

---

## 4. O meio — sinal elétrico + ruído gaussiano

O enunciado exige: sinal em **Volts/Watts** e ruído de uma **variável aleatória gaussiana n(x, σ)**.

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

1. A thread TX desce a pilha e coloca o sinal limpo na fila de saída.
2. A thread principal faz o papel do **canal**: retira o sinal, soma o ruído gaussiano e coloca o
   resultado na fila de entrada do RX.
3. A thread RX, que estava bloqueada esperando, sobe a pilha com o sinal ruidoso.
4. No fim, a principal calcula as potências do sinal e do ruído (SNR) para a GUI.

Cuidado: uma exceção dentro de uma thread não é propagada pelo `join()`; é preciso capturá-la na thread e
relançá-la na principal, senão a GUI espera para sempre.

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
| Enlace | entrelaçamento | `camada_enlace.py` | `enquadrar_entrelacamento` / `desenquadrar_entrelacamento` |
| Enlace | byte stuffing | `camada_enlace.py` | `enquadrar_bytes` / `desenquadrar_bytes` |
| Enlace | bit stuffing | `camada_enlace.py` | `enquadrar_bits` / `desenquadrar_bits` |
| Enlace | paridade | `camada_enlace.py` | `adicionar_paridade_par` / `verificar_paridade_par` |
| Enlace | checksum | `camada_enlace.py` | `adicionar_checksum` / `verificar_checksum` |
| Enlace | CRC-32 | `camada_enlace.py` | `adicionar_crc32` / `verificar_crc32` |
| Enlace | Hamming | `camada_enlace.py` | `codificar_hamming` / `decodificar_hamming` |
| Física | NRZ/Manchester/Bipolar | `camada_fisica.py` | `modular_digital` / `demodular_digital` |
| Física | ASK/FSK/8PSK/32-QAM | `camada_fisica.py` | `modular_portadora` / `demodular_portadora` |
| Meio | ruído AWGN | `meio_comunicacao.py` | `transmitir` / `potencia_media` |
| Simulador | orquestração TX/RX | `simulador.py` | `executar_simulacao`, `_rotina_tx`, `_rotina_rx` |

---

## 7. Como testar o sistema inteiro

### Suite completa (`testes.py`)
O bloco final faz **simulação ponta a ponta** combinando 4 enquadramentos × 5 opções de portadora,
conferindo que o texto recuperado == texto enviado.

Rodar tudo:
```bash
python3 testes.py    # meta: zero [TODO] e zero [FAIL] ("TODOS OS TESTES PASSARAM")
```
(`random.seed(42)` torna os resultados reprodutíveis em qualquer máquina.)

### Simulação manual no terminal (sem GUI)
Chame a função de simulação com um dicionário de configuração e inspecione o dicionário de resultados:
ele guarda os bits e sinais de cada camada (TX e RX), o relatório por quadro, o texto recuperado e as
potências. É a forma mais rápida de achar em qual camada a mensagem se corrompeu.


### Na GUI (visão integrada)
1. Configure todas as camadas e o ruído, clique **Transmitir**.
2. Aba **Transmissor**: bits após cada etapa (aplicação → enlace → física) e o gráfico do sinal.
3. Aba **Receptor**: sinal ruidoso recebido, bits demodulados, relatório por quadro e texto final.
4. Suba o σ gradualmente e observe a cadeia de defesa: primeiro o **Hamming** corrige (relatório mostra
   bits corrigidos), depois o **EDC** acusa erro quando o Hamming satura, por fim o texto sai com `�`.

---

## 8. Roteiro de revisão para a prova (ordem sugerida)

1. **Aplicação**: convenção texto↔bits (UTF-8, MSB primeiro).
2. **Enlace – enquadramento** (arquivo 02): 4 técnicas, vantagens/limitações.
3. **Enlace – detecção** (arquivo 03): paridade < checksum < CRC, e por quê.
4. **Enlace – correção** (arquivo 04): Hamming (11,7), síndrome, régua de distância.
5. **Física – banda-base**: NRZ-Polar, Manchester e Bipolar.
6. **Física – portadora** (arquivo 01): I/Q, ASK/FSK/PSK/QAM, Gray, trade-offs.
7. **Meio**: AWGN, SNR, ruído por amostra.
8. **Integração**: ordem TX (EDC→Hamming→enquadra) e RX (inverso); threads + filas como meio.

---

## 9. Código de referência — aplicação, meio, orquestração e simulador

> Código **testado** (ida e volta, com e sem ruído, e a simulação completa), no mesmo formato das
> assinaturas do esqueleto: dá para copiar para o arquivo indicado. Leiam e entendam cada linha antes de
> colar; o professor pergunta.


### Aplicação — `camada_aplicacao.py`

```python
def texto_para_bits(texto):
    """Texto -> lista de bits (UTF-8, MSB primeiro)."""
    bits = []
    for byte in texto.encode("utf-8"):
        for i in range(7, -1, -1):          # do bit 7 ao bit 0
            bits.append((byte >> i) & 1)    # isola o bit i
    return bits


def bits_para_texto(bits):
    """Lista de bits -> texto (bytes inválidos viram '�')."""
    dados = bytearray()
    for i in range(len(bits) // 8):         # só bytes completos
        byte = 0
        for bit in bits[i * 8:(i + 1) * 8]:
            byte = (byte << 1) | bit        # abre espaço e encaixa o bit
        dados.append(byte)
    return dados.decode("utf-8", errors="replace")
```


### Meio de comunicação — `meio_comunicacao.py`

```python
def transmitir(sinal, media, sigma):
    """Soma ruído gaussiano n(media, sigma) a cada amostra (em Volts)."""
    if media == 0 and sigma == 0:
        return list(sinal)                  # canal ideal: devolve uma cópia
    return [amostra + random.gauss(media, sigma) for amostra in sinal]


def potencia_media(sinal):
    """P = (1/N) * soma(v^2), em Watts sobre 1 ohm."""
    if not sinal:
        return 0.0
    return sum(v * v for v in sinal) / len(sinal)
```


### Pipeline do enlace — `camada_enlace.py`

```python
TAMANHO_EDC = {"nenhum": 0, "paridade": 1, "checksum": 2, "crc": 4}
# ------------------------------- orquestração -----------------------------
ENQUADRAR = {"contagem": enquadrar_contagem,
             "entrelacamento": enquadrar_entrelacamento,
             "bytes": enquadrar_bytes, "bits": enquadrar_bits}
DESENQUADRAR = {"contagem": desenquadrar_contagem,
                "entrelacamento": desenquadrar_entrelacamento,
                "bytes": desenquadrar_bytes, "bits": desenquadrar_bits}
ADICIONAR_EDC = {"nenhum": lambda b: b, "paridade": adicionar_paridade_par,
                 "checksum": adicionar_checksum, "crc": adicionar_crc32}
VERIFICAR_EDC = {"nenhum": lambda b: (b, True), "paridade": verificar_paridade_par,
                 "checksum": verificar_checksum, "crc": verificar_crc32}


def transmitir(bits, config):
    """divide em blocos -> + EDC -> + Hamming -> enquadra."""
    tam_bits = config["tam_max_quadro"] * 8
    if config["enquadramento"] in ("contagem", "entrelacamento"):
        n_bits = tam_bits + 8 * TAMANHO_EDC[config["deteccao"]]
        if config["correcao"] == "hamming":
            n_bits = len(codificar_hamming([0] * n_bits))
        extra = 2 if config["enquadramento"] == "entrelacamento" else 1
        if n_bits // 8 + extra > 255:     # + cabeçalho (+ linha de paridade)
            raise ValueError("Quadro final excede 255 bytes: reduza o "
                             "tamanho máximo de quadro.")
    payloads = []
    for i in range(0, len(bits), tam_bits):
        bloco = ADICIONAR_EDC[config["deteccao"]](bits[i:i + tam_bits])
        if config["correcao"] == "hamming":
            bloco = codificar_hamming(bloco)
        payloads.append(bloco)
    return ENQUADRAR[config["enquadramento"]](payloads)


def receber(bits, config):
    """desenquadra -> Hamming corrige -> EDC verifica. Devolve (bits, relatorio)."""
    payloads = DESENQUADRAR[config["enquadramento"]](bits)
    bits_app, relatorio = [], []
    for n, payload in enumerate(payloads):
        info = {"quadro": n + 1, "corrigidos": 0, "erro_duplo": False, "edc_ok": True}
        if config["correcao"] == "hamming":
            payload, info["corrigidos"], info["erro_duplo"] = \
                decodificar_hamming(payload)
        payload, info["edc_ok"] = VERIFICAR_EDC[config["deteccao"]](payload)
        bits_app += payload
        relatorio.append(info)
    return bits_app, relatorio
```


### Simulador — `simulador.py`

A função de simulação captura exceções das threads e as relança na principal (o `join()` não as propaga).

```python
CONFIG_PADRAO = {
    "texto": "Ola, TR1!",
    "tam_max_quadro": 8,
    "enquadramento": "bits",
    "deteccao": "crc",
    "correcao": "hamming",
    "mod_digital": "nrz",
    "mod_portadora": "8psk",
    "ruido_media": 0.0,
    "ruido_sigma": 0.1,
}


def _rotina_tx(config, meio, resultados):
    """Thread transmissora: aplicação -> enlace -> física -> meio."""
    bits_app = camada_aplicacao.texto_para_bits(config["texto"])
    resultados["tx_bits_aplicacao"] = bits_app

    bits_enlace = camada_enlace.transmitir(bits_app, config)
    resultados["tx_bits_enlace"] = bits_enlace

    sinal_banda_base = camada_fisica.modular_digital(bits_enlace, config["mod_digital"])
    resultados["tx_sinal_banda_base"] = sinal_banda_base

    if config["mod_portadora"] != "nenhuma":
        sinal_tx = camada_fisica.modular_portadora(bits_enlace, config["mod_portadora"])
    else:
        sinal_tx = sinal_banda_base
    resultados["tx_sinal_transmitido"] = sinal_tx
    meio.put(sinal_tx)


def _rotina_rx(config, meio, resultados):
    """Thread receptora: meio -> física -> enlace -> aplicação."""
    sinal_rx = meio.get()                      # bloqueia até o canal entregar
    resultados["rx_sinal_recebido"] = sinal_rx

    if config["mod_portadora"] != "nenhuma":
        bits_rx = camada_fisica.demodular_portadora(sinal_rx, config["mod_portadora"])
        resultados["rx_sinal_banda_base"] = camada_fisica.modular_digital(
            bits_rx, config["mod_digital"])    # só para exibir na GUI
    else:
        resultados["rx_sinal_banda_base"] = sinal_rx
        bits_rx = camada_fisica.demodular_digital(sinal_rx, config["mod_digital"])
    resultados["rx_bits_fisica"] = bits_rx

    bits_app, relatorio = camada_enlace.receber(bits_rx, config)
    resultados["rx_bits_aplicacao"] = bits_app
    resultados["rx_relatorio_quadros"] = relatorio
    resultados["rx_texto"] = camada_aplicacao.bits_para_texto(bits_app)


def executar_simulacao(config):
    """Roda TX e RX em threads; a thread principal faz o papel do canal."""
    resultados, erros = {}, []
    fila_tx, fila_rx = queue.Queue(), queue.Queue()

    def com_captura(rotina, fila):
        """Executa a rotina guardando a exceção (join() não a propaga)."""
        try:
            rotina(config, fila, resultados)
        except Exception as erro:
            erros.append(erro)
            fila_tx.put(None)                  # destrava a principal e o RX
            fila_rx.put(None)

    th_tx = threading.Thread(target=com_captura, args=(_rotina_tx, fila_tx))
    th_rx = threading.Thread(target=com_captura, args=(_rotina_rx, fila_rx))
    th_tx.start()
    th_rx.start()

    sinal_limpo = fila_tx.get()
    if sinal_limpo is not None:
        sinal_ruidoso = meio_comunicacao.transmitir(
            sinal_limpo, config["ruido_media"], config["ruido_sigma"])
        fila_rx.put(sinal_ruidoso)

    th_tx.join()
    th_rx.join()
    if erros:
        raise erros[0]

    ruido = [r - s for r, s in zip(sinal_ruidoso, sinal_limpo)]
    resultados["potencia_sinal_w"] = meio_comunicacao.potencia_media(sinal_limpo)
    resultados["potencia_ruido_w"] = meio_comunicacao.potencia_media(ruido)
    return resultados
```


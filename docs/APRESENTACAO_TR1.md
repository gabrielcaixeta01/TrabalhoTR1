# Apresentação TR1 - roteiro completo

## objetivo do arquivo

Este é o material único da apresentação e defesa do Simulador TR1. Ele junta:

- roteiro de fala para no mínimo 10 minutos;
- divisão entre Fernando e Gustavo;
- conceitos teóricos que precisam aparecer antes do código;
- excertos de código curtos;
- explicação de cada excerto para o professor;
- perguntas prováveis de defesa.

Tempo alvo: **11 a 12 minutos**. O tempo mínimo pedido é 10 minutos, então o roteiro foi montado com folga.

## divisão geral

| bloco | tempo | quem fala | foco |
|---|---:|---|---|
| abertura e visão geral | 1 min | Fernando | problema, objetivo e fluxo |
| conceitos antes do código | 2 min | Fernando + Gustavo | camadas, enlace, física e ruído |
| arquitetura do simulador | 1 min 30 s | Fernando | threads, filas e meio |
| camada de enlace | 3 min | Gustavo | quadros, edc, crc e hamming |
| camada física e meio | 2 min 30 s | Gustavo | sinais, portadora, constelação e ruído |
| interface e validação | 1 min | Fernando | gtk, testes e resultados |
| fechamento | 30 s | Fernando | conclusão |

## ordem de fala

1. Fernando abre e apresenta o fluxo completo.
2. Fernando explica a arquitetura geral.
3. Gustavo explica a teoria da camada de enlace.
4. Gustavo explica a teoria da camada física.
5. Gustavo entra nos excertos principais de enlace e física.
6. Fernando mostra interface, testes e fechamento.

## 1. abertura - Fernando - 1 minuto

Fala sugerida:

> O trabalho simula a comunicação entre um transmissor e um receptor. A mensagem começa como texto, vira bits, é organizada em quadros, recebe mecanismos de detecção e correção de erros, vira sinal elétrico, atravessa um meio com ruído gaussiano e depois é reconstruída no receptor.

Fluxo para falar:

```text
texto -> bits -> enlace -> física -> meio ruidoso -> física -> enlace -> texto
```

Pontos obrigatórios:

- não é apenas uma interface gráfica;
- a gui principal é gtk 3;
- transmissor e receptor são separados;
- o ruído entra no meio;
- crc, hamming, enquadramento e modulações foram implementados manualmente.

## 2. conceitos antes do código - Fernando e Gustavo - 2 minutos

### 2.1 visão de camadas - Fernando

Fala sugerida:

> A separação por camadas ajuda a explicar o código. A aplicação transforma texto em bits. A camada de enlace cria quadros e protege os dados contra erros. A camada física transforma os bits em amostras de tensão. O meio recebe esse sinal e soma ruído.

Mapa:

| camada | papel | arquivo |
|---|---|---|
| aplicação | texto <-> bits | `camada_aplicacao.py` |
| enlace | quadros, edc, hamming | `camada_enlace.py` |
| física | banda-base e portadora | `camada_fisica.py` |
| meio | ruído e potência | `meio_comunicacao.py` |
| simulação | tx, canal e rx | `simulador.py` |

### 2.2 teoria de enlace - Gustavo

Fala sugerida:

> A camada de enlace resolve três problemas. Primeiro, ela define onde cada quadro começa e termina. Segundo, ela adiciona redundância para detectar erro. Terceiro, quando hamming está ligado, ela tenta corrigir erro simples antes de verificar o edc.

Conceitos:

- **contagem de caracteres**: um byte informa o tamanho do quadro;
- **byte stuffing**: usa flag e escape;
- **bit stuffing**: insere 0 depois de cinco bits 1;
- **paridade**: detecta quantidade ímpar de erros;
- **checksum**: soma em complemento de 1;
- **crc-32**: divisão polinomial em gf(2);
- **hamming(8,4)**: corrige erro simples e detecta erro duplo.

### 2.3 teoria de física - Gustavo

Fala sugerida:

> A camada física mostra que bits não trafegam como objetos abstratos. O que trafega é sinal. No projeto, esse sinal é uma lista de amostras em volts. Em banda-base, cada bit vira níveis de tensão. Na portadora, grupos de bits escolhem amplitude, frequência, fase ou ponto de constelação.

Conceitos:

- **nrz-polar**: 1 vira `+V`, 0 vira `-V`;
- **manchester**: sempre há transição no meio do bit;
- **bipolar ami**: 0 vira `0 V`, 1 alterna `+V` e `-V`;
- **ask**: muda amplitude;
- **fsk**: muda frequência;
- **qpsk**: 2 bits por símbolo;
- **16-qam**: 4 bits por símbolo;
- **i/q**: coordenadas que representam amplitude e fase;
- **awgn**: ruído gaussiano aditivo no canal.

## 3. arquitetura do simulador - Fernando - 1 min 30 s

Arquivo: `simulador.py`.

Excerto:

```python
th_tx = threading.Thread(target=_rotina_tx, args=(config, fila_tx, resultados))
th_rx = threading.Thread(target=_rotina_rx, args=(config, fila_rx, resultados))

th_tx.start()
th_rx.start()

sinal_limpo = fila_tx.get()
sinal_ruidoso = meio_comunicacao.transmitir(
    sinal_limpo, config["ruido_media"], config["ruido_sigma"])
fila_rx.put(sinal_ruidoso)
```

Explicação do excerto:

- `th_tx` executa a rotina transmissora;
- `th_rx` executa a rotina receptora;
- `fila_tx` leva o sinal limpo até o canal;
- `meio_comunicacao.transmitir` soma ruído ao sinal;
- `fila_rx` entrega o sinal ruidoso ao receptor;
- isso mostra que tx e rx não se chamam diretamente.

Fala sugerida:

> Esse trecho é a espinha dorsal do simulador. O transmissor gera o sinal, o canal altera esse sinal com ruído e o receptor recebe a versão ruidosa. Isso deixa o código alinhado com o diagrama do enunciado.

Excerto da aplicação:

```python
for byte in texto.encode("utf-8"):
    for i in range(7, -1, -1):
        bits.append((byte >> i) & 1)
```

Explicação:

- o texto é convertido para bytes;
- cada byte é lido do bit mais significativo ao menos significativo;
- isso gera a lista de bits que entra na camada de enlace.

## 4. camada de enlace - Gustavo - 3 minutos

### 4.1 pipeline de enlace

Arquivo: `camada_enlace.py`.

Excerto:

```python
for i in range(0, len(bits), tam_bits):
    bloco = bits[i:i + tam_bits]
    bloco = ADICIONAR_EDC[config["deteccao"]](bloco)
    if config["correcao"] == "hamming":
        bloco = codificar_hamming(bloco)
    payloads.append(bloco)
return ENQUADRAR[config["enquadramento"]](payloads)
```

Explicação do excerto:

- o payload é dividido em blocos do tamanho configurado;
- `ADICIONAR_EDC` adiciona paridade, checksum ou crc;
- se hamming estiver ligado, ele codifica payload + edc;
- só depois o quadro é enquadrado;
- no receptor a ordem é inversa: desenquadrar, corrigir, verificar edc.

Fala sugerida:

> A ordem é importante. O edc vem antes do hamming para que o hamming também proteja os bits de verificação. Assim o receptor tenta corrigir erro simples antes de decidir se o quadro está íntegro.

### 4.2 enquadramento

Byte stuffing:

```python
if byte in (FLAG_BYTE, ESC_BYTE):
    quadro.append(ESC_BYTE)
quadro.append(byte)
```

Explicação:

- `FLAG_BYTE` marca começo e fim de quadro;
- `ESC_BYTE` protege dados que poderiam ser confundidos com flag;
- se o payload contém flag ou escape, o transmissor insere escape antes.

Bit stuffing:

```python
if uns == 5:
    trem.append(0)
    uns = 0
```

Explicação:

- a flag em bits é `01111110`;
- quando o payload tem cinco bits 1 seguidos, o transmissor insere 0;
- isso impede que o payload imite uma flag.

Fala sugerida:

> O objetivo das duas técnicas é o mesmo: impedir que dados sejam confundidos com delimitadores de quadro.

### 4.3 crc-32

Excerto:

```python
for bit in reversed(byte):
    if (crc ^ bit) & 1:
        crc = (crc >> 1) ^ POLI_CRC32_REFLETIDO
    else:
        crc >>= 1
return crc ^ 0xFFFFFFFF
```

Explicação:

- o crc é calculado bit a bit;
- o operador xor representa soma em gf(2);
- o polinômio refletido usado é `0xedb88320`;
- o teste clássico `123456789` precisa gerar `0xcbf43926`;
- não há uso de `zlib`.

Fala sugerida:

> O crc é mais forte que paridade e checksum para detectar erros em rajada. No projeto, ele foi implementado manualmente para obedecer ao enunciado.

### 4.4 hamming(8,4)

Excerto:

```python
s1 = (bloco[0] + bloco[2] + bloco[4] + bloco[6]) % 2
s2 = (bloco[1] + bloco[2] + bloco[5] + bloco[6]) % 2
s4 = (bloco[3] + bloco[4] + bloco[5] + bloco[6]) % 2
sindrome = s4 * 4 + s2 * 2 + s1
par_geral = sum(bloco) % 2
```

Explicação:

- `s1`, `s2` e `s4` recalculam as paridades de hamming;
- a síndrome aponta a posição do erro simples;
- `par_geral` identifica se o número total de bits errados é compatível com erro simples ou duplo;
- erro simples é corrigido;
- erro duplo é detectado, mas não corrigido.

Tabela para defender:

| síndrome | paridade geral | resultado |
|---|---|---|
| 0 | par | sem erro |
| diferente de 0 | ímpar | erro simples corrigível |
| 0 | ímpar | erro no bit de paridade geral |
| diferente de 0 | par | erro duplo detectado |

Fala sugerida:

> O custo do hamming(8,4) é dobrar o tamanho dos dados, mas ele permite corrigir erro simples e detectar erro duplo por bloco.

## 5. camada física e meio - Gustavo - 2 min 30 s

### 5.1 banda-base

Fala sugerida:

> Em banda-base, os bits viram diretamente níveis de tensão. No nrz, 1 é positivo e 0 é negativo. No manchester, a informação está na transição do meio do bit. No bipolar, os bits 1 alternam polaridade.

Exemplo de defesa:

- nrz é simples, mas pode ter componente dc;
- manchester ajuda no sincronismo porque sempre tem transição;
- bipolar reduz componente dc alternando os bits 1.

### 5.2 portadora e i/q

Arquivo: `camada_fisica.py`.

Excerto:

```python
def onda(i, q, ciclos):
    N = AMOSTRAS_POR_SIMBOLO
    amostras = []
    for n in range(N):
        angulo = 2 * math.pi * ciclos * n / N
        amostras.append(i * math.cos(angulo) - q * math.sin(angulo))
    return amostras
```

Explicação:

- cada símbolo é uma sequência de amostras;
- `i` multiplica o cosseno;
- `q` multiplica o seno com sinal negativo;
- isso implementa a representação i/q;
- escolher `(i, q)` é escolher amplitude e fase.

Excerto da correlação:

```python
i = 2 / N * soma_cos
q = -2 / N * soma_sen
return i, q
```

Explicação:

- o receptor mede quanto o sinal recebido parece com as bases cosseno e seno;
- isso estima o ponto da constelação recebido;
- o demodulador escolhe o ponto válido mais próximo.

### 5.3 qpsk e 16-qam

Fala sugerida:

> QPSK transmite 2 bits por símbolo. 16-QAM transmite 4 bits por símbolo. Isso aumenta eficiência, mas também aproxima os pontos da constelação. Por isso, 16-QAM é mais sensível ao ruído.

Pontos para citar:

- qpsk usa mapeamento gray;
- 16-qam usa níveis `-3`, `-1`, `1`, `3` em cada eixo;
- quando faltam bits no último símbolo, o código completa com zeros;
- o desenquadramento ignora esse excedente.

### 5.4 meio e potência

Arquivo: `meio_comunicacao.py`.

Excerto:

```python
return [amostra + random.gauss(media, sigma) for amostra in sinal]
```

Explicação:

- cada amostra recebe um ruído independente;
- `media` desloca o sinal;
- `sigma` controla a intensidade do ruído;
- se sigma cresce, aumenta a chance de decisão errada.

Excerto:

```python
return sum(amostra * amostra for amostra in sinal) / len(sinal)
```

Explicação:

- calcula potência média;
- assume resistência normalizada de 1 ohm;
- é usado para exibir potência do sinal e potência do ruído na interface.

## 6. interface e validação - Fernando - 1 minuto

Arquivo: `interface_gui.py`.

Excerto:

```python
resultado = simulador.executar_simulacao(config)
diagnostico = diagnosticar_camadas(
    resultado["tx_bits_aplicacao"], resultado, config)
```

Explicação:

- a interface não reimplementa protocolos;
- ela chama a função real do simulador;
- `diagnosticar_camadas` calcula quantos bits cada fase adicionou;
- a gui mostra transmissor, receptor, sinais, métricas e relatório de quadros.

Arquivo: `testes.py`.

Excerto:

```python
bits_123 = app.texto_para_bits("123456789")
ok &= testar("crc32 do vetor de teste '123456789' == 0xCBF43926",
             enlace.calcular_crc32(bits_123) == 0xCBF43926)
```

Explicação:

- esse teste valida o crc contra um vetor conhecido;
- a suíte também testa enquadramento, edc, hamming, modulações e simulação completa;
- quando todos passam, temos evidência de ida e volta correta.

Fala sugerida:

> A validação não testa apenas se o programa abre. Ela testa se a informação chega corretamente ao receptor em várias combinações de protocolos.

## 7. fechamento - Fernando - 30 segundos

Fala sugerida:

> O projeto cumpre o enunciado porque separa transmissor e receptor, usa gtk como interface principal, implementa enlace e física manualmente, usa sinal em volts, injeta ruído gaussiano no meio e valida a transmissão com testes. A principal contribuição é tornar visível o caminho completo da informação: texto, bits, quadros, sinal, ruído e texto recuperado.

## perguntas prováveis

**Por que não usar `zlib` para crc?**

Porque o enunciado proíbe bibliotecas prontas para os protocolos. O crc foi implementado bit a bit.

**Por que o hamming vem depois do edc no transmissor?**

Para proteger também os bits de verificação. No receptor, o hamming tenta corrigir antes de verificar o edc.

**Por que usar hamming(8,4), e não hamming(7,4)?**

Porque o bit extra de paridade geral permite detectar erro duplo e mantém o resultado alinhado em bytes.

**Por que 16-QAM é mais sensível a ruído?**

Porque os pontos da constelação ficam mais próximos. Uma variação menor já pode empurrar o símbolo para a decisão errada.

**O que acontece se o ruído aumentar muito?**

O demodulador passa a errar bits. O hamming pode corrigir erro simples por bloco, mas erros múltiplos podem ser apenas detectados ou até escapar dependendo do edc.

**A interface web substitui a gtk?**

Não. A interface principal é gtk. A web é opcional e chama a mesma função do simulador.

**Como provar que o crc está correto?**

Pelo vetor clássico `123456789`, que deve retornar `0xcbf43926`.

## checklist de domínio por pessoa

Fernando deve conseguir explicar:

- `simulador.executar_simulacao`;
- `_rotina_tx` e `_rotina_rx`;
- filas e ruído no meio;
- `interface_gui.py`;
- `diagnosticar_camadas`;
- testes de validação.

Gustavo deve conseguir explicar:

- `enquadrar_bytes` e `enquadrar_bits`;
- `calcular_crc32`;
- `codificar_hamming` e `decodificar_hamming`;
- `onda` e `correlacionar`;
- qpsk e 16-qam;
- ruído e potência média.

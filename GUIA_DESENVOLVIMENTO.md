# Guia de Desenvolvimento — Ordem de Implementação

Este documento descreve a ordem recomendada para implementar o simulador do zero, explicando o propósito de cada etapa e por que ela vem antes das outras.

---

## Por que essa ordem?

Cada camada depende da anterior. Não faz sentido construir a interface antes de ter o que ela vai exibir, nem modular um sinal antes de ter os dados para modular. A ordem abaixo vai do dado bruto até a tela.

```
Dado bruto → Enlace → Física → Simulador → GUI
```

---

## Etapa 1 — `CamadaEnlace.py`: preparar os dados para transmissão

**Comece aqui porque** essa camada não depende de nada além de Python puro. É possível testá-la isoladamente, antes de qualquer sinal ou interface.

### 1.1 — Funções auxiliares de conversão de bits

Primeiro implemente `_bytes_para_bits` e `_bits_para_bytes`. Tudo no projeto transita entre bytes e bits — essas funções serão usadas em quase todas as outras.

> **Finalidade:** converter a mensagem de texto em sequência de bits (e vice-versa) para que os demais protocolos possam operar bit a bit.

### 1.2 — Enquadramento

Implemente as três técnicas na ordem de complexidade crescente:

1. **Contagem de caracteres** — o mais simples: apenas prefixar o tamanho do quadro.
2. **Inserção de bytes (byte stuffing)** — introduz o conceito de flag e escape.
3. **Inserção de bits (bit stuffing)** — mesma ideia do anterior, mas no nível dos bits.

> **Finalidade:** dividir a mensagem em quadros de tamanho controlado e delimitar onde cada quadro começa e termina, para que o receptor saiba separar os dados corretamente.

### 1.3 — Detecção de erros

Implemente na ordem de complexidade crescente:

1. **Paridade par** — conta bits 1 e acrescenta um bit/byte de ajuste.
2. **Checksum** — soma palavras de 16 bits em complemento de 1.
3. **CRC-32 (IEEE 802)** — divisão polinomial; o resto é a assinatura do quadro.

> **Finalidade:** acrescentar uma "assinatura matemática" ao quadro para que o receptor detecte se algum bit foi corrompido durante a transmissão.

### 1.4 — Correção de erros (Hamming)

Por último, implemente `hamming_codificar` e `hamming_decodificar`.

> **Finalidade:** diferente da detecção, o Hamming não só identifica que houve erro — ele localiza e corrige o bit errado automaticamente, sem necessidade de retransmissão.

---

## Etapa 2 — `CamadaFisica.py`: transformar bits em sinal elétrico

**Comece essa etapa depois da Etapa 1** porque as modulações recebem bits como entrada — e agora você já sabe produzir bits da camada de enlace.

### 2.1 — Canal com ruído gaussiano

Implemente `adicionar_ruido` antes das modulações. Ela é a mais simples e ajuda a entender o modelo de canal antes de construir os sinais.

> **Finalidade:** simular o efeito do mundo real sobre o sinal. Toda transmissão sofre interferência; o ruído gaussiano é o modelo matemático padrão para isso.

### 2.2 — Parâmetros globais

Defina `SAMPLE_RATE` (amostras por bit) e `CARRIER_FREQ` (frequência da portadora) como constantes no topo do arquivo.

> **Finalidade:** centralizar os parâmetros usados por todas as modulações, facilitando ajuste e manutenção.

### 2.3 — Modulações digitais (banda-base)

Implemente as três na ordem de complexidade:

1. **NRZ-Polar** — mapeamento direto bit → tensão (+A ou −A).
2. **Bipolar (AMI)** — igual ao NRZ, mas os bits 1 alternam de polaridade.
3. **Manchester** — cada bit vira uma transição no meio do período.

Junto de cada modulador, implemente o **demodulador** correspondente (`demodular_nrz_polar`, `demodular_bipolar`, `demodular_manchester`).

> **Finalidade:** representar os bits como variações de tensão (em Volts) para transmissão direta no cabo, sem portadora.

### 2.4 — Modulações analógicas (por portadora)

Implemente na ordem de complexidade crescente:

1. **ASK** — varia a amplitude; bit 1 = sinal presente, bit 0 = silêncio.
2. **FSK** — varia a frequência entre dois valores.
3. **PSK (BPSK)** — varia a fase entre 0° e 180°.
4. **QPSK** — quatro fases possíveis; transmite 2 bits por símbolo.
5. **16-QAM** — combina amplitude e fase; transmite 4 bits por símbolo.

Junto de cada modulador, implemente o **demodulador** correspondente (`demodular_ask`, `demodular_fsk`, `demodular_psk`, `demodular_qpsk`, `demodular_qam16`).

> **Finalidade:** representar os bits como variações numa onda portadora de alta frequência. Necessário para transmissão sem fio ou em meios que não suportam corrente contínua.

---

## Etapa 3 — `Simulador.py`: conectar as duas camadas

**Comece essa etapa depois das Etapas 1 e 2** porque o simulador é o "maestro" — ele apenas chama funções que você já implementou.

### 3.1 — Função `transmissor` (thread TX)

Implemente o pipeline de transmissão em ordem:

```
bytes da mensagem
  → enquadramento (CamadaEnlace)
  → EDC: acrescenta assinatura (CamadaEnlace)
  → modulação: bits → sinal em V (CamadaFisica)
  → coloca sinal na fila (canal)
```

> **Finalidade:** representar o equipamento que envia. Roda em thread separada para simular transmissão assíncrona.

### 3.2 — Função `receptor` (thread RX)

Implemente o pipeline de recepção em ordem inversa ao TX:

```
sinal da fila (canal)
  → ruído gaussiano adicionado (CamadaFisica)
  → demodulação: sinal → bits (CamadaFisica)
  → EDC: verifica/corrige erros (CamadaEnlace)
  → desenquadramento: remonta a mensagem (CamadaEnlace)
```

> **Finalidade:** representar o equipamento que recebe. Roda em thread separada, consumindo o sinal que o TX colocou no canal.

### 3.3 — Função `transmitir`

Crie uma fila local por chamada, dispare as duas threads e retorne os três sinais (TX, canal, RX) e a mensagem recebida.

> **Finalidade:** ser o ponto de entrada chamado pela GUI. A fila sendo local garante que transmissões consecutivas não interfiram entre si.

### 3.4 — Helpers de desenquadramento

Implemente `_partir_quadros_contagem`, `_partir_quadros_flags` e `_partir_quadros_bits`.

> **Finalidade:** o RX recebe um stream contínuo de bytes — essas funções sabem como repartir esse stream nos quadros originais para passar ao desenquadrador da CamadaEnlace.

---

## Etapa 4 — `InterfaceGUI.py`: tornar tudo visível

**Comece essa etapa por último** porque a GUI apenas exibe o que o `Simulador.py` retorna. Sem as etapas anteriores prontas, não há nada para mostrar.

### 4.1 — Janela principal e layout

Crie a `JanelaPrincipal` com dois painéis: configurações (esquerda) e gráficos (direita).

> **Finalidade:** estabelecer a estrutura visual antes de adicionar os componentes internos.

### 4.2 — Painel de configurações

Adicione os widgets na ordem em que aparecem no fluxo de transmissão:

1. Campo de texto da mensagem
2. SpinButton: tamanho máximo do quadro
3. SpinButton: tamanho do EDC
4. ComboBox: tipo de enquadramento
5. ComboBox: tipo de detecção/correção
6. ComboBox: modulação digital (banda-base)
7. ComboBox: modulação analógica (portadora)
8. SpinButton: ruído σ
9. Botão "Transmitir" e label de status

> **Finalidade:** permitir que o usuário configure cada parâmetro do pipeline sem editar código.

### 4.3 — Painel gráfico

Crie a `Figure` do matplotlib embutida no GTK com 3 subplots (TX, Canal, RX).

> **Finalidade:** exibir visualmente como o sinal se transforma ao longo do pipeline — do transmissor até o receptor, passando pelo canal ruidoso.

### 4.4 — Callback do botão "Transmitir"

Leia todos os widgets, monte o `dict` de configuração e chame `Simulador.transmitir`. Atualize os gráficos e o label de status com o resultado.

> **Finalidade:** conectar a interface ao simulador. É o único ponto de integração entre a GUI e as camadas de enlace e física.

---

## Resumo da ordem

| Etapa | Arquivo | O que implementar |
|-------|---------|-------------------|
| 1 | `CamadaEnlace.py` | Conversão bits↔bytes, enquadramento, detecção de erros, Hamming |
| 2 | `CamadaFisica.py` | Ruído, modulações banda-base, modulações por portadora, demoduladores |
| 3 | `Simulador.py` | Threads TX e RX, pipeline completo, helpers de desenquadramento |
| 4 | `InterfaceGUI.py` | Layout GTK, widgets de configuração, gráficos matplotlib, callback |

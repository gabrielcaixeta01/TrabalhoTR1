# Roteiro em formato de artigo científico

## Título

**Simulador TR1: implementação das camadas física e de enlace com transmissão ruidosa, detecção e correção de erros**

Autores da apresentação:

- Gustavo Henrique Andrade Cavalcanti
- Fernando Augusto Hortencio

## Resumo

Apresentar em 40-60 segundos.

O trabalho implementa um simulador didático das camadas física e de enlace. A entrada é uma mensagem de texto, que é convertida em bits, enquadrada, protegida por mecanismos de detecção e correção de erros, modulada como sinal elétrico, transmitida por um meio com ruído gaussiano e reconstruída no receptor. O projeto implementa manualmente os protocolos exigidos no enunciado, usa GTK 3 para a interface gráfica e valida a transmissão com testes de ida e volta.

Quem fala: **Fernando**.

## 1. Introdução

Objetivo da seção:

Explicar o problema do enunciado e a motivação do simulador.

Fala sugerida:

O enunciado pede a simulação da camada física e da camada de enlace. Por isso, o projeto foi organizado como uma pilha de comunicação completa: aplicação, enlace, física, meio ruidoso e receptor. A interface permite observar o texto, os bits, os quadros, os sinais e o resultado recuperado.

Pontos obrigatórios:

- o simulador não é uma tela de terminal;
- a GUI principal usa GTK 3;
- transmissor e receptor são separados;
- o ruído entra no meio de comunicação;
- os protocolos centrais não usam bibliotecas prontas.

Quem fala: **Fernando**.

Código para mostrar:

- `simulador.py`, visão geral de `executar_simulacao`.
- `interface_gui.py`, classe `JanelaSimulador`.

## 2. Fundamentação teórica

Objetivo da seção:

Explicar, em alto nível, os conceitos usados antes de entrar no código.

### 2.1 Camada de enlace

Fala sugerida:

A camada de enlace organiza os bits em quadros, adiciona mecanismos para detectar alterações e, quando configurado, usa Hamming para corrigir erro simples. No transmissor, a ordem é: dividir em blocos, anexar EDC, aplicar Hamming e enquadrar. No receptor, fazemos o caminho inverso: desenquadrar, corrigir e verificar.

Quem fala: **Gustavo**.

Conceitos:

- contagem de caracteres;
- flags com inserção de bytes;
- flags com inserção de bits;
- paridade par;
- checksum;
- CRC-32 IEEE 802;
- Hamming(8,4) estendido.

### 2.2 Camada física

Fala sugerida:

A camada física transforma bits em amostras de tensão. Implementamos modulação digital em banda-base e modulação por portadora. No receptor, os demoduladores convertem o sinal recebido de volta para bits usando média ou correlação.

Quem fala: **Gustavo**.

Conceitos:

- NRZ-Polar;
- Manchester;
- Bipolar/AMI;
- ASK;
- FSK;
- QPSK;
- 16-QAM;
- representação I/Q;
- mapeamento Gray;
- potência em watts.

## 3. Metodologia

Objetivo da seção:

Mostrar como o simulador foi construído.

### 3.1 Arquitetura do sistema

Fala sugerida:

O simulador usa duas threads: uma para o transmissor e outra para o receptor. Elas não chamam uma à outra diretamente. Entre elas há filas, e o meio de comunicação fica entre essas filas. Isso deixa claro onde o sinal limpo vira sinal ruidoso.

Quem fala: **Fernando**.

Código para mostrar:

- `simulador.py`
- `_rotina_tx`
- `_rotina_rx`
- `executar_simulacao`

Fluxo para desenhar no quadro ou slide:

```text
texto -> bits -> enlace tx -> física tx -> meio ruidoso -> física rx -> enlace rx -> texto
```

### 3.2 Implementação da camada de enlace

Fala sugerida:

No arquivo `camada_enlace.py`, as funções são separadas por responsabilidade. Cada técnica de enquadramento tem uma função de ida e outra de volta. O mesmo vale para os códigos de detecção. O Hamming também tem codificação e decodificação separadas.

Quem fala: **Gustavo**.

Código para mostrar:

- `enquadrar_bits` e `desenquadrar_bits`;
- `adicionar_crc32`, `verificar_crc32` e `calcular_crc32`;
- `codificar_hamming` e `decodificar_hamming`;
- `transmitir` e `receber`.

Pontos de defesa:

- CRC-32 foi implementado bit a bit, sem `zlib`;
- Hamming vem depois do EDC para proteger também os bits de verificação;
- Hamming(8,4) mantém alinhamento em bytes e detecta erro duplo;
- o padding de QPSK/16-QAM é descartado naturalmente pelo desenquadramento.

### 3.3 Implementação da camada física

Fala sugerida:

No arquivo `camada_fisica.py`, o sinal é uma lista de amostras em volts. A banda-base usa níveis diretos de tensão. A portadora usa uma função comum `onda(i, q, ciclos)`, que permite implementar ASK, FSK, QPSK e 16-QAM a partir da mesma ideia.

Quem fala: **Gustavo**.

Código para mostrar:

- `modular_nrz_polar`;
- `modular_manchester`;
- `modular_bipolar`;
- `onda`;
- `correlacionar`;
- `modular_qpsk`;
- `modular_16qam`;
- `demodular_portadora`.

Pontos de defesa:

- as demodulações banda-base usam média das amostras;
- as demodulações por portadora usam correlação;
- QPSK carrega 2 bits por símbolo;
- 16-QAM carrega 4 bits por símbolo, mas é mais sensível a ruído;
- o mapeamento Gray reduz o impacto de erro para símbolos vizinhos.

### 3.4 Meio de comunicação

Fala sugerida:

O meio recebe o sinal limpo e soma ruído gaussiano em cada amostra. O parâmetro `media` desloca o sinal, e o parâmetro `sigma` controla a intensidade da variação aleatória.

Quem fala: **Gustavo**.

Código para mostrar:

- `meio_comunicacao.py`
- `transmitir`
- `potencia_media`

Equações para falar:

```text
amostra_recebida = amostra_original + n(media, sigma)
P = média(v²)
```

### 3.5 Interface gráfica

Fala sugerida:

A interface GTK concentra os controles de configuração e mostra o resultado por fase. Ela também diferencia transmissor e receptor. A tabela de processamento por fase ajuda a explicar quantos bits cada etapa adiciona, e os gráficos são desenhados com `Gtk.DrawingArea`, sem `matplotlib`.

Quem fala: **Fernando**.

Código para mostrar:

- `interface_gui.py`
- `diagnosticar_camadas`
- `GraficoSinal`
- `ao_transmitir`

Pontos de defesa:

- a GUI não é terminal;
- GTK 3 segue a recomendação do enunciado;
- os gráficos são nativos da GUI;
- a interface web é opcional e chama a mesma função do simulador.

## 4. Resultados

Objetivo da seção:

Mostrar que o simulador funciona e que os requisitos do PDF foram atendidos.

Fala sugerida:

Os testes verificam ida e volta: quando o ruído está controlado, o texto recuperado deve ser igual ao texto de entrada. A suíte cobre aplicação, enquadramentos, detecção, correção, modulações e simulação completa.

Quem fala: **Fernando**.

Código para mostrar:

- `testes.py`

Resultados para destacar:

- CRC-32 confere com `0xCBF43926` para `"123456789"`;
- Hamming corrige erro simples;
- Hamming detecta erro duplo;
- todas as modulações passam em ida e volta;
- a simulação completa passa para todos os enquadramentos e portadoras testados;
- a GUI GTK foi validada.

Frase curta:

> A validação não testa apenas se o código executa. Ela testa se a informação transmitida volta corretamente ao receptor.

## 5. Discussão

Objetivo da seção:

Defender decisões de projeto e limitações.

Quem fala: **Gustavo e Fernando**, em diálogo curto.

Gustavo explica:

- por que Hamming(8,4) foi escolhido;
- por que correlação é usada na portadora;
- por que 16-QAM é mais eficiente e mais sensível;
- por que o ruído afeta a constelação.

Fernando explica:

- por que a arquitetura usa threads e filas;
- por que a GUI mostra etapas intermediárias;
- por que a interface web é opcional;
- por que a organização em módulos ajuda a explicar o código.

Limitações honestas:

- o canal é um modelo simplificado AWGN;
- não há sincronização real de relógio;
- o foco é didático, não desempenho de telecomunicação profissional.

## 6. Conclusão

Fala sugerida:

O trabalho implementa todos os protocolos pedidos no enunciado, organiza as responsabilidades por camada, usa sinais em volts, adiciona ruído gaussiano no meio, separa transmissor e receptor, usa GTK 3 para a interface e valida o comportamento com testes. O resultado é uma ferramenta didática para visualizar como enlace e física transformam uma mensagem durante a transmissão.

Quem fala: **Fernando**.

Fechamento:

> A principal contribuição do simulador é tornar visível o caminho completo da informação: do texto original ao sinal elétrico, do sinal ruidoso de volta aos bits, e dos bits de volta ao texto recuperado.

## Divisão final entre Gustavo e Fernando

### Gustavo Henrique Andrade Cavalcanti

Responsável por apresentar:

- fundamentação da camada de enlace;
- enquadramento;
- paridade, checksum e CRC-32;
- Hamming;
- camada física;
- modulações digitais;
- modulações por portadora;
- ruído e potência.

Arquivos que deve dominar:

- `camada_enlace.py`;
- `camada_fisica.py`;
- `meio_comunicacao.py`;
- partes de `testes.py` ligadas a enlace/física.

### Fernando Augusto Hortencio

Responsável por apresentar:

- problema e objetivo do trabalho;
- arquitetura geral;
- threads tx/rx;
- filas e meio de comunicação;
- interface GTK;
- tabela por fase;
- gráficos nativos em GTK;
- interface web opcional;
- validação final;
- organização do repositório.

Arquivos que deve dominar:

- `simulador.py`;
- `interface_gui.py`;
- `simulador_web.py`;
- `README.md`;
- `docs/CHECKLIST_CONFORMIDADE.md`;
- `docs/APRESENTACAO_TR1.md`.

## Ordem sugerida de fala

1. Fernando: resumo e objetivo.
2. Fernando: arquitetura geral e threads.
3. Gustavo: camada de enlace.
4. Gustavo: camada física e meio.
5. Fernando: interface GTK e visualização.
6. Fernando: testes e resultados.
7. Gustavo: discussão técnica.
8. Fernando: conclusão.

## Perguntas prováveis e respostas curtas

**Por que não usar `zlib` para CRC?**

Porque o enunciado proíbe bibliotecas externas prontas para os protocolos. O CRC foi implementado bit a bit.

**Por que usar GTK?**

Porque o enunciado pede GUI e recomenda GTK. A interface principal usa GTK 3.

**O que o Hamming corrige?**

Corrige erro simples por bloco e detecta erro duplo usando paridade geral.

**Por que QPSK e 16-QAM precisam de padding?**

Porque QPSK usa grupos de 2 bits e 16-QAM usa grupos de 4 bits. Quando faltam bits, completamos com zero para fechar o símbolo.

**A interface web substitui a GTK?**

Não. Ela é opcional. A entrega principal de GUI é `interface_gui.py` com GTK 3.

# LEIAME - Simulador TR1

Este pacote contem o trabalho final de Teleinformatica e Redes 1 (TR1),
desenvolvido por:

- Gustavo Henrique Andrade Cavalcanti
- Fernando Augusto Hortencio

O projeto implementa a simulacao completa das camadas fisica e de enlace,
conforme o enunciado do trabalho. A transmissao segue o fluxo:

```text
texto -> bits -> enlace -> fisica -> meio com ruido -> fisica -> enlace -> texto
```

## 1. Conformidade com o enunciado

O enunciado pede a simulacao da camada fisica e da camada de enlace, com
interface grafica real, relatorio em PDF e codigo-fonte compactado em `.zip`.
Este pacote atende esses pontos da seguinte forma:

- Relatorio em PDF com mais de 3 paginas:
  `relatorio/pdfs/relatorio_tr1.pdf`.
- Capa com nome do simulador e nomes dos integrantes.
- Introducao, implementacao, membros e conclusao no relatorio.
- Codigo-fonte em Python, modularizado nos arquivos principais.
- Interface grafica em GTK 3, nao terminal, em `interface_gui.py`.
- Rotina principal de simulacao em `simulador.py`.
- Diferenciacao explicita entre transmissor e receptor usando `threading.Thread`
  e `queue.Queue`.
- Meio de comunicacao com ruido gaussiano por amostra em Volts, e potencia
  media calculada em Watts.
- Algoritmos centrais implementados manualmente, sem `zlib` para CRC e sem
  bibliotecas prontas para modulacao, Hamming ou checksum.

## 2. Protocolos implementados

Camada fisica - modulacao digital:

- NRZ-Polar
- Manchester
- Bipolar (AMI)

Camada fisica - modulacao por portadora:

- ASK
- FSK
- QPSK
- 16-QAM

Camada de enlace - enquadramento:

- Contagem de caracteres
- FLAGS com insercao de bytes
- FLAGS com insercao de bits

Camada de enlace - deteccao de erros:

- Bit de paridade par
- Checksum
- CRC-32 IEEE 802

Camada de enlace - correcao de erros:

- Hamming(8,4) estendido

## 3. Por que existem GTK e web?

O projeto possui um unico nucleo de simulacao, em `simulador.py`,
`camada_fisica.py`, `camada_enlace.py`, `camada_aplicacao.py` e
`meio_comunicacao.py`.

As duas interfaces chamam esse mesmo nucleo. Portanto, nao sao dois trabalhos
diferentes nem duas implementacoes concorrentes dos protocolos. Sao duas formas
de visualizar a mesma simulacao.

### GTK - interface principal e de conformidade

A interface GTK fica em `interface_gui.py` e e a interface principal do
trabalho. Ela existe para cumprir diretamente o enunciado, que pede uma
`InterfaceGUI` que nao seja uma tela de terminal e sugere GTK como preferencia.

Use esta versao para avaliacao do requisito de GUI. Ela permite configurar:

- texto de entrada;
- tamanho maximo do quadro;
- tipo de enquadramento;
- tipo de deteccao e correcao;
- modulacao digital;
- modulacao por portadora;
- media e desvio padrao do ruido.

Ela tambem mostra:

- metricas gerais;
- processamento por fase;
- bits e quadros TX/RX;
- graficos dos sinais transmitidos e recebidos.

### Web - visualizacao opcional para apresentacao

A interface web fica em `simulador_web.py`. Ela foi adicionada como apoio
didatico e visual para apresentacao, porque o navegador facilita projetar,
ampliar e comparar graficos em uma tela grande.

Ela nao substitui a GTK no enunciado. A intencao da web e tornar mais clara a
defesa oral: visualizar melhor os sinais, os quadros, os bits adicionados pelo
protocolo e o efeito do ruido. A conformidade formal com o trabalho fica na
interface GTK.

Em resumo:

- GTK: interface oficial para cumprir o enunciado.
- Web: interface auxiliar para visualizacao e apresentacao.
- Ambas usam o mesmo nucleo de simulacao.

## 4. Como rodar

### 4.1 Requisitos

Python 3 deve estar instalado.

Para a interface GTK em Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

O codigo dos protocolos usa apenas bibliotecas padrao do Python. A dependencia
GTK e apenas para a interface grafica principal.

### 4.2 Rodar a interface GTK principal

No diretorio do projeto:

```bash
./scripts/rodar_gtk.sh
```

Tambem e possivel abrir a mesma interface por:

```bash
python3 simulador.py
```

Esta e a forma recomendada para mostrar a conformidade com a `InterfaceGUI` do
enunciado.

### 4.3 Rodar a interface web opcional

No diretorio do projeto:

```bash
python3 simulador_web.py
```

O terminal mostrara a URL local. Abra essa URL no navegador. Esta interface e
opcional e serve para visualizacao mais confortavel durante a apresentacao.

### 4.4 Rodar os testes

No diretorio do projeto:

```bash
python3 testes.py
```

O resultado esperado e:

```text
RESULTADO GERAL: TODOS OS TESTES PASSARAM
```

## 5. Mapa de arquivos e pastas

Arquivos principais no diretorio raiz:

- `simulador.py`: rotina principal. Cria transmissor e receptor em threads,
  passa o sinal pelo meio e retorna os resultados.
- `camada_aplicacao.py`: converte texto UTF-8 para bits e bits para texto.
- `camada_enlace.py`: implementa enquadramento, deteccao e correcao de erros.
- `camada_fisica.py`: implementa modulacoes digitais e por portadora.
- `meio_comunicacao.py`: soma ruido gaussiano ao sinal e calcula potencia
  media.
- `interface_gui.py`: interface GTK 3 principal, com configuracao, resultados
  e graficos.
- `simulador_web.py`: interface web opcional para apresentacao visual.
- `testes.py`: testes automaticos de ida-e-volta e casos criticos.
- `README.md`: resumo curto do projeto e comandos principais.
- `LEIAME.md`: este arquivo, com explicacao da entrega para avaliacao.

Pastas:

- `scripts/`: scripts de execucao. Contem `rodar_gtk.sh`, que abre a GUI GTK.
- `relatorio/pdfs/`: PDFs finais. O principal para entrega e
  `relatorio_tr1.pdf`.
- `relatorio/fontes/`: fontes LaTeX do relatorio e da apresentacao.
- `relatorio/arquivos_auxiliares/`: imagens usadas no relatorio, como
  diagramas, graficos de sinais, interface GTK e saida dos testes.
- `docs/`: material de apoio versionado. Inclui checklist do enunciado e guia
  de apresentacao.
- `estudos/`: textos de estudo dos conceitos de camada fisica, enlace,
  deteccao, correcao e pipeline completo.

## 6. Observacoes para avaliacao

O enunciado cita arquivos como `CamadaFisica`, `CamadaEnlace`, `InterfaceGUI`
e `Simulador`. Como a implementacao esta em Python, os nomes seguem o padrao
snake_case da linguagem:

- `camada_fisica.py` corresponde a `CamadaFisica`.
- `camada_enlace.py` corresponde a `CamadaEnlace`.
- `interface_gui.py` corresponde a `InterfaceGUI`.
- `simulador.py` corresponde a `Simulador`.

O tamanho do EDC nao aparece como um campo livre separado porque ele e derivado
automaticamente do tipo de deteccao escolhido:

- nenhum: 0 byte;
- paridade: 1 byte;
- checksum: 2 bytes;
- CRC-32: 4 bytes.

Essa decisao evita combinacoes invalidas e esta documentada no relatorio como
decisao de projeto.

## 7. Entrega no Moodle

O Moodle deve receber o arquivo `.zip` contendo este projeto. Dentro dele estao
o codigo-fonte, o relatorio PDF e os materiais auxiliares. Para avaliacao
formal, considerar principalmente:

- `relatorio/pdfs/relatorio_tr1.pdf`
- `simulador.py`
- `camada_fisica.py`
- `camada_enlace.py`
- `interface_gui.py`
- `meio_comunicacao.py`
- `testes.py`


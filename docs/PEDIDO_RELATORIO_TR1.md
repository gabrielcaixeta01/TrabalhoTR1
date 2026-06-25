# Pedido do relatorio - Trabalho Final TR1

Este documento versiona, de forma organizada, o que o enunciado pede para o
relatorio e como o relatorio atual atende cada ponto.

## 1. Entregavel pedido

O trabalho pede um relatorio em PDF, com no minimo 3 paginas, entregue junto
com o codigo-fonte compactado em `.zip` no Moodle.

Relatorio atual:

- PDF final: `relatorio/pdfs/relatorio_tr1.pdf`
- Fonte LaTeX: `relatorio/fontes/main.tex`
- Figuras: `relatorio/arquivos_auxiliares/`
- Quantidade atual: 11 paginas

## 2. Estrutura obrigatoria do relatorio

| Item pedido | O que precisa conter | Onde esta no relatorio atual | Status |
|---|---|---|---|
| Capa | Nome do simulador e nomes dos membros do grupo | Pagina de capa | OK |
| Introducao | Problema resolvido e visao geral do simulador | Secao `Introducao` | OK |
| Implementacao | Funcionamento dos protocolos, procedimentos, diagramas e decisoes de projeto | Secoes `Arquitetura do Simulador` e `Implementacao` | OK |
| Membros | Atividades desenvolvidas por cada integrante | Secao `Membros e Atividades Desenvolvidas` | OK |
| Conclusao | Comentarios gerais e principais dificuldades | Secao `Conclusao` | OK |

## 3. Conteudo tecnico que o relatorio deve cobrir

### Camada fisica - modulacao digital

O relatorio deve explicar e relacionar com o codigo:

- NRZ-Polar
- Manchester
- Bipolar

No relatorio atual, isso aparece na subsecao `Camada Fisica - Modulacao
Digital (Banda-Base)`, com figura das formas de onda.

### Camada fisica - modulacao por portadora

O relatorio deve explicar e relacionar com o codigo:

- ASK
- FSK
- PSK/QPSK
- 16-QAM

No relatorio atual, isso aparece na subsecao `Camada Fisica - Modulacao por
Portadora`, com constelacoes, sinais e explicacao de I/Q.

### Camada de enlace - enquadramento

O relatorio deve explicar:

- Contagem de caracteres
- FLAGS com insercao de bytes/caracteres
- FLAGS com insercao de bits

No relatorio atual, isso aparece na subsecao `Camada de Enlace -
Enquadramento`.

### Camada de enlace - deteccao de erros

O relatorio deve explicar:

- Bit de paridade par
- Checksum
- CRC-32 IEEE 802

No relatorio atual, isso aparece na subsecao `Camada de Enlace - Deteccao de
Erros`. O CRC e descrito como implementado manualmente, sem `zlib`, e validado
com o vetor conhecido `123456789 -> 0xCBF43926`.

### Camada de enlace - correcao de erros

O relatorio deve explicar:

- Hamming

No relatorio atual, isso aparece na subsecao `Camada de Enlace - Correcao de
Erros (Hamming)`, com explicacao de Hamming(8,4) estendido, sindrome,
correcao de erro simples e deteccao de erro duplo.

## 4. Pontos de implementacao que precisam estar claros

O enunciado tambem cobra que o projeto faca sentido como simulador completo.
Por isso, o relatorio deve deixar explicito:

- a diferenca entre transmissor e receptor;
- o caminho completo `texto -> bits -> enlace -> fisica -> meio -> fisica -> enlace -> texto`;
- que o meio soma ruido gaussiano;
- que o sinal e tratado como amostras em Volts;
- que o projeto usa GUI real, nao tela de terminal;
- que os algoritmos centrais foram implementados manualmente;
- que existem testes e evidencias de funcionamento.

No relatorio atual:

- TX/RX aparecem na arquitetura, no diagrama de pilha e na explicacao das
  threads.
- O ruido aparece na introducao, no meio de comunicacao e nas figuras de sinal
  e constelacao.
- A GUI GTK aparece em secao propria, com imagem da interface.
- Os testes aparecem na secao `Validacao e Resultados`.

## 5. Mapeamento entre arquivos e requisitos

| Arquivo | Papel na entrega |
|---|---|
| `simulador.py` | Rotina principal, threads TX/RX, filas e meio |
| `camada_fisica.py` | Modulacoes digitais e por portadora |
| `camada_enlace.py` | Enquadramento, deteccao e correcao de erros |
| `interface_gui.py` | Interface grafica GTK |
| `camada_aplicacao.py` | Conversao texto/bits |
| `meio_comunicacao.py` | Ruido gaussiano e potencia media |
| `testes.py` | Validacao automatica |
| `relatorio/fontes/main.tex` | Fonte do relatorio |
| `relatorio/pdfs/relatorio_tr1.pdf` | PDF final do relatorio |

## 6. Checklist final antes de entregar

Antes de compactar e enviar no Moodle, conferir:

- [ ] O PDF `relatorio/pdfs/relatorio_tr1.pdf` abre corretamente.
- [ ] O relatorio tem pelo menos 3 paginas.
- [ ] A capa contem nome do simulador e membros do grupo.
- [ ] A introducao explica o problema e a visao geral.
- [ ] A implementacao descreve fisica, enlace, meio, TX/RX e decisoes de
      projeto.
- [ ] A secao de membros descreve a contribuicao de cada integrante.
- [ ] A conclusao fala das dificuldades e resultado final.
- [ ] O codigo executa sem erro.
- [ ] A GUI GTK abre e nao e apenas terminal.
- [ ] `python3 testes.py` termina com `TODOS OS TESTES PASSARAM`.
- [ ] O `.zip` final inclui codigo-fonte e relatorio PDF.

## 7. Observacao sobre a apresentacao

A apresentacao nao substitui o relatorio. Ela serve como roteiro de defesa e
esta versionada em:

- `docs/APRESENTACAO_TR1.md`
- `relatorio/fontes/apresentacao_tr1.tex`
- `relatorio/pdfs/apresentacao_tr1.pdf`


# Simulador TR1 - Camadas Física e de Enlace

Trabalho final de Teleinformática e Redes 1 (UnB). O projeto simula uma transmissão completa entre um transmissor e um receptor, passando por aplicação, enlace, camada física e meio ruidoso.

Integrantes: Gustavo Henrique Andrade Cavalcanti e Fernando Augusto Hortencio.

Os algoritmos centrais foram implementados manualmente: enquadramento, paridade, checksum, CRC-32, Hamming, modulações banda-base e modulações por portadora. Não usamos `zlib`, NumPy, SciPy ou bibliotecas prontas para resolver os protocolos.

## Estrutura

```text
TrabalhoTR1/
├── simulador.py              # rotina principal: thread tx, meio e thread rx
├── camada_aplicacao.py       # texto <-> bits em utf-8
├── camada_enlace.py          # enquadramento, detecção e correção de erros
├── camada_fisica.py          # modulação digital e por portadora
├── meio_comunicacao.py       # canal com ruído gaussiano em volts
├── interface_gui.py          # interface GTK 3 e gráficos nativos
├── simulador_web.py          # interface web local opcional, sem dependências externas
├── testes.py                 # testes de ida e volta
├── scripts/                  # scripts de execução
├── docs/                     # roteiro, conformidade e apresentação
├── estudos/                  # material de estudo por módulo
└── relatorio/                # relatório, imagens e fontes latex
```

## Como rodar

No Linux, instale o GTK 3 para Python:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

Abra a interface GTK:

```bash
./scripts/rodar_gtk.sh
```

Ou rode diretamente:

```bash
/usr/bin/python3 simulador.py
```

Rode os testes:

```bash
python3 testes.py
```

A interface web opcional roda só com biblioteca padrão:

```bash
python3 simulador_web.py
```

## Requisitos atendidos

| Enunciado | Implementação |
|---|---|
| NRZ-Polar, Manchester e Bipolar | `camada_fisica.py` |
| ASK, FSK, QPSK e 16-QAM | `camada_fisica.py` |
| Contagem, byte stuffing e bit stuffing | `camada_enlace.py` |
| Paridade par, checksum e CRC-32 IEEE 802 | `camada_enlace.py` |
| Hamming | `camada_enlace.py` |
| GUI não-terminal com preferência GTK | `interface_gui.py` |
| Separação transmissor/receptor | `simulador.py`, com threads e filas |
| Meio com ruído gaussiano em V/W | `meio_comunicacao.py` |
| Relatório com capa, implementação, membros e conclusão | `relatorio/` |

## Dependências

Protocolos e testes usam apenas biblioteca padrão do Python (`math`, `random`, `threading`, `queue`).

A GUI usa `PyGObject`/GTK 3, que é a biblioteca recomendada no enunciado. Os gráficos da interface GTK são desenhados com `Gtk.DrawingArea`, sem `matplotlib`.

## Documentação da entrega

- `docs/REGISTRO_ALTERACOES_FERNANDO.md`: registro consolidado da branch `Fernando`.
- `docs/CHECKLIST_CONFORMIDADE.md`: conferência dos requisitos do enunciado.
- `docs/APRESENTACAO_TR1.md`: roteiro da apresentação no formato de artigo científico.
- `docs/WALKTHROUGH_TR1.md`: walkthrough técnico do funcionamento do simulador.

## Validação

`testes.py` cobre:

- texto UTF-8 para bits e volta;
- os três enquadramentos, incluindo casos de stuffing;
- paridade, checksum e CRC-32, com vetor conhecido `123456789 -> 0xCBF43926`;
- Hamming com ida e volta, correção de um erro e detecção de erro duplo;
- todas as modulações com e sem ruído;
- simulação completa combinando enquadramento e portadora.

Estado validado nesta branch: todos os testes passam.

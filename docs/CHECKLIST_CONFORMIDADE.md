# Checklist de conformidade com o enunciado

Fonte: `Trabalho_de_TR1-5.pdf`, trabalho final de Teleinformática e Redes 1.

## Resumo

O projeto atende ao escopo principal do enunciado: simula camada física e camada de enlace, separa transmissor e receptor, usa GUI em GTK 3, implementa os protocolos manualmente e mantém relatório com as seções exigidas.

## Camada física

| Requisito | Status | Evidência |
|---|---|---|
| NRZ-Polar | ok | `camada_fisica.py`, `modular_nrz_polar`, `demodular_nrz_polar` |
| Manchester | ok | `camada_fisica.py`, `modular_manchester`, `demodular_manchester` |
| Bipolar/AMI | ok | `camada_fisica.py`, `modular_bipolar`, `demodular_bipolar` |
| ASK | ok | `camada_fisica.py`, `modular_ask`, `demodular_ask` |
| FSK | ok | `camada_fisica.py`, `modular_fsk`, `demodular_fsk` |
| QPSK | ok | `camada_fisica.py`, `modular_qpsk`, `demodular_qpsk` |
| 16-QAM | ok | `camada_fisica.py`, `modular_16qam`, `demodular_16qam` |
| valores elétricos em V/W | ok | sinais são listas em volts; `potencia_media` calcula watts sobre 1 ohm |
| ruído gaussiano `n(x, sigma)` | ok | `meio_comunicacao.transmitir`, usando `random.gauss(media, sigma)` |

## Camada de enlace

| Requisito | Status | Evidência |
|---|---|---|
| contagem de caracteres | ok | `enquadrar_contagem`, `desenquadrar_contagem` |
| flags + inserção de bytes | ok | `enquadrar_bytes`, `desenquadrar_bytes`, `FLAG_BYTE`, `ESC_BYTE` |
| flags + inserção de bits | ok | `enquadrar_bits`, `desenquadrar_bits`, `FLAG_BITS` |
| bit de paridade par | ok | `adicionar_paridade_par`, `verificar_paridade_par` |
| checksum | ok | `adicionar_checksum`, `verificar_checksum`, `soma_complemento1` |
| CRC-32 IEEE 802 | ok | `calcular_crc32`, `adicionar_crc32`, `verificar_crc32` |
| Hamming | ok | `codificar_hamming`, `decodificar_hamming` |

## Código fonte exigido

| Arquivo exigido no PDF | Arquivo no projeto | Observação |
|---|---|---|
| CamadaFisica | `camada_fisica.py` | nome em `snake_case`, padrão Python |
| CamadaEnlace | `camada_enlace.py` | nome em `snake_case`, padrão Python |
| InterfaceGUI | `interface_gui.py` | GTK 3, não terminal |
| Simulador | `simulador.py` | rotina principal com threads tx/rx |

Arquivos auxiliares:

- `camada_aplicacao.py`: conversão texto/bits.
- `meio_comunicacao.py`: canal com ruído.
- `testes.py`: validação automática.
- `simulador_web.py`: interface web opcional, não substitui a GUI GTK.

## GUI

| Requisito | Status | Evidência |
|---|---|---|
| não ser terminal | ok | `interface_gui.py` cria janela GTK |
| preferência GTK | ok | `gi.repository.Gtk` |
| entrada de dados | ok | texto, quadro, enquadramento, edc, hamming, modulações e ruído |
| saídas tx/rx | ok | abas Transmissor/Receptor |
| gráficos | ok | `Gtk.DrawingArea`, sem `matplotlib` |
| transmissor e receptor diferenciados | ok | `simulador.py`, `_rotina_tx`, `_rotina_rx`, abas na interface |

## Bibliotecas externas

Protocolos implementados sem bibliotecas externas prontas:

- CRC-32 não usa `zlib`.
- Hamming não usa biblioteca externa.
- checksum, paridade e enquadramentos são manuais.
- modulações e demodulações usam apenas `math`.
- ruído usa `random.gauss`, biblioteca padrão para gerar a variável normal.

Uso permitido/justificado:

- `PyGObject`/GTK 3: usado para a interface, conforme recomendação do enunciado.
- biblioteca padrão Python: `math`, `random`, `threading`, `queue`, `http.server`, `json`, `sys`, `webbrowser`.

Removido nesta revisão:

- `matplotlib` deixou de ser usado na GUI. Os gráficos agora são desenhados diretamente no GTK.

## Relatório

| Seção exigida | Status | Evidência |
|---|---|---|
| capa | ok | `relatorio/main.tex`, `relatorio/relatorio_tr1.pdf` |
| introdução | ok | seção 1 do relatório |
| implementação detalhada | ok | seção 3 do relatório |
| atividades dos membros | ok | seção 5 do relatório |
| conclusão | ok | seção 6 do relatório |
| mínimo de 3 páginas | ok | PDF atual tem mais de 3 páginas |

Observação: o fonte `relatorio/main.tex` e o PDF `relatorio/relatorio_tr1.pdf` foram atualizados nesta revisão para refletir a GUI sem `matplotlib`.

## Validação executada

Comandos usados:

```bash
python3 -m py_compile camada_aplicacao.py camada_enlace.py camada_fisica.py meio_comunicacao.py simulador.py interface_gui.py simulador_web.py testes.py
python3 testes.py
/usr/bin/python3 testes.py
xvfb-run -a /usr/bin/python3 simulador.py
```

Resultado:

- compilação Python sem erro;
- todos os testes passaram;
- interface GTK importou e rodou em display virtual;
- captura da interface atualizada em `relatorio/interface_gtk.png`.

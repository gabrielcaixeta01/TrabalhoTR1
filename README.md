# Simulador TR1

Simulador das camadas física e de enlace para o trabalho final de Teleinformática e Redes 1.

Integrantes:

- Gustavo Henrique Andrade Cavalcanti
- Fernando Augusto Hortencio

## O que o projeto faz

O simulador transmite uma mensagem de texto por uma pilha completa:

```text
texto -> bits -> enlace -> física -> meio com ruído -> física -> enlace -> texto
```

Ele implementa manualmente:

- enquadramento por contagem, byte stuffing e bit stuffing;
- paridade par, checksum e crc-32 ieee 802;
- hamming(8,4) estendido;
- nrz-polar, manchester e bipolar;
- ask, fsk, qpsk e 16-qam;
- canal com ruído gaussiano em volts.

## Como rodar

Interface gtk:

```bash
./scripts/rodar_gtk.sh
```

A janela se ajusta à resolução da tela. No macOS, a barra de título usa
aparência clara via `pyobjc` (opcional; sem ele a interface funciona normalmente):

```bash
.venv-gtk/bin/pip install pyobjc-core pyobjc-framework-Cocoa
```

Execução direta:

```bash
.venv-gtk/bin/python simulador.py
```

Testes:

```bash
python3 testes.py
```

Interface web opcional:

```bash
python3 simulador_web.py
```

## Arquivos principais

- `simulador.py`: orquestra tx, meio e rx com threads e filas.
- `camada_aplicacao.py`: converte texto em bits e bits em texto.
- `camada_enlace.py`: enquadramento, detecção e correção de erros.
- `camada_fisica.py`: modulações digitais e por portadora.
- `meio_comunicacao.py`: ruído gaussiano e potência média.
- `interface_gui.py`: interface gtk principal.
- `simulador_web.py`: interface web opcional.
- `testes.py`: validação automática.

## Entrega

- `docs/PEDIDO_RELATORIO_TR1.md`: checklist versionado do que o enunciado pede para o relatório.
- `docs/APRESENTACAO_TR1.md`: guia único da apresentação, com divisão de fala e trechos de código.
- `relatorio/pdfs/relatorio_tr1.pdf`: relatório final.
- `relatorio/pdfs/apresentacao_tr1.pdf`: apresentação e defesa completas, com roteiro de 10+ minutos.

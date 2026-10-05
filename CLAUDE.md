# TrabalhoTR1 — contexto do projeto

Trabalho final de Teleinformática e Redes 1 (UnB, Engenharia de Computação, prof. Marcelo Antonio Marotta):
simulador das camadas física e de enlace em Python + GTK 3. Grupo: Gabriel Caixeta Romero, Henrique
Martins Fortes, Pedro Henrique Mantovani Conti (só esses três).

Este repositório é um **esqueleto para o grupo implementar**: estrutura, assinaturas, docstrings, GUI e
testes prontos; o corpo dos protocolos é `TODO` (`raise NotImplementedError`). O nível das decisões e do
código é o de uma graduação em Engenharia de Computação: correto e explicável, sem sofisticação extra.

## Organização

- Raiz: código Python (`simulador.py`, `camada_*.py`, `meio_comunicacao.py`, `interface_gui.py`,
  `testes.py`), `README.md`, `requirements.txt` e este arquivo (precisa ficar na raiz).
- `docs/DESENVOLVIMENTO.md`: o que implementar, em ordem, e checklist do enunciado.
- `docs/DECISOES.md`: decisões de projeto e justificativas (insumo do relatório).
- `docs/enunciado/`: PDF do professor. `docs/referencias/`: resumos dos slides (NotebookLM).
- `estudos/01..05`: material de estudo (conceito nas seções 0..8, código de referência testado na seção 9).

## Fontes de verdade (nesta ordem)

1. **Enunciado do professor** (`docs/enunciado/Trabalho_de_TR1-7.pdf`). Requisitos:
   - Meio: sinal em Volts + ruído gaussiano n(x, σ).
   - Física, banda-base: NRZ-Polar, Manchester, Bipolar.
   - Física, portadora: ASK, FSK, 8PSK, 32-QAM.
   - Enlace, enquadramento: contagem de caracteres, entrelaçamento de bits, byte stuffing, bit stuffing.
   - Enlace, detecção: paridade par, checksum, CRC-32 (IEEE 802).
   - Enlace, correção: código de Hamming.
   - Aplicação: chat de texto. GUI em GTK. Threads TX/RX distintas.
   - Proibido importar bibliotecas externas que entreguem o protocolo (ex.: zlib para CRC).
2. **Slides via NotebookLM**: `docs/referencias/referencia-slides-detalhes.md` (respostas com o slide de
   origem; mais confiáveis em caso de conflito) e `docs/referencias/referencia-slides.md` (resumo geral).
3. `docs/DECISOES.md` para o que os slides não definem.

## Regras combinadas com o usuário

- `estudos/`: seções 0..8 explicam o que é cada coisa e para que serve, sem código. A última seção de
  cada arquivo ("9. Código de referência") traz o código Python testado, para o grupo copiar e entender.
  Esse código foi validado num rascunho (fora do repositório) contra o `testes.py`.
- `docs/DESENVOLVIMENTO.md`: lista do que fazer em ordem de implementação. **Sem nomes de pessoas e sem
  divisão de tarefas**, e sem percentuais.
- A GUI (`interface_gui.py`) fica implementada e comentada; o foco da defesa são os protocolos.
- O relatório foi removido de propósito: será refeito do zero.
- Todos os membros precisam dominar todo o código (o professor pergunta a qualquer um): manter
  comentários e docstrings explicativos, em português.
- Ao implementar ou revisar, rodar `python3 testes.py` (ambiente: `.venv` com `--system-site-packages`).
- Commits e GitHub: o usuário faz.

## Estado atual

- Esqueleto, `testes.py`, estudos e `DECISOES.md` estão alinhados com os slides e entre si.
- No esqueleto, `testes.py` mostra 2 FAIL (mapas 8PSK e 32-QAM vazios) e o resto TODO, até o grupo implementar.
- Sem pendências: a convenção do Manchester foi confirmada no slide 8 do `CF-10` (1 = alto→baixo).

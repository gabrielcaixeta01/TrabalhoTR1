# Registro de alterações da branch Fernando

Consolidação feita na branch `Fernando` em 2026-06-25.

## Grupo

O trabalho passa a considerar apenas os integrantes:

- Gustavo Henrique Andrade Cavalcanti
- Fernando Augusto Hortencio

As referências ao integrante removido foram retiradas dos textos editáveis e dos PDFs gerados.

## Organização da entrega

- O walkthrough foi movido para `docs/WALKTHROUGH_TR1.md`.
- O roteiro da apresentação foi registrado em `docs/APRESENTACAO_TR1.md`.
- A checagem de conformidade com o enunciado foi registrada em `docs/CHECKLIST_CONFORMIDADE.md`.
- O script GTK foi movido para `scripts/rodar_gtk.sh`.
- Arquivos temporários e de sistema, como `.DS_Store`, foram removidos ou ignorados.

## Separação entre Gustavo e Fernando

Gustavo ficou associado às partes de camada física e enlace:

- NRZ-Polar, Manchester e Bipolar;
- ASK, FSK, QPSK e 16-QAM;
- meio de comunicação com ruído gaussiano;
- enquadramento;
- detecção e correção de erros.

Fernando ficou associado às partes de integração, interface e documentação:

- simulação completa entre transmissor e receptor;
- uso de threads e filas;
- interface GTK;
- interface web opcional;
- organização do repositório;
- roteiro de apresentação;
- validação final com testes.

## Relatório e apresentação

Foram atualizados:

- `relatorio/main.tex`
- `relatorio/relatorio_tr1.pdf`
- `relatorio/defesa_tr1.tex`
- `relatorio/defesa_tr1.pdf`
- `README.md`

O roteiro da apresentação foi escrito no formato de artigo científico, com resumo, introdução, fundamentação teórica, metodologia, resultados, discussão e conclusão.

## Validação

Validações executadas antes do commit:

```bash
python3 -m py_compile camada_aplicacao.py camada_enlace.py camada_fisica.py meio_comunicacao.py simulador.py interface_gui.py simulador_web.py testes.py
python3 testes.py
git diff --check
```

Resultado: todos os testes passaram e não foram encontradas referências restantes ao integrante removido.

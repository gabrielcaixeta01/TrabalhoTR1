# TrabalhoTR1 — Simulador de Camada Física e Enlace

Trabalho prático de TR1 (Redes de Telecomunicações 1). Simulador com GUI das camadas física e de enlace.

## Estrutura de Arquivos Obrigatória

```
CamadaFisica.py   — modulações banda-base e por portadora
CamadaEnlace.py   — enquadramento, detecção e correção de erros
InterfaceGUI.py   — interface gráfica (GTK, não terminal)
Simulador.py      — rotina principal (TX/RX em threads separadas)
```

## Canal com Ruído

- Implementado com valores de eletricidade (Volts/Watts)
- Ruído gaussiano: `n(x, σ)` somado ao sinal em V/W

## Checklist de Implementação

### Camada Física (CamadaFisica.py)
- [ ] NRZ-Polar (banda-base)
- [ ] Manchester (banda-base)
- [ ] Bipolar (banda-base)
- [ ] ASK (portadora)
- [ ] FSK (portadora)
- [ ] PSK / QPSK (portadora)
- [ ] 16-QAM (portadora)

### Camada de Enlace — Enquadramento (CamadaEnlace.py)
- [ ] Contagem de caracteres
- [ ] Flags + inserção de bytes/caracteres
- [ ] Flags + inserção de bits

### Camada de Enlace — Detecção de Erros
- [ ] Bit de paridade par
- [ ] Checksum (conforme aula)
- [ ] CRC-32 (IEEE 802)

### Camada de Enlace — Correção de Erros
- [ ] Hamming

## GUI (InterfaceGUI.py)

Biblioteca: GTK (não terminal). Deve permitir configurar:
1. Tamanho máximo do quadro
2. Tamanho do EDC (Error Detection Code)
3. Tipo de enquadramento
4. Tipo de detecção/correção de erros
5. Tipo de modulação digital (banda-base)
6. Tipo de modulação analógica (por portadora)

Exibir resultados gráficos (formas de onda, sinais).

## Regras de Qualidade (penalidade de até -10 pts)

- Código **deve** ter comentários e indentação adequada
- Sem funções duplicadas ou redundantes
- Cada função na declaração/implementação correta por arquivo
- TX e RX em thread ou processo separado

## Critérios de Avaliação

| Item | Pontos |
|---|---|
| Relatório PDF (mín. 3 páginas) | +2 |
| Compilou e executou corretamente | +2 |
| Saídas corretas pelos protocolos | +3 |
| Conceitos de TR1 implementados | +3 |
| Sem comentários / funções duplicadas / fora de estrutura | -10 |
| Atraso (máx -5) | -1/dia |
| Plágio | -10 (nota zero) |

## Entrega

- Relatório PDF + código fonte em `.zip` no Moodle
- Relatório em Jupyter também aceito

## Relatório (PDF, mín. 3 páginas)

1. **Capa:** nome do simulador + membros do grupo
2. **Introdução:** descrição do problema e visão geral
3. **Implementação:** diagramas, funcionamento dos protocolos, decisões
4. **Membros:** atividades de cada membro
5. **Conclusão:** dificuldades e comentários gerais

# README de Execução — Simulador TR1 (UnB)

Documento gerado a partir da análise do código-fonte. Objetivo: permitir que um avaliador/professor execute o projeto em ambiente Linux sem ambiguidades.

---

## 1. Visão Geral do Projeto

Simulador educacional das camadas física e de enlace de uma rede de computadores, implementado em Python 3 com interface gráfica GTK 3. O projeto simula uma transmissão completa de texto entre um transmissor (Thread TX) e um receptor (Thread RX) passando por um canal ruidoso (ruído gaussiano AWGN em Volts).

Funcionalidades implementadas:

- **Camada de Aplicação:** codificação/decodificação texto ↔ bits (UTF-8)
- **Camada de Enlace:** enquadramento (contagem de caracteres, inserção de bytes, inserção de bits), detecção de erros (paridade par, checksum complemento de 1, CRC-32 IEEE 802), correção de erros (Hamming(8,4) SECDED)
- **Camada Física:** modulação digital banda-base (NRZ-Polar, Manchester, Bipolar AMI) e modulação por portadora (ASK, FSK, QPSK, 16-QAM)
- **Meio de Comunicação:** canal com ruído gaussiano N(x, σ) amostra a amostra em Volts
- **Interface Gráfica:** janela GTK 3 com painéis TX e RX, gráficos matplotlib embutidos

**Integrantes:** Gabriel Caixeta Romero, Gustavo Henrique Andrade Cavalcanti, Fernando Augusto Hortencio.

---

## 2. Estrutura de Pastas e Arquivos

```
TrabalhoTR1/
├── simulador.py          # Ponto de entrada principal — orquestra TX → meio → RX
├── Simulador.py          # Compatibilidade para executar pelo nome antigo
├── camada_aplicacao.py   # Camada de aplicação: texto ↔ bits (UTF-8)
├── camada_enlace.py      # Camada de enlace: enquadramento, detecção e correção
├── camada_fisica.py      # Camada física: modulações banda-base e por portadora
├── meio_comunicacao.py   # Canal: adiciona ruído gaussiano ao sinal em Volts
├── interface_gui.py      # Interface gráfica GTK 3 com gráficos matplotlib
├── testes.py             # Testes automatizados (não requer GTK)
├── requirements.txt      # Dependência Python instalada no venv: matplotlib
└── relatorio/
    └── RelatórioTR1 (provisório).pdf
```

---

## 3. Pré-requisitos do Ambiente

### Sistema operacional

O projeto foi desenvolvido com suporte explícito a Linux (Ubuntu/Debian). O README original afirma: *"testar sempre no Linux (o trabalho será corrigido em Linux)"*.

### Versão do Python

Python **3.8 ou superior**. O projeto foi testado com Python 3.12 e 3.14 (evidenciado pelos arquivos `.pyc` em `__pycache__/`).

Verificar a versão instalada:

```bash
python3 --version
```

### Bibliotecas do sistema (GTK 3)

Obrigatórias para a interface gráfica. Sem elas, `simulador.py` não abre:

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

> Em distribuições baseadas em Fedora/RHEL:
> ```bash
> sudo dnf install python3-gobject python3-cairo gobject-introspection
> ```

### Bibliotecas Python

Listadas em `requirements.txt`:

```
matplotlib
```

> **Nota sobre numpy:** O `README.md` original menciona numpy, mas nenhum arquivo de código-fonte importa numpy diretamente. O `requirements.txt` também não o lista. A instalação de numpy **não é obrigatória** para executar o projeto.

---

## 4. Dependências Necessárias

| Dependência | Uso no projeto | Obrigatória? |
|---|---|---|
| `PyGObject` (gi) | Interface gráfica GTK 3 em `interface_gui.py` | Sim, para a GUI |
| `matplotlib` | Gráficos dos sinais embutidos na GUI (`FigureCanvas`) | Sim, para a GUI |
| `threading` | Threads TX e RX em `simulador.py` | Stdlib Python |
| `queue` | Canal de comunicação entre threads em `simulador.py` | Stdlib Python |
| `math` | Funções trigonométricas em `camada_fisica.py` | Stdlib Python |
| `random` | Gerador de ruído gaussiano em `meio_comunicacao.py` | Stdlib Python |

---

## 5. Passo a Passo para Instalação

### 5.1 Instalar dependências do sistema (GTK)

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### 5.2 Instalar dependências Python

Recomenda-se usar um ambiente virtual para não poluir o sistema:

```bash
# Criar ambiente virtual com acesso ao PyGObject do sistema
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Instalar dependências Python listadas no requirements.txt
pip install -r requirements.txt
```

Neste checkout local, o ambiente `.venv` já foi criado com `uv` e está pronto para uso.

Se não usar ambiente virtual, instalar globalmente:

```bash
pip install matplotlib
```

> **Atenção:** PyGObject/GTK deve ser instalado pelo gerenciador de pacotes do sistema. O `requirements.txt` não tenta instalar PyGObject via pip.

### 5.3 Entrar no diretório do projeto

```bash
cd TrabalhoTR1
```

---

## 6. Passo a Passo para Executar o Projeto

### 6.1 Executar a interface gráfica (modo principal)

```bash
python3 simulador.py
```

Isso abrirá a janela GTK com o simulador completo.

### 6.2 Executar os testes automatizados (sem GTK)

Os testes rodam no terminal e **não requerem GTK instalado**:

```bash
python3 testes.py
```

A saída esperada é uma lista de linhas `[PASS]` ou `[FAIL]` seguida de `RESULTADO GERAL: TODOS OS TESTES PASSARAM`.

---

## 7. Comandos Exatos para Rodar

```bash
# 1. Instalar dependências do sistema
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# 2. Instalar dependências Python
.venv/bin/python -m pip install -r requirements.txt

# 3. Rodar a interface gráfica
.venv/bin/python simulador.py

# OU: rodar apenas os testes (sem GTK)
.venv/bin/python testes.py
```

---

## 8. Explicação do Ponto de Entrada

O ponto de entrada principal é o arquivo **`simulador.py`**. O arquivo
**`Simulador.py`** permanece como compatibilidade para quem executar o nome antigo.

O bloco `if __name__ == "__main__":` no final do arquivo executa:

```python
from interface_gui import JanelaSimulador
JanelaSimulador().executar()
```

Isso importa a GUI somente quando o arquivo é executado diretamente, permitindo que os módulos das camadas (`camada_fisica.py`, etc.) sejam importados e testados em máquinas sem GTK instalado.

A classe `JanelaSimulador` é definida em `interface_gui.py` e, ao ser instanciada, monta a janela GTK. O método `executar()` exibe a janela e entra no loop de eventos do GTK (`Gtk.main()`).

---

## 9. Fluxo Geral de Funcionamento

Ao clicar em **"Transmitir"** na interface gráfica, o seguinte pipeline é executado:

```
CONFIGURAÇÃO DA GUI
        |
        v
[simulador.py: executar_simulacao(config)]
        |
        |-- THREAD TX (threading.Thread) --------------------
        |   1. texto → bits (camada_aplicacao)
        |   2. bits → quadros (camada_enlace: EDC + Hamming + enquadramento)
        |   3. quadros → sinal banda-base (camada_fisica: NRZ/Manchester/Bipolar)
        |   4. sinal → sinal portadora (camada_fisica: ASK/FSK/QPSK/16-QAM)
        |   5. sinal → queue.Queue (fila_tx)
        |
        |-- CANAL (thread principal) -------------------------
        |   6. sinal_limpo ← fila_tx
        |   7. sinal_ruidoso = sinal_limpo + ruído N(x, σ) (meio_comunicacao)
        |   8. sinal_ruidoso → fila_rx
        |
        |-- THREAD RX (threading.Thread) --------------------
        |   9.  sinal_ruidoso ← fila_rx
        |   10. sinal → bits (camada_fisica: demodulação)
        |   11. bits → quadros desenquadrados (camada_enlace: Hamming + EDC + desenquadramento)
        |   12. bits → texto (camada_aplicacao)
        |
        v
RESULTADOS EXIBIDOS NA GUI (bits por camada, gráficos, SNR, erros detectados)
```

As duas threads (TX e RX) se comunicam exclusivamente por filas (`queue.Queue`), que representam o meio físico.

---

## 10. Possíveis Erros de Execução e Como Resolver

### Erro: `ModuleNotFoundError: No module named 'gi'`

**Causa:** PyGObject não está instalado ou não foi instalado para o Python correto.

**Solução:**

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

Se usar ambiente virtual, o `gi` do sistema pode não ser visível. Nesse caso:

```bash
# Criar ambiente virtual com acesso aos pacotes do sistema
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install matplotlib
python3 simulador.py
```

---

### Erro: `ModuleNotFoundError: No module named 'matplotlib'`

**Causa:** matplotlib não está instalado.

**Solução:**

```bash
pip install matplotlib
```

---

### Erro: `ValueError: Quadro final excede 255 bytes`

**Causa:** O tamanho máximo de quadro configurado na GUI, combinado com o EDC e o Hamming, resulta em um quadro maior que 255 bytes (limite do enquadramento por contagem de caracteres).

**Solução:** Reduzir o "Tam. máx. de quadro (bytes)" na GUI para um valor menor (ex.: 8 ou 16) quando o enquadramento for "Contagem de caracteres".

---

### Erro: `Gtk-WARNING: cannot open display`

**Causa:** Não há display gráfico disponível (ex.: servidor SSH sem X11 forwarding).

**Solução:** Usar X11 forwarding via SSH (`ssh -X usuario@host`) ou rodar apenas os testes:

```bash
python3 testes.py
```

---

### Texto recuperado com diferenças (`COM DIFERENÇAS`)

**Causa:** O ruído gaussiano é alto o suficiente para corromper bits além da capacidade de correção.

**Solução:** Reduzir o desvio padrão σ na GUI (campo "Ruído - desvio σ (V)") para 0.1 ou menos, ou selecionar uma modulação mais robusta (ex.: NRZ-Polar com σ baixo).

---

## 11. Observações Importantes para o Avaliador/Professor (Linux)

1. **Nome do arquivo de entrada:** use `simulador.py` como ponto de entrada principal. `Simulador.py` existe apenas como compatibilidade com o nome antigo.

2. **Requisito de display gráfico:** O simulador abre uma janela GTK 3. É obrigatório ter um servidor gráfico disponível (X11 ou Wayland) para rodar `simulador.py`. Para ambientes sem display, usar `python3 testes.py`.

3. **PyGObject via sistema, não pip:** Em muitas distribuições Linux, `PyGObject` funciona melhor quando instalado via `apt` (`python3-gi`) do que via `pip`. Se houver conflito, criar o ambiente virtual com `--system-site-packages` (ver seção 10).

4. **Numpy não é necessário:** Apesar de mencionado no `README.md` original, nenhum arquivo de código-fonte importa numpy. O `requirements.txt` também não o lista. A instalação é desnecessária.

5. **Sem dependências externas para os algoritmos centrais:** Os algoritmos de CRC-32, Hamming, checksum e todas as modulações foram implementados manualmente, sem bibliotecas externas. Apenas `math`, `random`, `threading` e `queue` da stdlib Python são usados nas camadas.

6. **Testes reprodutíveis:** `testes.py` usa `random.seed(42)`, garantindo resultados idênticos em qualquer máquina.

7. **Python 3.8+:** O código usa f-strings e anotações de tipo compatíveis com Python 3.8 ou superior. Versões anteriores não foram testadas.

8. **Arquivo de relatório:** `relatorio/RelatórioTR1 (provisório).pdf` contém o relatório do trabalho. O nome do arquivo inclui caracteres especiais (acento e espaços) — ao acessar via terminal, use aspas: `xdg-open "relatorio/RelatórioTR1 (provisório).pdf"`.

---

## Resumo do que foi documentado

- Visão geral do simulador e suas funcionalidades
- Estrutura completa de arquivos e responsabilidade de cada módulo
- Pré-requisitos de ambiente (Python 3, GTK 3, matplotlib, PyGObject)
- Dependências reais identificadas no código-fonte (nenhuma delas é numpy)
- Passo a passo de instalação com ambiente virtual opcional
- Comandos exatos para rodar a GUI e os testes
- Explicação detalhada do ponto de entrada (`simulador.py`) e do bloco `__main__`
- Diagrama do fluxo completo TX → canal → RX com as duas threads
- Cinco erros comuns com causa e solução específica
- Observações críticas para execução em Linux e dependências gráficas

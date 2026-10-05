# Decisões de projeto

O enunciado e os slides deixam vários detalhes em aberto. Este documento registra **o que foi decidido e
por quê**; ele serve de base para a seção "decisões tomadas" do relatório e para a defesa oral. Cada decisão
mira o nível de uma disciplina de graduação em Engenharia de Computação: correta e explicável, sem
sofisticação além do que o trabalho pede.

Legenda da fonte: **slides** = confirmado nos slides (detalhes em `docs/referencias/`); **projeto** = os
slides não dizem, a escolha é nossa.

## Camada física

| Tema | Decisão | Fonte | Por quê |
|---|---|---|---|
| NRZ-Polar | 1 = +V, 0 = −V, durante todo o bit | slides (CF-10) | — |
| Manchester | bit 1 = alto→baixo, bit 0 = baixo→alto (dado XOR clock) | slides (CF-10, slide 8) | Confirmado no slide 8: 1 = Dado XOR Clock → alto na 1ª metade e baixo na 2ª. Atenção: é a convenção de Thomas/Tanenbaum; a IEEE 802.3 é a inversa, e o resumo geral dos slides a cita por engano. |
| Bipolar | AMI: 0 = 0 V, cada 1 alterna entre +V e −V | slides (CF-10, slide 9) | RZ Bipolar é outra técnica, não pedida |
| Decisão banda-base | média das amostras de cada bit (Manchester: comparação das duas metades) | projeto | Os slides amostram no centro do bit; a média usa as 100 amostras e filtra melhor o ruído gaussiano |
| Resolução | 100 amostras por bit e por símbolo | projeto | Suficiente para gráficos legíveis e correlação estável |
| ASK | on-off: bit 1 = portadora com amplitude V, bit 0 = 0 V; limiar V/2 sobre `√(I²+Q²)` | slides (CF-11) | — |
| FSK | duas frequências inteiras (2 e 4 ciclos por símbolo), mesma amplitude; decide pela maior energia | slides (modulação) / projeto (demodulação) | Frequências inteiras são ortogonais no símbolo, o que torna a correlação exata |
| 8PSK | 3 bits por símbolo, fase = k·45°, raio V, Gray `000,001,011,010,110,111,101,100` | slides (CF-12) | Gray reduz o erro de bit a 1 por erro de símbolo vizinho |
| 32-QAM | cruz 6×6 sem os 4 cantos, níveis ±1, ±3, ±5 vezes V/5 | slides (formato) / projeto (níveis) | 32 não é quadrado perfeito; os cantos têm a maior energia |
| Rotulagem do 32-QAM | 2 bits de quadrante (Gray) + 3 bits de posição (Gray ao longo do ciclo de 8 pontos do quadrante) | projeto | Gray perfeito não existe na cruz; este mapeamento deixa 48 dos 52 pares de vizinhos a 1 bit (4 pares a 3 bits) e é fácil de explicar |
| Demodulação da portadora | correlação com cos/−sen (recupera I e Q) e ponto de constelação mais próximo | slides (modulador I/Q) / projeto | A decisão por mínima distância é a ótima para ruído gaussiano |
| Padding | zeros no fim para fechar o último símbolo; o enlace os ignora | projeto | O 8PSK e o 32-QAM não dividem o fluxo em bytes inteiros |

## Meio de comunicação

| Tema | Decisão | Fonte |
|---|---|---|
| Ruído | AWGN: a cada amostra soma-se `random.gauss(x, σ)` (Volts) | enunciado |
| Potência | `P = média(v²)` em Watts, carga de 1 Ω; SNR = P_sinal / P_ruído | slides (SNR) / projeto |

## Camada de enlace

| Tema | Decisão | Fonte | Por quê |
|---|---|---|---|
| Ordem no TX | dividir em blocos → anexar EDC → Hamming → enquadrar (RX inverso) | projeto | O Hamming protege também o EDC |
| Contagem de caracteres | 1 byte; **inclui o próprio cabeçalho** (2 bytes de dados → 3); quadro de até 255 bytes | slides (TR1_08, 28-30) | Cabeçalho `0` marca o padding |
| Byte stuffing | FLAG `0x7E`, ESC `0x7D`; ESC antes de FLAG e de ESC | slides (regra) / projeto (valores) | Valores do HDLC/PPP |
| Bit stuffing | FLAG `01111110`; insere 0 após cinco 1s | slides (TR1_08, 36-37) | — |
| Entrelaçamento | matriz com paridade par por coluna, transmitida linha a linha; N = 8 colunas (cada linha é um byte, a linha de paridade é 1 byte); quadro delimitado pela contagem de caracteres | slides (algoritmo) / projeto (N e delimitação) | Mantém o quadro alinhado em bytes e reaproveita a contagem. Como a transmissão é por linhas, a ordem dos bits não muda; o ganho é a paridade por coluna (os slides tratam como detecção) |
| Paridade par | 1 byte por quadro: 7 zeros + bit de paridade | slides (conceito) / projeto (byte) | Alinhamento em bytes |
| Checksum | palavras de 16 bits, soma em complemento de 1 com end-around carry, complemento da soma anexado em 2 bytes; o receptor soma tudo e espera `0xFFFF` | slides (conceito) / projeto (16 bits) | Mesmo formato do checksum da Internet |
| CRC-32 | gerador `0x104C11DB7`; divisão módulo 2 pura (anexa 32 zeros, resto de 32 bits); 4 bytes, MSB primeiro; o receptor divide o quadro inteiro e espera resto 0 | slides (algoritmo) / projeto (polinômio) | Sem valor inicial nem XOR final, como nos slides. O CRC-32 padrão refletido (`0xCBF43926` para `"123456789"`) fica como variante opcional de validação |
| Hamming | (11,7) dos slides; dados completados com zeros até múltiplo de 7 e saída até múltiplo de 8 | slides (código) / projeto (padding) | Fecha em bytes para os enquadramentos. Não detecta erro duplo: quem pega é o EDC |
| Quadro com EDC inválido | **sinalizar**: os bits ficam no texto e o quadro é marcado com `edc_ok = False` | projeto | A GUI mostra o erro e o texto corrompido, o que é mais didático do que descartar |
| Tamanho máximo de quadro | configurável (padrão 8 bytes); com contagem/entrelaçamento o quadro final não pode passar de 255 bytes | projeto | `transmitir` valida e lança `ValueError` |

## Aplicação e simulador

| Tema | Decisão | Fonte |
|---|---|---|
| Codificação do texto | UTF-8, MSB primeiro; bytes inválidos viram `�` | projeto |
| Transmissor e receptor | duas threads (`threading.Thread`); a thread principal faz o papel do canal, ligada por filas (`queue.Queue`) | enunciado |
| Erros nas threads | capturados na thread e relançados na principal | projeto |
| Interface | GTK 3 + matplotlib; só lê a configuração, chama o simulador e mostra os resultados | enunciado |

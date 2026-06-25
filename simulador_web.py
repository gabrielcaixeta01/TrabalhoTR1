# -*- coding: utf-8 -*-
"""Interface web local para o Simulador TR1.

Roda sem GTK, Tk ou matplotlib. A pagina chama a mesma funcao
simulador.executar_simulacao usada pela GUI original.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys
import webbrowser

import camada_enlace
import camada_fisica
import simulador


HOST = "127.0.0.1"
PORTA_PADRAO = 8765
MAX_BITS_TEXTO = 2048
MAX_AMOSTRAS_JSON = 500

ROTULOS_ENQUADRAMENTO = {
    "contagem": "Contagem de caracteres",
    "bytes": "FLAGs + inserção de bytes",
    "bits": "FLAGs + inserção de bits",
}
ROTULOS_DETECCAO = {
    "nenhum": "Nenhuma",
    "paridade": "Bit de paridade par",
    "checksum": "Checksum",
    "crc": "CRC-32",
}
ROTULOS_CORRECAO = {
    "nenhum": "Nenhuma",
    "hamming": "Hamming",
}
ROTULOS_DIGITAL = {
    "nrz": "NRZ-Polar",
    "manchester": "Manchester",
    "bipolar": "Bipolar AMI",
}
ROTULOS_PORTADORA = {
    "nenhuma": "Nenhuma",
    "ask": "ASK",
    "fsk": "FSK",
    "qpsk": "QPSK",
    "16qam": "16-QAM",
}
BITS_POR_SIMBOLO = {
    "ask": 1,
    "fsk": 1,
    "qpsk": 2,
    "16qam": 4,
}


HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Simulador TR1 - Camadas Física e de Enlace</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef2f7;
      --panel: #ffffff;
      --panel-2: #f8fafc;
      --text: #0f172a;
      --muted: #475569;
      --border: #cbd5e1;
      --blue: #1d4ed8;
      --blue-2: #2563eb;
      --green: #047857;
      --red: #b91c1c;
      --trace: #0f766e;
      --shadow: 0 14px 36px rgba(15, 23, 42, 0.12);
      --mono: "SFMono-Regular", "Menlo", "Consolas", monospace;
      --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: var(--sans);
      font-size: 14px;
    }

    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(280px, 340px) 1fr;
      gap: 16px;
      padding: 16px;
    }

    aside, main, .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    aside {
      padding: 16px;
      overflow: auto;
    }

    main {
      padding: 16px;
      overflow: auto;
    }

    h1 {
      margin: 0 0 4px;
      font-size: 22px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .sub {
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.35;
    }

    label {
      display: block;
      margin: 12px 0 6px;
      color: var(--text);
      font-weight: 700;
    }

    input, select, button, textarea {
      width: 100%;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #ffffff;
      color: var(--text);
      font: inherit;
      min-height: 38px;
    }

    input, select, textarea {
      padding: 8px 10px;
    }

    input:focus, select:focus, textarea:focus, button:focus {
      outline: 3px solid rgba(37, 99, 235, 0.25);
      border-color: var(--blue-2);
    }

    button {
      margin-top: 16px;
      border-color: var(--blue);
      background: var(--blue);
      color: #ffffff;
      font-weight: 800;
      cursor: pointer;
    }

    button:hover { background: var(--blue-2); }
    button:disabled { opacity: 0.6; cursor: wait; }

    button.secondary {
      border-color: var(--border);
      background: #ffffff;
      color: var(--blue);
    }

    button.secondary.active {
      border-color: var(--red);
      background: var(--red);
      color: #ffffff;
    }

    input[type="range"] {
      padding: 0;
      min-height: 30px;
      accent-color: var(--blue);
    }

    .range-row, .button-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }

    .button-row {
      grid-template-columns: 1fr 1fr;
      margin-top: 16px;
    }

    .button-row button {
      margin-top: 0;
    }

    .value-pill, .live-pill {
      min-width: 72px;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 6px 10px;
      background: var(--panel-2);
      color: var(--text);
      font-family: var(--mono);
      font-size: 12px;
      text-align: center;
    }

    .range-row .value-pill {
      width: 86px;
    }

    .live-pill {
      width: 100%;
      margin-top: 10px;
      border-radius: 6px;
      font-family: var(--sans);
      font-weight: 700;
    }

    .live-pill.on {
      border-color: rgba(4, 120, 87, 0.45);
      background: rgba(4, 120, 87, 0.12);
      color: var(--green);
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .card {
      box-shadow: none;
      padding: 14px;
      min-width: 0;
    }

    .card h2 {
      margin: 0 0 10px;
      font-size: 16px;
      line-height: 1.2;
    }

    .status {
      border-left: 5px solid var(--blue);
      margin-bottom: 14px;
      padding: 12px 14px;
      background: var(--panel-2);
      color: var(--text);
    }

    .status.ok { border-left-color: var(--green); }
    .status.error { border-left-color: var(--red); }

    .metrics {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }

    .metric {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
    }

    .metric b {
      display: block;
      font-size: 18px;
      margin-top: 2px;
    }

    .diagnostics {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }

    .diagnostics h2 {
      margin: 0 0 10px;
      font-size: 16px;
    }

    .diagnostics table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .diagnostics th, .diagnostics td {
      padding: 8px 10px;
      border-top: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }

    .diagnostics th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }

    .diagnostics td:nth-child(2),
    .diagnostics td:nth-child(3),
    .diagnostics td:nth-child(4) {
      font-family: var(--mono);
      white-space: nowrap;
    }

    .delta {
      color: var(--green);
      font-weight: 800;
    }

    .delta.zero {
      color: var(--muted);
      font-weight: 700;
    }

    pre {
      margin: 0;
      padding: 10px;
      overflow: auto;
      max-height: 220px;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 6px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    canvas {
      width: 100%;
      height: 180px;
      display: block;
      margin-top: 10px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 6px;
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .empty {
      min-height: 420px;
      display: grid;
      place-items: center;
      text-align: center;
      color: var(--muted);
      background:
        linear-gradient(90deg, rgba(29, 78, 216, 0.08) 1px, transparent 1px),
        linear-gradient(rgba(29, 78, 216, 0.08) 1px, transparent 1px);
      background-size: 24px 24px;
      border: 1px dashed var(--border);
      border-radius: 8px;
    }

    .empty strong {
      display: block;
      color: var(--text);
      font-size: 18px;
      margin-bottom: 6px;
    }

    @media (max-width: 920px) {
      .app { grid-template-columns: 1fr; }
      .grid, .metrics { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>Simulador TR1</h1>
      <p class="sub">Transmissão completa: aplicação, enlace, física e meio ruidoso.</p>

      <label for="texto">Texto de entrada</label>
      <input id="texto" value="Ola, TR1!">

      <label for="tam_max_quadro">Tamanho máximo do quadro</label>
      <input id="tam_max_quadro" type="number" min="1" max="100" value="8">

      <label for="enquadramento">Enquadramento</label>
      <select id="enquadramento">
        <option value="contagem">Contagem de caracteres</option>
        <option value="bytes">FLAGs + inserção de bytes</option>
        <option value="bits" selected>FLAGs + inserção de bits</option>
      </select>

      <label for="deteccao">Detecção de erros</label>
      <select id="deteccao">
        <option value="nenhum">Nenhuma</option>
        <option value="paridade">Bit de paridade par</option>
        <option value="checksum">Checksum</option>
        <option value="crc" selected>CRC-32 (IEEE 802)</option>
      </select>

      <label for="correcao">Correção de erros</label>
      <select id="correcao">
        <option value="nenhum">Nenhuma</option>
        <option value="hamming" selected>Hamming</option>
      </select>

      <label for="mod_digital">Modulação digital</label>
      <select id="mod_digital">
        <option value="nrz" selected>NRZ-Polar</option>
        <option value="manchester">Manchester</option>
        <option value="bipolar">Bipolar (AMI)</option>
      </select>

      <label for="mod_portadora">Modulação por portadora</label>
      <select id="mod_portadora">
        <option value="nenhuma">Nenhuma (banda-base)</option>
        <option value="ask">ASK</option>
        <option value="fsk">FSK</option>
        <option value="qpsk" selected>QPSK</option>
        <option value="16qam">16-QAM</option>
      </select>

      <label for="ruido_media">Ruído - média x (V)</label>
      <input id="ruido_media" type="number" step="0.01" value="0.00">

      <label for="ruido_sigma">Ruído - desvio σ (V)</label>
      <div class="range-row">
        <input id="ruido_sigma" type="range" min="0" max="50" step="0.10" value="0.10">
        <input id="ruido_sigma_valor" class="value-pill" type="number"
               min="0" max="50" step="0.01" value="0.10"
               aria-label="Valor do desvio sigma em Volts">
      </div>

      <label for="intervalo_ms">Intervalo contínuo (ms)</label>
      <input id="intervalo_ms" type="number" min="250" max="5000" step="50" value="900">

      <div class="button-row">
        <button id="transmitir">Transmitir uma vez</button>
        <button id="continuo" class="secondary">Iniciar contínua</button>
      </div>
      <div id="modo_status" class="live-pill">Modo manual</div>
    </aside>

    <main>
      <div id="status" class="status">Pronto. Ajuste os parâmetros e clique em Transmitir.</div>
      <div id="conteudo" class="empty">
        <div>
          <strong>Nenhuma transmissão ainda</strong>
          Escolha os parâmetros e rode a simulação para ver bits, quadros, sinais e texto recuperado.
        </div>
      </div>
    </main>
  </div>

  <script>
    const $ = (id) => document.getElementById(id);
    const botao = $("transmitir");
    const botaoContinuo = $("continuo");
    const status = $("status");
    const conteudo = $("conteudo");
    const sigma = $("ruido_sigma");
    const sigmaValor = $("ruido_sigma_valor");
    const modoStatus = $("modo_status");
    let modoContinuo = false;
    let transmitindo = false;
    let timerContinuo = null;
    let contadorTransmissoes = 0;

    function limitarSigma(valor) {
      if (!Number.isFinite(valor)) return 0;
      return Math.min(50, Math.max(0, valor));
    }

    function atualizarSigma() {
      sigmaValor.value = limitarSigma(Number(sigma.value)).toFixed(2);
    }

    function atualizarSliderSigma() {
      const valor = limitarSigma(Number(sigmaValor.value));
      sigma.value = valor;
      sigmaValor.value = valor.toFixed(2);
    }

    function configAtual() {
      return {
        texto: $("texto").value,
        tam_max_quadro: Number($("tam_max_quadro").value),
        enquadramento: $("enquadramento").value,
        deteccao: $("deteccao").value,
        correcao: $("correcao").value,
        mod_digital: $("mod_digital").value,
        mod_portadora: $("mod_portadora").value,
        ruido_media: Number($("ruido_media").value),
        ruido_sigma: limitarSigma(Number(sigmaValor.value)),
      };
    }

    function escapeHtml(text) {
      return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    async function transmitir() {
      if (transmitindo) return;
      transmitindo = true;
      botao.disabled = true;
      if (!modoContinuo) {
        status.className = "status";
        status.textContent = "Transmitindo...";
      }
      try {
        const resposta = await fetch("/api/simular", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(configAtual()),
        });
        const dados = await resposta.json();
        if (!resposta.ok || dados.erro) {
          throw new Error(dados.erro || "Falha ao simular.");
        }
        contadorTransmissoes += 1;
        renderizar(dados);
      } catch (erro) {
        status.className = "status error";
        status.textContent = erro.message;
        pararContinuo();
      } finally {
        transmitindo = false;
        botao.disabled = false;
        if (modoContinuo) agendarContinuo();
      }
    }

    function intervaloAtual() {
      const valor = Number($("intervalo_ms").value);
      if (!Number.isFinite(valor)) return 900;
      return Math.min(5000, Math.max(250, valor));
    }

    function iniciarContinuo() {
      if (modoContinuo) return;
      modoContinuo = true;
      botaoContinuo.textContent = "Parar contínua";
      botaoContinuo.classList.add("active");
      modoStatus.classList.add("on");
      modoStatus.textContent = "Transmissão contínua ativa";
      transmitir();
    }

    function pararContinuo() {
      modoContinuo = false;
      if (timerContinuo) clearTimeout(timerContinuo);
      timerContinuo = null;
      botaoContinuo.textContent = "Iniciar contínua";
      botaoContinuo.classList.remove("active");
      modoStatus.classList.remove("on");
      modoStatus.textContent = "Modo manual";
    }

    function alternarContinuo() {
      if (modoContinuo) pararContinuo();
      else iniciarContinuo();
    }

    function agendarContinuo() {
      if (!modoContinuo) return;
      if (timerContinuo) clearTimeout(timerContinuo);
      timerContinuo = setTimeout(transmitir, intervaloAtual());
    }

    function renderizar(dados) {
      status.className = "status " + (dados.ok ? "ok" : "error");
      const sufixo = modoContinuo ? ` | contínua #${contadorTransmissoes}` : "";
      status.textContent = `${dados.status} | sigma ${limitarSigma(Number(sigmaValor.value)).toFixed(2)} V${sufixo}`;

      conteudo.className = "stack";
      conteudo.innerHTML = `
        <section class="metrics">
          <div class="metric">Bits da aplicação<b>${dados.diagnostico.bits_aplicacao}</b></div>
          <div class="metric">Bits no enlace<b>${dados.diagnostico.bits_enlace}</b></div>
          <div class="metric">Bits adicionados<b>${dados.diagnostico.bits_adicionados}</b></div>
          <div class="metric">Potência do sinal<b>${dados.potencia_sinal_w}</b></div>
          <div class="metric">Potência do ruído<b>${dados.potencia_ruido_w}</b></div>
          <div class="metric">Texto recuperado<b>${dados.ok ? "OK" : "com diferenças"}</b></div>
        </section>
        <section class="diagnostics">
          <h2>Processamento por fase</h2>
          <table>
            <thead>
              <tr>
                <th>Fase</th>
                <th>Entrada</th>
                <th>Saída</th>
                <th>Adicionou</th>
                <th>Diagnóstico</th>
              </tr>
            </thead>
            <tbody>
              ${dados.diagnostico.fases.map(renderizarFase).join("")}
            </tbody>
          </table>
        </section>
        <section class="grid">
          <article class="card">
            <h2>Transmissor (Tx)</h2>
            <pre>${escapeHtml(dados.texto_tx)}</pre>
            <canvas id="tx1"></canvas>
            <canvas id="tx2"></canvas>
          </article>
          <article class="card">
            <h2>Receptor (Rx)</h2>
            <pre>${escapeHtml(dados.texto_rx)}</pre>
            <canvas id="rx1"></canvas>
            <canvas id="rx2"></canvas>
          </article>
        </section>
      `;

      plotar($("tx1"), dados.sinais.tx_banda_base, "Sinal banda-base (Tx)");
      plotar($("tx2"), dados.sinais.tx_transmitido, "Sinal transmitido ao meio (Tx)");
      plotar($("rx1"), dados.sinais.rx_recebido, "Sinal recebido com ruído (Rx)");
      plotar($("rx2"), dados.sinais.rx_banda_base, "Banda-base reconstruído (Rx)");
    }

    function renderizarFase(fase) {
      const deltaClass = fase.delta === "0 bits" ? "delta zero" : "delta";
      return `
        <tr>
          <td>${escapeHtml(fase.nome)}</td>
          <td>${escapeHtml(fase.entrada)}</td>
          <td>${escapeHtml(fase.saida)}</td>
          <td class="${deltaClass}">${escapeHtml(fase.delta)}</td>
          <td>${escapeHtml(fase.detalhe)}</td>
        </tr>
      `;
    }

    function plotar(canvas, serie, titulo) {
      const ctx = canvas.getContext("2d");
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      canvas.width = Math.max(1, Math.floor(width * ratio));
      canvas.height = Math.max(1, Math.floor(height * ratio));
      ctx.scale(ratio, ratio);
      ctx.clearRect(0, 0, width, height);

      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#0f172a";
      ctx.font = "12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      ctx.fillText(titulo, 12, 18);

      if (!serie || serie.length < 2) {
        ctx.fillStyle = "#64748b";
        ctx.fillText("Sem amostras", 12, 42);
        return;
      }

      const top = 28;
      const bottom = height - 14;
      const left = 10;
      const right = width - 10;
      const min = Math.min(...serie);
      const max = Math.max(...serie);
      const span = max - min || 1;

      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      for (let i = 0; i < 4; i++) {
        const y = top + ((bottom - top) * i / 3);
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();
      }

      ctx.strokeStyle = "#0f766e";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      serie.forEach((valor, idx) => {
        const x = left + ((right - left) * idx / (serie.length - 1));
        const y = bottom - ((valor - min) / span) * (bottom - top);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    sigma.addEventListener("input", atualizarSigma);
    sigmaValor.addEventListener("input", atualizarSliderSigma);
    sigmaValor.addEventListener("change", atualizarSliderSigma);
    botao.addEventListener("click", transmitir);
    botaoContinuo.addEventListener("click", alternarContinuo);
    atualizarSigma();
    transmitir();
  </script>
</body>
</html>
"""


def bits_str(bits):
    texto = "".join(str(b) for b in bits[:MAX_BITS_TEXTO])
    if len(bits) > MAX_BITS_TEXTO:
        texto += f"... ({len(bits)} bits no total)"
    return texto


def amostrar(sinal):
    if not sinal:
        return []
    if len(sinal) <= MAX_AMOSTRAS_JSON:
        return [round(float(v), 5) for v in sinal]
    passo = len(sinal) / MAX_AMOSTRAS_JSON
    return [round(float(sinal[int(i * passo)]), 5)
            for i in range(MAX_AMOSTRAS_JSON)]


def plural_bits(n):
    return f"{n} bit" if n == 1 else f"{n} bits"


def plural_amostras(n):
    return f"{n} amostra" if n == 1 else f"{n} amostras"


def plural_quadros(n):
    return f"{n} quadro" if n == 1 else f"{n} quadros"


def diagnosticar(bits_app, resultado, config):
    tam_bits = config["tam_max_quadro"] * 8
    blocos = [bits_app[i:i + tam_bits] for i in range(0, len(bits_app), tam_bits)]
    bits_blocos = sum(len(bloco) for bloco in blocos)

    payloads_edc = []
    for bloco in blocos:
        payloads_edc.append(
            camada_enlace.ADICIONAR_EDC[config["deteccao"]](bloco))
    bits_apos_edc = sum(len(payload) for payload in payloads_edc)
    bits_edc = bits_apos_edc - bits_blocos

    payloads_correcao = []
    for payload in payloads_edc:
        if config["correcao"] == "hamming":
            payloads_correcao.append(camada_enlace.codificar_hamming(payload))
        else:
            payloads_correcao.append(payload)
    bits_apos_correcao = sum(len(payload) for payload in payloads_correcao)
    bits_correcao = bits_apos_correcao - bits_apos_edc

    fluxo_enquadrado = camada_enlace.ENQUADRAR[config["enquadramento"]](
        payloads_correcao)
    bits_enlace = len(fluxo_enquadrado)
    bits_enquadramento = bits_enlace - bits_apos_correcao

    amostras_digitais = len(resultado["tx_sinal_banda_base"])
    amostras_tx = len(resultado["tx_sinal_transmitido"])

    if config["mod_portadora"] == "nenhuma":
        simbolos = bits_enlace
        bits_representados = bits_enlace
        padding_portadora = 0
        detalhe_portadora = "Sem portadora: o sinal banda-base trafega no meio."
        saida_portadora = plural_amostras(amostras_tx)
    else:
        bits_por_simbolo = BITS_POR_SIMBOLO[config["mod_portadora"]]
        simbolos = (bits_enlace + bits_por_simbolo - 1) // bits_por_simbolo
        bits_representados = simbolos * bits_por_simbolo
        padding_portadora = bits_representados - bits_enlace
        detalhe_portadora = (
            f"{bits_por_simbolo} bit(s) por símbolo; "
            f"{simbolos} símbolo(s) geram {plural_amostras(amostras_tx)}.")
        saida_portadora = (
            f"{simbolos} símbolo(s), {plural_amostras(amostras_tx)}")

    fases = [
        {
            "nome": "Aplicação: texto -> bits",
            "entrada": f"{len(config['texto'].encode('utf-8'))} byte(s) UTF-8",
            "saida": plural_bits(len(bits_app)),
            "delta": "0 bits",
            "detalhe": "Conversão de texto para bytes UTF-8 e bits; não é redundância.",
        },
        {
            "nome": "Divisão em quadros",
            "entrada": plural_bits(len(bits_app)),
            "saida": f"{plural_quadros(len(blocos))}, {plural_bits(bits_blocos)}",
            "delta": "0 bits",
            "detalhe": f"Cada quadro carrega até {config['tam_max_quadro']} byte(s) de dados.",
        },
        {
            "nome": f"Detecção de erros: {ROTULOS_DETECCAO[config['deteccao']]}",
            "entrada": plural_bits(bits_blocos),
            "saida": plural_bits(bits_apos_edc),
            "delta": plural_bits(bits_edc),
            "detalhe": detalhe_deteccao(config["deteccao"], len(blocos)),
        },
        {
            "nome": f"Correção de erros: {ROTULOS_CORRECAO[config['correcao']]}",
            "entrada": plural_bits(bits_apos_edc),
            "saida": plural_bits(bits_apos_correcao),
            "delta": plural_bits(bits_correcao),
            "detalhe": detalhe_correcao(config["correcao"]),
        },
        {
            "nome": f"Enquadramento: {ROTULOS_ENQUADRAMENTO[config['enquadramento']]}",
            "entrada": plural_bits(bits_apos_correcao),
            "saida": plural_bits(bits_enlace),
            "delta": plural_bits(bits_enquadramento),
            "detalhe": detalhe_enquadramento(config["enquadramento"], len(blocos)),
        },
        {
            "nome": f"Modulação digital: {ROTULOS_DIGITAL[config['mod_digital']]}",
            "entrada": plural_bits(bits_enlace),
            "saida": plural_amostras(amostras_digitais),
            "delta": "0 bits",
            "detalhe": (
                f"Mapeia cada bit para {camada_fisica.AMOSTRAS_POR_BIT} "
                "amostras em Volts; muda representação, não quantidade de bits."
            ),
        },
        {
            "nome": f"Modulação por portadora: {ROTULOS_PORTADORA[config['mod_portadora']]}",
            "entrada": plural_bits(bits_enlace),
            "saida": saida_portadora,
            "delta": plural_bits(padding_portadora),
            "detalhe": detalhe_portadora,
        },
        {
            "nome": "Meio ruidoso",
            "entrada": plural_amostras(amostras_tx),
            "saida": plural_amostras(len(resultado["rx_sinal_recebido"])),
            "delta": "0 bits",
            "detalhe": (
                f"Soma ruído gaussiano com média {config['ruido_media']:.2f} V "
                f"e sigma {config['ruido_sigma']:.2f} V em cada amostra."
            ),
        },
    ]

    return {
        "bits_aplicacao": len(bits_app),
        "bits_enlace": bits_enlace,
        "bits_adicionados": bits_enlace - len(bits_app),
        "bits_edc": bits_edc,
        "bits_correcao": bits_correcao,
        "bits_enquadramento": bits_enquadramento,
        "padding_portadora": padding_portadora,
        "fases": fases,
    }


def detalhe_deteccao(tipo, n_quadros):
    if tipo == "nenhum":
        return "Nenhum EDC anexado; o receptor não consegue validar corrupção."
    if tipo == "paridade":
        return f"Adiciona 1 byte por quadro: {n_quadros} x 8 bits."
    if tipo == "checksum":
        return f"Adiciona 2 bytes por quadro: {n_quadros} x 16 bits."
    return f"Adiciona 4 bytes por quadro: {n_quadros} x 32 bits."


def detalhe_correcao(tipo):
    if tipo == "hamming":
        return "Hamming(8,4) dobra payload + EDC: cada 4 bits viram 8 bits."
    return "Nenhuma redundância de correção foi adicionada."


def detalhe_enquadramento(tipo, n_quadros):
    if tipo == "contagem":
        return f"Adiciona 1 byte de contagem por quadro: {n_quadros} x 8 bits."
    if tipo == "bytes":
        return "Adiciona FLAGs e ESCs quando payload contém bytes especiais."
    return "Adiciona FLAGs e bits 0 após sequências de cinco bits 1."


def config_de_payload(payload):
    return {
        "texto": str(payload.get("texto", "")),
        "tam_max_quadro": int(payload.get("tam_max_quadro", 8)),
        "enquadramento": str(payload.get("enquadramento", "bits")),
        "deteccao": str(payload.get("deteccao", "crc")),
        "correcao": str(payload.get("correcao", "hamming")),
        "mod_digital": str(payload.get("mod_digital", "nrz")),
        "mod_portadora": str(payload.get("mod_portadora", "qpsk")),
        "ruido_media": float(payload.get("ruido_media", 0.0)),
        "ruido_sigma": float(payload.get("ruido_sigma", 0.1)),
    }


def montar_resposta(payload):
    config = config_de_payload(payload)
    if not config["texto"]:
        raise ValueError("Digite um texto para transmitir.")

    resultado = simulador.executar_simulacao(config)

    linhas_quadros = "\n".join(
        f"  Quadro {q['quadro']}: "
        f"EDC {'OK' if q['edc_ok'] else 'ERRO DETECTADO'}"
        + (f", {q['corrigidos']} bit(s) corrigido(s) por Hamming"
           if config["correcao"] == "hamming" else "")
        + (", ERRO DUPLO detectado" if q["erro_duplo"] else "")
        for q in resultado["rx_relatorio_quadros"]
    ) or "  (nenhum quadro recuperado)"

    texto_tx = (
        f"TEXTO DE ENTRADA:\n{config['texto']}\n\n"
        f"SAÍDA DE BITS - APLICAÇÃO "
        f"({len(resultado['tx_bits_aplicacao'])} bits):\n"
        f"{bits_str(resultado['tx_bits_aplicacao'])}\n\n"
        f"SAÍDA DE BITS - ENLACE/quadros "
        f"({len(resultado['tx_bits_enlace'])} bits):\n"
        f"{bits_str(resultado['tx_bits_enlace'])}"
    )

    texto_rx = (
        f"SAÍDA DE BITS - FÍSICA/demodulados "
        f"({len(resultado['rx_bits_fisica'])} bits):\n"
        f"{bits_str(resultado['rx_bits_fisica'])}\n\n"
        f"RELATÓRIO DOS QUADROS (enlace):\n{linhas_quadros}\n\n"
        f"SAÍDA DE BITS - APLICAÇÃO "
        f"({len(resultado['rx_bits_aplicacao'])} bits):\n"
        f"{bits_str(resultado['rx_bits_aplicacao'])}\n\n"
        f"SAÍDA DE TEXTO:\n{resultado['rx_texto']}"
    )

    ok = resultado["rx_texto"] == config["texto"]
    diagnostico = diagnosticar(resultado["tx_bits_aplicacao"], resultado, config)
    return {
        "ok": ok,
        "status": "Texto recuperado corretamente."
        if ok else "Texto recuperado com diferenças.",
        "potencia_sinal_w": f"{resultado['potencia_sinal_w']:.4f} W",
        "potencia_ruido_w": f"{resultado['potencia_ruido_w']:.4f} W",
        "texto_tx": texto_tx,
        "texto_rx": texto_rx,
        "diagnostico": diagnostico,
        "sinais": {
            "tx_banda_base": amostrar(resultado["tx_sinal_banda_base"]),
            "tx_transmitido": amostrar(resultado["tx_sinal_transmitido"]),
            "rx_recebido": amostrar(resultado["rx_sinal_recebido"]),
            "rx_banda_base": amostrar(resultado["rx_sinal_banda_base"]),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, formato, *args):
        return

    def enviar(self, status, corpo, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.enviar(200, HTML)
        elif self.path == "/health":
            self.enviar(200, "ok", "text/plain; charset=utf-8")
        elif self.path == "/favicon.ico":
            self.enviar(204, b"", "image/x-icon")
        else:
            self.enviar(404, "Nao encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/simular":
            self.enviar(404, "Nao encontrado", "text/plain; charset=utf-8")
            return

        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(tamanho).decode("utf-8"))
            resposta = montar_resposta(payload)
            self.enviar(200, json.dumps(resposta).encode("utf-8"),
                        "application/json; charset=utf-8")
        except Exception as exc:
            corpo = json.dumps({"erro": str(exc)}).encode("utf-8")
            self.enviar(400, corpo, "application/json; charset=utf-8")


def criar_servidor(porta_inicial=PORTA_PADRAO):
    ultimo_erro = None
    for porta in range(porta_inicial, porta_inicial + 20):
        try:
            return porta, HTTPServer((HOST, porta), Handler)
        except OSError as exc:
            ultimo_erro = exc
    raise RuntimeError(f"Nao foi possivel abrir porta local: {ultimo_erro}")


def main():
    abrir_browser = "--no-open" not in sys.argv
    porta, servidor = criar_servidor()
    url = f"http://{HOST}:{porta}"
    print(f"Simulador TR1 web rodando em {url}")
    print("Pressione Ctrl+C para encerrar.")
    if abrir_browser:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")


if __name__ == "__main__":
    main()

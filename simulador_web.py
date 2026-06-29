"""interface web local para o simulador tr1.

roda sem gtk, tk ou matplotlib. a página chama a mesma função
`simulador.executar_simulacao` usada pela gui.
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
MAX_AMOSTRAS_JSON = 1200
MAX_BITS_QUADRO = 192

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
      --bg: #eceff5;
      --panel: #ffffff;
      --panel-2: #f8fafc;
      --panel-3: #f1f5f9;
      --text: #0f172a;
      --muted: #475569;
      --soft: #94a3b8;
      --border: #cbd5e1;
      --blue: #1d4ed8;
      --blue-2: #2563eb;
      --blue-soft: rgba(37, 99, 235, 0.14);
      --green: #047857;
      --green-soft: rgba(4, 120, 87, 0.12);
      --red: #b91c1c;
      --trace: #0f766e;
      --shadow: 0 12px 28px rgba(15, 23, 42, 0.10);
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
      grid-template-columns: minmax(320px, 360px) minmax(0, 1fr);
      gap: 16px;
      padding: 16px;
    }

    aside, main, .card, .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    aside {
      padding: 16px;
      overflow: auto;
      align-self: start;
      max-height: calc(100vh - 32px);
      display: flex;
      flex-direction: column;
    }

    main {
      padding: 16px;
      overflow: auto;
      min-width: 0;
    }

    h1 {
      margin: 0 0 4px;
      font-size: 24px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .sub {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.35;
    }

    .section-label {
      margin: 16px 0 8px;
      color: var(--soft);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 1px;
      text-transform: uppercase;
    }

    label {
      display: block;
      margin: 10px 0 6px;
      color: var(--text);
      font-weight: 700;
    }

    input, select, button, textarea {
      width: 100%;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: #ffffff;
      color: var(--text);
      font: inherit;
      min-height: 44px;
    }

    input, select, textarea {
      padding: 9px 12px;
    }

    textarea {
      min-height: 82px;
      resize: vertical;
      line-height: 1.35;
    }

    input:focus, select:focus, textarea:focus, button:focus {
      outline: 3px solid rgba(37, 99, 235, 0.25);
      border-color: var(--blue-2);
    }

    button {
      border-color: var(--blue);
      background: var(--blue);
      color: #ffffff;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 6px 16px rgba(37, 99, 235, 0.20);
    }

    button:hover { background: var(--blue-2); }
    button:disabled { opacity: 0.6; cursor: wait; }

    button.secondary {
      border-color: var(--border);
      background: #ffffff;
      color: var(--blue);
      box-shadow: none;
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
      border-radius: 8px;
      font-family: var(--sans);
      font-weight: 700;
    }

    .live-pill.on {
      border-color: rgba(4, 120, 87, 0.45);
      background: var(--green-soft);
      color: var(--green);
    }

    .side-summary {
      margin-top: 14px;
      padding: 10px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel-2);
      color: var(--text);
      line-height: 1.45;
    }

    .controls-scroll {
      flex: 1;
      min-height: 0;
      overflow: auto;
      padding-right: 2px;
    }

    .action-dock {
      flex: none;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
      background: var(--panel);
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
      display: none;
    }

    .status.error {
      display: block;
      border-left: 5px solid var(--red);
      margin-bottom: 14px;
      padding: 12px 14px;
      background: var(--panel-2);
      color: var(--text);
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 14px;
    }

    .metric {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.2px;
    }

    .metric b {
      display: block;
      margin-top: 6px;
      color: var(--text);
      font-size: 23px;
      letter-spacing: 0;
    }

    .inspection-panel {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }

    .inspection-panel h2 {
      margin: 0 0 10px;
      font-size: 22px;
    }

    .panel-view {
      display: none;
    }

    .panel-view.active {
      display: block;
    }

    .table-wrap {
      overflow-x: auto;
      overflow-y: visible;
      margin-top: 14px;
    }

    .inspection-panel table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .inspection-panel th, .inspection-panel td {
      padding: 8px 10px;
      border-top: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }

    .inspection-panel th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }

    .inspection-panel td:nth-child(2),
    .inspection-panel td:nth-child(3),
    .inspection-panel td:nth-child(5) {
      font-family: var(--mono);
      white-space: normal;
    }

    .table-text {
      font-family: var(--sans);
      font-weight: 800;
    }

    .phase-note {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .bits-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: -2px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }

    .bits-legend span {
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .legend-swatch {
      width: 14px;
      height: 14px;
      border-radius: 4px;
      border: 1px solid var(--border);
    }

    .legend-swatch.payload {
      border-color: rgba(29, 78, 216, 0.35);
      background: var(--blue-soft);
    }

    .legend-swatch.added {
      border-color: rgba(4, 120, 87, 0.35);
      background: var(--green-soft);
    }

    .bits-cell {
      min-width: 260px;
      max-width: 390px;
    }

    .bit-frame {
      display: grid;
      gap: 5px;
      min-width: 240px;
    }

    .bit-frame-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 5px 8px;
      color: var(--muted);
      font-family: var(--sans);
      font-size: 11px;
      font-weight: 800;
      line-height: 1.2;
    }

    .bit-frame-meta span {
      padding: 2px 6px;
      border-radius: 999px;
      background: var(--panel-3);
    }

    .bit-byte-list {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      padding: 2px 0;
    }

    .bit-byte {
      display: inline-flex;
      gap: 1px;
      align-items: center;
      padding: 2px 4px;
      border: 1px solid var(--border);
      border-radius: 5px;
      background: var(--panel-2);
      color: var(--text);
      line-height: 1.15;
      white-space: nowrap;
    }

    .bit-byte.added-byte {
      border-color: rgba(4, 120, 87, 0.35);
      background: var(--green-soft);
    }

    .bit-byte.payload-byte {
      border-color: rgba(29, 78, 216, 0.35);
      background: var(--blue-soft);
    }

    .bit-bit {
      display: inline-block;
      min-width: 7px;
      text-align: center;
    }

    .bit-bit.added {
      border-radius: 3px;
      background: rgba(4, 120, 87, 0.16);
      color: var(--green);
      font-weight: 900;
    }

    .bit-bit.payload {
      border-radius: 3px;
      background: rgba(37, 99, 235, 0.14);
      color: var(--blue);
      font-weight: 900;
    }

    .bit-omitted {
      align-self: center;
      color: var(--muted);
      font-family: var(--sans);
      font-size: 11px;
      font-weight: 800;
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
      max-height: 260px;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 6px;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .info-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
    }

    .info-card {
      min-width: 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel-2);
      padding: 12px;
    }

    .info-card.full {
      grid-column: 1 / -1;
    }

    .info-card h3 {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.7px;
      text-transform: uppercase;
    }

    .info-value {
      color: var(--text);
      font-size: 24px;
      font-weight: 900;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }

    .info-value.text {
      font-size: 20px;
      font-weight: 700;
    }

    .info-detail {
      margin-top: 8px;
      color: var(--muted);
      line-height: 1.35;
    }

    .bit-preview {
      margin-top: 10px;
      padding: 9px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #ffffff;
      color: #334155;
      font-family: var(--mono);
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    .quadros-list {
      display: grid;
      gap: 8px;
      margin-top: 8px;
    }

    .quadro-item {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 9px 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #ffffff;
    }

    .quadro-num {
      color: var(--text);
      font-weight: 900;
    }

    .quadro-detail {
      color: var(--muted);
      line-height: 1.25;
    }

    .status-chip {
      border-radius: 999px;
      padding: 5px 9px;
      color: var(--green);
      background: var(--green-soft);
      font-size: 12px;
      font-weight: 900;
      white-space: nowrap;
    }

    .status-chip.error {
      color: var(--red);
      background: rgba(185, 28, 28, 0.10);
    }

    canvas {
      width: 100%;
      height: 260px;
      display: block;
      margin-top: 8px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: grab;
      touch-action: none;
    }

    canvas.dragging {
      cursor: grabbing;
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .view-toggle {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--border);
    }

    .view-toggle button {
      margin: 0;
      min-height: 42px;
      border-color: var(--border);
      background: #ffffff;
      color: var(--blue);
      box-shadow: none;
    }

    .view-toggle button.active {
      border-color: var(--blue);
      background: var(--blue);
      color: #ffffff;
      box-shadow: 0 6px 16px rgba(37, 99, 235, 0.18);
    }

    .graph-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 16px;
    }

    .tabs {
      display: flex;
      gap: 0;
      border-bottom: 1px solid var(--border);
      background: #dedad7;
      border-radius: 8px 8px 0 0;
      overflow: hidden;
    }

    .tab-button {
      width: auto;
      min-height: 42px;
      margin: 0;
      padding: 0 22px;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: var(--text);
      box-shadow: none;
      font-weight: 900;
    }

    .tab-button.active {
      background: #ffffff;
      color: var(--blue);
      box-shadow: inset 0 -4px 0 var(--blue);
    }

    .tab-panel {
      display: none;
      padding: 14px;
      border: 1px solid var(--border);
      border-top: 0;
      border-radius: 0 0 8px 8px;
      background: #ffffff;
    }

    .tab-panel.active {
      display: grid;
      gap: 14px;
    }

    .output-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
    }

    .output-block {
      min-width: 0;
      padding-top: 12px;
      border-top: 1px solid var(--border);
    }

    .output-block.full {
      grid-column: 1 / -1;
    }

    .graph-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }

    .graph-title {
      min-width: 0;
    }

    .step-chip {
      display: inline-flex;
      margin-bottom: 4px;
      padding: 2px 7px;
      border-radius: 999px;
      background: var(--panel-3);
      color: var(--muted);
      font-size: 11px;
      font-weight: 900;
      line-height: 1.2;
      text-transform: uppercase;
    }

    .output-block h3 {
      margin: 0;
      color: var(--text);
      font-size: 14px;
      line-height: 1.2;
    }

    .graph-actions {
      display: inline-flex;
      flex: none;
      align-items: center;
      gap: 6px;
    }

    .graph-actions button {
      width: 34px;
      min-height: 34px;
      margin: 0;
      padding: 0;
      border-color: var(--border);
      background: #ffffff;
      color: var(--blue);
      box-shadow: none;
      font-family: var(--mono);
      font-weight: 900;
    }

    .graph-actions button:hover {
      border-color: var(--blue);
      background: var(--blue-soft);
    }

    .zoom-level {
      min-width: 48px;
      color: var(--muted);
      font-family: var(--mono);
      font-size: 12px;
      font-weight: 800;
      text-align: right;
    }

    .text-box {
      min-height: 92px;
      padding: 10px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel-2);
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.45;
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
      aside { max-height: none; }
      .grid, .metrics, .output-grid, .graph-grid, .info-grid { grid-template-columns: 1fr; }
      .output-block.full, .info-card.full { grid-column: auto; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>Simulador TR1</h1>
      <p class="sub">Transmissão completa: aplicação, enlace, física e meio ruidoso.</p>

      <div class="controls-scroll">
      <div class="section-label">Mensagem</div>
      <label for="texto">Texto de entrada</label>
      <textarea id="texto" spellcheck="false">Ola, TR1!</textarea>

      <div class="section-label">Camada de enlace</div>
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

      <div class="section-label">Camada física</div>
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

      <div class="section-label">Meio e ruído</div>
      <label for="ruido_media">Ruído - média x (V)</label>
      <input id="ruido_media" type="number" step="0.01" value="0.00">

      <label for="ruido_sigma">Ruído - desvio σ (V)</label>
      <div class="range-row">
        <input id="ruido_sigma" type="range" min="0" max="50" step="0.10" value="0.10">
        <input id="ruido_sigma_valor" class="value-pill" type="number"
               min="0" max="50" step="0.01" value="0.10"
               aria-label="Valor do desvio sigma em Volts">
      </div>

      <div class="section-label">Execução</div>
      <label for="intervalo_ms">Intervalo contínuo (ms)</label>
      <input id="intervalo_ms" type="number" min="250" max="5000" step="50" value="900">
      </div>

      <div class="action-dock">
      <div class="button-row">
        <button id="transmitir">Transmitir uma vez</button>
        <button id="continuo" class="secondary">Iniciar contínua</button>
      </div>
      <div id="modo_status" class="live-pill">Modo manual</div>
      <div id="resumo_lateral" class="side-summary">
        Ajuste os parâmetros e transmita para ver potências, texto recuperado e
        detalhes de cada etapa.
      </div>
      </div>
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
    const resumoLateral = $("resumo_lateral");
    let modoContinuo = false;
    let transmitindo = false;
    let timerContinuo = null;
    let contadorTransmissoes = 0;
    let visualizacaoAtual = "processamento";
    let estadosGraficos = {};

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
        status.textContent = "";
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
      status.className = dados.ok ? "status" : "status error";
      const sufixo = modoContinuo ? ` | contínua #${contadorTransmissoes}` : "";
      status.textContent = dados.ok ? "" : `${dados.status}${sufixo}`;
      resumoLateral.innerHTML = `
        <strong>${modoContinuo ? "Modo contínuo" : "Modo manual"}</strong><br>
        Potência do sinal: ${escapeHtml(dados.potencia_sinal_w)}<br>
        Potência do ruído: ${escapeHtml(dados.potencia_ruido_w)}<br>
        Texto recuperado ${dados.ok ? "corretamente" : "com diferenças"}.
      `;
      const quadrosBits = dados.diagnostico.quadros_bits || {};

      conteudo.className = "stack";
      conteudo.innerHTML = `
        <section class="metrics">
          <div class="metric">Bits da aplicação<b>${escapeHtml(dados.diagnostico.bits_aplicacao)}</b></div>
          <div class="metric">Bits no enlace<b>${escapeHtml(dados.diagnostico.bits_enlace)}</b></div>
          <div class="metric">Bits adicionados<b>${escapeHtml(dados.diagnostico.bits_adicionados)}</b></div>
          <div class="metric">Potência do sinal<b>${escapeHtml(dados.potencia_sinal_w)}</b></div>
          <div class="metric">Potência do ruído<b>${escapeHtml(dados.potencia_ruido_w)}</b></div>
          <div class="metric">Texto recuperado<b>${dados.ok ? "OK" : "com diferenças"}</b></div>
        </section>
        <section class="inspection-panel">
          <div id="view_processamento" class="panel-view ${visualizacaoAtual === "processamento" ? "active" : ""}">
            <h2>Processamento por fase</h2>
            <div class="bits-legend" aria-label="Legenda dos bits">
              <span><i class="legend-swatch payload"></i>Carga original</span>
              <span><i class="legend-swatch added"></i>Bits adicionados</span>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Fase</th>
                    <th>Entrada</th>
                    <th>Saída</th>
                    <th>Bits/bytes</th>
                    <th>Adicionou</th>
                    <th>Diagnóstico</th>
                  </tr>
                </thead>
                <tbody>
                  ${renderizarLinhaTabela(
                    "Texto de entrada",
                    `"${dados.texto_entrada}"`,
                    `${bytesUtf8(dados.texto_entrada)} byte(s) UTF-8`,
                    quadrosBits.texto_entrada,
                    "0 bits",
                    "Mensagem original recebida pela aplicação."
                  )}
                  ${dados.diagnostico.fases.map(renderizarFase).join("")}
                  ${renderizarLinhaTabela(
                    "Física RX: demodulação",
                    "sinal recebido",
                    `${quadrosBits.fisica_rx ? quadrosBits.fisica_rx.total_bits : dados.diagnostico.bits_enlace} bits`,
                    quadrosBits.fisica_rx,
                    "0 bits",
                    "Demodula o sinal recebido e recupera o fluxo de bits da camada física."
                  )}
                  ${renderizarLinhaQuadrosTabela(dados.quadros, quadrosBits.quadros_rx)}
                  ${renderizarLinhaTabela(
                    "Aplicação RX: bits -> texto",
                    `${quadrosBits.aplicacao_rx ? quadrosBits.aplicacao_rx.total_bits : dados.diagnostico.bits_aplicacao} bits`,
                    `"${dados.texto_saida}"`,
                    quadrosBits.aplicacao_rx,
                    "0 bits",
                    dados.ok
                      ? "Texto recuperado corretamente; saída igual à entrada."
                      : "Texto recuperado com diferenças em relação à entrada."
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div id="view_graficos" class="panel-view ${visualizacaoAtual === "graficos" ? "active" : ""}">
            <h2>Gráficos do sinal</h2>
            <div class="graph-grid">
              <div class="output-block">
                <div class="graph-head">
                  <div class="graph-title">
                    <span class="step-chip">Etapa 1</span>
                    <h3>Sinal banda-base (Tx)</h3>
                  </div>
                  ${renderizarControlesGrafico("tx1")}
                </div>
                <canvas id="tx1"></canvas>
              </div>
              <div class="output-block">
                <div class="graph-head">
                  <div class="graph-title">
                    <span class="step-chip">Etapa 2</span>
                    <h3>Sinal transmitido ao meio (Tx)</h3>
                  </div>
                  ${renderizarControlesGrafico("tx2")}
                </div>
                <canvas id="tx2"></canvas>
              </div>
              <div class="output-block">
                <div class="graph-head">
                  <div class="graph-title">
                    <span class="step-chip">Etapa 3</span>
                    <h3>Sinal recebido com ruído (Rx)</h3>
                  </div>
                  ${renderizarControlesGrafico("rx1")}
                </div>
                <canvas id="rx1"></canvas>
              </div>
              <div class="output-block">
                <div class="graph-head">
                  <div class="graph-title">
                    <span class="step-chip">Etapa 4</span>
                    <h3>Banda-base reconstruída (Rx)</h3>
                  </div>
                  ${renderizarControlesGrafico("rx2")}
                </div>
                <canvas id="rx2"></canvas>
              </div>
            </div>
          </div>
          <div class="view-toggle" role="group" aria-label="Alternar painel central">
            <button type="button" data-view="processamento" class="${visualizacaoAtual === "processamento" ? "active" : ""}">Processamento</button>
            <button type="button" data-view="graficos" class="${visualizacaoAtual === "graficos" ? "active" : ""}">Gráficos</button>
          </div>
        </section>
      `;

      conectarVisualizacao();
      conectarControlesGraficos();
      desenharGraficos(dados);
      requestAnimationFrame(() => desenharGraficos(dados));
      setTimeout(() => desenharGraficos(dados), 80);
    }

    function renderizarControlesGrafico(id) {
      return `
        <div class="graph-actions" data-graph-actions="${id}">
          <button type="button" data-graph="${id}" data-graph-action="zoom-in"
                  title="Aproximar" aria-label="Aproximar gráfico">+</button>
          <button type="button" data-graph="${id}" data-graph-action="zoom-out"
                  title="Afastar" aria-label="Afastar gráfico">-</button>
          <button type="button" data-graph="${id}" data-graph-action="reset"
                  title="Redefinir zoom" aria-label="Redefinir zoom">1:1</button>
          <span class="zoom-level" id="${id}_zoom">x1.0</span>
        </div>
      `;
    }

    function desenharGraficos(dados) {
      const meta = dados.sinais_meta || {};
      plotar($("tx1"), dados.sinais.tx_banda_base, "Sinal banda-base (Tx)", meta.tx_banda_base);
      plotar($("tx2"), dados.sinais.tx_transmitido, "Sinal transmitido ao meio (Tx)", meta.tx_transmitido);
      plotar($("rx1"), dados.sinais.rx_recebido, "Sinal recebido com ruído (Rx)", meta.rx_recebido);
      plotar($("rx2"), dados.sinais.rx_banda_base, "Banda-base reconstruída (Rx)", meta.rx_banda_base);
    }

    function conectarVisualizacao() {
      document.querySelectorAll(".view-toggle button").forEach((botaoView) => {
        botaoView.addEventListener("click", () => {
          visualizacaoAtual = botaoView.dataset.view;
          document.querySelectorAll(".view-toggle button").forEach((item) => {
            item.classList.toggle("active", item === botaoView);
          });
          document.querySelectorAll(".panel-view").forEach((panel) => {
            panel.classList.toggle(
              "active",
              panel.id === `view_${visualizacaoAtual}`
            );
          });
          redesenharGraficosExistentes();
        });
      });
    }

    function conectarControlesGraficos() {
      document.querySelectorAll(".graph-actions button").forEach((botaoGrafico) => {
        botaoGrafico.addEventListener("click", () => {
          const id = botaoGrafico.dataset.graph;
          const acao = botaoGrafico.dataset.graphAction;
          if (acao === "zoom-in") aplicarZoomGrafico(id, 0.55, 0.5);
          if (acao === "zoom-out") aplicarZoomGrafico(id, 1.8, 0.5);
          if (acao === "reset") resetarZoomGrafico(id);
        });
      });

      document.querySelectorAll(".graph-grid canvas").forEach((canvas) => {
        canvas.addEventListener("wheel", (evento) => {
          if (!canvas.dataset.serie) return;
          evento.preventDefault();
          const rect = canvas.getBoundingClientRect();
          const esquerdaPlot = 52;
          const direitaPlot = Math.max(esquerdaPlot + 1, rect.width - 14);
          const posicao = (evento.clientX - rect.left - esquerdaPlot)
            / (direitaPlot - esquerdaPlot);
          const ancora = Math.min(1, Math.max(0, posicao));
          aplicarZoomGrafico(canvas.id, evento.deltaY < 0 ? 0.72 : 1.28, ancora);
        }, {passive: false});

        canvas.addEventListener("pointerdown", (evento) => {
          const estado = estadosGraficos[canvas.id];
          if (!estado || estado.fim <= estado.inicio) return;
          canvas.classList.add("dragging");
          canvas.setPointerCapture(evento.pointerId);
          canvas.dataset.dragX = evento.clientX;
          canvas.dataset.dragInicio = estado.inicio;
          canvas.dataset.dragFim = estado.fim;
        });

        canvas.addEventListener("pointermove", (evento) => {
          if (!canvas.classList.contains("dragging")) return;
          const estado = estadosGraficos[canvas.id];
          if (!estado) return;
          const rect = canvas.getBoundingClientRect();
          const larguraPlot = Math.max(1, rect.width - 66);
          const deslocamentoPx = evento.clientX - Number(canvas.dataset.dragX || 0);
          const faixa = Number(canvas.dataset.dragFim || estado.fim)
            - Number(canvas.dataset.dragInicio || estado.inicio);
          const deslocamento = -deslocamentoPx / larguraPlot * faixa;
          moverJanelaGrafico(
            canvas.id,
            Number(canvas.dataset.dragInicio || 0) + deslocamento,
            Number(canvas.dataset.dragFim || estado.total - 1) + deslocamento
          );
        });

        const soltar = (evento) => {
          if (canvas.classList.contains("dragging")) {
            canvas.classList.remove("dragging");
            if (canvas.hasPointerCapture(evento.pointerId)) {
              canvas.releasePointerCapture(evento.pointerId);
            }
          }
        };
        canvas.addEventListener("pointerup", soltar);
        canvas.addEventListener("pointercancel", soltar);
      });
    }

    function redesenharGraficosExistentes() {
      ["tx1", "tx2", "rx1", "rx2"].forEach((id) => {
        const canvas = $(id);
        if (canvas && canvas.dataset.serie) {
          plotar(
            canvas,
            JSON.parse(canvas.dataset.serie),
            canvas.dataset.titulo,
            Number(canvas.dataset.totalAmostras || 0)
          );
        }
      });
    }

    function bytesUtf8(texto) {
      return new TextEncoder().encode(String(texto)).length;
    }

    function renderizarQuadroBits(quadro) {
      if (!quadro) {
        return `<span class="phase-note">sem bits</span>`;
      }
      if (quadro.tipo === "nota") {
        return `<span class="phase-note">${escapeHtml(quadro.texto || "")}</span>`;
      }

      const grupos = (quadro.grupos || []).map((grupo) => {
        const bits = String(grupo.bits || "");
        const mask = String(grupo.added || grupo.mask || "");
        const payloadMask = String(grupo.payload || "");
        const byteInteiroAdicionado = bits.length > 0
          && mask.length === bits.length
          && mask.split("").every((valor) => valor === "1");
        const byteInteiroPayload = bits.length > 0
          && !byteInteiroAdicionado
          && payloadMask.length === bits.length
          && payloadMask.split("").every((valor) => valor === "1");
        const classesByte = [
          "bit-byte",
          byteInteiroAdicionado ? "added-byte" : "",
          byteInteiroPayload ? "payload-byte" : "",
        ].filter(Boolean).join(" ");
        const conteudo = bits.split("").map((bit, indice) => {
          const adicionado = mask[indice] === "1";
          const payload = payloadMask[indice] === "1";
          const classeBit = [
            "bit-bit",
            adicionado ? "added" : "",
            !adicionado && payload ? "payload" : "",
          ].filter(Boolean).join(" ");
          const titulo = adicionado
            ? ` title="bit adicionado"`
            : (payload ? ` title="bit da carga original"` : "");
          return `<span class="${classeBit}"${titulo}>${escapeHtml(bit)}</span>`;
        }).join("");
        return `<span class="${classesByte}">${conteudo}</span>`;
      }).join("");
      const omitidos = Number(quadro.omitidos_bits || 0);
      const resumoOmitidos = omitidos > 0
        ? `<span class="bit-omitted">+${escapeHtml(omitidos)} bits</span>`
        : "";
      const medida = quadro.medida
        ? `<span>${escapeHtml(quadro.medida)}</span>`
        : "";
      return `
        <div class="bit-frame">
          <div class="bit-frame-meta">
            <span>${escapeHtml(quadro.rotulo || "bits")}</span>
            ${medida}
          </div>
          <div class="bit-byte-list">${grupos}${resumoOmitidos}</div>
        </div>
      `;
    }

    function renderizarLinhaTabela(fase, entrada, saida, quadro, delta, diagnostico) {
      const deltaClass = delta === "0 bits" ? "delta zero" : "delta";
      return `
        <tr>
          <td>${escapeHtml(fase)}</td>
          <td><span class="table-text">${escapeHtml(entrada)}</span></td>
          <td><span class="table-text">${escapeHtml(saida)}</span></td>
          <td class="bits-cell">${renderizarQuadroBits(quadro)}</td>
          <td class="${deltaClass}">${escapeHtml(delta)}</td>
          <td>${escapeHtml(diagnostico)}</td>
        </tr>
      `;
    }

    function renderizarLinhaQuadrosTabela(quadros, quadroBits) {
      const lista = quadros || [];
      const saida = `${lista.length} ${lista.length === 1 ? "quadro validado" : "quadros validados"}`;
      const diagnostico = lista.map((quadro) => {
        const chipClass = quadro.edc_ok ? "status-chip" : "status-chip error";
        const correcao = quadro.corrigidos === 1 ? "1 bit corrigido" : `${quadro.corrigidos} bits corrigidos`;
        const duplo = quadro.erro_duplo ? " erro duplo" : "";
        return `
          <span class="${chipClass}">#${escapeHtml(quadro.quadro)} ${quadro.edc_ok ? "EDC OK" : "EDC erro"}</span>
          <span class="phase-note">${escapeHtml(correcao + duplo)}</span>
        `;
      }).join(" ");
      return `
        <tr>
          <td>Quadros RX: validação</td>
          <td>bits desenquadrados</td>
          <td><span class="table-text">${escapeHtml(saida)}</span></td>
          <td class="bits-cell">${renderizarQuadroBits(quadroBits)}</td>
          <td class="delta zero">0 bits</td>
          <td>${diagnostico || "Nenhum quadro recuperado."}</td>
        </tr>
      `;
    }

    function renderizarFase(fase) {
      const deltaClass = fase.delta === "0 bits" ? "delta zero" : "delta";
      return `
        <tr>
          <td>${escapeHtml(fase.nome)}</td>
          <td>${escapeHtml(fase.entrada)}</td>
          <td>${escapeHtml(fase.saida)}</td>
          <td class="bits-cell">${renderizarQuadroBits(fase.quadro)}</td>
          <td class="${deltaClass}">${escapeHtml(fase.delta)}</td>
          <td>${escapeHtml(fase.detalhe)}</td>
        </tr>
      `;
    }

    function faixaCompleta(total) {
      return Math.max(1, Number(total || 1) - 1);
    }

    function estadoGrafico(canvas, serie, totalAmostras) {
      const total = Math.max(serie.length, Number(totalAmostras || serie.length), 1);
      const existente = estadosGraficos[canvas.id];
      if (!existente || existente.total !== total || existente.pontos !== serie.length) {
        estadosGraficos[canvas.id] = {
          total,
          pontos: serie.length,
          inicio: 0,
          fim: faixaCompleta(total),
        };
      }
      return estadosGraficos[canvas.id];
    }

    function limitarJanela(inicio, fim, total) {
      const maximo = faixaCompleta(total);
      let novoInicio = Number.isFinite(inicio) ? inicio : 0;
      let novoFim = Number.isFinite(fim) ? fim : maximo;
      const larguraMinima = Math.max(4, maximo / 120);
      if (novoFim - novoInicio < larguraMinima) {
        const centro = (novoInicio + novoFim) / 2;
        novoInicio = centro - larguraMinima / 2;
        novoFim = centro + larguraMinima / 2;
      }
      if (novoInicio < 0) {
        novoFim -= novoInicio;
        novoInicio = 0;
      }
      if (novoFim > maximo) {
        novoInicio -= novoFim - maximo;
        novoFim = maximo;
      }
      return {
        inicio: Math.max(0, novoInicio),
        fim: Math.min(maximo, novoFim),
      };
    }

    function moverJanelaGrafico(id, inicio, fim) {
      const estado = estadosGraficos[id];
      const canvas = $(id);
      if (!estado || !canvas) return;
      const janela = limitarJanela(inicio, fim, estado.total);
      estado.inicio = janela.inicio;
      estado.fim = janela.fim;
      redesenharGrafico(id);
    }

    function aplicarZoomGrafico(id, fator, ancora) {
      const estado = estadosGraficos[id];
      if (!estado) return;
      const faixaAtual = estado.fim - estado.inicio;
      const centro = estado.inicio + faixaAtual * ancora;
      const novaFaixa = faixaAtual * fator;
      moverJanelaGrafico(
        id,
        centro - novaFaixa * ancora,
        centro + novaFaixa * (1 - ancora)
      );
    }

    function resetarZoomGrafico(id) {
      const estado = estadosGraficos[id];
      if (!estado) return;
      estado.inicio = 0;
      estado.fim = faixaCompleta(estado.total);
      redesenharGrafico(id);
    }

    function redesenharGrafico(id) {
      const canvas = $(id);
      if (!canvas || !canvas.dataset.serie) return;
      plotar(
        canvas,
        JSON.parse(canvas.dataset.serie),
        canvas.dataset.titulo,
        Number(canvas.dataset.totalAmostras || 0)
      );
    }

    function formatarEscala(valor) {
      const numero = Number(valor);
      if (!Number.isFinite(numero)) return "0";
      if (Math.abs(numero) >= 1000) return String(Math.round(numero));
      if (Math.abs(numero) >= 10) return numero.toFixed(1);
      return numero.toFixed(2);
    }

    function coordenadaAmostra(indice, pontos, total) {
      if (pontos <= 1) return 0;
      return indice * faixaCompleta(total) / (pontos - 1);
    }

    function atualizarNivelZoom(id, estado) {
      const etiqueta = $(`${id}_zoom`);
      if (!etiqueta) return;
      const zoom = faixaCompleta(estado.total) / Math.max(1, estado.fim - estado.inicio);
      etiqueta.textContent = `x${zoom.toFixed(1)}`;
    }

    function plotar(canvas, serie, titulo, totalAmostras) {
      canvas.dataset.serie = JSON.stringify(serie || []);
      canvas.dataset.titulo = titulo;
      canvas.dataset.totalAmostras = String(totalAmostras || (serie || []).length);
      serie = serie || [];
      const estado = estadoGrafico(canvas, serie, totalAmostras);
      atualizarNivelZoom(canvas.id, estado);
      const ctx = canvas.getContext("2d");
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth || 640;
      const height = canvas.clientHeight || 260;
      canvas.width = Math.max(1, Math.floor(width * ratio));
      canvas.height = Math.max(1, Math.floor(height * ratio));
      ctx.scale(ratio, ratio);
      ctx.clearRect(0, 0, width, height);

      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);
      if (!serie || serie.length < 2) {
        ctx.fillStyle = "#64748b";
        ctx.font = "700 12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
        ctx.fillText("Sem amostras", 52, 42);
        return;
      }

      const top = 16;
      const bottom = height - 44;
      const left = 52;
      const right = width - 14;
      const total = estado.total;
      const pontosVisiveis = serie
        .map((valor, idx) => ({
          valor,
          xAmostra: coordenadaAmostra(idx, serie.length, total),
        }))
        .filter((ponto) => (
          ponto.xAmostra >= estado.inicio && ponto.xAmostra <= estado.fim
        ));
      const serieVisivel = pontosVisiveis.length >= 2 ? pontosVisiveis : [
        {valor: serie[0], xAmostra: estado.inicio},
        {valor: serie[serie.length - 1], xAmostra: estado.fim},
      ];
      let minY = Math.min(...serieVisivel.map((ponto) => ponto.valor));
      let maxY = Math.max(...serieVisivel.map((ponto) => ponto.valor));
      if (minY === maxY) {
        minY -= 1;
        maxY += 1;
      }
      const margemY = (maxY - minY) * 0.08;
      minY -= margemY;
      maxY += margemY;
      const span = maxY - minY || 1;

      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      ctx.fillStyle = "#64748b";
      ctx.font = "11px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      for (let i = 0; i < 5; i++) {
        const y = top + ((bottom - top) * i / 4);
        const valor = maxY - (span * i / 4);
        ctx.beginPath();
        ctx.moveTo(left, y);
        ctx.lineTo(right, y);
        ctx.stroke();
        ctx.fillText(formatarEscala(valor), 8, y + 4);
      }

      ctx.strokeStyle = "#cbd5e1";
      ctx.beginPath();
      ctx.moveTo(left, top);
      ctx.lineTo(left, bottom);
      ctx.lineTo(right, bottom);
      ctx.stroke();

      const faixaX = Math.max(1, estado.fim - estado.inicio);
      for (let i = 0; i < 5; i++) {
        const x = left + ((right - left) * i / 4);
        const valor = estado.inicio + faixaX * i / 4;
        ctx.strokeStyle = "#e2e8f0";
        ctx.beginPath();
        ctx.moveTo(x, top);
        ctx.lineTo(x, bottom);
        ctx.stroke();
        ctx.fillStyle = "#64748b";
        ctx.textAlign = i === 0 ? "left" : (i === 4 ? "right" : "center");
        ctx.fillText(formatarEscala(valor), x, bottom + 18);
      }
      ctx.textAlign = "left";
      ctx.fillText("amostras", right - 48, height - 10);
      ctx.save();
      ctx.translate(14, top + 32);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText("Volts", 0, 0);
      ctx.restore();

      ctx.strokeStyle = "#0d9488";
      ctx.lineWidth = 2;
      ctx.beginPath();
      serieVisivel.forEach((ponto, idx) => {
        const x = left + ((ponto.xAmostra - estado.inicio) / faixaX) * (right - left);
        const y = bottom - ((ponto.valor - minY) / span) * (bottom - top);
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();

      ctx.fillStyle = "#475569";
      ctx.font = "700 11px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      ctx.fillText(
        `${serieVisivel.length} pontos visíveis, ${serie.length} amostrados de ${total} amostras`,
        left,
        height - 10
      );
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


def plural_bytes(n):
    return f"{n} byte" if n == 1 else f"{n} bytes"


def medida_bits_bytes(n_bits):
    bytes_cheios, resto = divmod(n_bits, 8)
    if resto == 0:
        return f"{plural_bits(n_bits)} / {plural_bytes(bytes_cheios)}"
    if bytes_cheios == 0:
        return f"{plural_bits(n_bits)} / byte parcial"
    return f"{plural_bits(n_bits)} / {plural_bytes(bytes_cheios)} + {plural_bits(resto)}"


def quadro_bits(bits, adicionados=None, payload=None, rotulo="bits"):
    if adicionados is None:
        adicionados = [False] * len(bits)
    if payload is None:
        payload = [False] * len(bits)

    pares = list(zip(bits, adicionados, payload))
    visiveis = pares[:MAX_BITS_QUADRO]
    grupos = []
    for i in range(0, len(visiveis), 8):
        grupo = visiveis[i:i + 8]
        grupos.append({
            "bits": "".join(str(bit) for bit, _, _ in grupo),
            "added": "".join("1" if adicionado else "0"
                             for _, adicionado, _ in grupo),
            "payload": "".join("1" if bit_payload else "0"
                               for _, _, bit_payload in grupo),
            "mask": "".join("1" if adicionado else "0"
                            for _, adicionado, _ in grupo),
        })

    return {
        "tipo": "bits",
        "rotulo": rotulo,
        "medida": medida_bits_bytes(len(bits)),
        "total_bits": len(bits),
        "omitidos_bits": max(0, len(bits) - len(visiveis)),
        "grupos": grupos,
    }


def quadro_nota(texto):
    return {"tipo": "nota", "texto": texto}


def juntar_payloads(payloads):
    bits = []
    for payload in payloads:
        bits += payload
    return bits


def mascara_hamming(bits_codificados):
    padrao = [True, True, False, True, False, False, False, True]
    mascara = []
    for i in range(0, len(bits_codificados), 8):
        tamanho = min(8, len(bits_codificados) - i)
        mascara += padrao[:tamanho]
    return mascara


def mascara_payload_hamming(mascara_entrada):
    mascara = []
    for i in range(0, len(mascara_entrada), 4):
        nibble = mascara_entrada[i:i + 4]
        if len(nibble) < 4:
            nibble += [False] * (4 - len(nibble))
        d1, d2, d3, d4 = nibble
        mascara += [False, False, d1, False, d2, d3, d4, False]
    return mascara


def marcar_enquadramento(payloads, tipo, mascaras_payload=None):
    bits, adicionados, payload = [], [], []
    if mascaras_payload is None:
        mascaras_payload = [[False] * len(item) for item in payloads]

    if tipo == "contagem":
        for payload_bits, payload_mask in zip(payloads, mascaras_payload):
            n_bytes = len(payload_bits) // 8
            cabecalho = camada_enlace.bytes_para_bits([n_bytes])
            bits += cabecalho + payload_bits
            adicionados += [True] * len(cabecalho) + [False] * len(payload_bits)
            payload += [False] * len(cabecalho) + payload_mask
        return bits, adicionados, payload

    if tipo == "bytes":
        for payload_bits, payload_mask in zip(payloads, mascaras_payload):
            flag = camada_enlace.bytes_para_bits([camada_enlace.FLAG_BYTE])
            bits += flag
            adicionados += [True] * len(flag)
            payload += [False] * len(flag)
            for i, byte in enumerate(camada_enlace.bits_para_bytes(payload_bits)):
                if byte in (camada_enlace.FLAG_BYTE, camada_enlace.ESC_BYTE):
                    esc = camada_enlace.bytes_para_bits([camada_enlace.ESC_BYTE])
                    bits += esc
                    adicionados += [True] * len(esc)
                    payload += [False] * len(esc)
                byte_bits = camada_enlace.bytes_para_bits([byte])
                bits += byte_bits
                adicionados += [False] * len(byte_bits)
                payload += payload_mask[i * 8:i * 8 + 8]
            bits += flag
            adicionados += [True] * len(flag)
            payload += [False] * len(flag)
        return bits, adicionados, payload

    for payload_bits, payload_mask in zip(payloads, mascaras_payload):
        bits += camada_enlace.FLAG_BITS
        adicionados += [True] * len(camada_enlace.FLAG_BITS)
        payload += [False] * len(camada_enlace.FLAG_BITS)
        uns = 0
        for bit, bit_payload in zip(payload_bits, payload_mask):
            bits.append(bit)
            adicionados.append(False)
            payload.append(bit_payload)
            if bit == 1:
                uns += 1
            else:
                uns = 0
            if uns == 5:
                bits.append(0)
                adicionados.append(True)
                payload.append(False)
                uns = 0
        bits += camada_enlace.FLAG_BITS
        adicionados += [True] * len(camada_enlace.FLAG_BITS)
        payload += [False] * len(camada_enlace.FLAG_BITS)
    return bits, adicionados, payload


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

    bits_blocos_visual = juntar_payloads(blocos)
    payload_blocos = [True] * len(bits_blocos_visual)
    mascara_blocos = [False] * len(bits_blocos_visual)

    bits_edc_visual, mascara_edc, payload_edc_visual = [], [], []
    mascaras_payload_edc = []
    for bloco, payload in zip(blocos, payloads_edc):
        bits_edc_visual += payload
        mascara_edc += [False] * len(bloco)
        mascara_edc += [True] * (len(payload) - len(bloco))
        payload_mask = [True] * len(bloco)
        payload_mask += [False] * (len(payload) - len(bloco))
        payload_edc_visual += payload_mask
        mascaras_payload_edc.append(payload_mask)

    bits_correcao_visual, mascara_correcao, payload_correcao_visual = [], [], []
    mascaras_payload_correcao = []
    for payload, payload_mask_entrada in zip(payloads_correcao,
                                             mascaras_payload_edc):
        bits_correcao_visual += payload
        if config["correcao"] == "hamming":
            mascara_correcao += mascara_hamming(payload)
            payload_mask_saida = mascara_payload_hamming(payload_mask_entrada)
        else:
            mascara_correcao += [False] * len(payload)
            payload_mask_saida = payload_mask_entrada[:]
        payload_correcao_visual += payload_mask_saida
        mascaras_payload_correcao.append(payload_mask_saida)

    (
        bits_enquadramento_visual,
        mascara_enquadramento,
        payload_enquadramento_visual,
    ) = marcar_enquadramento(
        payloads_correcao, config["enquadramento"],
        mascaras_payload_correcao)

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

    bits_portadora_visual = fluxo_enquadrado + [0] * padding_portadora
    mascara_portadora = [False] * len(fluxo_enquadrado)
    mascara_portadora += [True] * padding_portadora
    payload_portadora = payload_enquadramento_visual + [False] * padding_portadora

    fases = [
        {
            "nome": "Aplicação: texto -> bits",
            "entrada": f"{len(config['texto'].encode('utf-8'))} byte(s) UTF-8",
            "saida": plural_bits(len(bits_app)),
            "quadro": quadro_bits(bits_app, payload=[True] * len(bits_app),
                                  rotulo="UTF-8"),
            "delta": "0 bits",
            "detalhe": "Conversão de texto para bytes UTF-8 e bits; não é redundância.",
        },
        {
            "nome": "Divisão em quadros",
            "entrada": plural_bits(len(bits_app)),
            "saida": f"{plural_quadros(len(blocos))}, {plural_bits(bits_blocos)}",
            "quadro": quadro_bits(bits_blocos_visual, mascara_blocos,
                                  payload_blocos, rotulo="quadros"),
            "delta": "0 bits",
            "detalhe": f"Cada quadro carrega até {config['tam_max_quadro']} byte(s) de dados.",
        },
        {
            "nome": f"Detecção de erros: {ROTULOS_DETECCAO[config['deteccao']]}",
            "entrada": plural_bits(bits_blocos),
            "saida": plural_bits(bits_apos_edc),
            "quadro": quadro_bits(bits_edc_visual, mascara_edc,
                                  payload_edc_visual,
                                  rotulo="payload + EDC"),
            "delta": plural_bits(bits_edc),
            "detalhe": detalhe_deteccao(config["deteccao"], len(blocos)),
        },
        {
            "nome": f"Correção de erros: {ROTULOS_CORRECAO[config['correcao']]}",
            "entrada": plural_bits(bits_apos_edc),
            "saida": plural_bits(bits_apos_correcao),
            "quadro": quadro_bits(bits_correcao_visual, mascara_correcao,
                                  payload_correcao_visual,
                                  rotulo="payload codificado"),
            "delta": plural_bits(bits_correcao),
            "detalhe": detalhe_correcao(config["correcao"]),
        },
        {
            "nome": f"Enquadramento: {ROTULOS_ENQUADRAMENTO[config['enquadramento']]}",
            "entrada": plural_bits(bits_apos_correcao),
            "saida": plural_bits(bits_enlace),
            "quadro": quadro_bits(bits_enquadramento_visual,
                                  mascara_enquadramento,
                                  payload_enquadramento_visual,
                                  rotulo="quadro Tx"),
            "delta": plural_bits(bits_enquadramento),
            "detalhe": detalhe_enquadramento(config["enquadramento"], len(blocos)),
        },
        {
            "nome": f"Modulação digital: {ROTULOS_DIGITAL[config['mod_digital']]}",
            "entrada": plural_bits(bits_enlace),
            "saida": plural_amostras(amostras_digitais),
            "quadro": quadro_bits(fluxo_enquadrado,
                                  payload=payload_enquadramento_visual,
                                  rotulo="bits modulados"),
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
            "quadro": quadro_bits(bits_portadora_visual, mascara_portadora,
                                  payload_portadora,
                                  rotulo="bits por símbolo"),
            "delta": plural_bits(padding_portadora),
            "detalhe": detalhe_portadora,
        },
        {
            "nome": "Meio ruidoso",
            "entrada": plural_amostras(amostras_tx),
            "saida": plural_amostras(len(resultado["rx_sinal_recebido"])),
            "quadro": quadro_nota(
                f"{plural_amostras(amostras_tx)} no meio; bits preservados no sinal."),
            "delta": "0 bits",
            "detalhe": (
                f"Soma ruído gaussiano com média {config['ruido_media']:.2f} V "
                f"e sigma {config['ruido_sigma']:.2f} V em cada amostra."
            ),
        },
    ]

    payload_rx_fisica = payload_enquadramento_visual[:]
    if len(resultado["rx_bits_fisica"]) > len(payload_rx_fisica):
        payload_rx_fisica += [False] * (
            len(resultado["rx_bits_fisica"]) - len(payload_rx_fisica))
    payload_rx_fisica = payload_rx_fisica[:len(resultado["rx_bits_fisica"])]
    payload_rx_aplicacao = [True] * len(resultado["rx_bits_aplicacao"])

    return {
        "bits_aplicacao": len(bits_app),
        "bits_enlace": bits_enlace,
        "bits_adicionados": bits_enlace - len(bits_app),
        "bits_edc": bits_edc,
        "bits_correcao": bits_correcao,
        "bits_enquadramento": bits_enquadramento,
        "padding_portadora": padding_portadora,
        "quadros_bits": {
            "texto_entrada": quadro_bits(bits_app, payload=[True] * len(bits_app),
                                         rotulo="UTF-8"),
            "fisica_rx": quadro_bits(resultado["rx_bits_fisica"],
                                     payload=payload_rx_fisica,
                                     rotulo="bits demodulados"),
            "quadros_rx": quadro_bits(resultado["rx_bits_aplicacao"],
                                      payload=payload_rx_aplicacao,
                                      rotulo="payload validado"),
            "aplicacao_rx": quadro_bits(resultado["rx_bits_aplicacao"],
                                        payload=payload_rx_aplicacao,
                                        rotulo="bits RX"),
        },
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
    quadros = [
        {
            "quadro": q["quadro"],
            "edc_ok": q["edc_ok"],
            "corrigidos": q["corrigidos"],
            "erro_duplo": q["erro_duplo"],
        }
        for q in resultado["rx_relatorio_quadros"]
    ]

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
        "texto_entrada": config["texto"],
        "texto_saida": resultado["rx_texto"],
        "bits_tx_aplicacao": bits_str(resultado["tx_bits_aplicacao"]),
        "bits_tx_enlace": bits_str(resultado["tx_bits_enlace"]),
        "bits_rx_fisica": bits_str(resultado["rx_bits_fisica"]),
        "relatorio_quadros": linhas_quadros,
        "quadros": quadros,
        "bits_rx_aplicacao": bits_str(resultado["rx_bits_aplicacao"]),
        "texto_tx": texto_tx,
        "texto_rx": texto_rx,
        "diagnostico": diagnostico,
        "sinais": {
            "tx_banda_base": amostrar(resultado["tx_sinal_banda_base"]),
            "tx_transmitido": amostrar(resultado["tx_sinal_transmitido"]),
            "rx_recebido": amostrar(resultado["rx_sinal_recebido"]),
            "rx_banda_base": amostrar(resultado["rx_sinal_banda_base"]),
        },
        "sinais_meta": {
            "tx_banda_base": len(resultado["tx_sinal_banda_base"]),
            "tx_transmitido": len(resultado["tx_sinal_transmitido"]),
            "rx_recebido": len(resultado["rx_sinal_recebido"]),
            "rx_banda_base": len(resultado["rx_sinal_banda_base"]),
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

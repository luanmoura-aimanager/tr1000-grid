// app.mjs - o topo, as abas e o laco de estado (~4x/s, como o TR-8S Controller).
import { $, h, texto, attr } from "./dom.mjs";
import * as rede from "./rede.mjs";
import pattern from "./abas/pattern.mjs";
import mixer from "./abas/mixer.mjs";
import efeitos from "./abas/efeitos.mjs";
import performance from "./abas/performance.mjs";

const ABAS = [pattern, mixer, efeitos, performance];
const ESTADO_A_CADA = 250; // ms

let D = null;
let E = {};
let atual = 0;
try {
  atual = Math.min(ABAS.length - 1, +(localStorage.getItem("tr1000-aba") || 0));
} catch (e) {
  /* sem storage */
}

function msg(t) {
  texto($("#msg"), t);
}

// a acao com o erro virando mensagem no rodape, em vez de sumir
async function acao(nome, args) {
  try {
    await rede.acao(nome, args);
  } catch (e) {
    msg(`(!) ${e.message}`);
  }
}

const ctx = {
  acao,
  get D() {
    return D;
  },
  get E() {
    return E;
  },
  espacado: rede.espacado,
};

function mostrarAba(i) {
  const antes = ABAS[atual];
  atual = i;
  try {
    localStorage.setItem("tr1000-aba", String(i));
  } catch (e) {
    /* sem storage */
  }
  ABAS.forEach((a, k) => {
    attr(a._botao, "aria-selected", k === i ? "true" : "false");
    a._painel.hidden = k !== i;
  });
  if (antes !== ABAS[i]) pedirKit();
  if (E && Object.keys(E).length) ABAS[i].atualizar(E, ctx);
}

// UM pedido so, com o que a aba nova quer (revisao do PR #7: dois POSTs sem
// esperar - false da aba velha, true da nova - chegavam em qualquer ordem)
let kitPedido = null;
function pedirKit(forcar = false) {
  const sim = !!ABAS[atual].querKit;
  if (!E.ligado || (!forcar && sim === kitPedido)) return;
  kitPedido = sim;
  acao("quer_kit", { sim });
}

function montar() {
  const nav = $("#abas"),
    main = $("#paineis");
  ABAS.forEach((a, i) => {
    a._botao = h(
      "button.aba",
      { type: "button", role: "tab", onclick: () => mostrarAba(i) },
      a.nome,
    );
    a._painel = h("section.painel", { role: "tabpanel", "aria-label": a.nome });
    nav.append(a._botao);
    main.append(a._painel);
    a.montar(a._painel, ctx);
  });
  $("#b-ligar").addEventListener("click", async () => {
    const ligar = !E.ligado;
    msg(
      ligar
        ? "ligando: serial, Launchpads e controladoras..."
        : "desligando: soltando a serial...",
    );
    try {
      await rede.ligar(ligar);
    } catch (e) {
      msg(`(!) ${e.message}`);
    }
  });
  texto($("#build"), `build ${D.build}`);
  mostrarAba(atual);
}

function pintarTopo() {
  const ligado = !!E.ligado;
  attr($("#b-ligar"), "aria-pressed", ligado ? "true" : "false");
  texto($("#b-ligar"), ligado ? "ON" : "OFF");
  $("#aviso-off").hidden = ligado;
  texto($("#d-ptn"), E.pattern || "—");
  texto($("#d-bpm"), E.tempo ? E.tempo.toFixed(1) : "—");
  texto(
    $("#d-var"),
    E.variacao !== undefined && ligado ? D.variacoes[E.variacao] : "—",
  );
  texto($("#d-step"), E.tocando && E.passo >= 0 ? String(E.passo + 1) : "—");
  const leds = [
    ["TR-1000", ligado],
    ["Launchpads", ligado && E.launchpads],
    ["MC-24", ligado && (E.controladoras || []).includes("MC-24")],
    ["CM-MC50", ligado && (E.controladoras || []).includes("CM-MC50")],
  ];
  const el = $("#leds");
  if (!el.children.length)
    leds.forEach(([n]) => el.append(h("span.led", {}, h("i"), n)));
  leds.forEach(([, on], i) => attr(el.children[i], "data-on", !!on));
  const log = E.log || [];
  if (log.length) msg(log[log.length - 1]);
}

let ligadoAntes = false;

async function laco() {
  try {
    E = await rede.estado();
    // a maquina acabou de ligar: a aba aberta pede de novo o que precisa
    // (Mixer/Efeitos pedem a leitura do kit - pedido feito com ela desligada se perde)
    if (E.ligado && !ligadoAntes) pedirKit(true);
    ligadoAntes = !!E.ligado;
    pintarTopo();
    ABAS[atual].atualizar(E, ctx);
  } catch (e) {
    msg("sem contato com o servidor - ele esta no ar? (python3 servidor.py)");
  }
  setTimeout(laco, ESTADO_A_CADA);
}

(async () => {
  try {
    D = await rede.dados();
  } catch (e) {
    msg("sem contato com o servidor");
    setTimeout(() => location.reload(), 2000);
    return;
  }
  montar();
  laco();
})();

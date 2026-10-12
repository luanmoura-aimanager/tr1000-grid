// app.mjs - o topo, as abas e o laco de estado (~4x/s, como o TR-8S Controller).
// O playhead vem a parte, pelo /passo (um evento por step): o laco de 250 ms
// pulava steps a 128 BPM (F3, 12/10/2026).
import { $, h, texto, attr } from "./dom.mjs";
import * as rede from "./rede.mjs";
import { t, tLog, linguaAtual, trocarLingua } from "./i18n.mjs";
import { xDoPattern } from "./ptn.mjs";
import pattern from "./abas/pattern.mjs";
import mixer from "./abas/mixer.mjs";
import efeitos from "./abas/efeitos.mjs";

const ABAS = [pattern, mixer, efeitos];
const ESTADO_A_CADA = 250; // ms
const N_AH = 8; // A..H

let D = null;
let E = {};
let atual = 0;
try {
  atual = Math.min(ABAS.length - 1, +(localStorage.getItem("tr1000-aba") || 0));
} catch (e) {
  /* sem storage */
}

function msg(s) {
  texto($("#msg"), s);
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

function montarPtn() {
  const bt = $("#b-ptn"),
    campo = $("#c-ptn");
  attr(bt, "title", t("trocar o pattern"));
  attr(campo, "aria-label", t("trocar o pattern"));
  attr(
    campo,
    "title",
    t("Digite o pattern (1-05, ou 1..128) e Enter. Esc cancela."),
  );
  const fechar = () => {
    campo.hidden = true;
    bt.hidden = false;
  };
  bt.addEventListener("click", () => {
    if (!E.ligado) return;
    campo.value = E.pattern || "";
    bt.hidden = true;
    campo.hidden = false;
    campo.focus();
    campo.select();
  });
  campo.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") fechar();
    if (ev.key !== "Enter") return;
    const x = xDoPattern(campo.value);
    if (x === null) {
      msg(t("pattern inválido: use banco-número (1-05) ou 1..128"));
      return;
    }
    msg(
      t("pedindo o pattern {p} (Program Change)...", { p: campo.value.trim() }),
    );
    acao("ptn", { x });
    fechar();
  });
  campo.addEventListener("blur", fechar);
  attr(
    $("#s-bpm"),
    "title",
    t(
      "Digitar o BPM depende da sessão c5d (o endereço do TEMPO ainda não foi aprendido).",
    ),
  );
  attr(
    $("#s-toca"),
    "title",
    t("a chain (a variação que toca ainda não é detectada)"),
  );
}

function montar() {
  document.documentElement.lang = linguaAtual() === "en" ? "en" : "pt-BR";
  document
    .querySelectorAll("[data-t]")
    .forEach((el) => texto(el, t(el.dataset.t)));
  attr($("#abas"), "aria-label", t("seções"));
  document.querySelectorAll("[data-lingua]").forEach((b) => {
    attr(
      b,
      "aria-pressed",
      b.dataset.lingua === linguaAtual() ? "true" : "false",
    );
    b.addEventListener("click", () => {
      if (b.dataset.lingua !== linguaAtual()) trocarLingua(b.dataset.lingua);
    });
  });
  const nav = $("#abas"),
    main = $("#paineis");
  ABAS.forEach((a, i) => {
    a._botao = h(
      "button.aba",
      { type: "button", role: "tab", onclick: () => mostrarAba(i) },
      t(a.nome),
    );
    a._painel = h("section.painel", {
      role: "tabpanel",
      "aria-label": t(a.nome),
    });
    nav.append(a._botao);
    main.append(a._painel);
    a.montar(a._painel, ctx);
  });
  attr($("#modos"), "aria-label", t("modo"));
  document.querySelectorAll("[data-modo]").forEach((b) =>
    b.addEventListener("click", async () => {
      const m = b.dataset.modo;
      msg(
        {
          on: t("ligando: serial, Launchpads e controladoras..."),
          off: t("desligando: soltando a serial..."),
        }[m] || t("standby: soltando a serial; os Launchpads fazem ondas..."),
      );
      try {
        await rede.modo(m);
      } catch (e) {
        msg(`(!) ${e.message}`);
      }
    }),
  );
  montarPtn();
  texto($("#build"), `build ${D.build}`);
  mostrarAba(atual);
}

// a chain do cabecalho ("A+B"); a variacao que TOCA e o item 4 do plano
function textoToca() {
  const m = E.variacoes || 0;
  const v = D.variacoes.slice(0, N_AH).filter((_, i) => (m >> i) & 1);
  return v.length ? v.join("+") : "—";
}

function pintarTopo() {
  const ligado = !!E.ligado;
  const modo = E.modo || "off";
  document
    .querySelectorAll("[data-modo]")
    .forEach((b) => attr(b, "aria-pressed", b.dataset.modo === modo ? "true" : "false"));
  $("#aviso-off").hidden = ligado;
  texto(
    $("#aviso-off"),
    modo === "off"
      ? t(
          "Desligado: a serial está livre para o TR-1000 App da Roland. Aperte ON para o Controller assumir a máquina, os Launchpads e as controladoras.",
        )
      : t(
          "Standby ({m}): a serial está livre para o TR-1000 App da Roland, e os Launchpads fazem ondas. Toque um pad para soltar mais uma. ON volta ao grid.",
          { m: t(modo) },
        ),
  );
  texto($("#d-ptn"), E.pattern || "—");
  texto($("#d-bpm"), E.tempo ? E.tempo.toFixed(1) : "—");
  texto(
    $("#d-var"),
    E.variacao !== undefined && ligado ? D.variacoes[E.variacao] : "—",
  );
  texto($("#d-toca"), ligado ? textoToca() : "—");
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
  if (log.length) msg(tLog(log[log.length - 1]));
}

// o playhead: um evento por step. O EventSource reconecta sozinho se o
// servidor reiniciar (o /passo nao pede cookie, como o /estado).
function ouvirPasso() {
  let fonte;
  try {
    fonte = new EventSource("/passo");
  } catch (e) {
    return;
  }
  fonte.onmessage = (ev) => {
    let info;
    try {
      info = JSON.parse(ev.data);
    } catch (e) {
      return;
    }
    texto(
      $("#d-step"),
      info.tocando && info.passo >= 0 ? String(info.passo + 1) : "—",
    );
    for (const a of ABAS) if (a.passo) a.passo(info);
  };
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
    msg(
      t("sem contato com o servidor - ele esta no ar? (python3 servidor.py)"),
    );
  }
  setTimeout(laco, ESTADO_A_CADA);
}

(async () => {
  try {
    D = await rede.dados();
  } catch (e) {
    msg(t("sem contato com o servidor"));
    setTimeout(() => location.reload(), 2000);
    return;
  }
  montar();
  laco();
  ouvirPasso();
})();

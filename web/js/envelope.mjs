// envelope.mjs - o grafico do SIDE CHAIN, clicavel (pedido do Luan, 11/10/2026,
// com a tela do App como modelo). E a NOSSA leitura do grafico do App:
//   - ponto de baixo: x = HOLD (HLD STEP ou HLD TIME, conforme o HLD MODE),
//     y = MSTR DEP (o quanto o master abaixa)
//   - ponto de cima: x = HOLD + RELEASE (a volta)
//   - ponto do meio: a CURVE (o formato da volta)
//   - GATE (POLARITY 1) vira o desenho de cabeca para baixo
// Arrastar manda o mesmo `param` dos sliders (espacado); os sliders do lado
// seguem na proxima leitura do kit. As unidades do RELEASE e da CURVE nao
// foram medidas: o desenho e proporcional a faixa crua, nao a milissegundos.
import { entradaDe } from "./params.mjs";

const NS = "http://www.w3.org/2000/svg";
const L = 360,
  A = 150; // viewBox
const X0 = 24,
  TOPO = 18,
  BASE = A - 18; // o "volume cheio" e o "silencio"
const LARG_HOLD = 110,
  LARG_REL = 200;

function el(tag, attrs = {}) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

const limitar = (v, a, b) => Math.max(a, Math.min(b, v));

export function envelope(ctx) {
  const svg = el("svg", {
    viewBox: `0 0 ${L} ${A}`,
    class: "envelope",
    role: "img",
    "aria-label": "side chain",
  });
  const fundo = el("rect", {
    x: 0,
    y: 0,
    width: L,
    height: A,
    class: "env-fundo",
  });
  const grade = el("path", { class: "env-grade" });
  const area = el("path", { class: "env-area" });
  const linha = el("path", { class: "env-linha" });
  const pBase = el("circle", { r: 7, class: "env-ponto", tabindex: 0 });
  const pTopo = el("circle", { r: 7, class: "env-ponto", tabindex: 0 });
  const pMeio = el("circle", {
    r: 6,
    class: "env-ponto env-meio",
    tabindex: 0,
  });
  const rotHold = el("text", { class: "env-rot", y: A - 4 });
  svg.append(fundo, grade, area, linha, rotHold, pBase, pTopo, pMeio);
  grade.setAttribute(
    "d",
    `M${X0},${TOPO}H${L - 8}M${X0},${BASE}H${L - 8}M${X0},${TOPO}V${BASE}`,
  );

  // o estado local: o que a maquina tem (E.kit), ou o que o dedo esta arrastando
  let v = null;
  let arrastando = null;
  const faixa = (id) => entradaDe(ctx.D, ctx.E, id) || { min: 0, max: 1 };
  const idHold = () => (v["sc.hld_mode"] ? "sc.hld_step" : "sc.hld_time");
  const norm = (id) => {
    const f = faixa(id);
    return f.max > f.min ? (v[id] - f.min) / (f.max - f.min) : 0;
  };
  const deNorm = (id, n) => {
    const f = faixa(id);
    return Math.round(f.min + limitar(n, 0, 1) * (f.max - f.min));
  };
  const manda = {};
  const mandar = (id, valor) => {
    v[id] = valor;
    (manda[id] =
      manda[id] || ctx.espacado((x) => ctx.acao("param", { id, valor: x })))(
      valor,
    );
  };

  function pontos() {
    const gate = v["sc.polarity"] === 1;
    const fundoY = TOPO + norm("sc.mstr_dep") * (BASE - TOPO);
    // GATE de cabeca para baixo: o "abaixado" fica em cima
    const yAbaixo = gate ? BASE - (fundoY - TOPO) : fundoY;
    const yCheio = gate ? BASE : TOPO;
    const xHold = X0 + norm(idHold()) * LARG_HOLD;
    const xRel = xHold + Math.max(4, norm("sc.release") * LARG_REL);
    // a curva: 0 = reta; 1000 = a volta demora e sobe no fim
    const c = norm("sc.curve");
    const meio = [(xHold + xRel) / 2, (yAbaixo + yCheio) / 2];
    const ctrl = [
      meio[0] + c * (xRel - meio[0]),
      meio[1] + c * (yAbaixo - meio[1]),
    ];
    return { gate, yAbaixo, yCheio, xHold, xRel, ctrl };
  }

  function desenhar() {
    if (!v) return;
    const p = pontos();
    const q = (t) => {
      // o ponto da bezier quadratica em t (para o ponto do meio)
      const a = [p.xHold, p.yAbaixo],
        b = p.ctrl,
        c = [p.xRel, p.yCheio];
      return [0, 1].map(
        (i) => (1 - t) * (1 - t) * a[i] + 2 * (1 - t) * t * b[i] + t * t * c[i],
      );
    };
    const d =
      `M${X0},${p.yCheio}V${p.yAbaixo}H${p.xHold}` +
      `Q${p.ctrl[0]},${p.ctrl[1]} ${p.xRel},${p.yCheio}H${L - 8}`;
    linha.setAttribute("d", d);
    area.setAttribute("d", `${d}V${p.gate ? TOPO : BASE}H${X0}Z`);
    pBase.setAttribute("cx", p.xHold);
    pBase.setAttribute("cy", p.yAbaixo);
    pTopo.setAttribute("cx", p.xRel);
    pTopo.setAttribute("cy", p.yCheio);
    const m = q(0.5);
    pMeio.setAttribute("cx", m[0]);
    pMeio.setAttribute("cy", m[1]);
    rotHold.setAttribute("x", p.xHold);
    rotHold.textContent = v["sc.hld_mode"]
      ? `${v["sc.hld_step"]} step`
      : `${v["sc.hld_time"]}`;
  }

  // de pixel de tela para a coordenada do viewBox
  function noSvg(ev) {
    const r = svg.getBoundingClientRect();
    return [
      ((ev.clientX - r.left) / r.width) * L,
      ((ev.clientY - r.top) / r.height) * A,
    ];
  }

  function arrastar(alvo, ev) {
    if (!v) return;
    const [x, y] = noSvg(ev);
    const p = pontos();
    if (alvo === "base") {
      mandar(idHold(), deNorm(idHold(), (x - X0) / LARG_HOLD));
      const prof = p.gate
        ? (BASE - y) / (BASE - TOPO)
        : (y - TOPO) / (BASE - TOPO);
      mandar("sc.mstr_dep", deNorm("sc.mstr_dep", prof));
    } else if (alvo === "topo") {
      mandar("sc.release", deNorm("sc.release", (x - p.xHold) / LARG_REL));
    } else {
      // a CURVE: o quanto o dedo saiu da reta, em direcao ao canto
      const meioY = (p.yAbaixo + p.yCheio) / 2;
      const n = (y - meioY) / (p.yAbaixo - meioY || 1);
      mandar("sc.curve", deNorm("sc.curve", n));
    }
    desenhar();
  }

  for (const [ponto, nome] of [
    [pBase, "base"],
    [pTopo, "topo"],
    [pMeio, "meio"],
  ]) {
    ponto.addEventListener("pointerdown", (ev) => {
      if (ev.button !== 0) return;
      ponto.setPointerCapture(ev.pointerId);
      arrastando = nome;
    });
    ponto.addEventListener("pointermove", (ev) => {
      if (arrastando === nome) arrastar(nome, ev);
    });
    const soltar = () => {
      if (arrastando === nome) arrastando = null;
    };
    ponto.addEventListener("pointerup", soltar);
    ponto.addEventListener("lostpointercapture", soltar);
  }

  const IDS = [
    "sc.mstr_dep",
    "sc.release",
    "sc.curve",
    "sc.polarity",
    "sc.hld_mode",
    "sc.hld_step",
    "sc.hld_time",
  ];
  return {
    el: svg,
    atualizar(E) {
      const kit = E.kit || {};
      const tem = IDS.every((id) => kit[id] !== undefined);
      svg.classList.toggle("env-vazio", !tem);
      if (!tem) {
        v = null;
        return;
      }
      if (arrastando) return; // o dedo manda; o kit volta quando soltar
      v = Object.fromEntries(IDS.map((id) => [id, kit[id]]));
      desenhar();
    },
  };
}

/** O nome do preset que bate com o kit agora, ou null. */
export function presetAtual(presets, kit) {
  for (const [nome, vals] of Object.entries(presets || {}))
    if (Object.entries(vals).every(([id, x]) => kit && kit[id] === x))
      return nome;
  return null;
}

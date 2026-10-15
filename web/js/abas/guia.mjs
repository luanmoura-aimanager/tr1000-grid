// guia.mjs - como usar os dois Launchpads: uma bancada que simula as paginas
// do layout A (Steps, PAR, PERF, ROUT e o standby), a ficha de cada botao, as
// cores, as bordas por pagina, os "menus secretos" e o que foi testado.
//
// A bancada e SO simulacao: este modulo nao importa o rede.mjs e nao chama
// ctx.acao - clicar aqui nunca escreve na maquina (TesteGuia trava isso). A
// logica de cada toque e a do motor.py (alternar_track, tocar_par,
// tocar_perf, alvo_rout); os textos, em pt e en, estao no guia_textos.mjs.
import { h, texto, attr } from "../dom.mjs";
import { linguaAtual } from "../i18n.mjs";
import {
  T,
  PAR_PARAMS,
  NIVEIS_PAR,
  PAR_ESCOLHA,
  PERF,
  ROUT,
  FONTES_ROTA,
  VEL_FRACA,
  TRACKS_LAYER,
  CENA_CCS,
  PLAY,
} from "../guia_textos.mjs";

const CHAVE_PAGINA = "tr1000-guia-pagina";
const PAGINAS = ["steps", "par", "perf", "rout", "standby"];
const PNOME = {
  prob: "PROB",
  sub: "SUB",
  cycle: "CYCLE",
  start: "START",
  vel: "VEL",
  alt: "ALT",
};

// as cores dos LEDs (launchpad.py / motor.py), em hex para a tela
const C = {
  red: "#ff2d1f",
  redW: "#6e1710",
  green: "#2ee053",
  greenW: "#17602a",
  purple: "#a100ff",
  purpleW: "#3a0866",
  white: "#f2f2f2",
  play: "#4c4c4c",
  beat: "#35393d",
  blue: "#2f6dff",
  blueW: "#16306a",
  lblue: "#79c6ff",
  pink: "#ff1f7a",
  soando: "#1fa63a",
  soandoW: "#0e3d17",
  dim: "#3b3f43",
  faint: "#18191a",
  amber: "#ff7a00",
  amberW: "#4d2400",
  par: {
    prob: "#ff6a00",
    sub: "#00a2ff",
    cycle: "#e0cc00",
    start: "#e000a2",
    vel: "#ff1a1a",
    alt: "#a100ff",
  },
  destino: ["#a8a8a8", "#ff6a00", "#00b8e0"],
};

// o pattern de exemplo (1-based): BD e SD sao os do 1-01
const PAT = {
  BD: { A: [1, 5, 9, 13] },
  SD: { A: [4, 12], B: [2, 7, 9, 10, 13, 15, 16] },
  LT: { A: [11] },
  HT: { A: [15] },
  RS: { ALT: [3], A: [14] },
  HC: { A: [5, 13] },
  CH: { A: [1, 3, 5, 7, 9, 11, 13, 15], W: [3, 7, 11, 15] },
  OH: { A: [3, 7, 11, 15] },
  CC: { A: [1] },
  RC: { A: [1, 5, 9, 13], W: [5, 13] },
};

let D = null; // os catalogos do /dados
let S = null; // o estado da simulacao
let sel = { kind: "pad", i: 0, j: 0 };
let painel = null;
const cel = { pad: [], topE: [], ladoE: [], topD: [], ladoD: [], logo: [] };
const el = {};
let ondas = [],
  proxOnda = 0,
  animando = false;
const REDUZ = !!(
  window.matchMedia &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches
);

// ── texto ─────────────────────────────────────────────────
const L = (o) =>
  o && typeof o === "object" ? o[linguaAtual() === "en" ? "en" : "pt"] : o;
const fmt = (o, args = {}) =>
  String(L(o)).replace(/\{(\w+)\}/g, (m, k) => (k in args ? args[k] : m));
// "texto **forte**" -> nos, sem HTML
function rico(s) {
  return String(s)
    .split("**")
    .map((p, i) => (i % 2 ? h("b", {}, p) : p));
}

// ── o estado ──────────────────────────────────────────────
function inicial() {
  const s = {
    page: "steps",
    banco: 1,
    layer: "AB",
    vel: 3,
    varEdit: 0,
    varPlay: 1,
    mute: 1 << 1,
    parTrack: 1,
    parParam: 0,
    fill: 0,
    chain: 0b11,
    first: 0,
    last: 11,
    scale: 2,
    rota: FONTES_ROTA.map((_, i) => (i === 0 ? 1 : 0)),
    sc: 3,
    pol: 0,
    hld: 0,
    loop: null,
    a: [],
    b: [],
    alt: [],
    par: [],
  };
  D.tracks.forEach((t, tr) => {
    const p = PAT[t] || {};
    s.a[tr] = Array(16).fill(0);
    s.b[tr] = Array(16).fill(0);
    s.alt[tr] = Array(16).fill(false);
    s.par[tr] = Array.from({ length: 16 }, () => ({
      prob: 7,
      sub: 0,
      cycle: 0,
      start: 3,
    }));
    (p.A || []).forEach(
      (n) => (s.a[tr][n - 1] = (p.W || []).includes(n) ? 66 : 80),
    );
    (p.B || []).forEach((n) => (s.b[tr][n - 1] = 80));
    (p.ALT || []).forEach((n) => {
      s.a[tr][n - 1] = 80;
      s.alt[tr][n - 1] = true;
    });
  });
  s.par[1][3].prob = 3; // o SD step 4 em 43 %, como no F4.6c
  s.par[1][9].sub = 1;
  s.par[1][6].start = 5;
  s.par[0][12].cycle = 1;
  return s;
}

const trLinha = (l) => D.bancos[S.banco][l];
const slotsAlvo = (tr) =>
  tr >= TRACKS_LAYER ? ["a"] : { AB: ["a", "b"], A: ["a"], B: ["b"] }[S.layer];
const toca = (tr, s) => S.a[tr][s] > 0 || S.b[tr][s] > 0;
function nivelVel(tr, s) {
  const v = S.a[tr][s] || S.b[tr][s];
  if (!v) return -1;
  const n = NIVEIS_PAR.vel;
  return n.reduce(
    (best, x, i) => (Math.abs(x - v) < Math.abs(n[best] - v) ? i : best),
    0,
  );
}
function rotuloNivel(nome, i) {
  const v = NIVEIS_PAR[nome][i];
  if (nome === "prob") return `${v} %`;
  if (nome === "sub") return D.sub_nomes[v];
  if (nome === "cycle") return D.cycle_nomes[v];
  if (nome === "start") return v > 0 ? `+${v}` : v < 0 ? `−${-v}` : "0";
  return String(v);
}
function fraca(hex, f) {
  const n = parseInt(hex.slice(1), 16);
  return `rgb(${Math.round(((n >> 16) & 255) * f)},${Math.round(((n >> 8) & 255) * f)},${Math.round((n & 255) * f)})`;
}
function claro(cor) {
  let r, g, b;
  if (cor[0] === "#") {
    const n = parseInt(cor.slice(1), 16);
    [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  } else [r, g, b] = cor.match(/\d+/g).map(Number);
  return 0.299 * r + 0.587 * g + 0.114 * b > 110;
}

// ── as cores, como o motor.py pinta ───────────────────────
function corStep(l, s) {
  const tr = trLinha(l),
    a = S.a[tr][s],
    b = S.b[tr][s];
  if (s === PLAY) return a || b ? C.white : C.play;
  if (a && S.alt[tr][s]) return a < VEL_FRACA ? C.purpleW : C.purple;
  if (a) return a < VEL_FRACA ? C.redW : C.red;
  if (b) return b < VEL_FRACA ? C.greenW : C.green;
  return s % 4 === 0 ? C.beat : null;
}
function corPar(l, s) {
  const tr = S.parTrack,
    nome = PAR_PARAMS[S.parParam],
    nivel = 7 - l,
    cor = C.par[nome];
  const vazio = s % 4 === 0 && nivel === 0 ? C.faint : null;
  if (!toca(tr, s)) return vazio;
  if (nome === "alt") {
    if (tr < TRACKS_LAYER) return null;
    return S.alt[tr][s] ? cor : fraca(cor, 0.2);
  }
  const n = nome === "vel" ? nivelVel(tr, s) : S.par[tr][s][nome];
  const aceso = PAR_ESCOLHA.includes(nome) ? nivel === n : nivel <= n;
  return aceso ? cor : vazio;
}
function corPerf(l, s) {
  if (l === PERF.mute) {
    if (s < D.tracks.length) return (S.mute >> s) & 1 ? C.pink : C.soandoW;
    if (PERF.fills.includes(s))
      return S.fill === PERF.fills.indexOf(s) ? C.white : C.faint;
    return null;
  }
  if (l === PERF.chain && s < 8) return (S.chain >> s) & 1 ? C.blue : C.blueW;
  if (l === PERF.loop) return S.loop === s ? C.white : C.faint;
  if (l === PERF.last) {
    if (s === S.last) return C.amber;
    return S.first <= s && s < S.last ? C.amberW : null;
  }
  if (l === PERF.scale && s < D.scales.length)
    return S.scale === s ? C.white : C.faint;
  return null;
}
function alvoRout(l, s) {
  if (l < D.rotas.length && s < FONTES_ROTA.length)
    return { id: "rota", f: s, v: l };
  if (l === ROUT.sc1 || l === ROUT.sc2) {
    const n = s + (l === ROUT.sc2 ? 16 : 0);
    return n < D.sc_fontes.length ? { id: "sc", v: n } : null;
  }
  if (l === ROUT.chaves) {
    if (ROUT.polarity.includes(s))
      return { id: "pol", v: ROUT.polarity.indexOf(s) };
    if (ROUT.hld.includes(s)) return { id: "hld", v: ROUT.hld.indexOf(s) };
  }
  return null;
}
function corRout(l, s) {
  const a = alvoRout(l, s);
  if (!a) return null;
  if (a.id === "rota")
    return S.rota[a.f] === a.v ? C.destino[l] : fraca(C.destino[l], 0.16);
  if (a.id === "sc") return S.sc === a.v ? C.white : C.faint;
  return (a.id === "pol" ? S.pol : S.hld) === a.v ? C.amber : C.amberW;
}

// as ondas do standby (o _nova_onda / quadro_de_ondas do motor, em pequeno)
function hsv(hue) {
  const f = (n) => {
    const k = (n + hue / 60) % 6;
    return 255 * (1 - Math.max(0, Math.min(k, 4 - k, 1)));
  };
  return [f(5), f(3), f(1)];
}
function novaOnda(l, s, t) {
  // sem movimento (reduced-motion), a onda vira uma mancha parada
  ondas.push({
    l,
    s,
    t0: t,
    vel: REDUZ ? 0 : 6 + Math.random() * 7,
    larg: REDUZ ? 2.6 : 1.4 + Math.random() * 1.6,
    alc: 9 + Math.random() * 8,
    rgb: hsv(Math.random() * 360),
  });
}
function corOnda(l, s, t) {
  let r = 0,
    g = 0,
    b = 0;
  for (const o of ondas) {
    const vt = ((t - o.t0) / 1000) * o.vel;
    const anel = 1 - Math.abs(Math.hypot(l - o.l, s - o.s) - vt) / o.larg;
    if (anel <= 0) continue;
    const k = anel * (1 - vt / o.alc);
    r += o.rgb[0] * k;
    g += o.rgb[1] * k;
    b += o.rgb[2] * k;
  }
  if (r + g + b < 8) return null;
  return `rgb(${Math.min(255, r | 0)},${Math.min(255, g | 0)},${Math.min(255, b | 0)})`;
}

function corPad(l, s, t) {
  switch (S.page) {
    case "par":
      return corPar(l, s);
    case "perf":
      return corPerf(l, s);
    case "rout":
      return corRout(l, s);
    case "standby":
      return corOnda(l, s, t);
    default:
      return corStep(l, s);
  }
}
function txtPad(l, s) {
  if (S.page === "perf") {
    if (l === PERF.mute && s < D.tracks.length) return D.tracks[s];
    if (l === PERF.mute && PERF.fills.includes(s))
      return `FILL\n${PERF.fills.indexOf(s) + 1}`;
    if (l === PERF.chain && s < 8) return D.variacoes[s];
    if (l === PERF.last && s === S.last) return "LAST";
    if (l === PERF.scale && s < D.scales.length)
      return D.scales[s].replace("(T)", "\nT");
  }
  if (S.page === "rout") {
    const a = alvoRout(l, s);
    if (!a) return "";
    if (a.id === "rota") return l === 0 ? FONTES_ROTA[s] : "";
    if (a.id === "sc") return D.sc_fontes[a.v].replace(" ", "\n");
    return a.id === "pol" ? ["DUCK", "GATE"][a.v] : ["TIME", "STEP"][a.v];
  }
  return "";
}

// ── as bordas ─────────────────────────────────────────────
function borda(kind, i) {
  if (S.page === "standby")
    return { c: null, t: kind === "topE" ? D.variacoes[i] : "" };
  if (kind === "topE") {
    let c = i === S.varEdit ? C.blue : C.blueW;
    if (i === S.varPlay) c = i === S.varEdit ? C.lblue : C.white;
    return { c, t: D.variacoes[i] };
  }
  if (kind === "ladoE") {
    const tr = trLinha(i);
    if (S.page === "par")
      return { c: tr === S.parTrack ? C.white : C.faint, t: D.tracks[tr] };
    return { c: (S.mute >> tr) & 1 ? C.pink : C.soando, t: D.tracks[tr] };
  }
  if (kind === "topD") {
    const nomes = [
      "▲\nRS·HC",
      "▼\nCC·RC",
      "AB",
      "A",
      "B",
      "PAR",
      "PERF",
      "ROUT",
    ];
    let c;
    if (i < 2) c = S.banco === i + 1 ? C.white : C.dim;
    else if (i < 5) {
      const cor = [C.white, C.red, C.green][i - 2];
      c = S.layer === ["AB", "A", "B"][i - 2] ? cor : fraca(cor, 0.3);
    } else c = S.page === ["par", "perf", "rout"][i - 5] ? C.white : C.dim;
    return { c, t: nomes[i] };
  }
  if (kind === "ladoD") {
    if (S.page === "par") {
      if (i >= PAR_PARAMS.length) return { c: null, t: "" };
      const cor = C.par[PAR_PARAMS[i]];
      return {
        c: i === S.parParam ? cor : fraca(cor, 0.25),
        t: PNOME[PAR_PARAMS[i]],
      };
    }
    return { c: i === S.vel ? C.white : C.dim, t: String(D.velocidades[i]) };
  }
  return { c: null, t: "" };
}

// ── as fichas: o que cada coisa faz ───────────────────────
function lugar(kind, i) {
  const cc = {
    topE: CENA_CCS[i],
    ladoE: 98 - i,
    topD: 91 + i,
    ladoD: CENA_CCS[i],
  }[kind];
  return fmt(T.lugar[kind], { n: i + 1, cc });
}
const ds = (lista, args) => lista.map((x) => fmt(x, args));

function ficha(kind, i, j) {
  const F = T.f,
    p = S.page;
  if (kind === "logo") {
    const f = i === 0 ? F.logoE : F.logoD;
    return { t: L(f.t), w: L(T.lugar.logo), s: "ok", d: ds(f.d) };
  }
  if (p === "standby") {
    if (kind !== "pad")
      return {
        t: L(F.standbyBt.t),
        w: lugar(kind, i),
        s: "ok",
        d: ds(F.standbyBt.d),
      };
    return {
      t: L(F.standbyPad.t),
      w: fmt(T.lugar.pad, { l: i + 1, s: j + 1 }),
      s: "ok",
      d: ds(F.standbyPad.d),
    };
  }
  if (kind === "topE")
    return {
      t: fmt(F.variacao.t, { v: D.variacoes[i] }),
      w: lugar(kind, i),
      s: "part",
      d: ds(F.variacao.d),
    };
  if (kind === "ladoE") {
    const tr = trLinha(i),
      t = D.tracks[tr];
    if (p === "par")
      return {
        t: fmt(F.parTrack.t, { t }),
        w: lugar(kind, i),
        s: "ok",
        d: ds(F.parTrack.d),
      };
    return {
      t: fmt(F.mute.t, { t }),
      w: lugar(kind, i),
      s: "ok",
      d: [...ds(F.mute.d), L(i === 4 || i === 5 ? F.mute.banco : F.mute.perf)],
    };
  }
  if (kind === "topD") {
    if (i < 2)
      return {
        t: L(i === 0 ? F.banco.t1 : F.banco.t2),
        w: lugar(kind, i),
        s: "ok",
        d: ds(F.banco.d),
      };
    if (i < 5) {
      const m = ["AB", "A", "B"][i - 2];
      return {
        t: fmt(F.layer.t, { m }),
        w: lugar(kind, i),
        s: "ok",
        d: [L(F.layer[m]), L(F.layer.outros)],
      };
    }
    const pg = ["par", "perf", "rout"][i - 5];
    return {
      t: fmt(F.pagina.t, { p: pg.toUpperCase() }),
      w: lugar(kind, i),
      s: "ok",
      d: [L(F.pagina[pg]), ...ds(F.pagina.d)],
    };
  }
  if (kind === "ladoD") {
    if (p === "par") {
      if (i >= PAR_PARAMS.length)
        return {
          t: L(F.semPar.t),
          w: lugar(kind, i),
          s: "ok",
          d: ds(F.semPar.d),
        };
      const nome = PAR_PARAMS[i];
      const lista = NIVEIS_PAR[nome]
        ? NIVEIS_PAR[nome].map((_, k) => rotuloNivel(nome, k)).join(" · ")
        : "";
      return {
        t: fmt(F.param.t, { p: PNOME[nome] }),
        w: lugar(kind, i),
        s: statusPar(nome),
        d: [
          L(F.param.d),
          nome === "alt" ? L(F.param.alt) : fmt(F.param.alturas, { lista }),
        ],
      };
    }
    return {
      t: fmt(F.vel.t, { v: D.velocidades[i] }),
      w: lugar(kind, i),
      s: "ok",
      d: ds(F.vel.d),
    };
  }
  // os pads
  const s = j;
  if (p === "steps") {
    const tr = trLinha(i);
    return {
      t: fmt(F.step.t, { t: D.tracks[tr], s: s + 1 }),
      w: fmt(T.lugar.pad, { l: i + 1, s: s + 1 }),
      s: "ok",
      d: [...ds(F.step.d), L(tr < TRACKS_LAYER ? F.step.layer : F.step.alt)],
    };
  }
  if (p === "par") {
    const tr = S.parTrack,
      nome = PAR_PARAMS[S.parParam],
      nivel = 7 - i,
      t = D.tracks[tr];
    const val =
      nome === "alt"
        ? L(F.par.alt)
        : `${PNOME[nome]} = ${rotuloNivel(nome, nivel)}`;
    const d = [
      fmt(F.par.grava, { l: nivel + 1, val, s: s + 1, t }),
      L(F.par.d),
    ];
    if (nome === "vel") d.push(L(F.par.vel));
    if (nome === "alt")
      d.push(L(tr < TRACKS_LAYER ? F.par.altLayer : F.par.altVazio));
    if (PAR_ESCOLHA.includes(nome)) d.push(L(F.par.escolha));
    if (nome === "start") d.push(L(F.par.start));
    return {
      t: fmt(F.par.t, { p: PNOME[nome], t, s: s + 1 }),
      w: fmt(T.lugar.altura, { l: nivel + 1, s: s + 1 }),
      s: statusPar(nome),
      d,
    };
  }
  const w = fmt(T.lugar.padCol, { l: i + 1, s: s + 1 });
  if (p === "perf") {
    if (i === PERF.mute && s < D.tracks.length)
      return {
        t: fmt(F.perfMute.t, { t: D.tracks[s] }),
        w,
        s: "ok",
        d: ds(F.perfMute.d),
      };
    if (i === PERF.mute && PERF.fills.includes(s)) {
      const n = PERF.fills.indexOf(s) + 1;
      return { t: fmt(F.fill.t, { n }), w, s: "part", d: ds(F.fill.d, { n }) };
    }
    if (i === PERF.chain && s < 8)
      return {
        t: fmt(F.chain.t, { v: D.variacoes[s] }),
        w,
        s: "ok",
        d: ds(F.chain.d),
      };
    if (i === PERF.loop)
      return { t: fmt(F.loop.t, { s: s + 1 }), w, s: "part", d: ds(F.loop.d) };
    if (i === PERF.last)
      return { t: fmt(F.last.t, { s: s + 1 }), w, s: "ok", d: ds(F.last.d) };
    if (i === PERF.scale && s < D.scales.length)
      return {
        t: fmt(F.scale.t, { n: D.scales[s] }),
        w,
        s: "ok",
        d: ds(F.scale.d),
      };
    return { t: L(F.semFuncao.perf), w, s: "ok", d: ds(F.semFuncao.d) };
  }
  const a = alvoRout(i, s);
  if (!a) return { t: L(F.semFuncao.rout), w, s: "ok", d: ds(F.semFuncao.d) };
  if (a.id === "rota")
    return {
      t: fmt(F.rota.t, { f: FONTES_ROTA[a.f], d: D.rotas[a.v] }),
      w,
      s: "ok",
      d: ds(F.rota.d),
    };
  if (a.id === "sc")
    return {
      t: fmt(F.sc.t, { n: D.sc_fontes[a.v] }),
      w,
      s: "ok",
      d: ds(F.sc.d),
    };
  if (a.id === "pol")
    return {
      t: fmt(F.pol.t, { n: ["DUCK", "GATE"][a.v] }),
      w,
      s: "ok",
      d: ds(F.pol.d),
    };
  return {
    t: fmt(F.hld.t, { n: ["TIME", "STEP"][a.v] }),
    w,
    s: "ok",
    d: ds(F.hld.d),
  };
}
// PROB e VEL pela PAR: F4.6c; SUB/START/ALT so pela tela (F3); CYCLE nunca de ouvido
const statusPar = (nome) =>
  nome === "prob" || nome === "vel" ? "ok" : nome === "cycle" ? "no" : "part";

// ── tocar: o que o motor.py faz com cada toque ────────────
function tocar(kind, i, j, ev) {
  sel = { kind, i, j };
  const p = S.page;
  if (kind === "logo" || p === "standby") {
    if (p === "standby" && kind === "pad") novaOnda(i, j, performance.now());
    return pintar();
  }
  if (kind === "topE") S.varEdit = i;
  else if (kind === "ladoE") {
    const tr = trLinha(i);
    if (p === "par") S.parTrack = tr;
    else S.mute ^= 1 << tr;
  } else if (kind === "topD") {
    if (i < 2) S.banco = i + 1;
    else if (i < 5) S.layer = ["AB", "A", "B"][i - 2];
    else {
      const pg = ["par", "perf", "rout"][i - 5];
      S.loop = null; // trocar de pagina solta o STEP LOOP (motor._soltar_segurados)
      mudarPagina(S.page === pg ? "steps" : pg);
    }
  } else if (kind === "ladoD") {
    if (p === "par") {
      if (i < PAR_PARAMS.length) S.parParam = i;
    } else S.vel = i;
  } else if (kind === "pad") {
    if (p === "steps") tocarStep(trLinha(i), j);
    else if (p === "par") tocarPar(i, j);
    else if (p === "perf") tocarPerf(i, j, ev);
    else if (p === "rout") {
      const a = alvoRout(i, j);
      if (a && a.id === "rota") S.rota[a.f] = a.v;
      else if (a) S[a.id] = a.v;
    }
  }
  pintar();
}
// motor.alternar_track: apaga so se todos os slots-alvo ja tem a MESMA nota
// (o ALT muda a nota, entao um step roxo vira nota normal)
function tocarStep(tr, s) {
  const v = D.velocidades[S.vel],
    alvo = slotsAlvo(tr);
  const todos = alvo.every(
    (k) => S[k][tr][s] === v && !(k === "a" && S.alt[tr][s]),
  );
  alvo.forEach((k) => {
    S[k][tr][s] = todos ? 0 : v;
    if (k === "a") S.alt[tr][s] = false;
  });
}
// motor.tocar_par / definir_vel / definir_alt
function tocarPar(l, s) {
  const tr = S.parTrack,
    nome = PAR_PARAMS[S.parParam],
    nivel = 7 - l;
  if (nome === "alt") {
    if (tr < TRACKS_LAYER) return;
    const liga = !S.alt[tr][s];
    if (!liga && !S.a[tr][s]) return;
    if (liga && !S.a[tr][s]) S.a[tr][s] = D.velocidades[S.vel];
    S.alt[tr][s] = liga;
    return;
  }
  if (nome === "vel") {
    const tocam = ["a", "b"].filter((k) => S[k][tr][s] > 0);
    (tocam.length ? tocam : slotsAlvo(tr)).forEach(
      (k) => (S[k][tr][s] = NIVEIS_PAR.vel[nivel]),
    );
    return;
  }
  S.par[tr][s][nome] = nivel;
}
// motor.tocar_perf; o Shift faz o papel de "segurar outra variacao"
function tocarPerf(l, s, ev) {
  if (l === PERF.mute) {
    if (s < D.tracks.length) S.mute ^= 1 << s;
    else if (PERF.fills.includes(s)) S.fill = PERF.fills.indexOf(s);
  } else if (l === PERF.chain && s < 8) {
    const nova = ev && ev.shiftKey ? S.chain ^ (1 << s) : 1 << s;
    if (nova) S.chain = nova;
  } else if (l === PERF.loop) S.loop = s;
  else if (l === PERF.last) {
    if (s >= S.first) S.last = s;
  } else if (l === PERF.scale && s < D.scales.length) S.scale = s;
}
function soltar() {
  if (S && S.page === "perf" && S.loop !== null) {
    S.loop = null;
    pintar();
  }
}

// ── pintar ────────────────────────────────────────────────
function mudarPagina(pg) {
  S.page = pg;
  try {
    localStorage.setItem(CHAVE_PAGINA, pg);
  } catch (e) {
    /* sem storage */
  }
  if (pg === "standby") {
    ondas = [];
    proxOnda = 0;
    if (REDUZ)
      [
        [3, 4],
        [5, 12],
      ].forEach(([l, s]) => novaOnda(l, s, 0));
    else chover();
  }
}
function pintarCelula(b, cor, txt, f, marcada) {
  b.style.background = cor || "";
  b.style.color = cor ? (claro(cor) ? "#0b0c0d" : "#d6dcdf") : "";
  b.classList.toggle("g-apagado", !cor);
  texto(b, txt || "");
  attr(b, "aria-label", f ? f.t : "");
  attr(b, "data-sel", marcada);
}
function eSel(kind, i, j) {
  return sel.kind === kind && sel.i === i && (j === undefined || sel.j === j);
}
function pintar(t = performance.now()) {
  if (!S) return;
  for (let l = 0; l < 8; l++)
    for (let s = 0; s < 16; s++)
      pintarCelula(
        cel.pad[l][s],
        corPad(l, s, t),
        txtPad(l, s),
        ficha("pad", l, s),
        eSel("pad", l, s),
      );
  for (const kind of ["topE", "ladoE", "topD", "ladoD"])
    cel[kind].forEach((b, i) => {
      const x = borda(kind, i);
      pintarCelula(b, x.c, x.t, ficha(kind, i), eSel(kind, i));
    });
  cel.logo.forEach((b, i) => attr(b, "data-sel", eSel("logo", i)));
  el.abas.forEach((b, k) =>
    attr(b, "aria-pressed", PAGINAS[k] === S.page ? "true" : "false"),
  );
  pintarFicha();
}
function pintarFicha() {
  const f = ficha(sel.kind, sel.i, sel.j);
  texto(el.fPagina, fmt(T.pagina, { p: L(T.paginas[S.page]) }));
  texto(el.fTitulo, f.t);
  texto(el.fOnde, f.w);
  attr(el.fStatus, "data-s", f.s);
  texto(el.fStatus, L(T.status[f.s]));
  el.fDesc.replaceChildren(...f.d.map((x) => h("p", {}, rico(x))));
}
// a chuva: so os pads mudam de cor; para sozinha fora do standby ou com a aba escondida
function chover() {
  if (animando || REDUZ) return;
  animando = true;
  let ultimo = 0;
  const passo = (t) => {
    if (S.page !== "standby" || !painel || painel.hidden) {
      animando = false;
      return;
    }
    if (t - ultimo > 33) {
      ultimo = t;
      if (t > proxOnda) {
        proxOnda = t + 350 + Math.random() * 750;
        novaOnda(
          Math.floor(Math.random() * 8),
          Math.floor(Math.random() * 16),
          t,
        );
      }
      ondas = ondas.filter((o) => ((t - o.t0) / 1000) * o.vel < o.alc);
      for (let l = 0; l < 8; l++)
        for (let s = 0; s < 16; s++) {
          const b = cel.pad[l][s],
            cor = corOnda(l, s, t);
          b.style.background = cor || "";
          b.classList.toggle("g-apagado", !cor);
        }
    }
    requestAnimationFrame(passo);
  };
  requestAnimationFrame(passo);
}

// ── montar ────────────────────────────────────────────────
function botao(cls, kind, i, j) {
  const b = h(`button.g-cel.${cls}`, { type: "button" });
  b.addEventListener("pointerdown", (ev) => {
    if (ev.button !== 0) return;
    ev.preventDefault();
    tocar(kind, i, j, ev);
  });
  b.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    ev.preventDefault();
    tocar(kind, i, j, ev);
  });
  return b;
}
function aparelho(lado) {
  const lp = h("div.g-lp", {
    role: "group",
    "aria-label": L(lado === "E" ? T.lpE : T.lpD),
  });
  const off = lado === "E" ? 0 : 8;
  const logo = (n, txt) => {
    const b = botao("g-logo", "logo", n);
    texto(b, txt);
    cel.logo[n] = b;
    lp.append(b);
  };
  const borda = (kind, i) => lp.append((cel[kind][i] = botao("g-bt", kind, i)));
  const pad = (l, c) =>
    lp.append((cel.pad[l][off + c] = botao("g-pad", "pad", l, off + c)));
  const step = (n) => lp.append(h("div.g-step.mono", {}, String(n)));
  if (lado === "E") {
    logo(0, "VAR▸");
    for (let i = 0; i < 8; i++) borda("topE", i);
    for (let l = 0; l < 8; l++) {
      borda("ladoE", l);
      for (let c = 0; c < 8; c++) pad(l, c);
    }
    lp.append(h("div"));
    for (let s = 1; s <= 8; s++) step(s);
  } else {
    for (let i = 0; i < 8; i++) borda("topD", i);
    logo(1, "VEL▾");
    for (let l = 0; l < 8; l++) {
      for (let c = 0; c < 8; c++) pad(l, c);
      borda("ladoD", l);
    }
    for (let s = 9; s <= 16; s++) step(s);
    lp.append(h("div"));
  }
  return h(
    "div.g-unidade",
    {},
    lp,
    h("div.g-rot.mono", {}, L(lado === "E" ? T.esquerdo : T.direito)),
  );
}
const pill = (s) => h("span.g-pill", { "data-s": s }, L(T.status[s]));
const secao = (titulo, ...filhos) =>
  h("div.secao", {}, h("h2", {}, L(titulo)), ...filhos);

function montarBancada() {
  for (let l = 0; l < 8; l++) cel.pad[l] = [];
  el.abas = PAGINAS.map((pg) =>
    h(
      "button.bt",
      {
        type: "button",
        onclick: () => {
          S.loop = null;
          mudarPagina(pg);
          sel =
            pg === "standby"
              ? { kind: "pad", i: 3, j: 4 }
              : {
                  kind: "topD",
                  i: pg === "steps" ? 0 : PAGINAS.indexOf(pg) + 4,
                };
          pintar();
        },
      },
      L(T.paginas[pg]),
    ),
  );
  el.fPagina = h("span.g-eyebrow.mono");
  el.fTitulo = h("h3");
  el.fOnde = h("span.g-onde.mono");
  el.fStatus = h("span.g-pill");
  el.fDesc = h("div.g-desc");
  return secao(
    T.bancada,
    h("p.nota", {}, rico(L(T.bancadaNota))),
    h("div.fila", {}, el.abas),
    h(
      "div.g-bancada",
      {},
      h("div.g-aparelhos", {}, aparelho("E"), aparelho("D")),
      h(
        "aside.g-ficha",
        { "aria-live": "polite" },
        el.fPagina,
        el.fTitulo,
        el.fOnde,
        el.fStatus,
        el.fDesc,
      ),
    ),
    h(
      "div.fila",
      {},
      h(
        "button.bt",
        {
          type: "button",
          onclick: () => {
            const pg = S.page;
            S = inicial();
            S.page = pg;
            pintar();
          },
        },
        L(T.voltar),
      ),
      h("p.nota", {}, rico(L(T.shift))),
    ),
  );
}
// "par.prob" -> C.par.prob; "destino.1" -> C.destino[1]
const corDaChave = (k) => k.split(".").reduce((o, p) => o[p], C);
function montarCores() {
  const grupo = (titulo, itens) =>
    h(
      "div.g-grupo-cor",
      {},
      h("h3", {}, L(titulo)),
      h(
        "div.g-legenda",
        {},
        itens.map((x) =>
          h(
            "span.g-amostra",
            {},
            h(
              "span.g-cores",
              {},
              x.c.map((k) => {
                const i = h("i");
                i.style.background = corDaChave(k);
                return i;
              }),
            ),
            L(x),
          ),
        ),
      ),
    );
  return secao(
    T.cores,
    grupo(T.legendaGrid, T.legenda.grid),
    grupo(T.legendaBordas, T.legenda.bordas),
    h("p.nota", {}, L(T.coresNota)),
  );
}
function montarMapa() {
  const linhas = T.mapaLinhas.map((x) => {
    const celulas = [
      h("td", {}, L(x.b), h("span.g-cc.mono", {}, x.cc)),
      h("td", {}, rico(L(x.steps))),
    ];
    // "=" junta a celula com a da esquerda
    const span = 1 + (x.par === "=" ? 1 : 0) + (x.perf === "=" ? 1 : 0);
    if (x.par === "=") celulas[1].setAttribute("colspan", span);
    else {
      const c = h("td", {}, rico(L(x.par)));
      if (x.perf === "=") c.setAttribute("colspan", 2);
      celulas.push(c);
      if (x.perf !== "=") celulas.push(h("td", {}, rico(L(x.perf))));
    }
    return h("tr", {}, celulas);
  });
  return secao(
    T.mapa,
    h("p.nota", {}, L(T.mapaNota)),
    h(
      "div.g-tabela",
      {},
      h(
        "table",
        {},
        h(
          "thead",
          {},
          h(
            "tr",
            {},
            T.mapaCab.map((c) => h("th", {}, L(c))),
          ),
        ),
        h("tbody", {}, linhas),
      ),
    ),
  );
}
function montarSegredos() {
  return secao(
    T.segredos,
    h("p.nota", {}, L(T.segredosNota)),
    h(
      "div.g-segredos",
      {},
      T.listaSegredos.map((x) =>
        h(
          "div.g-segredo",
          {},
          h(
            "div.g-segredo-topo",
            {},
            h("span.g-onde.mono", {}, L(x.w)),
            pill(x.s),
          ),
          h("h3", {}, L(x.t)),
          h("p", {}, L(x.d)),
          h(
            "button.bt.bt-peq",
            {
              type: "button",
              onclick: () => {
                const [pg, kind, i, j] = x.go;
                S.loop = null;
                mudarPagina(pg);
                sel = { kind, i, j };
                pintar();
                el.bancada.scrollIntoView({
                  behavior: REDUZ ? "auto" : "smooth",
                  block: "start",
                });
              },
            },
            L(T.mostrar),
          ),
        ),
      ),
    ),
  );
}
function montarTestado() {
  return secao(
    T.testado,
    h(
      "div.colunas",
      {},
      ["ok", "part", "no"].map((s) =>
        h(
          "div.g-teste",
          {},
          pill(s),
          h(
            "ul",
            {},
            T.listaTestado[s].map(([txt, rot]) =>
              h(
                "li",
                {},
                L(txt),
                rot ? h("span.g-onde.mono", {}, ` ${rot}`) : null,
              ),
            ),
          ),
        ),
      ),
    ),
    h("p.nota", {}, L(T.testadoNota)),
  );
}

export default {
  nome: "Guia",

  montar(raiz, ctx) {
    D = ctx.D;
    painel = raiz;
    S = inicial();
    try {
      const pg = localStorage.getItem(CHAVE_PAGINA);
      if (PAGINAS.includes(pg)) S.page = pg;
    } catch (e) {
      /* sem storage */
    }
    window.addEventListener("pointerup", soltar);
    window.addEventListener("pointercancel", soltar);
    const topo = h(
      "div.g-topo",
      {},
      h("span.g-eyebrow.mono", {}, L(T.eyebrow)),
      h("h2.g-titulo", {}, L(T.titulo)),
      h("p.g-lede", {}, rico(L(T.lede))),
    );
    const antes = secao(
      T.antes,
      h(
        "div.g-passos",
        {},
        T.passos.map((x) =>
          h(
            "div.g-passo",
            {},
            h("span.g-n.mono", {}, L(x.n)),
            h("p", {}, rico(L(x.d))),
          ),
        ),
      ),
    );
    el.bancada = montarBancada();
    raiz.append(
      topo,
      antes,
      el.bancada,
      montarCores(),
      montarMapa(),
      montarSegredos(),
      montarTestado(),
    );
    if (S.page === "standby") mudarPagina("standby");
    pintar();
  },

  // o guia nao le o estado da maquina; so retoma a chuva quando a aba volta
  atualizar() {
    if (S && S.page === "standby" && !animando) chover();
  },
};

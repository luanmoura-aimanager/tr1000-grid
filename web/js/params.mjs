// params.mjs - um slider ou um seletor ligado a um parametro da parametros.py
// (o mesmo id dos knobs das controladoras). A faixa e o nome vem do /dados;
// os que dependem de type (DELAY 2-6, MFX 1-7, LFO RATE) trocam de faixa e de
// nome conforme o type que a maquina tem agora (E.kit).
import { slider, seletor, valor, attr } from "./dom.mjs";

export function entradaDe(D, E, id) {
  const p = D.params[id];
  if (!p) return null;
  if (p.por_tipo["-"]) return p.por_tipo["-"];
  const sel = D.seletores[id];
  const tipo = sel && E.kit ? E.kit[sel] : undefined;
  return tipo === undefined ? null : p.por_tipo[String(tipo)] || null;
}

const nomeCurto = (escala) =>
  String(escala || "")
    .split(" (type")[0]
    .split(" (")[0];

/** {el, atualizar(E)}. rot fixo, ou null para usar o nome do type atual. */
export function paramSlider(ctx, id, rot, fmt = (v) => v) {
  const s = slider({
    rot: rot || id,
    min: 0,
    max: 1,
    fmt,
    aoMudar: ctx.espacado((v) => ctx.acao("param", { id, valor: v })),
  });
  return {
    el: s.el,
    atualizar(E) {
      const e = entradaDe(ctx.D, E, id);
      if (!e) {
        s.set(null, false);
        if (!rot) s.rotulo("—");
        return;
      }
      if (+s.inp.min !== e.min) s.inp.min = e.min;
      if (+s.inp.max !== e.max) s.inp.max = e.max;
      if (!rot) s.rotulo(nomeCurto(e.escala));
      s.set(E.kit ? E.kit[id] : null, E.kit && E.kit[id] !== undefined);
    },
  };
}

/** Um parametro de escolha (TYPE, WAVEFORM, POLARITY...) como select. */
export function paramSeletor(ctx, id, nomes, rot) {
  const s = seletor(nomes, (v) => ctx.acao("param", { id, valor: v }), rot);
  return {
    el: s,
    atualizar(E) {
      const v = E.kit ? E.kit[id] : undefined;
      attr(s, "disabled", v === undefined);
      if (v !== undefined) valor(s, v);
    },
  };
}

// os formatos do visor do App (o que o Luan leu nas pontas)
export const fmt = {
  pct1000: (v) => `${Math.round(v / 10)}%`,
  pan: (v) =>
    v === 500
      ? "C"
      : v < 500
        ? `L${Math.round((500 - v) / 5)}`
        : `R${Math.round((v - 500) / 5)}`,
  bipolar: (v) => {
    const d = v - 1000;
    return d > 0 ? `+${d}` : `${d}`;
  },
  cru: (v) => String(v),
};

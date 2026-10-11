// efeitos.mjs - REVERB, DELAY, LFO, MASTER FX, SIDE CHAIN e a Routing Matrix.
// Os knobs que dependem do type (DELAY 2-6, MFX 1-7) mudam de nome e de faixa
// com o type que a maquina tem - igual aos knobs do MC-24.
import { h, attr, texto } from "../dom.mjs";
import { paramSlider, paramSeletor, fmt } from "../params.mjs";

let itens = [],
  matriz = [],
  lfoSync = null;
const FONTES = [
  "bd",
  "sd",
  "lt",
  "ht",
  "rs",
  "hc",
  "ch",
  "oh",
  "cc",
  "rc",
  "rvb",
  "dly",
  "ext",
];

export default {
  nome: "Efeitos",

  montar(el, ctx) {
    const D = ctx.D;
    const S = (id, rot, f) => {
      const s = paramSlider(ctx, id, rot, f);
      itens.push(s);
      return s.el;
    };
    const L = (id, nomes, rot) => {
      const s = paramSeletor(ctx, id, nomes, rot);
      itens.push(s);
      return s.el;
    };

    const reverb = h(
      "div.secao",
      {},
      h("h2", {}, "reverb"),
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "TYPE"),
        L("reverb.type", D.nomes["reverb.type"], "REVERB TYPE"),
      ),
      S("reverb.time", "TIME", fmt.pct1000),
      S("reverb.predelay", "PRE DLY"),
      S("reverb.lowcut", "LOW CUT"),
      S("reverb.highcut", "HIGH CUT"),
      S("reverb.density", "DENSITY"),
    );

    const delay = h(
      "div.secao",
      {},
      h("h2", {}, "delay"),
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "TYPE"),
        L("delay.type", D.delay_tipos, "DELAY TYPE"),
      ),
      S("delay.p1", "LEVEL", fmt.pct1000),
      S("delay.rvb_send", "RVB SEND", fmt.pct1000),
      [2, 3, 4, 5, 6].map((n) => S(`delay.p${n}`, null)),
    );

    lfoSync = h("span.mono.fraco");
    const lfo = h(
      "div.secao",
      {},
      h("h2", {}, "lfo do kit"),
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "WAVE"),
        L("lfo.waveform", D.nomes["lfo.waveform"], "WAVEFORM"),
        h("span.fraco", {}, "SYNC"),
        lfoSync,
      ),
      S("lfo.rate", null),
      h(
        "p.nota",
        {},
        "O LFO só se ouve com um TARGET escolhido no App (Mod (Kit)).",
      ),
    );

    const mfx = h(
      "div.secao",
      {},
      h("h2", {}, "master fx"),
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "TYPE"),
        L("mfx.type", D.mfx_tipos, "MASTER FX TYPE"),
      ),
      [1, 2, 3, 4, 5, 6, 7].map((n) => S(`mfx.p${n}`, null)),
      h("p.nota", {}, "O botão ON do MASTER FX fica no painel da TR-1000."),
    );

    const sc = h(
      "div.secao",
      {},
      h("h2", {}, "side chain"),
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "SOURCE"),
        L("sc.source", D.sc_fontes, "SOURCE"),
        h("span.fraco", {}, "POLARITY"),
        L("sc.polarity", ["DUCK", "GATE"], "POLARITY"),
        h("span.fraco", {}, "HLD MODE"),
        L("sc.hld_mode", ["TIME", "STEP"], "HLD MODE"),
      ),
      S("sc.hld_step", "HLD STEP"),
      S("sc.hld_time", "HLD TIME"),
      S("sc.release", "RELEASE"),
      S("sc.curve", "CURVE"),
      S("sc.mstr_dep", "MSTR DEP", fmt.pct1000),
      S("sc.depth.rvb", "SC DEPTH rvb", fmt.pct1000),
      S("sc.depth.dly", "SC DEPTH dly", fmt.pct1000),
      S("sc.depth.ext", "SC DEPTH ext", fmt.pct1000),
    );

    const tab = h(
      "div.matriz",
      {},
      h("span"),
      FONTES.map((f) => h("span.cab", {}, f.toUpperCase())),
    );
    D.rotas.forEach((nome, d) => {
      tab.append(h("span.cab.cab-esq", {}, nome));
      FONTES.forEach((f, i) => {
        const b = h("button.ponto", {
          type: "button",
          "aria-label": `${f} para ${nome}`,
          onclick: () => ctx.acao("param", { id: `rota.${f}`, valor: d }),
        });
        (matriz[i] = matriz[i] || [])[d] = b;
        tab.append(b);
      });
    });
    const rota = h(
      "div.secao",
      {},
      h("h2", {}, "routing matrix"),
      h("div.grade-rolo", {}, tab),
      h("p.nota", {}, "Cada som vai para THROUGH, MASTER FX ou ANALOG FX."),
    );

    el.append(h("div.colunas", {}, reverb, delay, lfo, mfx, sc), rota);
  },

  mostrar(sim, ctx) {
    if (ctx.E.ligado) ctx.acao("quer_kit", { sim });
  },

  atualizar(E, ctx) {
    itens.forEach((s) => s.atualizar(E));
    const sync = E.kit ? E.kit["lfo.sync"] : undefined;
    texto(lfoSync, sync === undefined ? "—" : ctx.D.lfo_syncs[sync]);
    FONTES.forEach((f, i) => {
      const v = E.kit ? E.kit[`rota.${f}`] : undefined;
      matriz[i].forEach((b, d) =>
        attr(b, "aria-pressed", v === d ? "true" : "false"),
      );
    });
  },
};

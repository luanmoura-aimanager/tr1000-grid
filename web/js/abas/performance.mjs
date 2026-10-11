// performance.mjs - MUTE, a chain de variacoes, FILL, STEP LOOP, FIRST/LAST
// (da variacao e de cada track) e a Scale. Tudo aprendido pelo PAINEL (C5) e
// liberado pelo Luan - ainda a testar no ROTEIRO-F3, o STEP LOOP mais que todos.
import { h, attr, valor, texto } from "../dom.mjs";

const PASSOS = Array.from({ length: 16 }, (_, i) => String(i + 1));
let mutes = [],
  vars = [],
  fills = [],
  scales = [],
  loopBt = null,
  loopSteps = [];
let varFirst,
  varLast,
  varRot,
  trk = [];

function selectSteps(aoMudar, rot) {
  const s = h(
    "select",
    { "aria-label": rot },
    PASSOS.map((n, i) => h("option", { value: i }, n)),
  );
  s.addEventListener("change", () => aoMudar(+s.value));
  return s;
}

export default {
  nome: "Performance",

  montar(el, ctx) {
    const D = ctx.D;
    mutes = D.tracks.map((t, tr) =>
      h(
        "button.bt",
        { type: "button", onclick: () => ctx.acao("mudo", { track: tr }) },
        t,
      ),
    );
    vars = D.variacoes.slice(0, 8).map((v, i) =>
      h(
        "button.bt",
        {
          type: "button",
          onclick: () => {
            const m = ctx.E.variacoes ^ (1 << i);
            if (m) ctx.acao("variacoes", { mascara: m }); // pelo menos uma variacao
          },
        },
        v,
      ),
    );
    // so FILL 1 e 2: o 3 e o 4 nao foram medidos (revisao do PR #7)
    fills = [0, 1].map((n) =>
      h(
        "button.bt",
        { type: "button", onclick: () => ctx.acao("fill", { n }) },
        `FILL ${n + 1}`,
      ),
    );
    scales = D.scales.map((s, n) =>
      h(
        "button.bt",
        { type: "button", onclick: () => ctx.acao("scale", { n }) },
        s,
      ),
    );
    loopBt = h(
      "button.bt",
      {
        type: "button",
        onclick: () => ctx.acao("loop", { ligado: !ctx.E.loop }),
      },
      "STEP LOOP",
    );
    loopSteps = PASSOS.map((n, s) => {
      const b = h(
        "button.bt.bt-peq",
        { type: "button", "aria-label": `segurar o step ${n}` },
        n,
      );
      b.addEventListener("pointerdown", () => {
        attr(b, "aria-pressed", "true");
        ctx.acao("loop", { ligado: true, step: s });
      });
      const soltar = () => {
        if (b.getAttribute("aria-pressed") === "true") {
          attr(b, "aria-pressed", "false");
          ctx.acao("loop", { ligado: false, step: s });
        }
      };
      b.addEventListener("pointerup", soltar);
      b.addEventListener("pointerleave", soltar);
      return b;
    });
    const mandaVar = () =>
      ctx.acao("extremos_var", {
        v: ctx.E.variacao,
        first: +varFirst.value,
        last: +varLast.value,
      });
    varFirst = selectSteps(mandaVar, "FIRST STEP da variação");
    varLast = selectSteps(mandaVar, "LAST STEP da variação");
    varRot = h("span.mono");

    const tabela = h(
      "div.tabela-trk",
      {},
      h("span.fraco", {}, "track"),
      h("span.fraco", {}, "próprio"),
      h("span.fraco", {}, "FIRST"),
      h("span.fraco", {}, "LAST"),
    );
    D.tracks.forEach((t, tr) => {
      const r = {};
      const manda = () =>
        ctx.acao(
          "extremos_track",
          r.sw.checked
            ? { track: tr, first: +r.first.value, last: +r.last.value }
            : { track: tr, first: null, last: null },
        );
      r.sw = h("input", {
        type: "checkbox",
        "aria-label": `${t} com FIRST/LAST próprio`,
      });
      r.sw.addEventListener("change", manda);
      r.first = selectSteps(manda, `FIRST do ${t}`);
      r.last = selectSteps(manda, `LAST do ${t}`);
      trk.push(r);
      tabela.append(h("strong.mono", {}, t), r.sw, r.first, r.last);
    });

    el.append(
      h(
        "div.colunas",
        {},
        h(
          "div.secao",
          {},
          h("h2", {}, "mute"),
          h("div.toques", {}, mutes),
          h(
            "p.nota",
            {},
            "Rosa = mutado. O mesmo mute da coluna lateral do Launchpad esquerdo.",
          ),
        ),
        h(
          "div.secao",
          {},
          h("h2", {}, "variações"),
          h("div.toques", {}, vars),
          h(
            "p.nota",
            {},
            "As acesas formam a chain (o painel faz igual apertando várias juntas).",
          ),
          h("div.toques", {}, fills),
          h("p.nota", {}, "Qual fill o FILL IN TRIG toca. FILL 3 e 4: ainda não medidos."),
        ),
        h(
          "div.secao",
          {},
          h("h2", {}, "step loop"),
          h("div.toques", {}, loopBt),
          h("div.toques", {}, loopSteps),
          h(
            "p.nota",
            {},
            "Segure um step para ele repetir. Não testado na máquina: o painel faz isso com a tecla segurada.",
          ),
        ),
        h("div.secao", {}, h("h2", {}, "scale"), h("div.toques", {}, scales)),
        h(
          "div.secao",
          {},
          h("h2", {}, "first / last"),
          h(
            "div.fila",
            {},
            h("span.fraco", {}, "variação"),
            varRot,
            h("span.fraco", {}, "FIRST"),
            varFirst,
            h("span.fraco", {}, "LAST"),
            varLast,
          ),
          tabela,
          h(
            "p.nota",
            {},
            'Track com "próprio" ligado usa os seus FIRST/LAST; desligado, segue a variação.',
          ),
        ),
      ),
    );
  },

  atualizar(E, ctx) {
    if (!E.grade) return;
    mutes.forEach((b, tr) => attr(b, "data-mudo", !!(E.mudos || [])[tr]));
    vars.forEach((b, i) =>
      attr(b, "aria-pressed", (E.variacoes >> i) & 1 ? "true" : "false"),
    );
    fills.forEach((b, n) =>
      attr(b, "aria-pressed", n === E.fill ? "true" : "false"),
    );
    scales.forEach((b, n) =>
      attr(b, "aria-pressed", n === E.scale ? "true" : "false"),
    );
    attr(loopBt, "aria-pressed", E.loop ? "true" : "false");
    texto(varRot, ctx.D.variacoes[E.variacao]);
    valor(varFirst, E.first_var[E.variacao]);
    valor(varLast, E.last_var[E.variacao]);
    trk.forEach((r, tr) => {
      if (document.activeElement !== r.sw) r.sw.checked = !!E.trk_sw[tr];
      valor(r.first, E.first_trk[tr]);
      valor(r.last, E.last_trk[tr]);
    });
  },
};

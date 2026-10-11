// pattern.mjs - a grade dos 10 tracks x 16 steps da variacao mostrada, o
// espelho dos Launchpads. Clique liga/desliga (o mesmo toque do pad, com a
// velocity e o layer escolhidos); Shift-clique (ou o modo "editar") abre o
// editor do step: PROB, SUB, CYCLE, START e ALT. O accent aparece, mas e
// feito no painel da TR-1000 (decisao do Luan, 10/10/2026).
import { h, texto, attr, slider, seletor, valor } from "../dom.mjs";

const VEL_FRACA = 80; // abaixo disso, a cor fraca (o painel: 66/74 fracos)
let celulas = [],
  acc = [],
  mutes = [],
  botVar = [],
  botVel = [],
  botLayer = {};
let sel = null; // [track, step] no editor
let editando = false;
let ed = {};

function kind(c) {
  if (c.a && c.alt) return c.vel < VEL_FRACA ? "altf" : "alt";
  if (c.a) return c.vel < VEL_FRACA ? "af" : "a";
  if (c.b) return c.vel < VEL_FRACA ? "bf" : "b";
  return "";
}

export default {
  nome: "Pattern",

  montar(el, ctx) {
    const D = ctx.D;
    botVar = D.variacoes.map((v, i) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          onclick: () => ctx.acao("exec", { tipo: "variacao", arg: i }),
        },
        v,
      ),
    );
    botVel = D.velocidades.map((v, i) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          onclick: () => ctx.acao("exec", { tipo: "velocidade", arg: i }),
        },
        String(v),
      ),
    );
    for (const m of ["AB", "A", "B"])
      botLayer[m] = h(
        "button.bt.bt-peq",
        {
          type: "button",
          onclick: () => ctx.acao("exec", { tipo: "layer", arg: m }),
        },
        m,
      );
    const bEdit = h(
      "button.bt.bt-peq",
      {
        type: "button",
        "aria-pressed": "false",
        onclick: () => {
          editando = !editando;
          attr(bEdit, "aria-pressed", editando ? "true" : "false");
        },
      },
      "editar step",
    );

    const grade = h("div.grade");
    D.tracks.forEach((t, tr) => {
      const m = h(
        "button.mute",
        {
          type: "button",
          title: `mute ${t}`,
          onclick: () => ctx.acao("mudo", { track: tr }),
        },
        "M",
      );
      mutes.push(m);
      grade.append(h("span.rot", {}, t), m);
      celulas[tr] = [];
      for (let s = 0; s < 16; s++) {
        const c = h("button.cel", {
          type: "button",
          "aria-label": `${t} step ${s + 1}`,
          onclick: (ev) => {
            if (ev.shiftKey || editando) {
              sel = [tr, s];
              this.atualizar(ctx.E, ctx);
            } else ctx.acao("step", { track: tr, step: s });
          },
          oncontextmenu: (ev) => {
            ev.preventDefault();
            sel = [tr, s];
            this.atualizar(ctx.E, ctx);
          },
        });
        if (s % 4 === 0) attr(c, "data-tempo", true);
        celulas[tr].push(c);
        grade.append(c);
      }
    });
    grade.append(
      h("span.rot", { title: "o accent e feito no painel da TR-1000" }, "ACC"),
      h("span"),
    );
    for (let s = 0; s < 16; s++) {
      const c = h("span.cel.acc");
      acc.push(c);
      grade.append(c);
    }
    grade.append(h("span"), h("span"));
    for (let s = 1; s <= 16; s++) grade.append(h("span.num", {}, String(s)));

    // o editor do step
    ed.titulo = h("h2", {}, "editor do step");
    ed.prob = slider({
      rot: "PROB",
      min: 0,
      max: 100,
      fmt: (v) => `${v}%`,
      aoMudar: ctx.espacado(
        (v) =>
          sel &&
          ctx.acao("campo_step", {
            track: sel[0],
            step: sel[1],
            nome: "prob",
            valor: v,
          }),
      ),
    });
    ed.start = slider({
      rot: "START",
      min: -100,
      max: 100,
      fmt: (v) => (v > 0 ? `+${v}` : `${v}`),
      aoMudar: ctx.espacado(
        (v) =>
          sel &&
          ctx.acao("campo_step", {
            track: sel[0],
            step: sel[1],
            nome: "start",
            valor: v,
          }),
      ),
    });
    ed.sub = seletor(
      D.sub_nomes,
      (v) =>
        sel &&
        ctx.acao("campo_step", {
          track: sel[0],
          step: sel[1],
          nome: "sub",
          valor: v,
        }),
      "SUB",
    );
    ed.cycle = seletor(
      D.cycle_nomes,
      (v) =>
        sel &&
        ctx.acao("campo_step", {
          track: sel[0],
          step: sel[1],
          nome: "cycle",
          valor: v,
        }),
      "CYCLE",
    );
    ed.alt = h("input", { type: "checkbox", "aria-label": "ALT" });
    ed.alt.addEventListener(
      "change",
      () =>
        sel &&
        ctx.acao("alt", {
          track: sel[0],
          step: sel[1],
          ligado: ed.alt.checked,
        }),
    );
    ed.altRot = h("label.fila", {}, ed.alt, "som ALT (tracks simples)");
    ed.secao = h(
      "div.secao.editor",
      {},
      ed.titulo,
      h(
        "p.nota",
        {},
        'Shift-clique (ou clique-direito, ou o modo "editar step") num step escolhe qual editar.',
      ),
      ed.prob.el,
      ed.start.el,
      h(
        "div.fila",
        {},
        h("span.fraco", {}, "SUB"),
        ed.sub,
        h("span.fraco", {}, "CYCLE"),
        ed.cycle,
      ),
      ed.altRot,
    );
    ed.secao.hidden = true;

    el.append(
      h(
        "div.secao",
        {},
        h("div.fila", {}, h("span.fraco", {}, "variação"), botVar),
        h(
          "div.fila",
          {},
          h("span.fraco", {}, "velocity"),
          botVel,
          h("span.fraco", {}, "layer"),
          Object.values(botLayer),
          bEdit,
        ),
        h("div.grade-rolo", {}, grade),
        h(
          "p.nota",
          {},
          "Clique liga ou desliga o step, com a velocity e o layer escolhidos. Vermelho = layer A, verde = só layer B, roxo = ALT; o pontinho branco marca PROB, SUB, CYCLE ou START mexidos.",
        ),
      ),
      ed.secao,
    );
  },

  atualizar(E, ctx) {
    if (!E.grade) return;
    const D = ctx.D;
    botVar.forEach((b, i) =>
      attr(b, "aria-pressed", i === E.variacao ? "true" : "false"),
    );
    botVel.forEach((b, i) =>
      attr(b, "aria-pressed", i === E.velocidade_idx ? "true" : "false"),
    );
    for (const [m, b] of Object.entries(botLayer))
      attr(b, "aria-pressed", m === E.modo_layer ? "true" : "false");
    E.grade.forEach((linha, tr) => {
      attr(mutes[tr], "data-mudo", !!(E.mudos || [])[tr]);
      linha.forEach((c, s) => {
        const el = celulas[tr][s];
        attr(el, "data-k", kind(c) || null);
        attr(el, "data-play", E.tocando && s === E.passo);
        attr(el, "data-sel", sel && sel[0] === tr && sel[1] === s);
        attr(
          el,
          "data-extra",
          (c.prob !== null && c.prob < 100) ||
            c.sub > 0 ||
            c.cycle > 0 ||
            c.start !== 0,
        );
      });
    });
    (E.acentos || []).forEach((on, s) => attr(acc[s], "data-on", on));
    ed.secao.hidden = !sel;
    if (sel) {
      const [tr, s] = sel,
        c = E.grade[tr][s];
      texto(
        ed.titulo,
        `editor · ${D.tracks[tr]} · step ${s + 1} · var ${D.variacoes[E.variacao]}`,
      );
      ed.prob.set(c.prob);
      ed.start.set(c.start);
      valor(ed.sub, c.sub);
      valor(ed.cycle, c.cycle);
      ed.alt.checked = !!c.alt;
      ed.altRot.hidden = tr < 4;
    }
  },
};

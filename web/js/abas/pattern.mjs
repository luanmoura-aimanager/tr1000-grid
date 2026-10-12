// pattern.mjs - a grade dos 10 tracks x 16 steps da variacao mostrada, o
// espelho dos Launchpads, e (desde o F3, 12/10/2026) tudo o que era a aba
// Performance: as variacoes em tres fileiras (edita / toca / fill), STEP LOOP,
// Scale e FIRST/LAST. Clique liga/desliga o step (o mesmo toque do pad, com a
// velocity e o layer escolhidos); Shift-clique (ou o modo "editar") abre o
// editor do step: PROB, SUB, CYCLE, START e ALT. O accent aparece, mas e feito
// no painel da TR-1000 (decisao do Luan, 10/10/2026).
//
// O playhead NAO vem do /estado (250 ms pulava steps a 128 BPM - F3): vem do
// /passo, um evento por step, pelo app.mjs (passo()).
import { h, texto, attr, slider, seletor, valor } from "../dom.mjs";
import { t } from "../i18n.mjs";

const VEL_FRACA = 80; // abaixo disso, a cor fraca (o painel: 66/74 fracos)
const N_AH = 8; // A..H; 8..11 sao as Fill 1..4
const PASSOS = Array.from({ length: 16 }, (_, i) => String(i + 1));
let celulas = [],
  acc = [],
  mutes = [],
  botEdita = [],
  botToca = [],
  botFill = [],
  botVel = [],
  botLayer = {},
  scales = [],
  loopBt = null,
  loopSteps = [];
let sel = null; // [track, step] no editor
let trkSel = null; // track com o FIRST/LAST aberto
let editando = false;
let ed = {},
  fl = {},
  tk = {};
let tocandoCols = []; // a coluna do playhead em cada track, ou -1

function kind(c) {
  if (c.a && c.alt) return c.vel < VEL_FRACA ? "altf" : "alt";
  if (c.a) return c.vel < VEL_FRACA ? "af" : "a";
  if (c.b) return c.vel < VEL_FRACA ? "bf" : "b";
  return "";
}

// sem "proprio", o FIRST/LAST do track nao vale: os selects ficam desligados
// (revisao do PR #8 - mexer neles mandava null e o valor sumia)
function habilitarTrk(sim) {
  attr(tk.first, "disabled", !sim);
  attr(tk.last, "disabled", !sim);
}

function selectSteps(aoMudar, rot) {
  const s = h(
    "select",
    { "aria-label": rot },
    PASSOS.map((n, i) => h("option", { value: i }, n)),
  );
  s.addEventListener("change", () => aoMudar(+s.value));
  return s;
}

const pressionado = (b, sim) => attr(b, "aria-pressed", sim ? "true" : "false");

export default {
  nome: "Pattern",

  montar(el, ctx) {
    const D = ctx.D;
    const self = this;

    // ── as variacoes: edita / toca / fill ─────────────────
    botEdita = D.variacoes.map((v, i) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          onclick: () => ctx.acao("exec", { tipo: "variacao", arg: i }),
        },
        v,
      ),
    );
    botToca = D.variacoes.slice(0, N_AH).map((v, i) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          onclick: (ev) => {
            // clique: toca so ela; Shift: soma/tira da chain (pelo menos uma)
            const m = ev.shiftKey ? ctx.E.variacoes ^ (1 << i) : 1 << i;
            if (m) ctx.acao("variacoes", { mascara: m });
          },
        },
        v,
      ),
    );
    // so FILL 1 e 2: o 3 e o 4 nao foram medidos (revisao do PR #7)
    botFill = [0, 1, 2, 3].map((n) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          disabled: n > 1,
          title: n > 1 ? t("FILL 3 e 4: ainda não medidos.") : null,
          onclick: () => ctx.acao("fill", { n }),
        },
        `Fill ${n + 1}`,
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
          pressionado(bEdit, editando);
        },
      },
      t("editar step"),
    );
    const bSessao = h(
      "button.bt.bt-peq",
      {
        type: "button",
        title: t(
          "Guarda uma foto do pattern e do kit SÓ no app (nunca na TR-1000). O RELOAD é no painel: SHIFT+MENU.",
        ),
        onclick: () => ctx.acao("sessao", {}),
      },
      t("salvar sessão"),
    );

    // ── a grade ───────────────────────────────────────────
    const grade = h("div.grade");
    D.tracks.forEach((tn, tr) => {
      const m = h(
        "button.mute",
        {
          type: "button",
          title: t("mute {t}", { t: tn }),
          onclick: () => ctx.acao("mudo", { track: tr }),
        },
        "M",
      );
      mutes.push(m);
      const rot = h(
        "button.rot",
        {
          type: "button",
          title: t("FIRST/LAST do {t}", { t: tn }),
          onclick: () => {
            trkSel = trkSel === tr ? null : tr;
            self.atualizar(ctx.E, ctx);
          },
        },
        tn,
      );
      grade.append(rot, m);
      celulas[tr] = [];
      for (let s = 0; s < 16; s++) {
        const c = h("button.cel", {
          type: "button",
          "aria-label": t("{t} step {s}", { t: tn, s: s + 1 }),
          onclick: (ev) => {
            if (ev.shiftKey || editando) {
              sel = [tr, s];
              self.atualizar(ctx.E, ctx);
            } else ctx.acao("step", { track: tr, step: s });
          },
          oncontextmenu: (ev) => {
            ev.preventDefault();
            sel = [tr, s];
            self.atualizar(ctx.E, ctx);
          },
        });
        if (s % 4 === 0) attr(c, "data-tempo", true);
        celulas[tr].push(c);
        grade.append(c);
      }
    });
    tocandoCols = D.tracks.map(() => -1);
    grade.append(
      h(
        "span.rot",
        { title: t("o accent é feito no painel da TR-1000") },
        "ACC",
      ),
      h("span"),
    );
    for (let s = 0; s < 16; s++) {
      const c = h("span.cel.acc");
      acc.push(c);
      grade.append(c);
    }
    grade.append(h("span"), h("span"));
    for (let s = 1; s <= 16; s++) grade.append(h("span.num", {}, String(s)));

    // ── o editor do step ──────────────────────────────────
    const campo = (nome) => (v) =>
      sel &&
      ctx.acao("campo_step", {
        track: sel[0],
        step: sel[1],
        nome,
        valor: v,
      });
    ed.titulo = h("h2", {}, t("editor do step"));
    ed.prob = slider({
      rot: "PROB",
      min: 0,
      max: 100,
      fmt: (v) => `${v}%`,
      aoMudar: ctx.espacado(campo("prob")),
    });
    ed.start = slider({
      rot: "START",
      min: -100,
      max: 100,
      fmt: (v) => (v > 0 ? `+${v}` : `${v}`),
      aoMudar: ctx.espacado(campo("start")),
    });
    ed.sub = seletor(D.sub_nomes, campo("sub"), "SUB");
    ed.cycle = seletor(D.cycle_nomes, campo("cycle"), "CYCLE");
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
    ed.altRot = h("label.fila", {}, ed.alt, t("som ALT (tracks simples)"));
    ed.secao = h(
      "div.secao.editor",
      {},
      h(
        "div.fila.entre",
        {},
        ed.titulo,
        h(
          "button.bt.bt-peq",
          {
            type: "button",
            onclick: () => {
              sel = null;
              self.atualizar(ctx.E, ctx);
            },
          },
          t("fechar"),
        ),
      ),
      h(
        "p.nota",
        {},
        t(
          'Shift-clique (ou clique-direito, ou o modo "editar step") num step escolhe qual editar.',
        ),
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

    // ── FIRST/LAST do track (clique no nome) ──────────────
    const mandaTrk = () =>
      trkSel !== null &&
      ctx.acao(
        "extremos_track",
        tk.sw.checked
          ? { track: trkSel, first: +tk.first.value, last: +tk.last.value }
          : { track: trkSel, first: null, last: null },
      );
    tk.titulo = h("h2");
    tk.sw = h("input", { type: "checkbox" });
    tk.sw.addEventListener("change", () => {
      habilitarTrk(tk.sw.checked);
      mandaTrk();
    });
    tk.first = selectSteps(mandaTrk, "FIRST");
    tk.last = selectSteps(mandaTrk, "LAST");
    tk.secao = h(
      "div.secao.editor",
      {},
      h(
        "div.fila.entre",
        {},
        tk.titulo,
        h(
          "button.bt.bt-peq",
          {
            type: "button",
            onclick: () => {
              trkSel = null;
              self.atualizar(ctx.E, ctx);
            },
          },
          t("fechar"),
        ),
      ),
      h(
        "div.fila",
        {},
        h("label.fila", {}, tk.sw, t("próprio")),
        h("span.fraco", {}, "FIRST"),
        tk.first,
        h("span.fraco", {}, "LAST"),
        tk.last,
      ),
      h(
        "p.nota",
        {},
        t(
          'Com "próprio" ligado, o track usa os seus FIRST/LAST; desligado, segue a variação.',
        ),
      ),
    );
    tk.secao.hidden = true;

    // ── a coluna do lado: STEP LOOP, Scale, FIRST/LAST ────
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
        { type: "button", "aria-label": t("segurar o step {n}", { n }) },
        n,
      );
      b.addEventListener("pointerdown", (ev) => {
        // so o botao principal, e com a maquina ligada (revisao do PR #8)
        if (ev.button !== 0 || !ctx.E.ligado) return;
        b.setPointerCapture?.(ev.pointerId);
        pressionado(b, true);
        ctx.acao("loop", { ligado: true, step: s });
      });
      const soltar = () => {
        if (b.getAttribute("aria-pressed") === "true") {
          pressionado(b, false);
          ctx.acao("loop", { ligado: false, step: s });
        }
      };
      b.addEventListener("pointerup", soltar);
      b.addEventListener("pointercancel", soltar);
      b.addEventListener("lostpointercapture", soltar);
      return b;
    });
    scales = D.scales.map((sc, n) =>
      h(
        "button.bt.bt-peq",
        { type: "button", onclick: () => ctx.acao("scale", { n }) },
        sc,
      ),
    );
    const mandaVar = () =>
      ctx.acao("extremos_var", {
        v: ctx.E.variacao,
        first: +fl.first.value,
        last: +fl.last.value,
      });
    fl.first = selectSteps(mandaVar, t("FIRST STEP da variação"));
    fl.last = selectSteps(mandaVar, t("LAST STEP da variação"));
    fl.rot = h("strong.mono");

    const lado = h(
      "div.lado",
      {},
      h(
        "div.secao",
        {},
        h("h2", {}, t("step loop")),
        h("div.toques", {}, loopBt),
        h("div.toques.loop", {}, loopSteps),
        h(
          "p.nota",
          {},
          t(
            "Segure um step: a máquina repete ele, e solta volta ao normal. O botão liga o modo; o LED do painel não acompanha.",
          ),
        ),
      ),
      h("div.secao", {}, h("h2", {}, t("scale")), h("div.toques", {}, scales)),
      h(
        "div.secao",
        {},
        h("h2", {}, t("first / last")),
        h(
          "div.fila",
          {},
          h("span.fraco", {}, t("variação")),
          fl.rot,
          h("span.fraco", {}, "FIRST"),
          fl.first,
          h("span.fraco", {}, "LAST"),
          fl.last,
        ),
      ),
    );

    const variacoes = h(
      "div.vars",
      {},
      h("span.fraco", {}, t("edita")),
      h("div.toques", {}, botEdita),
      h("span.fraco", {}, t("toca")),
      h("div.toques", {}, botToca),
      h("span.fraco", {}, t("fill")),
      h("div.toques", {}, botFill),
    );

    el.append(
      h(
        "div.pattern-corpo",
        {},
        h(
          "div.principal",
          {},
          h(
            "div.secao",
            {},
            variacoes,
            h(
              "p.nota",
              {},
              t(
                "edita: o que a grade mostra. toca: a chain (Shift-clique soma ou tira). fill: qual o FILL IN TRIG toca.",
              ),
            ),
            h(
              "div.fila",
              {},
              h("span.fraco", {}, t("velocity")),
              botVel,
              h("span.fraco", {}, t("layer")),
              Object.values(botLayer),
              bEdit,
              bSessao,
            ),
            h("div.grade-rolo", {}, grade),
            h(
              "p.nota",
              {},
              t(
                "Clique liga ou desliga o step, com a velocity e o layer escolhidos. Vermelho = layer A, verde = só layer B, roxo = ALT; o pontinho branco marca PROB, SUB, CYCLE ou START mexidos. Clique no nome do track para o FIRST/LAST dele.",
              ),
            ),
          ),
          ed.secao,
          tk.secao,
        ),
        lado,
      ),
    );
  },

  // um evento do /passo: so as colunas do playhead mudam
  passo(info) {
    if (!celulas.length) return;
    celulas.forEach((linha, tr) => {
      const col = !info.tocando
        ? -1
        : info.passos_trk
          ? info.passos_trk[tr]
          : info.passo;
      const antes = tocandoCols[tr];
      if (col === antes) return;
      if (antes >= 0 && linha[antes]) attr(linha[antes], "data-play", false);
      if (col >= 0 && linha[col]) attr(linha[col], "data-play", true);
      tocandoCols[tr] = col;
    });
  },

  atualizar(E, ctx) {
    if (!E.grade) return;
    const D = ctx.D;
    botEdita.forEach((b, i) => pressionado(b, i === E.variacao));
    botToca.forEach((b, i) => {
      pressionado(b, (E.variacoes >> i) & 1);
      attr(b, "data-tocando", !!E.tocando && E.tocando_var === i); // a que soa agora
    });
    botFill.forEach((b, n) => pressionado(b, n === E.fill));
    botVel.forEach((b, i) => pressionado(b, i === E.velocidade_idx));
    for (const [m, b] of Object.entries(botLayer))
      pressionado(b, m === E.modo_layer);
    E.grade.forEach((linha, tr) => {
      attr(mutes[tr], "data-mudo", !!(E.mudos || [])[tr]);
      linha.forEach((c, s) => {
        const el = celulas[tr][s];
        attr(el, "data-k", kind(c) || null);
        attr(el, "data-sel", sel && sel[0] === tr && sel[1] === s);
        attr(
          el,
          "data-extra",
          (c.a || c.b) &&
            c.prob !== null &&
            (c.prob < 100 || c.sub > 0 || c.cycle > 0 || c.start !== 0),
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
        t("editor · {t} · step {s} · var {v}", {
          t: D.tracks[tr],
          s: s + 1,
          v: D.variacoes[E.variacao],
        }),
      );
      ed.prob.set(c.prob);
      ed.start.set(c.start);
      valor(ed.sub, c.sub);
      valor(ed.cycle, c.cycle);
      ed.alt.checked = !!c.alt;
      ed.altRot.hidden = tr < 4;
    }

    tk.secao.hidden = trkSel === null;
    if (trkSel !== null) {
      texto(tk.titulo, t("FIRST/LAST do {t}", { t: D.tracks[trkSel] }));
      if (document.activeElement !== tk.sw) tk.sw.checked = !!E.trk_sw[trkSel];
      habilitarTrk(tk.sw.checked);
      valor(tk.first, E.first_trk[trkSel]);
      valor(tk.last, E.last_trk[trkSel]);
    }

    scales.forEach((b, n) => pressionado(b, n === E.scale));
    pressionado(loopBt, E.loop);
    // as Fill tambem tem FIRST/LAST no cabecalho (campos.N_VARS = 12)
    texto(fl.rot, D.variacoes[E.variacao]);
    valor(fl.first, E.first_var[E.variacao]);
    valor(fl.last, E.last_var[E.variacao]);
  },
};

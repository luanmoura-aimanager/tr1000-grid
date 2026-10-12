// mixer.mjs - os 10 canais: GAIN, PAN, RVB SND, DLY SND, LFO DTH e MUTE. Sao
// os mesmos parametros do CM-MC50: girar um knob na controladora move o
// fader daqui (na proxima leitura do kit, ~2 s), e mexer aqui faz o knob
// voltar a "pegar no caminho".
import { h, attr } from "../dom.mjs";
import { t } from "../i18n.mjs";
import { paramSlider, fmt } from "../params.mjs";

const COLUNAS = [
  ["gain", "GAIN", fmt.cru],
  ["pan", "PAN", fmt.pan],
  ["rvb", "RVB SND", fmt.pct1000],
  ["dly", "DLY SND", fmt.pct1000],
  ["lfo", "LFO DTH", fmt.bipolar],
];
let sliders = [],
  mutes = [];

export default {
  nome: "Mixer",

  montar(el, ctx) {
    const mesa = h(
      "div.mesa",
      {},
      h("span.cab", {}, t("track")),
      COLUNAS.map(([, r]) => h("span.cab", {}, r)),
      h("span.cab", {}, t("mute")),
    );
    ctx.D.tracks.forEach((t, tr) => {
      mesa.append(h("strong.mono", {}, t));
      for (const [k, , f] of COLUNAS) {
        const s = paramSlider(ctx, `${t.toLowerCase()}.${k}`, " ", f);
        s.el.classList.add("celula-mesa");
        s.el.firstChild.remove(); // o rotulo e o cabecalho da coluna
        sliders.push(s);
        mesa.append(s.el);
      }
      const m = h(
        "button.mute",
        { type: "button", onclick: () => ctx.acao("mudo", { track: tr }) },
        "M",
      );
      mutes.push(m);
      mesa.append(m);
    });
    el.append(
      h(
        "div.secao",
        {},
        h("h2", {}, t("mixer")),
        h("div.grade-rolo", {}, mesa),
        h(
          "p.nota",
          {},
          t("GAIN vai de −INF a +6 dB (0..661 na máquina). Os valores relêem a máquina a cada 2 s enquanto esta aba está aberta."),
        ),
      ),
    );
  },

  querKit: true, // a aba mostra o kit: o app pede a leitura ao motor

  atualizar(E) {
    sliders.forEach((s) => s.atualizar(E));
    mutes.forEach((m, tr) => attr(m, "data-mudo", !!(E.mudos || [])[tr]));
  },
};

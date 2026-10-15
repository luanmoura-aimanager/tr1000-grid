// ritmos.mjs - os ritmos prontos (biblioteca.py): escolher, ver as variacoes,
// escolher o kit e dar Play: o motor escreve no pattern que esta na tela as
// variacoes e a chain, o tempo, o kit e o mix (decisao do Luan, 15/10/2026).
// Antes, a foto da sessao; depois, o diario do Restaurar.
import { h, attr, texto } from "../dom.mjs";
import { t } from "../i18n.mjs";

const CHAVE_SEL = "tr1000-ritmo";
// steps por tempo (seminima) em cada Scale (campos.SCALES)
const PASSOS_POR_TEMPO = { "8th(T)": 3, "16th(T)": 6, "16th": 4, "32nd": 8 };

let D = null,
  ctx = null;
let sel = null; // o ritmo escolhido (o objeto de D.ritmos)
let varVista = null; // a variacao no preview
let kitN = null; // o kit do menu (comeca no sugerido pelo ritmo)
const el = {};

function ler(chave, padrao) {
  try {
    const v = localStorage.getItem(chave);
    return v === null ? padrao : JSON.parse(v);
  } catch (e) {
    return padrao;
  }
}
function guardar(chave, v) {
  try {
    localStorage.setItem(chave, JSON.stringify(v));
  } catch (e) {
    /* sem storage */
  }
}

function letrasDaChain(m) {
  return D.variacoes
    .slice(0, 8)
    .filter((_, i) => (m >> i) & 1)
    .join("");
}

// um char do preview -> a cor da celula (as mesmas do grid)
const COR = { X: "a", x: "a", o: "af", g: "af", R: "alt", r: "alt", q: "altf" };

function montarLista() {
  const filtro = el.filtro.value.trim().toLowerCase();
  el.lista.replaceChildren();
  const grupos = new Map();
  for (const r of D.ritmos) {
    const alvo = `${r.nome} ${r.estilo} ${r.kit}`.toLowerCase();
    if (filtro && !alvo.includes(filtro)) continue;
    if (!grupos.has(r.estilo)) grupos.set(r.estilo, []);
    grupos.get(r.estilo).push(r);
  }
  for (const [estilo, rs] of grupos) {
    el.lista.append(
      h("h3.estilo", {}, estilo),
      h(
        "div.ritmos-grupo",
        {},
        rs.map((r) =>
          h(
            "button.bt.bt-peq.ritmo-bt",
            {
              type: "button",
              "aria-pressed": sel && sel.id === r.id ? "true" : "false",
              onclick: () => escolher(r),
            },
            r.nome,
          ),
        ),
      ),
    );
  }
  if (!grupos.size)
    el.lista.append(h("p.nota", {}, t("nenhum ritmo com esse filtro")));
}

function escolher(r) {
  sel = r;
  varVista = Object.keys(r.variacoes)[0];
  kitN = r.kit_n;
  guardar(CHAVE_SEL, r.id);
  montarLista();
  montarSel();
}

function montarPreview() {
  const linhas = sel.variacoes[varVista];
  const g = h("div.mini-grade");
  g.style.setProperty("--n", sel.last);
  D.tracks.forEach((nome, tr) => {
    g.append(h("span.rot.mono", {}, nome));
    [...linhas[tr]].forEach((c, s) => {
      const cel = h("span.cel.mini");
      if (COR[c]) attr(cel, "data-k", COR[c]);
      else if (s % PASSOS_POR_TEMPO[sel.scale] === 0)
        attr(cel, "data-tempo", true);
      g.append(cel);
    });
  });
  el.preview.replaceChildren(g);
  el.abasVar
    .querySelectorAll("button")
    .forEach((b) =>
      attr(b, "aria-pressed", b.dataset.v === varVista ? "true" : "false"),
    );
}

function montarSel() {
  if (!sel) {
    el.sel.replaceChildren(h("p.nota", {}, t("Escolha um ritmo na lista.")));
    return;
  }
  const r = sel;
  el.abasVar = h(
    "div.toques",
    {},
    Object.keys(r.variacoes).map((v) =>
      h(
        "button.bt.bt-peq",
        {
          type: "button",
          "data-v": v,
          onclick: () => {
            varVista = v;
            montarPreview();
          },
        },
        v,
      ),
    ),
  );
  el.preview = h("div.grade-rolo");
  el.play = h("button.bt", { type: "button", onclick: tocar }, `▶ ${t("Play")}`);
  el.kit = h(
    "select",
    { "aria-label": t("kit") },
    D.kits
      .map((nome, n) => [nome, n])
      .filter(([nome]) => nome)
      .map(([nome, n]) =>
        h(
          "option",
          { value: n },
          `${n + 1} ${nome}${n === r.kit_n ? ` (${t("sugerido")})` : ""}`,
        ),
      ),
  );
  el.kit.value = String(kitN);
  el.kit.addEventListener("change", () => {
    kitN = +el.kit.value;
  });
  el.sel.replaceChildren(
    h("h2", {}, r.nome),
    h(
      "p.mono.fraco",
      {},
      `${r.estilo} · ${r.bpm} BPM · ${t("kit")} ${r.kit_n + 1} ${r.kit} · Scale ${r.scale} · LAST ${r.last} · chain ${letrasDaChain(r.chain)}`,
    ),
    r.obs ? h("p.nota", {}, r.obs) : null,
    h("p.nota", {}, `${t("fonte")}: ${r.fonte}`),
    el.abasVar,
    el.preview,
    h("div.fila", {}, el.kit, el.play),
    h(
      "p.nota",
      {},
      t(
        "O Play escreve no pattern da tela as variações e a chain, o BPM, o kit e o mix (só na memória: o WRITE é no painel). Antes, a foto da sessão vai para o app; o Restaurar devolve o que estava.",
      ),
    ),
  );
  montarPreview();
}

function tocar() {
  if (!sel) return;
  ctx.acao("ritmo", { id: sel.id, kit: kitN });
}

const FASES = {
  foto: "tirando a foto da sessão…",
  kit: "trocando o kit…",
  lendo: "lendo o pattern…",
  escrevendo: "escrevendo…",
  pronto: "pronto",
  falhou: "falhou",
  desfazendo: "desfazendo…",
  desfeito: "desfeito",
};

export default {
  nome: "Ritmos",

  montar(painel, c) {
    ctx = c;
    D = c.D;
    el.filtro = h("input.filtro", {
      type: "search",
      placeholder: t("filtrar (nome, estilo, kit)"),
      "aria-label": t("filtrar (nome, estilo, kit)"),
    });
    el.filtro.addEventListener("input", montarLista);
    el.lista = h("div.ritmos-lista");
    el.sel = h("div.secao");
    el.status = h("p.mono");
    el.barra = h("progress", { max: 1, value: 0 });
    el.avisos = h("ul.avisos");
    el.desfazer = h(
      "button.bt",
      { type: "button", onclick: () => ctx.acao("desfazer_ritmo", {}) },
      t("Restaurar"),
    );
    el.desfazerNome = h("span.fraco");
    painel.append(
      h(
        "div.ritmos-corpo",
        {},
        h(
          "div.secao",
          {},
          h("h2", {}, t("ritmos")),
          el.filtro,
          el.lista,
          h(
            "p.nota",
            {},
            t(
              "Nenhum ritmo foi ouvido na TR-1000 ainda: a fonte de cada um está no ritmo, e o som é o ROTEIRO-F5.",
            ),
          ),
        ),
        h(
          "div.lado",
          {},
          el.sel,
          h(
            "div.secao",
            {},
            h("h2", {}, t("escrita")),
            el.status,
            el.barra,
            el.avisos,
            h("div.fila", {}, el.desfazer, el.desfazerNome),
          ),
        ),
      ),
    );
    const id = ler(CHAVE_SEL, null);
    sel = D.ritmos.find((r) => r.id === id) || null;
    if (sel) {
      varVista = Object.keys(sel.variacoes)[0];
      kitN = sel.kit_n;
    }
    montarLista();
    montarSel();
  },

  atualizar(E) {
    const r = E.ritmo;
    if (r) {
      texto(
        el.status,
        `${r.nome}: ${t(FASES[r.fase] || r.fase)}${r.total ? ` (${r.feito}/${r.total})` : ""}`,
      );
      attr(el.barra, "max", Math.max(1, r.total));
      el.barra.value =
        r.fase === "pronto" || r.fase === "desfeito"
          ? Math.max(1, r.total)
          : r.feito;
      const avisos = (r.avisos || []).join("\n");
      if (el.avisos.dataset.txt !== avisos) {
        el.avisos.dataset.txt = avisos;
        el.avisos.replaceChildren(
          ...(r.avisos || []).map((a) => h("li", {}, a)),
        );
      }
    } else {
      texto(el.status, t("nada escrito ainda"));
    }
    const ocupado =
      r &&
      ["foto", "kit", "lendo", "escrevendo", "desfazendo"].includes(r.fase);
    attr(el.desfazer, "disabled", !E.ligado || !E.ritmo_desfazer || ocupado);
    texto(el.desfazerNome, E.ritmo_desfazer || "");
    if (el.play) attr(el.play, "disabled", !E.ligado || ocupado);
  },
};

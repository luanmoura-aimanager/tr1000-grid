// dom.mjs - o minimo para montar DOM sem framework (do tr8s-grid).
export const $ = (s, r = document) => r.querySelector(s);

/** h("button.bt", {onclick, "aria-pressed": "true"}, "texto", filho) */
export function h(tag, props = {}, ...filhos) {
  const [nome, ...cls] = String(tag).split(".");
  const el = document.createElement(nome || "div");
  if (cls.length) el.className = cls.join(" ");
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on") && typeof v === "function")
      el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className += " " + v;
    else if (k === "texto") el.textContent = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const f of filhos.flat()) {
    if (f === null || f === undefined || f === false) continue;
    el.append(f.nodeType ? f : document.createTextNode(String(f)));
  }
  return el;
}

/** Escreve so quando muda. */
export function texto(el, v) {
  const s = v === null || v === undefined ? "" : String(v);
  if (el.textContent !== s) el.textContent = s;
}
export function attr(el, k, v) {
  if (v === null || v === undefined || v === false) {
    if (el.hasAttribute(k)) el.removeAttribute(k);
  } else {
    const s = v === true ? "" : String(v);
    if (el.getAttribute(k) !== s) el.setAttribute(k, s);
  }
}

/** Atualiza um input SO se o usuario nao esta mexendo nele agora. */
export function valor(input, v) {
  if (v === null || v === undefined) return;
  if (document.activeElement === input || input.dataset.arrastando === "1")
    return;
  if (String(input.value) !== String(v)) input.value = v;
}

/** Slider com rotulo e leitura: {rot, min, max, passo, fmt, aoMudar} */
export function slider({ rot, min, max, passo = 1, fmt = (v) => v, aoMudar }) {
  const leitura = h("span.leitura.mono");
  const inp = h("input", {
    type: "range",
    min,
    max,
    step: passo,
    "aria-label": rot,
  });
  inp.addEventListener("pointerdown", () => (inp.dataset.arrastando = "1"));
  inp.addEventListener("pointerup", () => (inp.dataset.arrastando = "0"));
  inp.addEventListener("input", () => {
    texto(leitura, fmt(+inp.value));
    aoMudar(+inp.value);
  });
  const el = h("label.slider", {}, h("span.rot", {}, rot), inp, leitura);
  return {
    el,
    inp,
    set(v, ativo = true) {
      attr(el, "data-inativo", !ativo);
      if (v === null || v === undefined) {
        texto(leitura, "—");
        return;
      }
      valor(inp, v);
      if (inp.dataset.arrastando !== "1") texto(leitura, fmt(v));
    },
    rotulo(r) {
      texto(el.firstChild, r);
    },
  };
}

/** Select a partir de uma lista de nomes (valor = indice). */
export function seletor(nomes, aoMudar, rot) {
  const s = h(
    "select",
    { "aria-label": rot || "" },
    nomes.map((n, i) => h("option", { value: i }, n)),
  );
  s.addEventListener("change", () => aoMudar(+s.value));
  return s;
}

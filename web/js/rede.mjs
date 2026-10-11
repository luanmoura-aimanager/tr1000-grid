// rede.mjs - falar com o servidor.py. O token vem do /token (que exige o
// cookie HttpOnly que a propria pagina recebeu) e vai num header proprio em
// todo POST - um <form> de outro site nao consegue mandar header.
let token = null;

async function pegarToken() {
  const r = await fetch("/token", { credentials: "same-origin" });
  if (!r.ok) throw new Error("sem sessao - recarregue a pagina (Cmd+R)");
  token = (await r.json()).token;
}

async function postar(rota, corpo) {
  if (!token) await pegarToken();
  const r = await fetch(rota, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-TR1000-Token": token },
    body: JSON.stringify(corpo),
  });
  const j = await r.json().catch(() => ({}));
  if (r.status === 403) token = null; // servidor reiniciou: pega de novo
  if (!r.ok) throw new Error(j.erro || `erro ${r.status}`);
  return j;
}

export const acao = (nome, args = {}) =>
  postar("/acao", { acao: nome, ...args });
export const ligar = (sim) => postar("/ligar", { ligar: !!sim });

export async function estado() {
  const r = await fetch("/estado", {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`estado ${r.status}`);
  return r.json();
}

export async function dados() {
  const r = await fetch("/dados", { credentials: "same-origin" });
  return r.json();
}

// Para sliders: manda no maximo a cada `ms`, e sempre o ultimo valor.
export function espacado(fn, ms = 80) {
  let ultimo = null,
    timer = null;
  return (...args) => {
    ultimo = args;
    if (timer) return;
    fn(...ultimo);
    timer = setTimeout(() => {
      timer = null;
      if (ultimo !== args) fn(...ultimo);
    }, ms);
  };
}

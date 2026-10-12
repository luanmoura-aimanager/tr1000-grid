// ptn.mjs - o que se digita no PTN do topo -> o x do pattern (0..127), que
// vira o Program Change (motor.trocar_pattern). Modulo a parte para o teste
// rodar no node sem DOM.

// "1-05" (banco-numero, como o visor) ou "37" (1..128) -> x 0..127, ou null
export function xDoPattern(s) {
  const m = String(s)
    .trim()
    .match(/^(\d)\s*-\s*(\d{1,2})$/);
  if (m) {
    const b = +m[1],
      n = +m[2];
    return b >= 1 && b <= 8 && n >= 1 && n <= 16 ? (b - 1) * 16 + n - 1 : null;
  }
  if (/^\d{1,3}$/.test(String(s).trim())) {
    const n = +s;
    return n >= 1 && n <= 128 ? n - 1 : null;
  }
  return null;
}

// "124.5" ou "124,5" -> 12450 (BPM x 100, como a maquina guarda), ou null
// fora de 40..300
export function x100DoBpm(s) {
  const t = String(s).trim().replace(",", ".");
  if (!/^\d{2,3}(\.\d{1,2})?$/.test(t)) return null;
  const v = Math.round(parseFloat(t) * 100);
  return v >= 4000 && v <= 30000 ? v : null;
}

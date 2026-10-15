// i18n.mjs - a tela em portugues (padrao) ou ingles (pedido do Luan,
// 12/10/2026). Os nomes da MAQUINA (BD, PROB, SUB, os types do MASTER FX...)
// nao se traduzem: sao os do painel. Trocar de lingua recarrega a pagina - os
// modulos montam tudo de novo com t(), sem cada aba ter que se repintar.
const CHAVE = "tr1000-lingua";

let lingua = "pt";
try {
  const salva = localStorage.getItem(CHAVE);
  if (salva === "en" || salva === "pt") lingua = salva;
} catch (e) {
  /* sem storage: fica o padrao */
}

export const linguaAtual = () => lingua;

export function trocarLingua(nova) {
  try {
    localStorage.setItem(CHAVE, nova);
  } catch (e) {
    /* sem storage: vale so ate recarregar */
  }
  location.reload();
}

const EN = {
  // topo
  ptn: "ptn",
  bpm: "bpm",
  edita: "edit",
  toca: "play",
  step: "step",
  "Desligado: a serial está livre para o TR-1000 App da Roland. Aperte ON para o Controller assumir a máquina, os Launchpads e as controladoras.":
    "Off: the serial port is free for Roland's TR-1000 App. Press ON for the Controller to take over the machine, the Launchpads and the knob controllers.",
  modo: "mode",
  chuva: "rain",
  ambiente: "ambient",
  "standby: soltando a serial; os Launchpads fazem ondas...":
    "standby: releasing the serial port; the Launchpads make waves...",
  "Standby ({m}): a serial está livre para o TR-1000 App da Roland, e os Launchpads fazem ondas. Toque um pad para soltar mais uma. ON volta ao grid.":
    "Standby ({m}): the serial port is free for Roland's TR-1000 App, and the Launchpads make waves. Touch a pad to drop another one. ON goes back to the grid.",
  "ligando: serial, Launchpads e controladoras...":
    "turning on: serial, Launchpads and controllers...",
  "desligando: soltando a serial...":
    "turning off: releasing the serial port...",
  "sem contato com o servidor - ele esta no ar? (python3 servidor.py)":
    "no contact with the server - is it running? (python3 servidor.py)",
  "sem contato com o servidor": "no contact with the server",
  seções: "sections",
  "trocar o pattern": "change pattern",
  "Digite o pattern (1-05, ou 1..128) e Enter. Esc cancela.":
    "Type the pattern (1-05, or 1..128) and Enter. Esc cancels.",
  "pattern inválido: use banco-número (1-05) ou 1..128":
    "invalid pattern: use bank-number (1-05) or 1..128",
  "pedindo o pattern {p} (Program Change)...":
    "asking for pattern {p} (Program Change)...",
  "mudar o BPM": "change the BPM",
  "Digite o BPM (ex.: 124.5, de 40 a 300) e Enter. Esc cancela.":
    "Type the BPM (e.g. 124.5, 40 to 300) and Enter. Esc cancels.",
  "BPM inválido: de 40 a 300, até duas casas (124.5)":
    "invalid BPM: 40 to 300, up to two decimals (124.5)",
  "tocando: a variação que as notas da máquina dizem (? = não dá para saber). Parada: a chain.":
    "playing: the variation the machine's notes point to (? = can't tell). Stopped: the chain.",
  // abas
  Pattern: "Pattern",
  Mixer: "Mixer",
  Efeitos: "Effects",
  // pattern
  variação: "variation",
  fill: "fill",
  velocity: "velocity",
  layer: "layer",
  "editar step": "edit step",
  "salvar sessão": "save session",
  "Guarda uma foto do pattern e do kit SÓ no app (nunca na TR-1000). O RELOAD é no painel: SHIFT+MENU.":
    "Saves a snapshot of the pattern and kit in the app ONLY (never on the TR-1000). RELOAD is on the panel: SHIFT+MENU.",
  "mute {t}": "mute {t}",
  "{t} step {s}": "{t} step {s}",
  "o accent é feito no painel da TR-1000": "accent is set on the TR-1000 panel",
  "FIRST/LAST do {t}": "{t} FIRST/LAST",
  "Clique liga ou desliga o step, com a velocity e o layer escolhidos. Vermelho = layer A, verde = só layer B, roxo = ALT; o pontinho branco marca PROB, SUB, CYCLE ou START mexidos. Clique no nome do track para o FIRST/LAST dele.":
    "Click toggles the step with the chosen velocity and layer. Red = layer A, green = layer B only, purple = ALT; the white dot marks a changed PROB, SUB, CYCLE or START. Click a track name for its FIRST/LAST.",
  "edita: o que a grade mostra. toca: a chain (Shift-clique soma ou tira). fill: qual o FILL IN TRIG toca.":
    "edit: what the grid shows. play: the chain (Shift-click adds or removes). fill: which one FILL IN TRIG plays.",
  "FILL 3 e 4: ainda não medidos.": "FILL 3 and 4: not measured yet.",
  "editor do step": "step editor",
  "editor · {t} · step {s} · var {v}": "editor · {t} · step {s} · var {v}",
  'Shift-clique (ou clique-direito, ou o modo "editar step") num step escolhe qual editar.':
    'Shift-click (or right-click, or "edit step" mode) on a step picks the one to edit.',
  "som ALT (tracks simples)": "ALT sound (single tracks)",
  fechar: "close",
  // performance (agora dentro do Pattern)
  "step loop": "step loop",
  "segurar o step {n}": "hold step {n}",
  "Segure um step: a máquina repete ele, e solta volta ao normal. O botão liga o modo; o LED do painel não acompanha.":
    "Hold a step: the machine repeats it, and releasing goes back to normal. The button turns the mode on; the panel LED does not follow.",
  scale: "scale",
  "first / last": "first / last",
  "FIRST STEP da variação": "variation FIRST STEP",
  "LAST STEP da variação": "variation LAST STEP",
  track: "track",
  próprio: "own",
  "{t} com FIRST/LAST próprio": "{t} with its own FIRST/LAST",
  "FIRST do {t}": "{t} FIRST",
  "LAST do {t}": "{t} LAST",
  'Com "próprio" ligado, o track usa os seus FIRST/LAST; desligado, segue a variação.':
    'With "own" on, the track uses its own FIRST/LAST; off, it follows the variation.',
  // mixer
  mixer: "mixer",
  mute: "mute",
  "GAIN vai de −INF a +6 dB (0..661 na máquina). Os valores relêem a máquina a cada 2 s enquanto esta aba está aberta.":
    "GAIN goes from −INF to +6 dB (0..661 on the machine). Values are re-read from the machine every 2 s while this tab is open.",
  // efeitos
  reverb: "reverb",
  delay: "delay",
  "lfo do kit": "kit lfo",
  "master fx": "master fx",
  "side chain": "side chain",
  "routing matrix": "routing matrix",
  "O LFO só se ouve com um TARGET escolhido no App (Mod (Kit)).":
    "The LFO is only heard with a TARGET chosen in the App (Mod (Kit)).",
  "O botão ON do MASTER FX fica no painel da TR-1000.":
    "The MASTER FX ON button is on the TR-1000 panel.",
  "Cada som vai para THROUGH, MASTER FX ou ANALOG FX.":
    "Each sound goes to THROUGH, MASTER FX or ANALOG FX.",
  "{f} para {d}": "{f} to {d}",
  "preset do side chain": "side chain preset",
  "Pump clássico": "Classic pump",
  "Pump forte": "Heavy pump",
  "Dança no CH": "Dancing CH",
  "Half-time pump": "Half-time pump",
  "Respiro na caixa": "Snare breath",
  "Reverb limpo": "Clean reverb",
  "Delay que respira": "Breathing delay",
  "Gate picotado": "Chopped gate",
  Desligado: "Off",
  // ritmos
  Ritmos: "Rhythms",
  ritmos: "rhythms",
  escrita: "writing",
  kit: "kit",
  fonte: "source",
  Play: "Play",
  Restaurar: "Restore",
  sugerido: "suggested",
  "Escolha um ritmo na lista.": "Pick a rhythm from the list.",
  "nenhum ritmo com esse filtro": "no rhythm matches this filter",
  "filtrar (nome, estilo, kit)": "filter (name, style, kit)",
  "nada escrito ainda": "nothing written yet",
  "O Play escreve no pattern da tela as variações e a chain, o BPM, o kit e o mix (só na memória: o WRITE é no painel). Antes, a foto da sessão vai para o app; o Restaurar devolve o que estava.":
    "Play writes the variations and the chain, the BPM, the kit and the mix into the pattern on screen (memory only: WRITE is on the panel). Before that, the session snapshot goes to the app; Restore brings back what was there.",
  "Nenhum ritmo foi ouvido na TR-1000 ainda: a fonte de cada um está no ritmo, e o som é o ROTEIRO-F5.":
    "No rhythm has been heard on the TR-1000 yet: each one carries its source, and the sound check is ROTEIRO-F5.",
  "tirando a foto da sessão…": "taking the session snapshot…",
  "trocando o kit…": "changing the kit…",
  "lendo o pattern…": "reading the pattern…",
  "escrevendo…": "writing…",
  pronto: "done",
  falhou: "failed",
  "desfazendo…": "undoing…",
  desfeito: "undone",
  "Arraste os pontos: o de baixo é o HOLD e o MSTR DEP, o de cima o RELEASE, o do meio a CURVE. Os presets são palpites crus, a acertar de ouvido.":
    "Drag the points: the bottom one is HOLD and MSTR DEP, the top one RELEASE, the middle one CURVE. The presets are raw guesses, to be tuned by ear.",
};

/** t("texto em portugues", {variaveis}) -> na lingua atual. Sem traducao,
 * volta o portugues (nunca uma chave crua na tela). */
export function t(pt, vars = {}) {
  const s = lingua === "en" && EN[pt] !== undefined ? EN[pt] : pt;
  return s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
}

// As linhas do rodape vem do Python, em portugues. As mais comuns ganham
// traducao por padrao; o resto aparece como veio.
const LOG_EN = [
  [
    /^(\S+ )?TR-1000 conectada, versao (.*)$/,
    "$1TR-1000 connected, version $2",
  ],
  [/^(\S+ )?pattern (\S+) \(x (\d+)\)$/, "$1pattern $2 (x $3)"],
  [
    /^(\S+ )?desligado: a serial esta livre para o TR-1000 App$/,
    "$1off: the serial port is free for the TR-1000 App",
  ],
  [
    /^(\S+ )?\(!\) nao deu para ligar: o TR-1000 App esta aberto (.*)$/,
    "$1(!) could not turn on: the TR-1000 App is open $2",
  ],
  [
    /^(\S+ )?\(!\) a TR-1000 nao ligou - veja a linha acima \(App da Roland aberto\?\)$/,
    "$1(!) the TR-1000 did not turn on - see the line above (Roland App open?)",
  ],
  [/^(\S+ )?controladoras: (.*)$/, "$1controllers: $2"],
  [/^(\S+ )?standby \((\w+)\): .*$/,
    "$1standby ($2): the serial port is free; the Launchpads make waves and a touch drops another one"],
  [
    /^(\S+ )?sessao salva no app: (\S+) \((.*)\)$/,
    "$1session saved in the app: $2 ($3)",
  ],
  [
    /^(\S+ )?pattern (\S+) pedido \(Program Change (\d+), canal (\d+)\)$/,
    "$1pattern $2 requested (Program Change $3, channel $4)",
  ],
  [/^(\S+ )?servidor no ar em (.*)$/, "$1server up at $2"],
  [
    /^(\S+ )?kit (\d+) (.*) pedido \(Program Change (\d+), canal (\d+)\)$/,
    "$1kit $2 $3 requested (Program Change $4, channel $5)",
  ],
  [
    /^(\S+ )?kit (\S+) \(bloco 3 \[2\.\.4\] = (.*)\)$/,
    "$1kit $2 (block 3 [2..4] = $3)",
  ],
  [/^(\S+ )?ritmo (.*) desfeito$/, "$1rhythm $2 undone"],
  [/^(\S+ )?ritmo (.*) escrito no (\S+): (\d+) escritas \((\d+) de mix\)$/,
    "$1rhythm $2 written to $3: $4 writes ($5 mix)"],
  [
    /^(\S+ )?\(!\) escrita recusada\/sem resposta: (.*)$/,
    "$1(!) write refused/no answer: $2",
  ],
  [/^(\S+ )?\(!\) ligue \(ON\) antes$/, "$1(!) turn ON first"],
];

export function tLog(linha) {
  if (lingua !== "en") return linha;
  for (const [re, en] of LOG_EN)
    if (re.test(linha)) return linha.replace(re, en);
  return linha;
}

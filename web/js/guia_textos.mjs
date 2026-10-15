// guia_textos.mjs - os textos da aba Guia, em pt e en lado a lado, e as
// constantes do motor que o /dados nao manda. So dados, sem DOM: o testes.py
// importa pelo node e confere (TesteGuia) que todo {pt} tem {en} e que as
// constantes batem com campos.py e motor.py. "**x**" e negrito; "{x}" e
// trocado pelo guia.mjs.

// ── do motor (copias conferidas pelo TesteGuia) ──────────────
export const PAR_PARAMS = ["prob", "sub", "cycle", "start", "vel", "alt"]; // campos.PAR_PARAMS
export const NIVEIS_PAR = {
  // campos.NIVEIS_PAR: de baixo para cima
  prob: [0, 14, 28, 43, 57, 71, 86, 100],
  sub: [0, 1, 2, 3, 4, 5, 6, 9],
  cycle: [0, 1, 2, 3, 6, 28, 36, 37],
  start: [-100, -67, -33, 0, 25, 50, 75, 100],
  vel: [10, 30, 50, 66, 80, 100, 110, 127],
};
export const PAR_ESCOLHA = ["sub", "cycle"]; // campos.PAR_ESCOLHA
export const PERF = {
  mute: 0,
  chain: 1,
  loop: 2,
  last: 3,
  scale: 4,
  fills: [12, 13],
}; // motor.PERF_*
export const ROUT = {
  sc1: 4,
  sc2: 5,
  chaves: 7,
  polarity: [0, 1],
  hld: [3, 4],
}; // motor.ROUT_*
export const FONTES_ROTA = [
  "BD",
  "SD",
  "LT",
  "HT",
  "RS",
  "HC",
  "CH",
  "OH",
  "CC",
  "RC",
  "RVB",
  "DLY",
  "EXT",
]; // motor.FONTES_ROTA
export const VEL_FRACA = 80; // motor.VEL_FRACA_ABAIXO
export const TRACKS_LAYER = 4; // motor.TRACKS_LAYER: BD SD LT HT
export const CENA_CCS = [89, 79, 69, 59, 49, 39, 29, 19]; // launchpad.CENA_CCS
export const FUNC_CCS = [91, 92, 93, 94, 95, 96, 97, 98]; // launchpad.FUNC_CCS
export const PLAY = 6; // o playhead do exemplo, parado no step 7

// ── os textos ────────────────────────────────────────────────
export const T = {
  eyebrow: {
    pt: "layout A · o código de 15/10/2026",
    en: "layout A · the code as of 15/10/2026",
  },
  titulo: { pt: "Guia dos Launchpads", en: "Launchpad guide" },
  lede: {
    pt: "Os dois Launchpad Mini MK3 viram um grid de 16 steps × 8 linhas que edita o pattern dentro da TR-1000. Quem toca é a máquina; os pads só escrevem nela. A bancada abaixo é uma simulação: clique em qualquer pad ou botão para ver o que ele faz naquela página. **Ela nunca escreve na máquina.**",
    en: "The two Launchpad Mini MK3 become a 16-step × 8-row grid that edits the pattern inside the TR-1000. The machine does the playing; the pads only write to it. The bench below is a simulation: click any pad or button to see what it does on that page. **It never writes to the machine.**",
  },
  antes: { pt: "Antes de tocar", en: "Before you play" },
  passos: [
    {
      n: { pt: "1 · FECHE O APP", en: "1 · CLOSE THE APP" },
      d: {
        pt: "Feche o TR-1000 App da Roland. O ON recusa com ele aberto, porque os dois brigariam pela mesma serial.",
        en: "Close Roland's TR-1000 App. ON refuses while it is open, because both would fight over the same serial port.",
      },
    },
    {
      n: { pt: "2 · APERTE ON", en: "2 · PRESS ON" },
      d: {
        pt: "Aperte **ON** no topo desta tela. Ele liga a máquina, os dois Launchpads e as controladoras de knobs. Em **OFF** os Launchpads apagam e não respondem.",
        en: "Press **ON** at the top of this screen. It connects the machine, both Launchpads and the knob controllers. In **OFF** the Launchpads go dark and do not respond.",
      },
    },
    {
      n: { pt: "3 · A POSIÇÃO", en: "3 · ORIENTATION" },
      d: {
        pt: "O esquerdo fica girado 90° anti-horário, o direito normal. Trocou um aparelho ou a porta USB? Rode **python3 lp_tr1000.py learn** de novo.",
        en: "The left one is rotated 90° counter-clockwise, the right one sits normally. Swapped a unit or a USB port? Run **python3 lp_tr1000.py learn** again.",
      },
    },
    {
      n: { pt: "4 · ELE SEGUE A MÁQUINA", en: "4 · IT FOLLOWS THE MACHINE" },
      d: {
        pt: "O grid relê a TR-1000 a cada meio segundo. O que você muda no painel, na aba Pattern ou no ▶ Play da aba Ritmos aparece nos pads sozinho.",
        en: "The grid re-reads the TR-1000 every half second. Whatever you change on the panel, in the Pattern tab or with ▶ Play in the Rhythms tab shows up on the pads by itself.",
      },
    },
  ],
  bancada: { pt: "A bancada", en: "The bench" },
  bancadaNota: {
    pt: "Feita a partir do motor.py. Os pads respondem como os de verdade: liga e apaga steps, troca de página, velocity, layer e banco. Os steps de BD e SD são os do pattern 1-01; o resto é exemplo. O playhead está parado no step 7 para mostrar a cor dele.",
    en: "Built from motor.py. The pads respond like the real ones: steps on and off, pages, velocity, layer and bank. The BD and SD steps are those of pattern 1-01; the rest is an example. The playhead sits still on step 7 to show its color.",
  },
  voltar: { pt: "Voltar ao exemplo", en: "Back to the example" },
  shift: {
    pt: 'Na PERF, **Shift**+clique numa variação faz o papel de "segurar uma e tocar a outra". Segure o clique para o STEP LOOP.',
    en: 'On PERF, **Shift**+click on a variation stands in for "hold one and tap the other". Hold the click for STEP LOOP.',
  },
  paginas: {
    steps: { pt: "Steps", en: "Steps" },
    par: { pt: "PAR", en: "PAR" },
    perf: { pt: "PERF", en: "PERF" },
    rout: { pt: "ROUT", en: "ROUT" },
    standby: { pt: "Standby (chuva)", en: "Standby (rain)" },
  },
  pagina: { pt: "Página {p}", en: "Page {p}" },
  esquerdo: {
    pt: "esquerdo · girado 90° anti-horário",
    en: "left · rotated 90° counter-clockwise",
  },
  direito: { pt: "direito · normal", en: "right · normal" },
  lpE: { pt: "Launchpad esquerdo", en: "Left Launchpad" },
  lpD: { pt: "Launchpad direito", en: "Right Launchpad" },
  status: {
    ok: { pt: "testado na máquina", en: "tested on the machine" },
    part: { pt: "em parte", en: "partly" },
    no: { pt: "não testado", en: "not tested" },
  },

  // onde fica cada botao
  lugar: {
    topE: {
      pt: "Esquerdo · topo, {n}º · CC {cc}",
      en: "Left · top, #{n} · CC {cc}",
    },
    ladoE: {
      pt: "Esquerdo · lateral, {n}º de cima · CC {cc}",
      en: "Left · side, #{n} from the top · CC {cc}",
    },
    topD: {
      pt: "Direito · topo, {n}º · CC {cc}",
      en: "Right · top, #{n} · CC {cc}",
    },
    ladoD: {
      pt: "Direito · borda, {n}º de cima · CC {cc}",
      en: "Right · edge, #{n} from the top · CC {cc}",
    },
    logo: { pt: "Logo · CC 99", en: "Logo · CC 99" },
    pad: { pt: "Pad · linha {l}, step {s}", en: "Pad · row {l}, step {s}" },
    padCol: {
      pt: "Pad · linha {l}, coluna {s}",
      en: "Pad · row {l}, column {s}",
    },
    altura: {
      pt: "Pad · altura {l}, step {s}",
      en: "Pad · height {l}, step {s}",
    },
  },

  // as fichas: o que cada coisa faz
  f: {
    logoE: {
      t: { pt: "O canto do esquerdo", en: "The left corner" },
      d: [
        {
          pt: 'Só um LED, sem botão embaixo: apertar não faz nada. A etiqueta "VAR ▸" aponta para as variações do topo.',
          en: 'Just an LED with no switch under it: pressing does nothing. The "VAR ▸" sticker points at the variations along the top.',
        },
      ],
    },
    logoD: {
      t: { pt: "O canto do direito", en: "The right corner" },
      d: [
        {
          pt: 'Só um LED, sem botão embaixo: apertar não faz nada. A etiqueta "VEL ▾" aponta para a velocity da borda.',
          en: 'Just an LED with no switch under it: pressing does nothing. The "VEL ▾" sticker points at the velocity column on the edge.',
        },
      ],
    },
    standbyBt: {
      t: { pt: "Botão em standby", en: "Button in standby" },
      d: [
        {
          pt: "Em chuva ou ambiente, os botões não fazem nada. Volte com ON no topo.",
          en: "In rain or ambient, the buttons do nothing. Go back with ON at the top.",
        },
      ],
    },
    standbyPad: {
      t: { pt: "Uma onda daqui", en: "A wave from here" },
      d: [
        {
          pt: "No standby (chuva ou ambiente, no topo), a serial fica livre e o App da Roland pode abrir. Os Launchpads fazem ondas sozinhos, e cada toque solta mais uma a partir do pad tocado.",
          en: "In standby (rain or ambient, at the top), the serial port is free and Roland's App can open. The Launchpads make waves on their own, and each touch drops another one from the pad you hit.",
        },
        {
          pt: "No ambiente, as ondas são maiores, mais lentas e mais fracas, e o toque segue o mesmo estilo. Clique nos pads aqui para ver.",
          en: "In ambient, the waves are bigger, slower and dimmer, and a touch follows the same style. Click the pads here to see.",
        },
      ],
    },
    variacao: {
      t: { pt: "Variação {v}", en: "Variation {v}" },
      d: [
        {
          pt: "Escolhe a variação que o grid **mostra e edita** (azul). Não muda o que a máquina toca.",
          en: "Picks the variation the grid **shows and edits** (blue). It does not change what the machine plays.",
        },
        {
          pt: "A que está tocando fica **branca**; se for a mesma que você edita, fica azul-clara. Com as variações da chain iguais, o grid não sabe qual toca e nenhuma fica branca.",
          en: "The one playing turns **white**; if it is also the one you edit, it turns light blue. When the chain's variations are identical, the grid cannot tell which is playing and none turns white.",
        },
        {
          pt: "Ela lê a variação nova antes de trocar: se a leitura falhar, o grid fica na de antes.",
          en: "It reads the new variation before switching: if the read fails, the grid stays on the previous one.",
        },
      ],
    },
    parTrack: {
      t: { pt: "Track {t}", en: "Track {t}" },
      d: [
        {
          pt: "Na PAR, a coluna do mute vira o **seletor de track**: o escolhido fica branco, os outros quase apagados.",
          en: "On PAR, the mute column becomes the **track selector**: the chosen one is white, the others nearly dark.",
        },
        {
          pt: "Para escolher CC ou RC, troque o banco com ▼ primeiro.",
          en: "To pick CC or RC, switch the bank with ▼ first.",
        },
      ],
    },
    mute: {
      t: { pt: "MUTE do {t}", en: "{t} MUTE" },
      d: [
        {
          pt: "Verde = soando, rosa = mudo. Antes de inverter, lê o mute atual da máquina, para não desfazer o que alguém fez no painel.",
          en: "Green = sounding, pink = muted. Before toggling, it reads the machine's current mute, so it does not undo what someone did on the panel.",
        },
      ],
      banco: {
        pt: "Esta tecla é RS/HC no banco ▲ e CC/RC no ▼.",
        en: "This key is RS/HC in bank ▲ and CC/RC in bank ▼.",
      },
      perf: {
        pt: "Na PERF, a linha de cima mostra os 10 mutes juntos.",
        en: "On PERF, the top row shows all 10 mutes together.",
      },
    },
    banco: {
      t1: { pt: "Banco ▲ RS·HC", en: "Bank ▲ RS·HC" },
      t2: { pt: "Banco ▼ CC·RC", en: "Bank ▼ CC·RC" },
      d: [
        {
          pt: "A TR-1000 tem 10 tracks e o grid tem 8 linhas. As linhas 5 e 6 mudam: **RS e HC** no ▲, **CC e RC** no ▼. BD, SD, LT, HT, CH e OH nunca saem do lugar.",
          en: "The TR-1000 has 10 tracks and the grid has 8 rows. Rows 5 and 6 change: **RS and HC** on ▲, **CC and RC** on ▼. BD, SD, LT, HT, CH and OH never move.",
        },
        {
          pt: "Vale para os steps, para os mutes da lateral e para o seletor de track da PAR.",
          en: "It applies to the steps, the side mutes and the PAR track selector.",
        },
      ],
    },
    layer: {
      t: { pt: "Layer {m}", en: "Layer {m}" },
      AB: {
        pt: "BD, SD, LT e HT têm dois sons por step, o layer A e o layer B. Este botão decide onde o toque escreve: **nos dois**.",
        en: "BD, SD, LT and HT have two sounds per step, layer A and layer B. This button decides where a tap writes: **to both**.",
      },
      A: {
        pt: "BD, SD, LT e HT têm dois sons por step, o layer A e o layer B. Este botão decide onde o toque escreve: **só no A** (vermelho).",
        en: "BD, SD, LT and HT have two sounds per step, layer A and layer B. This button decides where a tap writes: **A only** (red).",
      },
      B: {
        pt: "BD, SD, LT e HT têm dois sons por step, o layer A e o layer B. Este botão decide onde o toque escreve: **só no B** (verde).",
        en: "BD, SD, LT and HT have two sounds per step, layer A and layer B. This button decides where a tap writes: **B only** (green).",
      },
      outros: {
        pt: "Nos outros seis tracks não muda nada: eles só têm um som.",
        en: "On the other six tracks it changes nothing: they only have one sound.",
      },
    },
    pagina: {
      t: { pt: "Página {p}", en: "Page {p}" },
      par: {
        pt: "Abre os parâmetros de cada step: PROB, SUB, CYCLE, START, VEL e ALT.",
        en: "Opens each step's parameters: PROB, SUB, CYCLE, START, VEL and ALT.",
      },
      perf: {
        pt: "Abre a performance: mutes, fill, chain, STEP LOOP, LAST e Scale.",
        en: "Opens performance: mutes, fill, chain, STEP LOOP, LAST and Scale.",
      },
      rout: {
        pt: "Abre a Routing Matrix e o side chain.",
        en: "Opens the Routing Matrix and the side chain.",
      },
      d: [
        {
          pt: "**Apertar o botão aceso volta para os steps.** Apertar outro vai direto para a outra página.",
          en: "**Pressing the lit button goes back to the steps.** Pressing another one jumps straight to that page.",
        },
        {
          pt: "Trocar de página solta qualquer STEP LOOP segurado, para a máquina não ficar presa no loop.",
          en: "Changing pages releases any held STEP LOOP, so the machine is not left stuck in the loop.",
        },
      ],
    },
    semPar: {
      t: { pt: "Sem função na PAR", en: "No function on PAR" },
      d: [
        {
          pt: "Os dois botões de baixo ficam apagados na PAR.",
          en: "The two bottom buttons stay dark on PAR.",
        },
      ],
    },
    param: {
      t: { pt: "Parâmetro {p}", en: "Parameter {p}" },
      d: {
        pt: "Na PAR, a borda da velocity vira o **seletor de parâmetro**. Embaixo do número, a etiqueta diz qual.",
        en: "On PAR, the velocity edge becomes the **parameter selector**. Under the number, the sticker says which.",
      },
      alt: {
        pt: "ALT: o som alternativo dos tracks simples (RS até RC). Qualquer altura liga ou desliga.",
        en: "ALT: the alternate sound of the single-sound tracks (RS to RC). Any height toggles it.",
      },
      alturas: {
        pt: "As 8 alturas, de baixo para cima: {lista}.",
        en: "The 8 heights, bottom to top: {lista}.",
      },
    },
    vel: {
      t: { pt: "Velocity {v}", en: "Velocity {v}" },
      d: [
        {
          pt: "A velocity do próximo toque num step. 80 é o normal do painel; abaixo de 80 o pad fica com a cor escura.",
          en: "The velocity of the next tap on a step. 80 is the panel's normal; below 80 the pad shows the dark color.",
        },
        {
          pt: "Tocar um step já aceso com outra velocity **regrava** na velocity nova, em vez de apagar.",
          en: "Tapping a lit step with a different velocity **rewrites** it at the new velocity instead of clearing it.",
        },
      ],
    },
    step: {
      t: { pt: "{t} · step {s}", en: "{t} · step {s}" },
      d: [
        {
          pt: "Toque: liga o step com a velocity e o layer escolhidos. Aceso com a **mesma** velocity, apaga. Aceso com **outra**, regrava na nova.",
          en: "Tap: turns the step on with the chosen velocity and layer. Lit at the **same** velocity, it clears. Lit at a **different** one, it rewrites at the new one.",
        },
        {
          pt: "O pad só muda depois que a máquina confirma a escrita. Se ela recusar, o grid relê o track.",
          en: "The pad only changes after the machine confirms the write. If it refuses, the grid re-reads the track.",
        },
      ],
      layer: {
        pt: "Este track tem layer A e B: vermelho = A, verde = só B.",
        en: "This track has layers A and B: red = A, green = B only.",
      },
      alt: {
        pt: "Um step roxo tem o som ALT. Tocar nele grava uma nota normal (tira o ALT); tocar de novo apaga.",
        en: "A purple step has the ALT sound. Tapping it writes a normal note (removes ALT); tapping again clears it.",
      },
    },
    par: {
      t: { pt: "{p} · {t} step {s}", en: "{p} · {t} step {s}" },
      alt: { pt: "liga ou desliga o ALT", en: "toggles ALT" },
      grava: {
        pt: "Altura {l} de 8 (contando de baixo). O toque grava **{val}** no step {s} do {t}.",
        en: "Height {l} of 8 (counting from the bottom). A tap writes **{val}** to step {s} of {t}.",
      },
      d: {
        pt: "Só os steps que tocam mostram a barra. Um step vazio fica apagado, mas o toque nele grava mesmo assim.",
        en: "Only steps that play show the bar. An empty step stays dark, but a tap on it still writes.",
      },
      vel: {
        pt: "Com VEL, um toque num step vazio **liga a nota** nessa velocity (no layer escolhido).",
        en: "With VEL, a tap on an empty step **turns the note on** at that velocity (on the chosen layer).",
      },
      altLayer: {
        pt: "BD, SD, LT e HT não têm ALT: aqui o toque não faz nada.",
        en: "BD, SD, LT and HT have no ALT: here a tap does nothing.",
      },
      altVazio: {
        pt: "Num step vazio, o ALT liga a nota já com o som alternativo.",
        en: "On an empty step, ALT turns the note on with the alternate sound already set.",
      },
      escolha: {
        pt: "SUB e CYCLE são listas: acende só a altura escolhida, sem barra.",
        en: "SUB and CYCLE are lists: only the chosen height lights, with no bar.",
      },
      start: {
        pt: "O 0 fica na 4ª altura: três para trás, quatro para frente.",
        en: "0 sits at the 4th height: three earlier, four later.",
      },
    },
    perfMute: {
      t: { pt: "MUTE do {t}", en: "{t} MUTE" },
      d: [
        {
          pt: "A linha de cima da PERF mostra os 10 mutes de uma vez, sem depender do banco. Rosa = mudo.",
          en: "The top row of PERF shows all 10 mutes at once, regardless of the bank. Pink = muted.",
        },
      ],
    },
    fill: {
      t: { pt: "FILL {n}", en: "FILL {n}" },
      d: [
        {
          pt: "Escolhe qual fill o FILL IN da máquina toca: o {n}.",
          en: "Picks which fill the machine's FILL IN plays: number {n}.",
        },
        {
          pt: "Só existem o 1 e o 2: o FILL 3 e o 4 ainda não foram medidos, e o portão não deixa escrever.",
          en: "Only 1 and 2 exist: FILL 3 and 4 have not been measured yet, and the gate does not allow writing them.",
        },
      ],
    },
    chain: {
      t: { pt: "Chain · {v}", en: "Chain · {v}" },
      d: [
        {
          pt: "Um toque sozinho: a máquina passa a tocar **só esta** variação.",
          en: "A tap on its own: the machine plays **only this** variation.",
        },
        {
          pt: "**Segure uma variação e toque outra**: a outra entra na chain (ou sai, se já estava). É o mesmo gesto do painel. Aqui na bancada, use Shift+clique.",
          en: "**Hold one variation and tap another**: the other joins the chain (or leaves it, if it was there). Same gesture as the panel. Here on the bench, use Shift+click.",
        },
        {
          pt: "Antes de somar, ele lê a chain da máquina, para não desfazer o que o painel mudou.",
          en: "Before adding, it reads the machine's chain, so it does not undo what the panel changed.",
        },
      ],
    },
    loop: {
      t: { pt: "STEP LOOP · step {s}", en: "STEP LOOP · step {s}" },
      d: [
        {
          pt: "**Segure** o pad: a máquina fica repetindo esse step. Solte: ela volta ao normal.",
          en: "**Hold** the pad: the machine keeps repeating that step. Let go: it goes back to normal.",
        },
        {
          pt: "Se o modo STEP LOOP estava desligado, o grid liga sozinho enquanto você segura e devolve o modo como estava quando solta.",
          en: "If STEP LOOP mode was off, the grid turns it on while you hold and puts it back as it was when you let go.",
        },
        {
          pt: "O som foi provado; o LED do STEP LOOP do painel da TR-1000 não acende (F3.4.6). Aqui na bancada, segure o clique.",
          en: "The sound was proven; the STEP LOOP LED on the TR-1000 panel does not light (F3.4.6). Here on the bench, hold the click.",
        },
      ],
    },
    last: {
      t: { pt: "LAST = {s}", en: "LAST = {s}" },
      d: [
        {
          pt: "Escolhe o último step da variação editada: a máquina volta ao começo depois dele.",
          en: "Sets the last step of the edited variation: the machine goes back to the start after it.",
        },
        {
          pt: "Só aceita um LAST depois do FIRST. Os steps entre os dois ficam laranja-escuro.",
          en: "It only accepts a LAST after the FIRST. The steps between them are dark orange.",
        },
      ],
    },
    scale: {
      t: { pt: "Scale {n}", en: "Scale {n}" },
      d: [
        {
          pt: "A duração do step. 32nd toca no dobro da velocidade; 16th é o normal. O playhead segue a Scale nova a partir do próximo step.",
          en: "The step length. 32nd plays at double speed; 16th is normal. The playhead follows the new Scale from the next step on.",
        },
      ],
    },
    semFuncao: {
      perf: { pt: "Sem função na PERF", en: "No function on PERF" },
      rout: { pt: "Sem função na ROUT", en: "No function on ROUT" },
      d: [
        {
          pt: "Este pad fica apagado e não faz nada nesta página.",
          en: "This pad stays dark and does nothing on this page.",
        },
      ],
    },
    rota: {
      t: { pt: "{f} → {d}", en: "{f} → {d}" },
      d: [
        {
          pt: "As três primeiras linhas são a Routing Matrix: cada coluna é uma fonte, cada linha um destino (THROUGH, MASTER FX, ANALOG FX). O toque manda a fonte para esta linha.",
          en: "The first three rows are the Routing Matrix: each column is a source, each row a destination (THROUGH, MASTER FX, ANALOG FX). A tap sends the source to this row.",
        },
        {
          pt: "A página relê o kit a cada 2 s: o que o App ou o painel mudar aparece aqui.",
          en: "The page re-reads the kit every 2 s: whatever the App or the panel changes shows up here.",
        },
      ],
    },
    sc: {
      t: { pt: "SC SOURCE · {n}", en: "SC SOURCE · {n}" },
      d: [
        {
          pt: "As linhas 5 e 6 são as 19 fontes do side chain, na ordem do App. A acesa (branca) é o que faz o resto abaixar.",
          en: "Rows 5 and 6 are the 19 side chain sources, in the App's order. The lit one (white) is what makes the rest duck.",
        },
      ],
    },
    pol: {
      t: { pt: "POLARITY · {n}", en: "POLARITY · {n}" },
      d: [
        {
          pt: "DUCK abaixa o som quando a fonte toca; GATE faz o contrário.",
          en: "DUCK lowers the sound when the source hits; GATE does the opposite.",
        },
      ],
    },
    hld: {
      t: { pt: "HLD MODE · {n}", en: "HLD MODE · {n}" },
      d: [
        {
          pt: "Se o HOLD do side chain conta em tempo ou em steps. O MSTR DEP, o RELEASE e o CURVE ficam na aba Efeitos e nos knobs.",
          en: "Whether the side chain HOLD counts in time or in steps. MSTR DEP, RELEASE and CURVE live in the Effects tab and on the knobs.",
        },
      ],
    },
  },

  cores: { pt: "O que cada cor quer dizer", en: "What each color means" },
  coresNota: {
    pt: "Na tela, as cores são aproximadas. No aparelho, os botões de borda ficam um pouco mais escuros que os pads.",
    en: "On screen, the colors are approximate. On the device, the edge buttons are a little darker than the pads.",
  },
  // dois grupos: os pads (o grid 16x8) e os botoes de borda (fora dele).
  // c = as chaves de cor do guia.mjs (C); varias = uma amostra por cor
  legendaGrid: {
    pt: "Nos pads (o grid 16 × 8)",
    en: "On the pads (the 16 × 8 grid)",
  },
  legendaBordas: {
    pt: "Nos botões de borda (topo, laterais e a borda da velocity)",
    en: "On the edge buttons (top, sides and the velocity edge)",
  },
  legenda: {
    grid: [
      {
        c: ["red"],
        pt: "Step no layer A, ou o som de um track simples",
        en: "Step on layer A, or the sound of a single-sound track",
      },
      {
        c: ["redW"],
        pt: "O mesmo, com velocity abaixo de 80",
        en: "The same, with velocity below 80",
      },
      { c: ["green"], pt: "Step só no layer B", en: "Step on layer B only" },
      {
        c: ["greenW"],
        pt: "Só no layer B, com velocity abaixo de 80",
        en: "Layer B only, with velocity below 80",
      },
      {
        c: ["purple"],
        pt: "Step com o som ALT (RS até RC)",
        en: "Step with the ALT sound (RS to RC)",
      },
      {
        c: ["white"],
        pt: "Playhead sobre um step que toca",
        en: "Playhead over a step that plays",
      },
      {
        c: ["play"],
        pt: "Playhead sobre um step vazio",
        en: "Playhead over an empty step",
      },
      {
        c: ["beat"],
        pt: "Cabeça de tempo vazia: steps 1, 5, 9 e 13",
        en: "Empty beat head: steps 1, 5, 9 and 13",
      },
      {
        c: [
          "par.prob",
          "par.sub",
          "par.cycle",
          "par.start",
          "par.vel",
          "par.alt",
        ],
        pt: "PAR: a barra do parâmetro, na cor dele (PROB, SUB, CYCLE, START, VEL, ALT)",
        en: "PAR: the parameter's bar, in its color (PROB, SUB, CYCLE, START, VEL, ALT)",
      },
      {
        c: ["pink"],
        pt: "PERF, linha 1: track mudo",
        en: "PERF, row 1: muted track",
      },
      {
        c: ["blue"],
        pt: "PERF, linha 2: variação na chain",
        en: "PERF, row 2: variation in the chain",
      },
      {
        c: ["amber"],
        pt: "PERF: o LAST step. ROUT: POLARITY e HLD MODE escolhidos",
        en: "PERF: the LAST step. ROUT: chosen POLARITY and HLD MODE",
      },
      {
        c: ["white"],
        pt: "PERF e ROUT: o FILL, a Scale e o SC SOURCE escolhidos; o STEP LOOP segurado",
        en: "PERF and ROUT: the chosen FILL, Scale and SC SOURCE; the held STEP LOOP",
      },
      {
        c: ["destino.0", "destino.1", "destino.2"],
        pt: "ROUT: o destino da fonte (THROUGH, MASTER FX, ANALOG FX)",
        en: "ROUT: the source's destination (THROUGH, MASTER FX, ANALOG FX)",
      },
    ],
    bordas: [
      {
        c: ["blue"],
        pt: "Topo do esquerdo: a variação que você edita",
        en: "Left top: the variation you edit",
      },
      {
        c: ["white"],
        pt: "Topo do esquerdo: a variação que toca",
        en: "Left top: the variation playing",
      },
      {
        c: ["lblue"],
        pt: "Topo do esquerdo: a editada, que também é a que toca",
        en: "Left top: the edited one, which is also the one playing",
      },
      {
        c: ["soando"],
        pt: "Lateral do esquerdo: track soando",
        en: "Left side: track sounding",
      },
      {
        c: ["pink"],
        pt: "Lateral do esquerdo: track mudo",
        en: "Left side: muted track",
      },
      {
        c: ["white"],
        pt: "Direito: o banco, o layer AB, a página e a velocity escolhidos; na PAR, o track escolhido na lateral",
        en: "Right: the chosen bank, AB layer, page and velocity; on PAR, the track chosen on the side",
      },
      {
        c: ["red", "green"],
        pt: "Topo do direito: layer A ou layer B escolhido",
        en: "Right top: layer A or layer B chosen",
      },
      {
        c: [
          "par.prob",
          "par.sub",
          "par.cycle",
          "par.start",
          "par.vel",
          "par.alt",
        ],
        pt: "PAR, borda da velocity: o parâmetro escolhido aceso, os outros fracos",
        en: "PAR, velocity edge: the chosen parameter lit, the others dim",
      },
      {
        c: ["dim"],
        pt: "Disponível, não escolhido",
        en: "Available, not chosen",
      },
    ],
  },

  mapa: {
    pt: "Os botões de borda, página por página",
    en: "The edge buttons, page by page",
  },
  mapaNota: {
    pt: "As bordas mudam de função conforme a página. O número embaixo é o CC que o botão manda, para quem for mexer no código.",
    en: "The edges change function with the page. The number underneath is the CC the button sends, for whoever touches the code.",
  },
  mapaCab: [
    { pt: "Botão", en: "Button" },
    { pt: "Steps", en: "Steps" },
    { pt: "PAR", en: "PAR" },
    { pt: "PERF e ROUT", en: "PERF and ROUT" },
  ],
  // [botao, cc, steps, par, perf/rout]; "=" junta a celula com a da esquerda
  mapaLinhas: [
    {
      b: { pt: "Topo do esquerdo · A–H", en: "Left top · A–H" },
      cc: "CC 89 … 19",
      steps: {
        pt: "Escolhe a variação que o grid mostra e edita (azul). A que toca fica branca.",
        en: "Picks the variation the grid shows and edits (blue). The one playing is white.",
      },
      par: { pt: "Igual", en: "Same" },
      perf: {
        pt: "Igual. Na PERF, a linha 4 (LAST) segue a variação editada.",
        en: "Same. On PERF, row 4 (LAST) follows the edited variation.",
      },
    },
    {
      b: { pt: "Lateral do esquerdo", en: "Left side" },
      cc: "CC 98 … 91",
      steps: {
        pt: "MUTE do track da linha ao lado. Verde soa, rosa está mudo.",
        en: "MUTE of the track on that row. Green sounds, pink is muted.",
      },
      par: {
        pt: "**Escolhe o track** da página (branco)",
        en: "**Picks the track** for the page (white)",
      },
      perf: { pt: "MUTE, como nos steps", en: "MUTE, as on the steps" },
    },
    {
      b: { pt: "Topo do direito · ▲ ▼", en: "Right top · ▲ ▼" },
      cc: "CC 91, 92",
      steps: {
        pt: "Banco: linhas 5 e 6 = RS e HC (▲) ou CC e RC (▼)",
        en: "Bank: rows 5 and 6 = RS and HC (▲) or CC and RC (▼)",
      },
      par: {
        pt: "Igual: muda quais tracks a lateral oferece",
        en: "Same: changes which tracks the side offers",
      },
      perf: {
        pt: "Igual, mas a PERF e a ROUT mostram os 10 tracks de uma vez",
        en: "Same, but PERF and ROUT show all 10 tracks at once",
      },
    },
    {
      b: { pt: "Topo do direito · AB A B", en: "Right top · AB A B" },
      cc: "CC 93, 94, 95",
      steps: {
        pt: "Em qual layer o toque escreve (só BD SD LT HT)",
        en: "Which layer a tap writes to (BD SD LT HT only)",
      },
      par: {
        pt: "Vale para o VEL num step vazio",
        en: "Applies to VEL on an empty step",
      },
      perf: { pt: "Fica guardado para os steps", en: "Kept for the steps" },
    },
    {
      b: {
        pt: "Topo do direito · PAR PERF ROUT",
        en: "Right top · PAR PERF ROUT",
      },
      cc: "CC 96, 97, 98",
      steps: { pt: "Abre a página", en: "Opens the page" },
      par: {
        pt: "O botão aceso volta para os steps; outro botão vai direto para a outra página",
        en: "The lit button goes back to the steps; another button jumps straight to that page",
      },
      perf: "=",
    },
    {
      b: { pt: "Borda do direito · 127 … 10", en: "Right edge · 127 … 10" },
      cc: "CC 89 … 19",
      steps: {
        pt: "Velocity do próximo toque (80 é o normal do painel)",
        en: "Velocity of the next tap (80 is the panel's normal)",
      },
      par: {
        pt: "**Escolhe o parâmetro:** PROB SUB CYCLE START VEL ALT. Os dois de baixo não fazem nada.",
        en: "**Picks the parameter:** PROB SUB CYCLE START VEL ALT. The bottom two do nothing.",
      },
      perf: {
        pt: "Velocity, guardada para os steps",
        en: "Velocity, kept for the steps",
      },
    },
    {
      b: { pt: "Os cantos com logo", en: "The logo corners" },
      cc: "CC 99",
      steps: {
        pt: 'Só um LED, sem botão embaixo. As etiquetas "VAR ▸" e "VEL ▾" dizem o que é a borda ao lado.',
        en: 'Just an LED, no switch under it. The "VAR ▸" and "VEL ▾" stickers say what the edge next to them is.',
      },
      par: "=",
      perf: "=",
    },
  ],

  segredos: { pt: "Os menus secretos", en: "The secret menus" },
  segredosNota: {
    pt: 'Coisas que o grid faz e que nenhuma etiqueta conta. "Mostrar" leva a bancada até o pad certo. A etiqueta de cada uma diz se ela já foi conferida na máquina ou se só existe no código.',
    en: 'Things the grid does that no sticker tells you. "Show" takes the bench to the right pad. Each one\'s tag says whether it has been checked on the machine or only exists in the code.',
  },
  mostrar: { pt: "Mostrar na bancada", en: "Show on the bench" },
  // go: [pagina, tipo, i, j]
  listaSegredos: [
    {
      s: "ok",
      go: ["par", "topD", 5],
      w: { pt: "Topo do direito", en: "Right top" },
      t: { pt: "O mesmo botão volta", en: "The same button goes back" },
      d: {
        pt: 'Não existe botão de "steps". Para voltar, aperte de novo o PAR, o PERF ou o ROUT que está aceso.',
        en: 'There is no "steps" button. To go back, press the lit PAR, PERF or ROUT again.',
      },
    },
    {
      s: "ok",
      go: ["par", "ladoD", 0],
      w: { pt: "PAR", en: "PAR" },
      t: {
        pt: "A borda direita muda de função",
        en: "The right edge changes function",
      },
      d: {
        pt: "Na PAR, os botões da velocity viram o seletor de parâmetro: PROB, SUB, CYCLE, START, VEL e ALT, de cima para baixo. A etiqueta tem os dois nomes.",
        en: "On PAR, the velocity buttons become the parameter selector: PROB, SUB, CYCLE, START, VEL and ALT, top to bottom. The sticker carries both names.",
      },
    },
    {
      s: "ok",
      go: ["par", "ladoE", 1],
      w: { pt: "PAR", en: "PAR" },
      t: {
        pt: "O mute vira seletor de track",
        en: "Mute becomes the track selector",
      },
      d: {
        pt: "Na PAR, a coluna lateral do esquerdo para de mutar e passa a escolher o track que a página mostra. Fora da PAR, volta a ser mute.",
        en: "On PAR, the left unit's side column stops muting and picks the track the page shows. Outside PAR, it is mute again.",
      },
    },
    {
      s: "ok",
      go: ["perf", "pad", 1, 1],
      w: { pt: "PERF · linha 2", en: "PERF · row 2" },
      t: { pt: "Segure uma, toque outra", en: "Hold one, tap another" },
      d: {
        pt: "Um toque numa variação toca só ela. Segurando uma e tocando outra, a outra entra na chain ou sai dela, como no painel.",
        en: "A tap on a variation plays only that one. Holding one and tapping another adds the other to the chain or removes it, as on the panel.",
      },
    },
    {
      s: "part",
      go: ["perf", "pad", 2, 4],
      w: { pt: "PERF · linha 3", en: "PERF · row 3" },
      t: { pt: "STEP LOOP é segurar", en: "STEP LOOP is holding" },
      d: {
        pt: "Enquanto o dedo está no pad, a máquina repete aquele step. Solte e ela segue. Se o modo STEP LOOP estava desligado, o grid liga e desliga sozinho.",
        en: "While your finger is on the pad, the machine repeats that step. Let go and it moves on. If STEP LOOP mode was off, the grid turns it on and off by itself.",
      },
    },
    {
      s: "part",
      go: ["perf", "pad", 0, 12],
      w: {
        pt: "PERF · linha 1, colunas 13–14",
        en: "PERF · row 1, columns 13–14",
      },
      t: {
        pt: "Dois fills no fim da linha do mute",
        en: "Two fills at the end of the mute row",
      },
      d: {
        pt: "Depois dos 10 mutes, dois pads escolhem se o FILL IN toca o fill 1 ou o 2. O 3 e o 4 não existem aqui: ainda não foram medidos.",
        en: "After the 10 mutes, two pads pick whether FILL IN plays fill 1 or 2. 3 and 4 are not here: they have not been measured yet.",
      },
    },
    {
      s: "no",
      go: ["steps", "ladoD", 0],
      w: { pt: "Steps", en: "Steps" },
      t: {
        pt: "Tocar com outra velocity regrava",
        en: "Tapping at another velocity rewrites",
      },
      d: {
        pt: "Um step aceso só apaga se você tocar com a mesma velocity em que ele está. Com outra velocity escolhida, o toque regrava o step na velocity nova.",
        en: "A lit step only clears if you tap at the velocity it already has. With another velocity chosen, the tap rewrites the step at the new velocity.",
      },
    },
    {
      s: "no",
      go: ["steps", "pad", 4, 2],
      w: { pt: "Steps · RS até RC", en: "Steps · RS to RC" },
      t: { pt: "Tocar no roxo tira o ALT", en: "Tapping purple removes ALT" },
      d: {
        pt: "O toque grava uma nota normal, então um step com ALT vira vermelho no primeiro toque e só apaga no segundo.",
        en: "A tap writes a normal note, so a step with ALT turns red on the first tap and only clears on the second.",
      },
    },
    {
      s: "ok",
      go: ["steps", "topD", 1],
      w: { pt: "Topo do direito", en: "Right top" },
      t: { pt: "CC e RC moram no banco ▼", en: "CC and RC live in bank ▼" },
      d: {
        pt: "A 5ª e a 6ª linha são RS e HC no ▲ e CC e RC no ▼. As etiquetas laterais dizem RS/CC e HC/RC por isso.",
        en: "Rows 5 and 6 are RS and HC on ▲ and CC and RC on ▼. That is why the side stickers say RS/CC and HC/RC.",
      },
    },
    {
      s: "ok",
      go: ["steps", "topD", 3],
      w: { pt: "Topo do direito · AB A B", en: "Right top · AB A B" },
      t: { pt: "Layer só em quatro tracks", en: "Layers on four tracks only" },
      d: {
        pt: "AB, A e B só valem para BD, SD, LT e HT. Nos outros, o toque escreve sempre o único som que eles têm.",
        en: "AB, A and B only apply to BD, SD, LT and HT. On the others, a tap always writes the one sound they have.",
      },
    },
    {
      s: "no",
      go: ["par", "ladoD", 4],
      w: { pt: "PAR", en: "PAR" },
      t: { pt: "VEL e ALT ligam a nota", en: "VEL and ALT turn the note on" },
      d: {
        pt: "Com VEL ou ALT escolhido, tocar um step vazio liga a nota: o VEL na altura tocada, o ALT já com o som alternativo. Os outros parâmetros gravam o valor sem acender o step.",
        en: "With VEL or ALT chosen, tapping an empty step turns the note on: VEL at the height you hit, ALT with the alternate sound. The other parameters write the value without lighting the step.",
      },
    },
    {
      s: "part",
      go: ["steps", "topE", 1],
      w: { pt: "Topo do esquerdo", en: "Left top" },
      t: {
        pt: "O topo esquerdo é o que você edita",
        en: "The left top is what you edit",
      },
      d: {
        pt: "Os botões A–H escolhem a variação que o grid mostra. Quem diz o que toca é a máquina: a que toca fica branca. Para mudar o que toca, use a linha 2 da PERF.",
        en: "Buttons A–H pick the variation the grid shows. The machine decides what plays: the playing one is white. To change what plays, use row 2 of PERF.",
      },
    },
    {
      s: "ok",
      go: ["standby", "pad", 3, 4],
      w: { pt: "Chuva / ambiente", en: "Rain / ambient" },
      t: { pt: "O toque no standby", en: "Touching in standby" },
      d: {
        pt: "Com a serial solta, os pads não escrevem nada, mas cada toque solta uma onda dali. Os botões ficam mudos.",
        en: "With the serial port released, the pads write nothing, but each touch drops a wave from there. The buttons go silent.",
      },
    },
    {
      s: "ok",
      go: ["rout", "pad", 1, 0],
      w: { pt: "ROUT", en: "ROUT" },
      t: { pt: "A ROUT segue o App", en: "ROUT follows the App" },
      d: {
        pt: "A página relê o routing e o side chain a cada 2 s. Mudou no App da Roland ou no painel, os pads acompanham.",
        en: "The page re-reads the routing and side chain every 2 s. Change it in Roland's App or on the panel and the pads follow.",
      },
    },
    {
      s: "ok",
      go: ["steps", "logo", 1],
      w: { pt: "Logo", en: "Logo" },
      t: { pt: "O canto é só uma luz", en: "The corner is just a light" },
      d: {
        pt: "O quadrado do canto parece um botão, mas é um LED sem chave embaixo. As etiquetas VAR ▸ e VEL ▾ coladas ali dizem o que é a borda ao lado.",
        en: "The corner square looks like a button, but it is an LED with no switch. The VAR ▸ and VEL ▾ stickers there say what the edge next to it is.",
      },
    },
    {
      s: "no",
      go: ["steps", "pad", 0, 6],
      w: { pt: "Steps", en: "Steps" },
      t: {
        pt: "Cada track com seu playhead",
        en: "Each track with its own playhead",
      },
      d: {
        pt: "Um track com FIRST/LAST próprio anda sozinho, e o playhead dele fica em outra coluna. Com o DIRECTION em RND ou P-P, a linha fica sem playhead, porque o grid não sabe onde ela está.",
        en: "A track with its own FIRST/LAST runs on its own, and its playhead sits in another column. With DIRECTION on RND or P-P, the row has no playhead, because the grid cannot tell where it is.",
      },
    },
  ],

  testado: {
    pt: "O que foi testado na máquina e o que não",
    en: "What was tested on the machine and what was not",
  },
  testadoNota: {
    pt: "Este guia descreve o código e não foi conferido na frente da máquina. Se algum pad fizer outra coisa no aparelho, vale o aparelho.",
    en: "This guide describes the code and has not been checked in front of the machine. If a pad does something else on the device, the device wins.",
  },
  // [texto, roteiro]
  listaTestado: {
    ok: [
      [
        {
          pt: "Ligar e apagar step, velocity 66 e 127, layer B só soando o B",
          en: "Turning steps on and off, velocity 66 and 127, layer B sounding only B",
        },
        "F1.2–F1.4",
      ],
      [
        {
          pt: "Playhead andando depois de um START",
          en: "Playhead moving after a START",
        },
        "F1.5, F4.1",
      ],
      [
        {
          pt: "Bancos ▲ ▼; o toque cai no CC",
          en: "Banks ▲ ▼; the tap lands on CC",
        },
        "F3.2.5",
      ],
      [
        { pt: "MUTE pela tecla lateral", en: "MUTE from the side key" },
        "F3.4.1",
      ],
      [
        { pt: "PAR com PROB e com VEL", en: "PAR with PROB and with VEL" },
        "F4.6c",
      ],
      [
        {
          pt: "PERF: mute, chain segurando A e tocando B, STEP LOOP segurado, LAST 12, Scale",
          en: "PERF: mute, chain by holding A and tapping B, held STEP LOOP, LAST 12, Scale",
        },
        "F4.6c",
      ],
      [
        {
          pt: "ROUT: routing, SC SOURCE, DUCK/GATE e TIME/STEP",
          en: "ROUT: routing, SC SOURCE, DUCK/GATE and TIME/STEP",
        },
        "F4.6c",
      ],
      [
        {
          pt: "Chuva e ambiente com o App da Roland aberto",
          en: "Rain and ambient with Roland's App open",
        },
        "F4.6b",
      ],
      [
        {
          pt: "Ligar com a máquina já tocando: o grid acha a fase pelas notas",
          en: "Turning on with the machine already playing: the grid finds the phase from the notes",
        },
        "F4.6e",
      ],
    ],
    part: [
      [
        {
          pt: "SUB, START e ALT: provados pela aba Pattern, não pela PAR do Launchpad",
          en: "SUB, START and ALT: proven from the Pattern tab, not from the Launchpad's PAR",
        },
        "F3.2.3, F3.2.4",
      ],
      [
        {
          pt: "FILL: o FILL 2 foi provado pela tela; as duas colunas da PERF não foram tocadas",
          en: "FILL: FILL 2 was proven from the screen; the two PERF columns were not tried",
        },
        "F3.4.3",
      ],
      [
        {
          pt: "Variação tocando em branco: o TOCA alterna A/B na tela; o LED do Launchpad não foi conferido à parte",
          en: "Playing variation in white: PLAY alternates A/B on screen; the Launchpad LED was not checked separately",
        },
        "F4.1b",
      ],
      [
        {
          pt: "STEP LOOP: o som para no step, mas o LED do painel da TR-1000 não acende",
          en: "STEP LOOP: the sound holds on the step, but the TR-1000 panel LED does not light",
        },
        "F3.4.6",
      ],
    ],
    no: [
      [
        {
          pt: "CYCLE: nunca conferido de ouvido",
          en: "CYCLE: never checked by ear",
        },
        "",
      ],
      [
        {
          pt: "Tocar de novo um step com outra velocity, que regrava em vez de apagar",
          en: "Tapping a step again at another velocity, which rewrites instead of clearing",
        },
        "",
      ],
      [
        {
          pt: "Tocar um step roxo (ALT), que vira nota normal",
          en: "Tapping a purple (ALT) step, which becomes a normal note",
        },
        "",
      ],
      [
        {
          pt: "VEL e ALT da PAR num step vazio, que ligam a nota",
          en: "PAR's VEL and ALT on an empty step, which turn the note on",
        },
        "",
      ],
      [
        {
          pt: "Trocar de página com um STEP LOOP segurado, que solta o loop",
          en: "Changing pages with a held STEP LOOP, which releases the loop",
        },
        "",
      ],
      [
        {
          pt: "Playhead separado por track (FIRST/LAST por track) e a linha sem playhead com DIRECTION RND ou P-P",
          en: "Per-track playhead (per-track FIRST/LAST) and the row with no playhead on DIRECTION RND or P-P",
        },
        "",
      ],
    ],
  },
};

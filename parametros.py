#!/usr/bin/env python3
"""
parametros.py - os parametros de KIT e MIXER decifrados, um a um, das capturas

Cada parametro entra aqui SO depois de visto o TR-1000 App escrevendo nele
(decisao do Luan de 09/10/2026, plano B2): endereco e faixa vem da captura,
a escala vem do que o Luan leu no visor do App. A regra de escrita
(conexao_serial.escrita_permitida) aceita um parametro desta tabela com valor
DENTRO da faixa medida - e nada mais.

Enderecamento (REFERENCIA 2.1c):
  - x: o pattern/kit selecionado (bloco 3 [2..4]; nas capturas o pattern N
    usou o kit N, entao o x do kit e o do pattern coincidiram - o kit esta em
    [3] por DEDUCAO, a confirmar trocando o kit no painel)
  - y: o track (0..9 = BD..RC) quando o parametro e por track

Os ids sao os mesmos do mapa das controladoras (controladoras.ROTULOS).
"""
from collections import namedtuple

TRACKS = ["bd", "sd", "lt", "ht", "rs", "hc", "ch", "oh", "cc", "rc"]

# escopo: "pattern" (x = pattern), "kit" (x = kit)
# por_track: y = track; senao y = 0
# indice: o do BD (ou unico); por track e indice + passo_track * track
# tipo: None, ou (id do parametro TYPE, valor) quando o significado e a
# faixa mudam com o TYPE (DELAY 2-6, MFX 1-7): a entrada so vale com a maquina
# naquele type. Types nao capturados ficam sem entrada = knob inativo
# (decisao do Luan, 09/10/2026: capturar so os types que ele usa).
# passo_bloco: o BLOCO anda com o track (o LFO de cada instrumento mora no
# bloco 22 + 10 * track - inst-lfo, BD 22 e RC 112).
# condicao: None, ou (id de um SELETOR, valor) - uma 2a condicao alem do type,
# quando o mesmo knob da tela muda de indice (o STEP com SYNC ON/OFF, mfx-2).
# Em POR_TIPO, um type com condicao guarda uma tupla de alternativas.
Parametro = namedtuple("Parametro", "id bloco escopo por_track indice passo_track "
                                    "minimo maximo escala fonte tipo passo_bloco "
                                    "condicao")


def _p(id, bloco, escopo, por_track, indice, passo_track, minimo, maximo, escala,
       fonte, tipo=None, passo_bloco=0, condicao=None):
    return Parametro(id, bloco, escopo, por_track, indice, passo_track,
                     minimo, maximo, escala, fonte, tipo, passo_bloco, condicao)


# ─────────────────────────────────────────────────────────────
# A tabela (medida em 09/10/2026)
# ─────────────────────────────────────────────────────────────
_POR_TRACK = [
    #   linha        bloco escopo     indice passo   min  max  escala (visor do App)
    ("gain",          116, "pattern", 1014,    1,     0,  661, "-INF .. +6 dB"),
    ("pan",            13, "kit",      556,    0,     0, 1000, "L100% .. R100%"),
    ("rvb",            13, "kit",      557,    0,     0, 1000, "0 .. 1000"),
    ("dly",            13, "kit",      558,    0,     0, 1000, "0 .. 1000"),
]
# gain: TRK GAIN, mora no PATTERN (bloco 116, indice 1014 + track: BD 1014,
#       RC 1023 - mixer-bd e mixer-rc). pan/sends: bloco 13 com y = track
#       (mixer-bd y 0, mixer-rc y 9). Os 8 tracks do meio sao DEDUCAO pelo
#       passo (o App foi visto so no BD e no RC); SD pan/sends ouvidos no F2.2.

TABELA = {}
for _linha, _b, _esc, _i, _passo, _mn, _mx, _escala in _POR_TRACK:
    for _t in TRACKS:
        _id = f"{_t}.{_linha}"
        TABELA[_id] = _p(_id, _b, _esc, True, _i, _passo, _mn, _mx, _escala,
                         "2026-10-09-mixer-bd/rc")

for _id, _i, _mn, _mx, _escala in (
        # kit-reverb (09/10/2026): bloco 5, um por kit
        ("reverb.type",      2368, 0,    5, "AMBI ROOM HALL1 HALL2 PLATE MOD"),
        ("reverb.time",      2371, 0, 1000, "0% .. 100%"),
        ("reverb.predelay",  2402, 0,  100, "0 .. 100"),
        ("reverb.lowcut",    2403, 0,   17, "FLAT .. 800 Hz (discreto)"),
        ("reverb.highcut",   2404, 0,   14, "630 Hz .. FLAT (discreto)"),
        ("reverb.density",   2405, 0,   10, "0% .. 100% (discreto)")):
    TABELA[_id] = _p(_id, 5, "kit", False, _i, 0, _mn, _mx, _escala,
                     "2026-10-09-kit-reverb")
for _id, _i, _mn, _mx, _escala in (
        # kit-delay (09/10/2026): bloco 6, um por kit. Os comuns a todo type:
        ("delay.type",      2407, 0,    3, "DELAY PAN ECHO PITCH"),
        ("delay.rvb_send",  2410, 0, 1000, "0 .. 1000"),
        ("delay.p1",        2409, 0, 1000, "LEVEL (decisao do Luan: DELAY 1 = LEVEL)")):
    TABELA[_id] = _p(_id, 6, "kit", False, _i, 0, _mn, _mx, _escala,
                     "2026-10-09-kit-delay")
del _linha, _b, _esc, _i, _passo, _mn, _mx, _escala, _t, _id

# Os que dependem do TYPE: {id do knob: {valor do type: Parametro}}.
# DELAY 2-6 = os 5 primeiros parametros do type (decisao do Luan, 09/10/2026).
DELAY_TIPOS = ["DELAY", "PAN", "ECHO", "PITCH"]
POR_TIPO = {f"delay.p{n}": {} for n in range(2, 7)}
# Cada type tem os PROPRIOS indices (nao sao slots compartilhados - medido em
# delay-tipos, 10/10/2026). "Os 5 primeiros" = na ordem da tela do App (de
# cima, esquerda -> direita, depois a fileira de baixo), pulando LEVEL e os
# botoes. (indice, min, max, nome) por type:
_DELAY_POR_TIPO = {
    0: [(2429, 0,  14, "SYNC TIME"), (2430, 0, 998, "FEEDBACK"), (2431, 0, 14, "HIGH CUT"),
        (2432, 0,  81, "H DAMP"),    (2433, 0,  13, "H DAMP F")],           # DELAY
    1: [(2437, 0,  15, "SYNC TIME"), (2438, 0, 999, "FEEDBACK"), (2439, 0, 14, "HIGH CUT"),
        (2440, 0,  81, "H DAMP"),    (2441, 0,  13, "H DAMP F")],           # PAN
    2: [(2446, 0,  15, "SYNC TIME"), (2447, 0, 999, "INTENSITY"),
        (2448, 0,   6, "MODE (S M L S+M S+L M+L S+M+L)"),
        (2454, 0,   8, "TAPE DIST"), (2455, 0, 255, "W/F RATE")],          # ECHO
    3: [(2458, 0,  15, "SYNC TIME"), (2459, 0, 999, "FEEDBACK"), (2460, 0, 81, "H DAMP"),
        (2461, 0,  13, "H DAMP F"),  (2464, 0,  36, "COARSE")],             # PITCH
}
for _tipo, _lista in _DELAY_POR_TIPO.items():
    for _n, (_i, _mn, _mx, _nome) in enumerate(_lista, start=2):
        POR_TIPO[f"delay.p{_n}"][_tipo] = _p(
            f"delay.p{_n}", 6, "kit", False, _i, 0, _mn, _mx,
            f"{_nome} (type {DELAY_TIPOS[_tipo]})",
            "2026-10-09-kit-delay" if _tipo == 1 else "2026-10-10-delay-tipos",
            ("delay.type", _tipo))
del _tipo, _lista, _n, _i, _mn, _mx, _nome
# Medidos e fora das placas (registro), delay-tipos: DELAY L DAMP 2434 0..81,
# L DAMP F 2435 0..10; ECHO BASS 2449 0..30, TREBLE 2450 0..30, PAN S/M/L
# 2451/2452/2453 0..255, W/F DEPTH 2456 0..255; PITCH L DAMP 2462 0..81,
# L DAMP F 2463 0..10, FINE 2465 0..200; PAN L DAMP 2442, L DAMP F 2443, TAP 2444.

# kit-lfo / kit-lfo-2 (09/10/2026): o LFO do kit, bloco 10, um por kit.
# Os TARGETs dele sao so do kit (RVB DLY MFX AFX EXT_IN S_CHAIN) - nao ha
# profundidade por track; os knobs LFO DTH vao para o LFO de cada INSTRUMENTO
# (decisao do Luan, 09/10/2026), a capturar.
TABELA["lfo.waveform"] = _p("lfo.waveform", 10, "kit", False, 519, 0, 0, 4,
                            "SINE TRI SAW SQR RANDOM", "2026-10-09-kit-lfo")
LFO_MODOS = ["PATTERN", "TRIGGER", "TRIG 1X", "TRIG 1/2X", "FREE"]   # indice 520
LFO_SYNCS = ["TIME", "STEP", "NOTE"]                                 # indice 532
# O TIME (o RATE do MC-24) muda de INDICE com o SYNC (lfo-sync, 10/10/2026;
# as pontas lidas no visor do App pelo Luan):
POR_TIPO["lfo.rate"] = {
    0: _p("lfo.rate", 10, "kit", False, 529, 0, 0, 180, "TIME 10.0s .. 100ms",
          "2026-10-09-kit-lfo", ("lfo.sync", 0)),
    1: _p("lfo.rate", 10, "kit", False, 530, 0, 0, 255, "STEP 64.00stp .. 0.25stp",
          "2026-10-10-lfo-sync", ("lfo.sync", 1)),
    2: _p("lfo.rate", 10, "kit", False, 531, 0, 0, 24, "NOTE 4/1 .. 1/64",
          "2026-10-10-lfo-sync", ("lfo.sync", 2)),
}

# inst-lfo (10/10/2026): LFO DTH = o AMOUNT 1 do MODULATOR LFO de cada
# instrumento (decisao do Luan). Bloco 22 + 10*track (BD 22, RC 112: o grupo de
# 9 subblocos por track da REFERENCIA 2.1c), indice 606, 500..1500 com 1000 no
# centro (bipolar, como os AMOUNT do LFO do kit).
for _n, _t in enumerate(TRACKS):
    TABELA[f"{_t}.lfo"] = _p(f"{_t}.lfo", 22, "kit", True, 606, 0, 500, 1500,
                             "AMOUNT 1 do LFO do inst. (-500 .. +500)",
                             "2026-10-10-inst-lfo", passo_bloco=10)
del _n, _t

# Os parametros que dizem o TYPE/SYNC atual: o motor LE antes de escrever um
# knob dependente. Nao sao knobs - nao entram no portao de escrita.
SELETORES = {
    "delay.type": _p("delay.type", 6, "kit", False, 2407, 0, 0, 3, "", "2026-10-09-kit-delay"),
    "lfo.sync":   _p("lfo.sync", 10, "kit", False, 532, 0, 0, 2, "TIME STEP NOTE",
                     "2026-10-09-kit-lfo-2"),
}

# mfx-1/2/3 (10/10/2026): o MASTER FX, bloco 7, um por kit. TYPE no indice
# 2512, na ordem do seletor do App (manual RM p.56): os 19, BYPASS = 0
# incluido, medidos.
MFX_TIPOS = ["BYPASS", "CRUSHER", "FILTER+DRIVE", "DJFX LOOPER", "ISOLATOR",
             "SCATTER", "FLANGER", "PHASER", "SIDE BAND FILTER", "COMPRESSOR",
             "FET COMP 76", "SDD-320", "TRANSIENT", "TRANSIENT2", "NOISE",
             "303 VINYL SIM", "404 VINYL SIM", "CASSETTE SIM", "DJFX DELAY"]
TABELA["mfx.type"] = _p("mfx.type", 7, "kit", False, 2512, 0, 0, len(MFX_TIPOS) - 1,
                        "BYPASS CRUSHER .. DJFX DELAY", "2026-10-10-mfx-1/2/3")
SELETORES["mfx.type"] = TABELA["mfx.type"]
# O SYNC do FLANGER e do PHASER muda o INDICE do STEP (o knob continua se
# chamando STEP na tela - mfx-2): seletores proprios, lidos como o TYPE.
SELETORES["mfx.sync.flanger"] = _p("mfx.sync.flanger", 7, "kit", False, 2561, 0, 0, 1,
                                   "OFF ON", "2026-10-10-mfx-2")
SELETORES["mfx.sync.phaser"] = _p("mfx.sync.phaser", 7, "kit", False, 2570, 0, 0, 1,
                                  "OFF ON", "2026-10-10-mfx-2")
# MFX 1-7 = os parametros do efeito na ordem da tela (de cima, esquerda ->
# direita, depois a fileira de baixo), com os menus e sem os botoes (SYNC) e
# o FX ROUTE - a mesma regra do DELAY 2-6. Como no delay, cada efeito tem os
# PROPRIOS indices. (indice, min, max, nome) por type; um STEP que depende do
# SYNC e uma lista de (seletor, valor, indice) no lugar do indice.
_STEP_FLANGER = [("mfx.sync.flanger", 0, 2557), ("mfx.sync.flanger", 1, 2564)]
_STEP_PHASER = [("mfx.sync.phaser", 0, 2566), ("mfx.sync.phaser", 1, 2572)]
_MFX_POR_TIPO = {
    1: [(2536, 0, 255, "BALANCE"), (2537, 0, 255, "SAMPLE"), (2538, 0, 255, "FILTER")],
    2: [(2539, 0, 255, "CUTOFF"),  (2540, 0, 255, "RESO"),   (2541, 0, 255, "DRIVE"),
        (2542, 0,   1, "TYPE (menu HPF/LPF)"), (2543, 0, 255, "LOW FREQ"),
        (2544, 0,  48, "LOW GAIN")],
    3: [(2545, 0, 255, "LENGTH"),  (2546, 0, 200, "SPEED"),  (2547, 0, 1, "LOOP SW (OFF ON)")],
    4: [(2548, 0, 255, "LOW"),     (2549, 0, 255, "MID"),    (2550, 0, 255, "HIGH")],
    5: [(2551, 0,   9, "TYPE"),    (2552, 0,   9, "DEPTH"),  (2553, 0, 1, "SCATTER (OFF ON)"),
        (2554, 0, 255, "BALANCE")],
    6: [(2556, 0, 255, "DEPTH"),   (_STEP_FLANGER, 0, 255, "STEP"),
        (2558, 0, 255, "MANUAL"),  (2559, 0, 255, "RESO"),   (2563, 0, 1, "MODE (MONO STEREO)"),
        (2560, 0, 255, "BALANCE"), (2562, 0,  17, "LOW CUT")],
    7: [(2565, 0, 255, "DEPTH"),   (_STEP_PHASER, 0, 255, "STEP"),
        (2567, 0, 255, "MANUAL"),  (2568, 0, 255, "RESO"),
        (2571, 0,   3, "TYPE (4ST 8ST 12ST BI-PH)"), (2569, 0, 255, "BALANCE")],
    8: [(2573, 0,   5, "TYPE (SBF1..SBF6)"), (2574, 0, 255, "INTERVAL"),
        (2575, 0, 247, "WIDTH"),   (2576, 0, 255, "BALANCE"), (2577, 0, 255, "GAIN")],
    9: [(2578, 0, 255, "BALANCE"), (2579, 0, 255, "ATTACK"), (2580, 0, 255, "RELEASE"),
        (2581, 0,  40, "THRESHLD"), (2582, 0, 61, "RATIO"),  (2583, 0,  20, "KNEE"),
        (2584, 0,  80, "GAIN")],
    10: [(2585, 0, 241, "IN LEVEL"), (2586, 0, 241, "OUT LEVEL"), (2587, 0, 70, "ATTACK"),
         (2588, 0,  70, "RELEASE"),
         (2589, 0,   4, "RATIO (4 8 12 20 ALL)"), (2590, 0, 100, "BALANCE")],
    11: [(2591, 0,   6, "MODE (1 2 3 4 1+4 2+4 3+4)"), (2592, 0, 150, "LO GAIN"),
         (2593, 0, 150, "HI GAIN"), (2594, 0, 255, "LEVEL")],
    12: [(2595, 0, 255, "ENV DEPTH"), (2596, 0, 255, "ATTACK"), (2597, 0, 255, "RELEASE")],
    13: [(2598, 0, 255, "ENV DEPTH"), (2599, 0, 255, "ATTACK"), (2600, 0, 255, "RELEASE"),
         (2604, 0, 255, "LP LEVEL"),  (2603, 0, 255, "BP LEVEL"), (2602, 0, 255, "HP LEVEL"),
         (2605, 0, 255, "BYPASS")],                     # o 8o, Q 2601 0..7, fica fora
    14: [(2606, 0, 255, "COLOR"),   (2607, 0, 255, "LEVEL"),
         (2608, 0,   1, "DIRECTION (UP DOWN)")],
    15: [(2609, 0, 255, "COMP"),    (2610, 0, 255, "NOISE"),  (2611, 0, 255, "WOW FLUT"),
         (2612, 0, 255, "LEVEL")],
    16: [(2613, 0, 255, "FREQ"),    (2614, 0, 255, "NOISE"),  (2615, 0, 255, "WOW FLUT")],
    17: [(2616, 0, 255, "TONE"),    (2617, 0, 255, "HISS"),   (2618, 0, 255, "AGE"),
         (2619, 0, 255, "DRIVE"),   (2620, 0, 255, "WOW FLUT")],
    18: [(2621, 0, 255, "LENGTH"),  (2622, 0, 255, "TIME"),   (2623, 0, 1, "LOOP SW (OFF ON)"),
         (2624, 0, 255, "FEEDBACK"), (2625, 0, 255, "LEVEL")],
}
for _n in range(1, 8):
    POR_TIPO[f"mfx.p{_n}"] = {}
for _tipo, _lista in _MFX_POR_TIPO.items():
    _fonte = "2026-10-10-mfx-" + ("1" if _tipo <= 6 else "2" if _tipo <= 12 else "3")
    for _n, (_i, _mn, _mx, _nome) in enumerate(_lista, start=1):
        _id, _escala = f"mfx.p{_n}", f"{_nome} (type {MFX_TIPOS[_tipo]})"
        if isinstance(_i, list):                  # o indice depende do SYNC
            POR_TIPO[_id][_tipo] = tuple(
                _p(_id, 7, "kit", False, _ii, 0, _mn, _mx,
                   f"{_escala}, SYNC {'ON' if _v else 'OFF'}", "2026-10-10-mfx-2",
                   ("mfx.type", _tipo), condicao=(_sel, _v))
                for _sel, _v, _ii in _i)
        else:
            POR_TIPO[_id][_tipo] = _p(_id, 7, "kit", False, _i, 0, _mn, _mx, _escala,
                                      _fonte, ("mfx.type", _tipo))
del _tipo, _lista, _n, _i, _mn, _mx, _nome, _id, _escala, _fonte
# Medidos e fora das placas (registro), mfx-1/2: OFF 2513 0..1 (ON = 1; o
# botao ao lado do seletor, tocado sem querer no comeco da mfx-2); FX ROUTE
# 2514 0..1 (THROUGH ANALOG neste kit); SYNC do FLANGER 2561 e do PHASER 2570
# (ON = 1). Faixas que o giro NAO levou ao 255: SBF WIDTH 247 e FET IN/OUT
# LEVEL 241 - o portao aceita so o medido. mfx-3: o SYNC do DJFX DELAY (2626,
# ON = 1) NAO muda o indice do TIME (2622 foi a 0..255 nos dois); o TRANSIENT2
# tem 8 parametros e o Q (2601, 0..7, o ultimo da tela) fica fora das placas. A leitura em bloco do App cobre
# 2512..2534 (o comum do MFX); os parametros de cada efeito ele le um a um.
# Medidos e fora das placas (registro): LFO do kit PHASE 521 0..359, S&H 522
# 0..19, AMOUNT 1/2/3 523/524/525 500..1500 (centro 1000), MODE 520 (LFO_MODOS).
# Medidos e fora das placas (registro): SYNC 2408 0..1, FX ROUTE 2411 0..2
# (THROUGH MASTER ANALOG), SC DEPTH 2414 0..1000; no PAN: L DAMP 2442 0..81,
# L DAMP F 2443 0..10, TAP 2444 0..100.


# Os nomes dos knobs de escolha, para o terminal dizer onde o knob parou (o
# painel nao mostra o type do MFX - ROTEIRO-F2, 10/10/2026)
NOMES = {
    "reverb.type":  TABELA["reverb.type"].escala.split(),
    "delay.type":   DELAY_TIPOS,
    "mfx.type":     MFX_TIPOS,
    "lfo.waveform": TABELA["lfo.waveform"].escala.split(),
}


def todas_as_entradas():
    """A tabela fixa e as dependentes de type, para o portao."""
    yield from TABELA.values()
    for por_valor in POR_TIPO.values():
        for e in por_valor.values():
            yield from ((e,) if isinstance(e, Parametro) else e)


def seletor_de(id):
    """O SELETOR do TYPE que decide a entrada de um knob dependente de type
    (delay.type, lfo.sync, mfx.type), ou None para os da TABELA."""
    if id in TABELA or not POR_TIPO.get(id):
        return None
    e = next(iter(POR_TIPO[id].values()))
    return (e if isinstance(e, Parametro) else e[0]).tipo[0]


def condicoes_de(id, tipo_atual):
    """Os seletores de condicao que a entrada desse type precisa (ex.: o SYNC
    do FLANGER para o MFX 2 no FLANGER); vazio se ela nao depende de nada."""
    e = POR_TIPO.get(id, {}).get(tipo_atual)
    if e is None or isinstance(e, Parametro):
        return []
    return list(dict.fromkeys(a.condicao[0] for a in e))


def entrada_para(id, tipo_atual=None, seletores=None):
    """O Parametro de um knob com a maquina no type `tipo_atual` (o valor do
    TYPE correspondente), ou None se o knob esta inativo nesse type. Se o
    indice depende de outro seletor (condicao), `seletores` {id: valor} diz
    qual alternativa vale; sem o valor dele, o knob fica inativo."""
    if id in TABELA:
        return TABELA[id]
    e = POR_TIPO.get(id, {}).get(tipo_atual)
    if e is not None and not isinstance(e, Parametro):
        seletores = seletores or {}
        return next((a for a in e if seletores.get(a.condicao[0]) == a.condicao[1]), None)
    return e

# O que as placas tem e ainda nao foi decifrado (B2): o mapa nao esquece ninguem
PENDENTES = []


def endereco(p, x, track=0):
    """(bloco, x, y, indice) de um parametro para o pattern/kit x."""
    if p.passo_bloco:                             # o bloco anda com o track
        return p.bloco + p.passo_bloco * track, x, 0, p.indice
    if p.por_track:
        if p.passo_track:                         # o indice anda com o track
            return p.bloco, x, 0, p.indice + p.passo_track * track
        return p.bloco, x, track, p.indice        # o y e o track
    return p.bloco, x, 0, p.indice


def track_do_id(id):
    return TRACKS.index(id.split(".")[0]) if id.split(".")[0] in TRACKS else 0


def parametro_no_endereco(bloco, x, y, indice):
    """O primeiro parametro da tabela que mora nesse endereco (qualquer x), ou
    None. Com varias entradas no mesmo endereco (types diferentes),
    escrita_permitida confere cada uma."""
    return next((p for p in todas_as_entradas() if _casa(p, bloco, y, indice)), None)


def _casa(p, bloco, y, indice):
    if p.passo_bloco:
        rel = bloco - p.bloco
        return (y == 0 and indice == p.indice and rel % p.passo_bloco == 0
                and 0 <= rel // p.passo_bloco < len(TRACKS))
    if bloco != p.bloco:
        return False
    if p.por_track and p.passo_track:
        rel = indice - p.indice
        return y == 0 and rel % p.passo_track == 0 and 0 <= rel // p.passo_track < len(TRACKS)
    if p.por_track:
        return indice == p.indice and 0 <= y < len(TRACKS)
    return indice == p.indice and y == 0


def escrita_permitida(bloco, x, y, indice, valor):
    """O endereco e de um parametro decifrado e o valor esta na faixa medida
    de ALGUMA entrada dele (o type certo o motor confere antes de escrever)."""
    if not 0 <= x < 128:
        return False
    return any(_casa(p, bloco, y, indice) and p.minimo <= valor <= p.maximo
               for p in todas_as_entradas())


def converter(p, cc, cc_min=0, cc_max=127):
    """Posicao do knob (cc dentro da faixa medida do knob) -> valor do parametro.
    Linear e arredondado: os discretos (TYPE, LOW CUT...) caem no inteiro mais
    perto, e o knob inteiro cobre a faixa inteira mesmo parando em 125."""
    cc_max = max(cc_max, cc_min + 1)
    f = (min(max(cc, cc_min), cc_max) - cc_min) / (cc_max - cc_min)
    return int(round(p.minimo + f * (p.maximo - p.minimo)))

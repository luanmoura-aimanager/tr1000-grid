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
Parametro = namedtuple("Parametro", "id bloco escopo por_track indice passo_track "
                                    "minimo maximo escala fonte")


def _p(id, bloco, escopo, por_track, indice, passo_track, minimo, maximo, escala, fonte):
    return Parametro(id, bloco, escopo, por_track, indice, passo_track,
                     minimo, maximo, escala, fonte)


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
#       (mixer-bd y 0, mixer-rc y 9).

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
del _linha, _b, _esc, _i, _passo, _mn, _mx, _escala, _t, _id

# O que as placas tem e ainda nao foi decifrado (B2): o mapa nao esquece ninguem
PENDENTES = (["lfo.rate", "lfo.waveform", "delay.type", "delay.rvb_send"]
             + [f"delay.p{i}" for i in range(1, 7)]
             + ["mfx.type"] + [f"mfx.p{i}" for i in range(1, 8)]
             + [f"{t}.lfo" for t in TRACKS])


def endereco(p, x, track=0):
    """(bloco, x, y, indice) de um parametro para o pattern/kit x."""
    if p.por_track:
        if p.passo_track:                         # o indice anda com o track
            return p.bloco, x, 0, p.indice + p.passo_track * track
        return p.bloco, x, track, p.indice        # o y e o track
    return p.bloco, x, 0, p.indice


def track_do_id(id):
    return TRACKS.index(id.split(".")[0]) if id.split(".")[0] in TRACKS else 0


def parametro_no_endereco(bloco, x, y, indice):
    """O parametro da tabela que mora nesse endereco (qualquer x), ou None."""
    for p in TABELA.values():
        if p.bloco != bloco:
            continue
        if p.por_track and p.passo_track:
            rel = indice - p.indice
            if y == 0 and rel % p.passo_track == 0 and 0 <= rel // p.passo_track < len(TRACKS):
                return p
        elif p.por_track:
            if indice == p.indice and 0 <= y < len(TRACKS):
                return p
        elif indice == p.indice and y == 0:
            return p
    return None


def escrita_permitida(bloco, x, y, indice, valor):
    """O endereco e de um parametro decifrado e o valor esta na faixa medida."""
    p = parametro_no_endereco(bloco, x, y, indice)
    return p is not None and 0 <= x < 128 and p.minimo <= valor <= p.maximo


def converter(p, cc, cc_min=0, cc_max=127):
    """Posicao do knob (cc dentro da faixa medida do knob) -> valor do parametro.
    Linear e arredondado: os discretos (TYPE, LOW CUT...) caem no inteiro mais
    perto, e o knob inteiro cobre a faixa inteira mesmo parando em 125."""
    cc_max = max(cc_max, cc_min + 1)
    f = (min(max(cc, cc_min), cc_max) - cc_min) / (cc_max - cc_min)
    return int(round(p.minimo + f * (p.maximo - p.minimo)))

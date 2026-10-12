#!/usr/bin/env python3
"""
campos.py - o que o PAINEL mostrou onde mora (C5/C5b/C5c, 10/10/2026), para o
grid e o Controller lerem e escreverem. A contraparte do parametros.py, que e
o que o App foi visto escrevendo.

Tudo aqui foi MEDIDO pelo painel: um gesto, uma foto, o diff (REFERENCIA
7.6). Escrever nestes enderecos foi liberado pelo Luan em 10/10/2026, grupo a
grupo (step, cabecalho, performance do bloco 3) - cada um so com a faixa
medida, e cada um a testar no ROTEIRO-F3 antes de valer. O accent fica de
fora da escrita: ele e feito no painel (decisao do Luan, 10/10/2026, 22:30).

Indices ABSOLUTOS = o inicio da faixa que o App le + a posicao vista no diff
(steps 1249, cabecalho 988, bloco 3 112, accent 1236).
"""
from collections import namedtuple

import tr1000_serial as ts

INI_STEPS = ts.INDICE_STEPS                   # 1249
INI_CAB = 988                                 # bloco 116 (medido: faixa do App)
INI_B3 = 112                                  # bloco 3
INI_ACC = 1236                                # bloco 117 + 3v, y 0
N_STEPS, N_TRACKS, N_VARS = 16, 10, 12        # 12 = A..H + Fill 1..4
B3, CAB = 3, ts.BLOCO_CAB_PATTERN             # 3, 116

# ── no bloco de steps (118 + 3v, y = track) ───────────────────
#              pos   min   max  (medido)
CAMPOS_STEP = {
    "prob":  (64,    0,  100),                # c5: 100 -> 50
    "sub":   (80,    0,   13),                # c5c: o mapa inteiro
    "cycle": (98,    0,   37),                # c5c: o mapa inteiro
    "start": (114, -100, 100),                # c5c: -100..+100, u32 com sinal
}
SUB_NOMES = ["OFF", "1/2", "1/3", "1/4", "Flam", "Triplet 1", "Triplet 2", "Triplet 3",
             "Triplet 4", "Quad 1", "Quad 2", "Quad 3", "Quad 4", "Quad 5"]
CYCLE_NOMES = ([f"{a}/{b}" for b in range(1, 9) for a in range(1, b + 1)]
               + ["1st Only", "Except 1st"])   # o "a/b" vale b(b-1)/2 + a - 1
BIT_ALT = 1 << 23                              # c5: A503C -> 8A503C no RS

# ── no cabecalho do pattern (116, y 0, x = pattern) ───────────
CAB_VARIACOES = 18                             # mascara A=1, B=2, A+B=3 (c5)
CAB_SCALE = 36                                 # 0 8th(T) 1 16th(T) 2 16th 3 32nd (c5/c5c)
CAB_FIRST_VAR, CAB_LAST_VAR = 60, 72           # + v, 0-based (c5c / c5)
CAB_FIRST_TRK, CAB_LAST_TRK = 84, 95           # + track, 0-based (c5c / c5)
CAB_TRK_SW = 106                               # + track: o track tem FIRST/LAST proprio
CAB_FILL = 119                                 # 0 FILL1, 1 FILL2 (c5); 2-3 NAO medidos
SCALES = ["8th(T)", "16th(T)", "16th", "32nd"]

# ── no bloco 3 (estado da maquina, x 0) ───────────────────────
B3_MODO_MUTE, B3_MUTE = 11, 12                 # c5/c5c: o modo, e a mascara por track
B3_LOOP, B3_LOOP_STEP = 150, 151               # c5b: o modo, e o step segurado (+ s)

Campo = namedtuple("Campo", "bloco y indice minimo maximo")


def campo_step(nome, v, track, step):
    pos, mn, mx = CAMPOS_STEP[nome]
    return Campo(ts.bloco_de_steps(v), track, INI_STEPS + pos + step, mn, mx)


def campo_cab(pos, minimo, maximo):
    return Campo(CAB, 0, INI_CAB + pos, minimo, maximo)


def u32(v):
    """-100..100 -> o u32 que a maquina guarda (START, c5c: -100 = FFFFFF9C)."""
    return v & 0xFFFFFFFF


def com_sinal(v):
    return v - (1 << 32) if v & 0x80000000 else v


def acentos(mascara):
    """A mascara de accent (16 bits em nibbles, como na TR-8S: o nibble k sao os
    steps 4k+1..4k+4) -> os 16 steps, True/False. c5: 1111 = 1, 5, 9, 13."""
    return [bool(mascara >> s & 1) for s in range(N_STEPS)]


def mudos(mascara):
    return [bool(mascara >> t & 1) for t in range(N_TRACKS)]


def eh_alt(valor):
    return bool(valor & BIT_ALT) and ts.eh_nota(valor & ~BIT_ALT)


# ── a regra de escrita (o portao chama) ───────────────────────
def _no_cab(indice):
    """(minimo, maximo) do campo do cabecalho nesse indice, ou None."""
    p = indice - INI_CAB
    if p == CAB_VARIACOES:
        return 1, (1 << N_VARS) - 1             # pelo menos uma variacao
    if p == CAB_SCALE:
        return 0, len(SCALES) - 1
    if p == CAB_FILL:
        return 0, 1                             # so o medido (revisao do PR #7)
    if CAB_FIRST_VAR <= p < CAB_FIRST_VAR + N_VARS or CAB_LAST_VAR <= p < CAB_LAST_VAR + N_VARS:
        return 0, N_STEPS - 1
    if CAB_FIRST_TRK <= p < CAB_FIRST_TRK + N_TRACKS or CAB_LAST_TRK <= p < CAB_LAST_TRK + N_TRACKS:
        return 0, N_STEPS - 1
    if CAB_TRK_SW <= p < CAB_TRK_SW + N_TRACKS:
        return 0, 1
    return None


def _no_b3(indice):
    p = indice - INI_B3
    if p == B3_MUTE:
        return 0, (1 << N_TRACKS) - 1
    if p == B3_LOOP or B3_LOOP_STEP <= p < B3_LOOP_STEP + N_STEPS:
        return 0, 1
    return None


def _no_step(indice, valor, track):
    rel = indice - INI_STEPS
    for nome, (pos, mn, mx) in CAMPOS_STEP.items():
        if pos <= rel < pos + N_STEPS:
            v = com_sinal(valor) if mn < 0 else valor
            return mn <= v <= mx
    # o ALT: so no slot 0 dos tracks simples (RS..RC), nota com o bit 23
    if 0 <= rel < 4 * N_STEPS and rel % 4 == 0 and track >= 4:
        return eh_alt(valor)
    return None


def escrita_permitida(bloco, x, y, indice, valor):
    """Um campo medido pelo painel, com valor dentro da faixa. Os steps (nota
    ou pausa) continuam na regra do conexao_serial; aqui so o resto."""
    if not 0 <= x < 128:
        return False
    if bloco == CAB and y == 0:
        f = _no_cab(indice)
        return f is not None and f[0] <= valor <= f[1]
    if bloco == B3 and x == 0 and y == 0:
        f = _no_b3(indice)
        return f is not None and f[0] <= valor <= f[1]
    if bloco in {ts.bloco_de_steps(v) for v in range(N_VARS)} and 0 <= y < N_TRACKS:
        return bool(_no_step(indice, valor, y))
    return False


# ─────────────────────────────────────────────────────────────
# A pagina PAR do Launchpad (layout A, fase 2d): 8 niveis por coluna, de
# baixo (0) para cima (7). Um toque na linha poe o valor daquele nivel no
# step. As listas inteiras ficam na tela; aqui, as 8 mais usadas de cada.
# ─────────────────────────────────────────────────────────────
PAR_PARAMS = ("prob", "sub", "cycle", "start", "vel", "alt")
NIVEIS_PAR = {
    "prob":  (0, 14, 28, 43, 57, 71, 86, 100),
    # OFF, 1/2, 1/3, 1/4, Flam, Triplet 1, Triplet 2, Quad 1 (SUB_NOMES)
    "sub":   (0, 1, 2, 3, 4, 5, 6, 9),
    # 1/1, 1/2, 2/2, 1/3, 1/4, 1/8, 1st Only, Except 1st (CYCLE_NOMES)
    "cycle": (0, 1, 2, 3, 6, 28, 36, 37),
    # o 0 no 4o nivel: tres para tras, quatro para frente
    "start": (-100, -67, -33, 0, 25, 50, 75, 100),
    "vel":   (10, 30, 50, 66, 80, 100, 110, 127),
}
# os que sao escolha (nao quantidade): so o nivel exato acende, sem barra
PAR_ESCOLHA = ("sub", "cycle")


def nivel_par(nome, valor):
    """O nivel (0..7) que mostra `valor`: o exato nos de escolha (-1 se nao
    esta entre os 8); nos de quantidade, o mais proximo."""
    niveis = NIVEIS_PAR[nome]
    if valor is None:
        return -1
    if nome in PAR_ESCOLHA:
        return niveis.index(valor) if valor in niveis else -1
    return min(range(len(niveis)), key=lambda i: abs(niveis[i] - valor))

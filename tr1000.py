#!/usr/bin/env python3
"""
tr1000.py - o modelo da TR-1000: o que sabemos dela, e de onde veio cada coisa

Cada constante diz a FONTE na coluna de comentario:
    (manual MIC p.N)    MIDI Implementation Chart, versao 1.20, 14/04/2026
    (manual RM p.N)     Reference Manual eng03 (firmware 1.20+)
    (catalogo)          ordem de nomes no binario do TR-1000 App (catalogo_app.py)
    (medido DD/MM)      visto nesta maquina, com o metodo da REFERENCIA 3.2
    (deduzido)          inferencia nossa, a confirmar

O manual descreve o que a maquina PODE fazer; so o (medido) descreve o que ela
FAZ aqui. Na TR-8S a tabela de CC do manual estava certa e mesmo assim a
maquina nao transmitia CC nenhum (tr8s-grid REFERENCIA 2295) - nao confunda.

O mapa SysEx (enderecos de pattern, step, performance) NAO esta aqui ainda:
sai das sessoes C1/C2 (REFERENCIA 2.1). Ate la, nada neste projeto escreve
na maquina.
"""

# ─────────────────────────────────────────────────────────────
# Portas (medido 07/10/2026, `lp_tr1000.py ports`)
# ─────────────────────────────────────────────────────────────
PORTA_COMUM = "TR-1000"            # clock, notas, CC - nome EXATO (medido 07/10)
PORTA_CTRL  = "TR-1000 CTRL"       # onde o App fala; candidata ao SysEx (medido 07/10)
# "TR-1000 MIDI IN" / "MIDI OUT 1" / "MIDI OUT 2" sao as DIN do painel
# traseiro vistas pela USB (deduzido do nome; o manual RM p.11 tem as tomadas)

# ─────────────────────────────────────────────────────────────
# Tracks (manual RM p.12, 75)
# ─────────────────────────────────────────────────────────────
TRACKS        = ["BD", "SD", "LT", "HT", "RS", "HC", "CH", "OH", "CC", "RC"]
TRACKS_LAYER  = ["BD", "SD", "LT", "HT"]       # dois GEN, A e B, misturados pelo MIX
TRACKS_SIMPLES = ["RS", "HC", "CH", "OH", "CC", "RC"]   # tem ALT no lugar de layer
LINHAS        = TRACKS + ["ACC", "TRG"]        # as 12 linhas do grid

VARIACOES     = ["A", "B", "C", "D", "E", "F", "G", "H"]
FILLS         = ["Fill 1", "Fill 2", "Fill 3", "Fill 4"]          # (manual RM p.22)

# ─────────────────────────────────────────────────────────────
# Notas, MIDI Mode = Single Ch., no Pattern Ch. (manual MIC p.2)
# Mudam no MENU > SYSTEM > MIDI > Inst Note - por isso sao "padrao".
# ─────────────────────────────────────────────────────────────
CANAL_PATTERN_PADRAO = 10          # 1-based, como no visor (manual MIC p.1)
CANAL_KIT_PADRAO     = 1

#                 normal  layer A  layer B / ALT
NOTAS_PADRAO = {
    "BD":       (   36,     35,      99),
    "SD":       (   38,     40,     104),
    "LT":       (   43,     41,     105),
    "HT":       (   50,     48,     112),
    "RS":       (   37,   None,      56),
    "HC":       (   39,   None,      54),
    "CH":       (   42,   None,      44),
    "OH":       (   46,   None,      58),
    "CC":       (   49,   None,      61),
    "RC":       (   51,   None,      63),
    "TRG":      (   84,   None,    None),
}


def nome_da_nota(nota):
    """'BD', 'BD (A)', 'RS (ALT)'... ou None. So vale com as notas padrao."""
    for trk, (normal, a, b) in NOTAS_PADRAO.items():
        if nota == normal:
            return trk
        if nota == a:
            return f"{trk} (A)"
        if nota == b:
            return f"{trk} ({'B' if trk in TRACKS_LAYER else 'ALT'})"
    return None


# ─────────────────────────────────────────────────────────────
# Control Change: os 66 da chart, todos Tx e Rx (manual MIC p.1)
# Precisam de MENU > SYSTEM > MIDI > Rx/Tx Edit Data = ON.
# ─────────────────────────────────────────────────────────────
CC = {
     9: "EXT IN",
    12: "DELAY LEVEL",     13: "DELAY TIME",      14: "DELAY FEEDBACK",
    15: "MASTER FX ON",    16: "MASTER FX CTRL1", 17: "MASTER FX CTRL2",
    18: "MASTER FX CTRL3", 19: "ANALOG FX ON",    20: "AFX FILTER",
    21: "AFX DRIVE",
    22: "BD TUNE",  23: "BD DECAY",  24: "BD MIX",   25: "BD CTRL1",
    26: "BD CTRL2", 27: "BD CTRL3",  28: "BD LEVEL",
    29: "SD TUNE",  30: "SD DECAY",  31: "SD MIX",   46: "SD CTRL1",
    47: "SD CTRL2", 48: "SD CTRL3",  49: "SD LEVEL",
    50: "LT TUNE",  51: "LT DECAY",  52: "LT MIX",   53: "LT CTRL1",
    54: "LT CTRL2", 55: "LT CTRL3",  56: "LT LEVEL",
    57: "HT TUNE",  58: "HT DECAY",  59: "HT MIX",   60: "HT CTRL1",
    61: "HT CTRL2", 62: "HT CTRL3",  63: "HT LEVEL",
    80: "RS TUNE",  81: "RS DECAY",  82: "RS CTRL",  83: "RS LEVEL",
    84: "HC TUNE",  85: "HC DECAY",  86: "HC CTRL",  87: "HC LEVEL",
    89: "MORPH",
    90: "REVERB TIME",     91: "REVERB LEVEL",
   102: "CH TUNE", 103: "CH DECAY", 104: "CH CTRL", 105: "CH LEVEL",
   106: "OH TUNE", 107: "OH DECAY", 108: "OH CTRL", 109: "OH LEVEL",
   110: "CC TUNE", 111: "CC DECAY", 112: "CC CTRL", 113: "CC LEVEL",
   114: "RC TUNE", 115: "RC DECAY", 116: "RC CTRL", 117: "RC LEVEL",
}

#!/usr/bin/env python3
"""
sessao_c4.py - leituras ao vivo para os criterios 4 e 5 do portao (REFERENCIA 3.1)

    python3 sessao_c4.py pattern                 # le o pattern atual inteiro e
                                                 # mostra a grade (12 bancos x 10 tracks)
    python3 sessao_c4.py estado [--segundos 8]   # le os blocos de sistema/performance
                                                 # ~17x por segundo e mostra o que MUDA
    python3 sessao_c4.py foto <nome>             # le TUDO que o App le no boot, no
                                                 # pattern atual -> capturas/<data>-<nome>.serlog
    python3 sessao_c4.py diff <nome-a> <nome-b>  # o que mudou entre duas fotos
    python3 sessao_c4.py c5                      # a sessao guiada do ROTEIRO-C5: um gesto,
                                                 # uma foto, o diff na hora

SO LE. Nada aqui escreve: as leituras passam pelo mesmo portao de saida da
conexao_serial (so dentro das faixas que o proprio App leu no boot), e escrita
nao existe neste arquivo. O TR-1000 App (original e copia) tem que estar
FECHADO.

Criterio 4 (cumprido em 08/10/2026): o pattern entra no endereco, no x dos
blocos de pattern, e o x e o indice global do bloco 3 [2] (REFERENCIA 2.1c).
`pattern` le o bloco 3, calcula o x e le o pattern inteiro - so se o App ja
leu aquele x numa captura de referencia.

foto/diff (fase 2, ROTEIRO-C5): o snapdiff da TR-8S pela serial. Uma foto,
UM gesto no painel, outra foto, o gesto inverso, mais uma - e o diff diz onde
o gesto mora (Metodo 3.2). Duas fotos sem gesto no meio dao o piso de ruido.

Criterio 5: o step atual. Com a maquina TOCANDO, `estado` mostra quais valores
mudam entre leituras; o que andar em ciclo 0..15 (ou 1..16) no ritmo do
tempo e o candidato a cur_step. Rode tambem PARADA, para o piso de ruido
(Metodo, regra 2).
"""
import sys, time

import conexao_serial as cs
import tr1000_serial as ts

# Os blocos sem instancia que o App le no boot e que nao sao pattern: o 3
# (sistema/performance? 292 valores) e os pequenos 4..12 (REFERENCIA 2.1c).
BLOCOS_DE_ESTADO = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def _ler_bloco(c, bloco, x=0, y=0):
    indice, n = cs.faixa_do_bloco(bloco, x, y)     # PermissionError se nunca lido
    return c.ler(bloco, x, y, indice, n)


def chaves_do_pattern(x):
    """As 121 chaves (bloco, x, y) que ler_pattern le."""
    ks = [(ts.BLOCO_CAB_PATTERN, x, 0)]
    for v in range(len(ts.VARIACOES_SERIAL)):
        ks += [(ts.bloco_de_steps(v), x, tr) for tr in range(len(ts.TRACKS_SERIAL))]
    return ks


def pattern_atual(c):
    """(nome '1-01', x, tempo) lidos do bloco 3: o pattern SELECIONADO no
    painel. x e o indice global ([2]), que e o x dos blocos de pattern."""
    b3 = _ler_bloco(c, 3)
    x = b3[ts.OFF_PATTERN_GLOBAL]
    return ts.nome_do_pattern(x), x, b3[ts.OFF_TEMPO_ATUAL] / 100


def ler_pattern(c, x):
    """{(bloco, x, y): [u32...]} do cabecalho e dos 12 bancos x 10 tracks do
    pattern x. Recusa (PermissionError, pelo portao) se o App nunca leu esse
    x numa captura de referencia."""
    vals = {(ts.BLOCO_CAB_PATTERN, x, 0): _ler_bloco(c, ts.BLOCO_CAB_PATTERN, x)}
    for v in range(len(ts.VARIACOES_SERIAL)):
        bloco = ts.bloco_de_steps(v)
        for tr in range(len(ts.TRACKS_SERIAL)):
            vals[(bloco, x, tr)] = _ler_bloco(c, bloco, x, tr)
    return vals


def cmd_pattern():
    with cs.ConexaoTR1000(nome_captura="c4-pattern") as c:
        print(f"aperto de mao: versao {c.aperto()!r}")
        nome, x, tempo = pattern_atual(c)
        print(f"selecionado no painel (bloco 3): pattern {nome} -> x {x}, "
              f"tempo {tempo}")
        # TODAS as chaves antes de ler qualquer uma: ou o pattern sai inteiro,
        # ou nada sai (revisao do PR #3)
        if not all(cs.chave_lida(*k) for k in chaves_do_pattern(x)):
            print(f"(!) o pattern {nome} (x {x}) esta fora do que se pode ler "
                  f"(x 0..127, REFERENCIA 2.1c). Nada lido.")
            return
        t = time.time()
        vals = ler_pattern(c, x)
        print(f"({len(vals) + 1} leituras em {time.time() - t:.2f} s)\n")
    for l in ts.linhas_do_pattern(vals, x):
        print(l)
    print(f"\ncaptura: {c.captura}")


def mudancas(amostras):
    """[(t, {(bloco, i): valor})] -> {(bloco, i): [(t, valor), ...]} so dos
    que mudaram, com cada troca de valor (nao cada leitura)."""
    if not amostras:
        return {}
    out = {}
    for k in amostras[0][1]:
        serie, ultimo = [], None
        for t, a in amostras:
            v = a.get(k)
            if v != ultimo:
                serie.append((t, v))
                ultimo = v
        if len(serie) > 1:
            out[k] = serie
    return out


def chaves_da_foto(x):
    """[(bloco, x, y, indice, n)]: a maior faixa de cada chave que o App leu
    com x = 0, com o x trocado pelo do pattern atual nos blocos de pattern e
    de kit (os outros sao do sistema, x = 0 sempre). Uma leitura por chave: o
    diff (ts.ultimos_valores) guarda uma resposta por (bloco, x, y)."""
    out = []
    for (b, x0, y) in sorted(cs.leituras_do_app()):
        if x0 != 0:
            continue
        xx = x if (b in cs.BLOCOS_DE_PATTERN or b in cs.blocos_com_x()) else 0
        out.append((b, xx, y) + tuple(cs.faixa_do_bloco(b, xx, y)))
    return out


def tirar_foto(c):
    """Le a foto inteira do pattern selecionado. -> (nome, x, {(bloco, x, y):
    [u32]}). O x e o do bloco 3 [2]; com [3]/[4] diferentes (kit != pattern?)
    avisa: os blocos de kit seriam lidos no x do pattern."""
    b3 = _ler_bloco(c, 3)
    x = b3[ts.OFF_PATTERN_GLOBAL]
    if len({b3[2], b3[3], b3[4]}) != 1:
        print(f"(!) bloco 3 [2..4] = {b3[2:5]}: kit e pattern diferentes - "
              f"os blocos de kit vao no x {x} do pattern")
    vals = {}
    for b, xx, y, i, n in chaves_da_foto(x):
        vals[(b, xx, y)] = c.ler(b, xx, y, i, n)
    return ts.nome_do_pattern(x), x, vals


def cmd_foto(nome):
    with cs.ConexaoTR1000(nome_captura=nome) as c:
        c.aperto()
        t = time.time()
        pat, x, vals = tirar_foto(c)
        print(f"foto {nome}: pattern {pat} (x {x}), {len(vals) + 1} leituras em "
              f"{time.time() - t:.1f} s -> {c.captura}")


# ─────────────────────────────────────────────────────────────
# C5: a sessao guiada (ROTEIRO-C5.md) - os gestos do manual RM, um por vez
# ─────────────────────────────────────────────────────────────
# (id, o gesto, o gesto inverso). Os passos sao do manual (RM p.20-26, 44);
# o "de onde partir" de todos: pattern 1-01, var A, PARADA, TR-REC ligado,
# SD selecionado. O step 4 do SD tem nota (vermelho) no 1-01.
GESTOS = [
    ("velocity", "Segure a tecla de STEP 4 e gire o [C1] (VELOCITY) ate ~40. Solte.",
                 "Segure STEP 4 e volte o [C1] ao valor de antes (o visor mostrou). Solte."),
    ("start",    "Segure STEP 4 e gire o [C2] (START) uns cliques para a DIREITA. Solte.",
                 "Segure STEP 4 e volte o [C2] para o 0. Solte."),
    ("substep",  "Aperte [SUB], aperte STEP 4 (sub step 1/2). Aperte [SUB] de novo para sair.",
                 "Aperte [SUB], aperte STEP 4 de novo (desliga). Aperte [SUB] para sair."),
    ("flam",     "Segure [SUB] e gire o [C6/VALUE] ate 'Flam'; solte. [SUB], STEP 4, [SUB].",
                 "[SUB], STEP 4 (desliga), [SUB]; segure [SUB] e volte o [C6] para '1/2'."),
    ("prob",     "Segure STEP 4 e gire o [C4] (PROB) ate 50%. Solte.",
                 "Segure STEP 4 e volte o [C4] para 100%. Solte."),
    ("cycle",    "Segure STEP 4 e gire o [C5] (CYCLE) ate '1/3'. Solte.",
                 "Segure STEP 4 e volte o [C5] para '1/1'. Solte."),
    ("accent",   "Aperte ACCENT [STEP] e depois STEP 6 (accent no step 6).",
                 "Com o ACCENT [STEP] ainda selecionado, aperte STEP 6 de novo (tira)."),
    ("alt",      "Aperte [RS]. Segure LAYER [B] e aperte STEP 3 (som ALT no RS).",
                 "Segure LAYER [B] e aperte STEP 3 de novo (tira). Aperte [SD] de novo."),
    ("last-var", "Aperte [LAST], aperte [A], aperte STEP 12 (var A com 12 steps).",
                 "Aperte [LAST], aperte [A], aperte STEP 16. [EXIT]."),
    ("last-trk", "Aperte [LAST], aperte [SD], aperte STEP 8 (o SD com 8 steps). [EXIT].",
                 "Aperte [LAST]; segure [CLEAR] e aperte [SD] (limpa). [EXIT]."),
    ("scale",    "[SHIFT]+[PTN SELECT]; [C3] ate 'Scale'; [C6] ate '32nd'. [EXIT].",
                 "[SHIFT]+[PTN SELECT]; 'Scale' de volta para '16th'. [EXIT]."),
    ("var-b",    "Aperte a variacao [B] (so selecionar, sem tocar).",
                 "Aperte a variacao [A]."),
    ("chain",    "Aperte [A] e [B] AO MESMO TEMPO (variation chain A+B).",
                 "Aperte o [VARI CHAIN] aceso (cancela); aperte [A]."),
    ("mute",     "Aperte [MUTE], depois [SD] (o SD pisca: mutado).",
                 "Aperte [SD] de novo (desmuta) e [MUTE] para sair."),
    ("fill",     "[SHIFT]+[FILL IN TRIG]; [C1] (PLAY) de FILL1 para FILL2. [EXIT].",
                 "[SHIFT]+[FILL IN TRIG]; [C1] de volta para FILL1. [EXIT]."),
    ("loop",     "Aperte [START]; aperte [STEP LOOP] (pisca). Deixe tocando.",
                 "Aperte [STEP LOOP] (sai); aperte [STOP]."),
]


def piso_de_ruido(fotos):
    """{(bloco, x, y, i)} que mudou entre fotos SEM gesto no meio."""
    ruido = set()
    for a, b in zip(fotos, fotos[1:]):
        for k in set(a) & set(b):
            ruido |= {k + (i,) for i, (p, q) in enumerate(zip(a[k], b[k])) if p != q}
    return ruido


def _enter(c, texto):
    """Mostra o gesto e espera Enter (com a sessao viva: c.perguntar).
    -> '' (feito), 'p' (pular) ou 'q'."""
    try:
        return c.perguntar(f"\n>> {texto}\n   [Enter] feito   [p] pula   [q] encerra: ").strip().lower()
    except EOFError:
        return "q"


def cmd_c5():
    import os
    linhas_log = []

    def diga(t=""):
        print(t)
        linhas_log.append(t)

    with cs.ConexaoTR1000(nome_captura="c5") as c:
        c.aperto()

        def espera(texto):
            return _enter(c, texto)
        diga("C5 - de onde partir: pattern 1-01, var A, PARADA, [TR-REC] ligado, [SD] selecionado.")
        if espera("Confira o painel assim e aperte Enter (vou tirar 3 fotos sem gesto: o piso).") == "q":
            return
        fotos = [tirar_foto(c)[2] for _ in range(3)]
        ruido = piso_de_ruido(fotos)
        diga(f"piso de ruido: {len(ruido)} valores mudam sozinhos (ignorados daqui em diante)")
        base = fotos[-1]
        for id, ida, volta in GESTOS:
            r = espera(f"[{id}] {ida}")
            if r == "q":
                break
            if r == "p":
                diga(f"\n[{id}] pulado"); continue
            depois = tirar_foto(c)[2]
            ls, n = ts.linhas_do_diff(base, depois, ruido)
            diga(f"\n[{id}] ida: {n} valores mudaram")
            for l in ls:
                diga(l)
            espera(f"[{id}] VOLTA: {volta}")
            voltou = tirar_foto(c)[2]
            ls, n = ts.linhas_do_diff(base, voltou, ruido)
            diga(f"[{id}] volta: {'tudo como antes' if not n else f'{n} valores AINDA diferentes do inicio'}")
            for l in ls:
                diga(l)
            base = voltou
    txt = os.path.splitext(c.captura)[0] + ".txt"
    with open(txt, "w") as f:
        f.write("\n".join(linhas_log) + "\n")
    print(f"\ncaptura: {c.captura}\nresumo: {txt}")


def captura_da_foto(nome):
    """O .serlog mais recente com esse nome (o caminho_livre poe -2, -3...)."""
    import glob, os
    if os.path.exists(nome):
        return nome
    cs_ = sorted(glob.glob(os.path.join(cs.AQUI, "capturas", f"*-{nome}.serlog")),
                 key=os.path.getmtime)
    if not cs_:
        raise FileNotFoundError(f"nenhuma foto {nome!r} em capturas/")
    return cs_[-1]


def cmd_estado(segundos):
    amostras = []
    with cs.ConexaoTR1000(nome_captura="c4-estado") as c:
        print(f"aperto de mao: versao {c.aperto()!r}")
        print(f"lendo os blocos {BLOCOS_DE_ESTADO} por {segundos:.0f} s...")
        t0 = time.time()
        while time.time() - t0 < segundos:
            a = {}
            for b in BLOCOS_DE_ESTADO:
                for i, v in enumerate(_ler_bloco(c, b)):
                    a[(b, i)] = v
            amostras.append((time.time() - t0, a))
            time.sleep(0.05)
    m = mudancas(amostras)
    print(f"\n{len(amostras)} leituras completas; {len(m)} valores mudaram\n")
    for (b, i), serie in sorted(m.items()):
        idx = cs.faixa_do_bloco(b, 0, 0)[0] + i
        valores = " ".join(f"{v:X}" for _, v in serie[:24])
        print(f"   bloco {b:3d} [{i:3d}] (indice {idx:4d}): {len(serie) - 1:3d} trocas  "
              f"{valores}{' ...' if len(serie) > 24 else ''}")
    print(f"\ncaptura: {c.captura}")


def main(a):
    try:
        if a[:1] == ["pattern"]:
            cmd_pattern(); return 0
        if a[:1] == ["estado"]:
            seg = 8.0
            if "--segundos" in a:
                try:
                    seg = float(a[a.index("--segundos") + 1])
                except (IndexError, ValueError):
                    print("(!) --segundos precisa de um numero, ex.: --segundos 8")
                    return 1
            cmd_estado(seg); return 0
        if a[:1] == ["c5"]:
            cmd_c5(); return 0
        if a[:1] == ["foto"] and len(a) == 2:
            cmd_foto(a[1]); return 0
        if a[:1] == ["diff"] and len(a) == 3:
            ts.cmd_diffblocos(captura_da_foto(a[1]), captura_da_foto(a[2])); return 0
    except (cs.ErroConexao, PermissionError, FileNotFoundError) as e:
        print(f"(!) {e}")
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

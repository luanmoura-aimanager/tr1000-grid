#!/usr/bin/env python3
"""
sessao_c4.py - leituras ao vivo para os criterios 4 e 5 do portao (REFERENCIA 3.1)

    python3 sessao_c4.py pattern                 # le o pattern atual inteiro e
                                                 # mostra a grade (12 bancos x 10 tracks)
    python3 sessao_c4.py estado [--segundos 8]   # le os blocos de sistema/performance
                                                 # ~10x por segundo e mostra o que MUDA

SO LE. Nada aqui escreve: as leituras passam pelo mesmo portao de saida da
conexao_serial (so dentro das faixas que o proprio App leu no boot), e escrita
nao existe neste arquivo. O TR-1000 App (original e copia) tem que estar
FECHADO.

Criterio 4: o bloco 118+3v e o pattern SELECIONADO? Rode `pattern`, troque de
pattern no painel, rode de novo - se a grade e o nome acompanharem, o
enderecamento nao depende do numero do pattern (diferente da TR-8S, em que o
pattern entrava no endereco).

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
    indice, n = cs.leituras_do_app()[(bloco, x, y)]
    return c.ler(bloco, x, y, indice, n)


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
        bloco = ts.BLOCO_VAR0 + 1 + ts.BLOCOS_POR_VAR * v
        for tr in range(len(ts.TRACKS_SERIAL)):
            vals[(bloco, x, tr)] = _ler_bloco(c, bloco, x, tr)
    return vals


def cmd_pattern():
    with cs.ConexaoTR1000(nome_captura="c4-pattern") as c:
        print(f"aperto de mao: versao {c.aperto()!r}")
        nome, x, tempo = pattern_atual(c)
        print(f"selecionado no painel (bloco 3): pattern {nome} -> x {x}, "
              f"tempo {tempo}")
        if (ts.BLOCO_CAB_PATTERN, x, 0) not in cs.leituras_do_app():
            print(f"(!) o App ainda nao leu o pattern {nome} (x {x}) em nenhuma captura "
                  f"de referencia - capture o boot dele com o espiao antes "
                  f"(REFERENCIA 2.1c). Nada lido.")
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
        idx = cs.leituras_do_app()[(b, 0, 0)][0] + i
        valores = " ".join(f"{v:X}" for _, v in serie[:24])
        print(f"   bloco {b:3d} [{i:3d}] (indice {idx:4d}): {len(serie) - 1:3d} trocas  "
              f"{valores}{' ...' if len(serie) > 24 else ''}")
    print(f"\ncaptura: {c.captura}")


def main(a):
    try:
        if a[:1] == ["pattern"]:
            cmd_pattern(); return 0
        if a[:1] == ["estado"]:
            seg = float(a[a.index("--segundos") + 1]) if "--segundos" in a else 8.0
            cmd_estado(seg); return 0
    except cs.ErroConexao as e:
        print(f"(!) {e}")
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

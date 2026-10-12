#!/usr/bin/env python3
"""
tocando.py - qual variacao a TR-1000 esta tocando, pelas notas que ela manda

Nao ha de onde ler isso pela serial (REFERENCIA 7.3: o cur_vari do catalogo nao
mora em nenhum endereco que o App leia). Mas a maquina manda uma note_on por
disparo na porta 'TR-1000' (canal 10, as notas da MIDI chart), e o grid ja
tem os steps de cada variacao. Entao, a cada step:

    o que SOOU (os tracks das notas)  x  o que cada variacao da chain TOCARIA

e a variacao que bate com os ultimos steps, e SO ela, e a que toca. Empate ou
nenhuma: o detector nao chuta (a regra do "?" do tr8s-grid) - fica na de
antes, se ela ainda bate, ou em None.

O que fica de fora da comparacao, porque o grid nao sabe se ia soar:
  - track mutado (a maquina nao manda a nota? - nao medido; ignorar e seguro)
  - step com PROB < 100 ou CYCLE (soa as vezes)
O SUB, o START e o FLAM nao mudam QUAIS tracks soam no step - ficam dentro.
Limite: uma nota empurrada para o fim do step (START perto de +100) chega
depois do ultimo pulso dele e conta no step seguinte; aquele trecho fica "?".

A sequencia (desde o F4.1b): o motor anda (variacao, coluna) como a maquina -
a coluna sobe ate o LAST da variacao e a chain passa para a proxima, no FIRST
dela. Com o START, o estado e conhecido; as notas so CONFEREM (e
ressincronizam, se um so outro ponto explica o que soou). Sem o START (o
Controller ligou com a maquina ja tocando), o ponto de partida unico que
explica os ultimos steps ouvidos da o estado.
"""
import campos
import tr1000
import tr1000_serial as ts

# nota -> track (0..9), das notas padrao da chart (tr1000.NOTAS_PADRAO): a
# normal, a do layer A e a do layer B/ALT de cada track. O TRG nao e track.
NOTA_PARA_TRACK = {}
for _t, _nome in enumerate(tr1000.TRACKS):
    for _n in tr1000.NOTAS_PADRAO[_nome]:
        if _n is not None:
            NOTA_PARA_TRACK[_n] = _t
del _t, _nome, _n

JANELA = 8            # steps ouvidos que a decisao olha (os mais recentes)
MIN_STEPS_FASE = 8    # steps ouvidos para achar o estado sem START
MAX_ERROS = 1         # erros (fora os tracks que nenhum estado explica) que ainda "batem"


def track_da_nota(nota):
    return NOTA_PARA_TRACK.get(nota)


PROB_POS = campos.CAMPOS_STEP["prob"][0]
CYCLE_POS = campos.CAMPOS_STEP["cycle"][0]


def esperado(steps_da_var, coluna):
    """(os tracks que TOCAM com certeza, os que talvez) na coluna de uma
    variacao. `steps_da_var` = {track: [131 u32]} (o cache do motor)."""
    certos, talvez = set(), set()
    for tr, v in steps_da_var.items():
        if v is None:
            continue
        a, b = v[coluna * 4], v[coluna * 4 + 1]
        if not (ts.slot_toca(a) or ts.slot_toca(b)):
            continue
        prob = v[PROB_POS + coluna] if PROB_POS + coluna < len(v) else 100
        cycle = v[CYCLE_POS + coluna] if CYCLE_POS + coluna < len(v) else 0
        (certos if prob >= 100 and cycle == 0 else talvez).add(tr)
    return certos, talvez


def bate(ouvido, certos, talvez, mudos=frozenset()):
    """O step ouvido e o esperado concordam? Mutados e 'talvez' nao contam."""
    return not diferenca(ouvido, certos, talvez, mudos)


def volta(n, first, last, passos=16):
    if not (0 <= first <= last < passos):
        first, last = 0, passos - 1
    return first + n % (last - first + 1)


# ─────────────────────────────────────────────────────────────
# A sequencia: (variacao, coluna), andando como a maquina anda (F4.1b,
# 12/10/2026: contar "steps desde o START" e dividir pelo comprimento de UMA
# variacao errava com a chain A(12)+B(16) e com o LAST trocado tocando)
# ─────────────────────────────────────────────────────────────
def chain_de(mascara):
    """As variacoes A..H da chain, na ordem em que tocam (A antes de B -
    deducao a conferir no F4). Mascara vazia: a A."""
    return [v for v in range(8) if mascara >> v & 1] or [0]


def _extremos(extremos, v, passos=16):
    first, last = extremos.get(v, (0, passos - 1))
    if not (0 <= first <= last < passos):
        first, last = 0, passos - 1
    return first, last


def inicio(chain, extremos):
    """O estado do primeiro step depois do START."""
    v = chain[0]
    return v, _extremos(extremos, v)[0]


def proximo(estado, chain, extremos):
    """O step seguinte: a coluna anda; no LAST (ou alem dele), a proxima
    variacao da chain comeca no FIRST dela. Os extremos sao os de AGORA: um
    LAST trocado tocando vale quando a coluna chega nele, e um FIRST subido
    acima da coluna nao interrompe a volta (as duas regras sao deducao, a
    medir no F4)."""
    v, col = estado
    first, last = _extremos(extremos, v)
    if v in chain and col < last:
        return v, col + 1
    depois = [x for x in chain if x > v]
    nv = depois[0] if depois else chain[0]
    return nv, _extremos(extremos, nv)[0]


def proximo_trk(col, first, last, passos=16):
    """O mesmo para um track com FIRST/LAST proprio (polimetria)."""
    first, last = _extremos({0: (first, last)}, 0, passos)
    return col + 1 if col < last else first


def estados(chain, extremos):
    """Todos os (variacao, coluna) de uma volta da chain."""
    out = []
    for v in chain:
        first, last = _extremos(extremos, v)
        out += [(v, c) for c in range(first, last + 1)]
    return out


def diferenca(ouvido, certos, talvez, mudos=frozenset()):
    """Os tracks que discordam no step (soou sem esperar, ou o contrario).
    Mutados e 'talvez' (PROB < 100, CYCLE) nao contam."""
    fora = set(mudos) | set(talvez)
    return (set(ouvido) - fora) ^ (set(certos) - fora)


def confere(ouvidos_e_estados, vars_steps, mudos=frozenset()):
    """[(tracks ouvidos, (v, col))] -> quantos tracks discordam, somados."""
    erros = 0
    for ouvido, (v, col) in ouvidos_e_estados:
        if v in vars_steps:
            erros += len(diferenca(ouvido, *esperado(vars_steps[v], col), mudos))
    return erros


def analisar(janela, vars_steps, chain, extremos, mudos=frozenset()):
    """Cada ponto de partida da chain contra os steps ouvidos ->
    {estado no ULTIMO step: {track: erros}}, ou None sem os steps da chain."""
    if not janela or any(v not in vars_steps for v in chain):
        return None
    esp, cands = {}, {}
    for s0 in estados(chain, extremos):
        estado, por_track = s0, {}
        for _n, ouvido in janela:
            if estado not in esp:
                esp[estado] = esperado(vars_steps[estado[0]], estado[1])
            for tr in diferenca(ouvido, *esp[estado], mudos):
                por_track[tr] = por_track.get(tr, 0) + 1
            ultimo = estado
            estado = proximo(estado, chain, extremos)
        if ultimo not in cands or sum(por_track.values()) < sum(cands[ultimo].values()):
            cands[ultimo] = por_track
    return cands


def melhor(cands, sem=None):
    """O estado com menos erros (sem contar o track `sem`), se ele tem no
    maximo MAX_ERROS e nenhum outro empata; senao None."""
    notas = sorted((sum(n for t, n in pt.items() if t != sem), est) for est, pt in cands.items())
    if not notas or notas[0][0] > MAX_ERROS:
        return None
    if len(notas) > 1 and notas[1][0] == notas[0][0]:
        return None
    return notas[0][1]


def decidir(cands):
    """Primeiro a comparacao EXATA, com todos os tracks - um pattern de um ou
    dois tracks decide como sempre. So se ela nao decide: um track de fora
    por vez, e so vale se todas as respostas concordam. E o SD do F4.1b,
    deslocado da grade por algo que nao lemos, enquanto os outros batiam."""
    exato = melhor(cands)
    if exato is not None:
        return exato
    tracks = set().union(*cands.values()) if cands else set()
    respostas = {melhor(cands, t) for t in tracks} - {None}
    return respostas.pop() if len(respostas) == 1 else None


def modelo_bate(cands, estado):
    """O estado do modelo explica o que soou? Exato, ou com UM track de fora
    quando, sem esse track, ele e o melhor de todos."""
    pt = cands.get(estado)
    if pt is None:
        return False
    if sum(pt.values()) <= MAX_ERROS:
        return True
    return any(sum(n for x, n in pt.items() if x != t) <= MAX_ERROS and melhor(cands, t) == estado
               for t in pt)


def achar_estado(janela, vars_steps, chain, extremos, mudos=frozenset()):
    """O estado da sequencia no ULTIMO step da janela (decidir), ou None (nao
    chuta). Serve para adotar a maquina ja tocando e para ressincronizar."""
    if len(janela) < MIN_STEPS_FASE or sum(1 for _n, o in janela if o) < 2:
        return None
    cands = analisar(janela, vars_steps, chain, extremos, mudos)
    return None if cands is None else decidir(cands)

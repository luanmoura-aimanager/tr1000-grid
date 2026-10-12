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
MARGEM = 2            # erros a menos que o segundo melhor, para decidir


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
    return erros_step(ouvido, certos, talvez, mudos) == 0


def erros_step(ouvido, certos, talvez, mudos=frozenset()):
    """Quantos TRACKS discordam no step (soou sem esperar, ou o contrario).
    Contar por track, e nao "o step bateu ou nao", e o que deixa um track
    fora do lugar sem derrubar a conta toda: no F4.1b (12/10/2026) o SD do
    1-01 soava deslocado da grade enquanto os outros 8 batiam certinho."""
    fora = set(mudos) | set(talvez)
    return len((set(ouvido) - fora) ^ (set(certos) - fora))


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


def confere(ouvidos_e_estados, vars_steps, mudos=frozenset()):
    """[(tracks ouvidos, (v, col))] -> os erros somados, SEM o track que mais
    errou: um track fora da grade (o SD do F4.1b, deslocado por algo que nao
    lemos) nao decide nada sozinho; os outros nove decidem."""
    por_track = {}
    for ouvido, (v, col) in ouvidos_e_estados:
        if v not in vars_steps:
            continue
        certos, talvez = esperado(vars_steps[v], col)
        fora = set(mudos) | set(talvez)
        for tr in (set(ouvido) - fora) ^ (set(certos) - fora):
            por_track[tr] = por_track.get(tr, 0) + 1
    return sum(por_track.values()) - max(por_track.values(), default=0)


def achar_estado(janela, vars_steps, chain, extremos, mudos=frozenset()):
    """O estado da sequencia no ULTIMO step da janela, se um ponto de partida
    explica os steps ouvidos CLARAMENTE melhor que todos os outros: poucos
    erros (um track fora do lugar cabe) e pelo menos MARGEM erros a menos que
    o segundo melhor. Empate ou dois parecidos: None (nao chuta). Serve para
    adotar a maquina ja tocando e para ressincronizar."""
    if len(janela) < MIN_STEPS_FASE or sum(1 for _n, o in janela if o) < 2:
        return None
    if any(v not in vars_steps for v in chain):
        return None
    notas = {}                                   # ultimo estado -> menos erros
    for s0 in estados(chain, extremos):
        estado, seq = s0, []
        for _n, ouvido in janela:
            seq.append((ouvido, estado))
            ultimo = estado
            estado = proximo(estado, chain, extremos)
        e = confere(seq, vars_steps, mudos)
        notas[ultimo] = min(e, notas.get(ultimo, e))
    ordem = sorted((e, est) for est, e in notas.items())
    melhor_e, melhor = ordem[0]
    segundo = ordem[1][0] if len(ordem) > 1 else None
    if melhor_e > max_erros(len(janela)):
        return None
    if segundo is not None and segundo - melhor_e < MARGEM:
        return None
    return melhor


def max_erros(n_steps):
    """Erros (sem o pior track) que ainda contam como "bate"."""
    return max(1, n_steps // 4)

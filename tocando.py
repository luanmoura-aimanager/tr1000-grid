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

A mesma comparacao, deslizando o deslocamento, da a FASE quando o Controller
liga com a maquina ja tocando (sem o START, o playhead nao sabe em que step
esta): o (variacao, deslocamento) unico que bate com os steps ouvidos.

Limite, documentado: as variacoes da chain com comprimentos diferentes andam
com o mesmo contador de steps, entao a coluna de cada uma so e exata enquanto
o comprimento delas e o mesmo. E deducao nossa, a medir no ROTEIRO-F4.
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
MIN_STEPS = 4         # steps na janela antes de decidir qualquer coisa
MIN_STEPS_FASE = 8    # e para achar a fase (o deslocamento erra facil com pouco)


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
    fora = set(mudos) | set(talvez)
    return set(ouvido) - fora == set(certos) - fora


def volta(n, first, last, passos=16):
    if not (0 <= first <= last < passos):
        first, last = 0, passos - 1
    return first + n % (last - first + 1)


def candidatos(janela, vars_steps, extremos, mudos=frozenset(), deslocamento=0):
    """As variacoes que batem com TODOS os steps da janela.
    janela = [(n, tracks ouvidos)]; vars_steps = {v: {track: [131]}};
    extremos = {v: (first, last)}."""
    out = []
    for v, steps in vars_steps.items():
        first, last = extremos.get(v, (0, 15))
        ok = True
        for n, ouvido in janela:
            certos, talvez = esperado(steps, volta(n + deslocamento, first, last))
            if not bate(ouvido, certos, talvez, mudos):
                ok = False
                break
        if ok:
            out.append(v)
    return out


def qual_toca(janela, vars_steps, extremos, mudos=frozenset(), antes=None):
    """A variacao tocando, ou None. Olha o maior final da janela que ainda da
    resposta unica - assim a troca A -> B da chain aparece logo, sem esperar a
    janela inteira sair da A. Empate: fica na de antes se ela esta no empate."""
    if len(janela) < MIN_STEPS or not any(o for _n, o in janela):
        return antes
    for k in range(len(janela), 0, -1):
        final = janela[-k:]
        if sum(1 for _n, o in final if o) < 1:
            break
        c = candidatos(final, vars_steps, extremos, mudos)
        if len(c) == 1:
            return c[0]
        if len(c) > 1:
            return antes if antes in c else None
    return None


def achar_fase(janela, vars_steps, extremos, mudos=frozenset(), passos=16):
    """(variacao, deslocamento) unico que poe os steps ouvidos no lugar, ou
    None. O deslocamento soma no contador de steps do motor. Pattern que se
    repete dentro da variacao (o mesmo a cada 4 steps) da varios deslocamentos
    iguais de ouvido - e ai fica None: o playhead nao aparece em vez de
    aparecer no lugar errado."""
    if len(janela) < MIN_STEPS_FASE or sum(1 for _n, o in janela if o) < 2:
        return None
    achados = []
    for v in vars_steps:
        # so os deslocamentos de UMA volta da variacao: d e d + comprimento dao
        # as mesmas colunas (revisao do PR #13 - 8 steps davam sempre empate)
        first, last = extremos.get(v, (0, passos - 1))
        comprimento = (last - first + 1) if 0 <= first <= last < passos else passos
        for d in range(comprimento):
            if candidatos(janela, {v: vars_steps[v]}, extremos, mudos, deslocamento=d):
                achados.append((v, d))
                if len(achados) > 1:
                    return None
    return achados[0] if achados else None

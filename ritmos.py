#!/usr/bin/env python3
"""
ritmos.py - os ritmos prontos da aba Ritmos: o formato, a validacao, e a conta
que transforma um ritmo + o que a maquina tem agora na lista de escritas.

Os DADOS moram no biblioteca.py (como no tr8s-grid). Aqui nada fala com a
maquina: quem escreve e o Motor (escrever_ritmo / desfazer_ritmo), e cada
escrita passa pelo portao (conexao_serial.conferir_pacote) - este modulo so
diz QUAIS escritas. `python3 ritmos.py` valida tudo e imprime os previews.

Formato de um ritmo (biblioteca.RITMOS):
    id         identificador unico
    nome       como aparece na aba
    estilo     chave de agrupamento
    bpm        o tempo sugerido (o "Auto BPM" escreve; senao e so texto)
    kit        NOME de um kit da lista KITS (o "Auto kit" manda o Program
               Change; senao e so sugestao). Prefere os analogicos.
    scale      "16th" (padrao), "8th(T)", "16th(T)" ou "32nd" (campos.SCALES)
    last       o comprimento das variacoes (padrao 16)
    fonte      de onde veio o padrao - mostrado na aba
    obs        aviso opcional
    variacoes  {"A": {...}, "B": {...}, ..., "Fill 1": {...}}: pelo menos 2
               entre A..H. Cada uma: {track: linha}, track em TRACKS
    chain      as variacoes que tocam em sequencia ("AB"): a mascara do
               cabecalho. Padrao: todas as A..H definidas
    mix        opcional (os dub): {id do parametros.py: valor}, so os SENDS
               (rvb/dly dos tracks e o delay.rvb_send)

Uma linha e:
    string     um char por step: X 127 (o lugar do accent, que NAO e
               gravavel), x 80 (o Normal do painel), o 50, g 30, . nada.
               '|' e ' ' sao so separadores visuais (ignorados)
    lista      um item por step: None/0, um int (velocity) ou um dict
               {"vel", "layer": "A"|"B"|"AB", "prob", "sub", "cycle",
                "start", "alt"} - sub/cycle pelo NOME (campos.SUB_NOMES,
               CYCLE_NOMES) ou pelo indice
    (string, {step: dict})   a string, com alguns steps (1-based)
               detalhados - o jeito curto de um rolo ou de um ALT
"""
from collections import namedtuple

import campos
import parametros
import tr1000_serial as ts

TRACKS = ts.TRACKS_SERIAL                       # BD SD LT HT RS HC CH OH CC RC (sem MT)
VARIACOES = ts.VARIACOES_SERIAL                 # A..H, Fill 1..4
N_AH = 8
VEL = {"X": 127, "x": 80, "o": 50, "g": 30}
SEPARADORES = "| "
TRACKS_LAYER = 4                                # BD SD LT HT: slots 0 e 1
NEUTRO = {"prob": 100, "sub": 0, "cycle": 0, "start": 0}
SLOT_PAUSA = ts.SLOT_PAUSA

# Os nomes de kit da maquina do Luan: a lista 0c que a TR-1000 manda ao App
# (capturas/2026-10-08-s0-autoteste.serlog, carga "0c <indice u16> <16 chars>";
# o TesteRitmos redecodifica a captura e confere). 64..127 vieram vazios.
# O indice = o Program Change no Kit Ch. e DEDUCAO (nao medido: ROTEIRO-F5).
KITS = [
    "Dub Techno Kit", "Groovy Beach", "Tough Luck", "Nothing Static",          # 0
    "Downstep Life", "Tape Wave", "Slide MORPH !", "Subroot",                  # 4
    "Circuit Hop Kit", "Uncut Rhythm Kit", "Pumps Kit", "HardTechnoKit",       # 8
    "Rogue Drift", "Shuffle Inside", "Deep Techno Kit", "Interjection",        # 12
    "Weoow...", "Eccentric", "eVAporate", "Glitchy DnB Kit",                   # 16
    "Chrome Ghost", "Slant Deck", "Laidback", "Trance Kit",                    # 20
    "Check", "Aussie House Kit", "Trash Fence", "Rise",                        # 24
    "Westend Kit", "Jungle Kit", "Backline Kit", "Teccaeton Kit",              # 28
    "Hard Perc Kit", "Ground Swell", "Regular Kit", "Lofi Kit",                # 32
    "FM Clean Kit", "FM Bend Kit", "FM Dirty Kit", "FM Mix Kit",               # 36
    "TR-808-1000", "TR-808 OG 1", "TR-808 OG 2", "TR-808 OG 3",                # 40
    "TR-909-1000", "TR-909 OG 1", "TR-909 OG 2", "TR-909 OG 3",                # 44
    "808 Kit", "909 Kit", "808 & 8X Kit", "CR-78 Kit",                         # 48
    "8X Kit 1", "8X Kit 2", "606 Kit", "9X Kit",                               # 52
    "707 Kit 1", "707 Kit 2", "727 Kit 1", "727 Kit 2",                        # 56
    "626 Kit 1", "626 Kit 2", "9X & 727 Kit", "707 & 727 Kit",                 # 60
]
KIT_POR_NOME = {n: i for i, n in enumerate(KITS)}

# Um step que toca: a velocity, os slots (0 = layer A, 1 = layer B) e os
# campos do step (os que o ritmo nao diz voltam ao NEUTRO)
Passo = namedtuple("Passo", "vel slots prob sub cycle start alt")
# Uma escrita: o endereco, o valor novo e o que estava (o desfazer)
Escrita = namedtuple("Escrita", "bloco x y indice valor antigo")


# ── ler o formato ─────────────────────────────────────────
def _limpa(s):
    return "".join(c for c in s if c not in SEPARADORES)


def _indice_de(valor, nomes, campo):
    if isinstance(valor, str):
        if valor not in nomes:
            raise ValueError(f"{campo} {valor!r} desconhecido")
        return nomes.index(valor)
    return int(valor)


def _passo(item, track):
    """Um item da linha -> Passo ou None."""
    if item is None or item == 0:
        return None
    if isinstance(item, str):
        if item == ".":
            return None
        if item not in VEL:
            raise ValueError(f"char {item!r} (use {''.join(VEL)}.)")
        item = VEL[item]
    if isinstance(item, int):
        item = {"vel": item}
    d = dict(item)
    vel = int(d.pop("vel", VEL["x"]))
    if not 1 <= vel <= 127:
        raise ValueError(f"velocity {vel} fora de 1..127")
    layer = d.pop("layer", "AB")
    if layer not in ("A", "B", "AB"):
        raise ValueError(f"layer {layer!r}")
    if track < TRACKS_LAYER:
        slots = {"A": (0,), "B": (1,), "AB": (0, 1)}[layer]
    else:
        if layer != "AB":
            raise ValueError(f"{TRACKS[track]} nao tem layer (so BD SD LT HT)")
        slots = (0,)                            # track simples: so o slot 0 (medido)
    alt = bool(d.pop("alt", False))
    if alt and track < TRACKS_LAYER:
        raise ValueError(f"ALT so em RS..RC, nao em {TRACKS[track]}")
    vals = dict(NEUTRO)
    if "sub" in d:
        vals["sub"] = _indice_de(d.pop("sub"), campos.SUB_NOMES, "sub")
    if "cycle" in d:
        vals["cycle"] = _indice_de(d.pop("cycle"), campos.CYCLE_NOMES, "cycle")
    for k in ("prob", "start"):
        if k in d:
            vals[k] = int(d.pop(k))
    if d:
        raise ValueError(f"chaves desconhecidas no step: {sorted(d)}")
    for k, v in vals.items():
        _pos, mn, mx = campos.CAMPOS_STEP[k]
        if not mn <= v <= mx:
            raise ValueError(f"{k} {v} fora de {mn}..{mx}")
    return Passo(vel, slots, vals["prob"], vals["sub"], vals["cycle"], vals["start"], alt)


def linha(spec, track, last):
    """Uma linha do ritmo -> lista de `last` (Passo ou None)."""
    extras = {}
    if isinstance(spec, tuple):
        spec, extras = spec
    if isinstance(spec, str):
        itens = list(_limpa(spec))
    else:
        itens = list(spec)
    if len(itens) != last:
        raise ValueError(f"{TRACKS[track]}: {len(itens)} steps, o ritmo tem {last}")
    out = [_passo(i, track) for i in itens]
    for s, d in extras.items():
        if not 1 <= s <= last:
            raise ValueError(f"{TRACKS[track]}: step {s} fora de 1..{last}")
        base = itens[s - 1]
        d = dict(d)
        if "vel" not in d and isinstance(base, str) and base in VEL:
            d["vel"] = VEL[base]
        out[s - 1] = _passo(d, track)
    return out


def last_de(r):
    return r.get("last", 16)


def scale_de(r):
    return campos.SCALES.index(r.get("scale", "16th"))


def chain_de(r):
    """A mascara do cabecalho (A = 1, B = 2...)."""
    letras = r.get("chain") or "".join(v for v in r["variacoes"] if v in VARIACOES[:N_AH])
    m = 0
    for c in letras:
        m |= 1 << VARIACOES.index(c)
    return m


def expandir(r):
    """-> {indice da variacao: {track: [16 x (Passo ou None)]}}. Os steps
    depois do last e os tracks que o ritmo nao cita ficam None (pausa)."""
    last = last_de(r)
    out = {}
    for nome_v, linhas in r["variacoes"].items():
        v = VARIACOES.index(nome_v)
        grade = {}
        for tr in range(len(TRACKS)):
            nome_t = TRACKS[tr]
            passos = linha(linhas[nome_t], tr, last) if nome_t in linhas else [None] * last
            grade[tr] = passos + [None] * (campos.N_STEPS - last)
        out[v] = grade
    return out


# ── validar ───────────────────────────────────────────────
def validar(r):
    for chave in ("id", "nome", "estilo", "bpm", "kit", "fonte", "variacoes"):
        if chave not in r:
            raise ValueError(f"{r.get('id', '?')}: falta {chave!r}")
    conhecidas = {"id", "nome", "estilo", "bpm", "kit", "scale", "last", "fonte", "obs",
                  "variacoes", "chain", "mix"}
    sobra = set(r) - conhecidas
    if sobra:
        raise ValueError(f"{r['id']}: chaves desconhecidas {sorted(sobra)}")
    if r["kit"] not in KIT_POR_NOME:
        raise ValueError(f"{r['id']}: kit {r['kit']!r} nao esta na lista")
    if not campos.TEMPO_MIN <= round(r["bpm"] * 100) <= campos.TEMPO_MAX:
        raise ValueError(f"{r['id']}: bpm {r['bpm']} fora de 40..300")
    if r.get("scale", "16th") not in campos.SCALES:
        raise ValueError(f"{r['id']}: scale {r.get('scale')!r}")
    if not 1 <= last_de(r) <= campos.N_STEPS:
        raise ValueError(f"{r['id']}: last {last_de(r)}")
    for nome_v, linhas in r["variacoes"].items():
        if nome_v not in VARIACOES:
            raise ValueError(f"{r['id']}: variacao {nome_v!r}")
        for nome_t in linhas:
            if nome_t not in TRACKS:
                raise ValueError(f"{r['id']} {nome_v}: track {nome_t!r} (a TR-1000 nao tem MT)")
    ah = [v for v in r["variacoes"] if v in VARIACOES[:N_AH]]
    if len(ah) < 2:
        raise ValueError(f"{r['id']}: pelo menos 2 variacoes entre A..H")
    for c in r.get("chain", ""):
        if c not in ah:
            raise ValueError(f"{r['id']}: a chain cita {c!r}, que o ritmo nao define")
    if chain_de(r) == 0:
        raise ValueError(f"{r['id']}: chain vazia")
    try:
        grade = expandir(r)
    except ValueError as e:
        raise ValueError(f"{r['id']}: {e}") from None
    for v, g in grade.items():
        if not any(p for ps in g.values() for p in ps):
            raise ValueError(f"{r['id']} {VARIACOES[v]}: variacao vazia")
    for id, valor in r.get("mix", {}).items():
        if not (id.endswith((".rvb", ".dly")) or id == "delay.rvb_send") or id not in parametros.TABELA:
            raise ValueError(f"{r['id']}: mix {id!r} (so os sends)")
        p = parametros.TABELA[id]
        if not p.minimo <= valor <= p.maximo:
            raise ValueError(f"{r['id']}: mix {id} = {valor} fora de {p.minimo}..{p.maximo}")


# ── a conta: o ritmo contra o que a maquina tem ───────────
def _toca(v):
    return ts.slot_toca(v)


def valor_do_slot(passo, slot):
    v = ts.nota(passo.vel)
    return v | campos.BIT_ALT if (passo.alt and slot == 0) else v


def escritas_de_steps(grade, lidos):
    """As escritas dos steps de UMA variacao. `grade` = {track: [16 Passo/None]}
    (do expandir), `lidos` = {track: [131 u32]} (o que a maquina tem).
    So a diferenca: um slot que ja tem o valor nao e escrito; um step que o
    ritmo deixa vazio so e escrito se toca (vira FF). Os campos do step so
    importam nos steps que tocam: la, o que o ritmo nao diz volta ao NEUTRO.
    O DIRECTION ([96]) nao e tocado: e so leitura."""
    out = []
    for tr, passos in grade.items():
        atual = lidos[tr]
        for s, p in enumerate(passos):
            for slot in (0, 1):
                i = 4 * s + slot
                if p is not None and slot in p.slots:
                    novo = valor_do_slot(p, slot)
                elif _toca(atual[i]):
                    novo = SLOT_PAUSA
                else:
                    continue
                if atual[i] != novo:
                    out.append((tr, ts.INDICE_STEPS + i, novo, atual[i]))
            if p is None:
                continue
            for nome in ("prob", "sub", "cycle", "start"):
                pos, mn, _mx = campos.CAMPOS_STEP[nome]
                novo = getattr(p, nome)
                novo = campos.u32(novo) if mn < 0 else novo
                if atual[pos + s] != novo:
                    out.append((tr, ts.INDICE_STEPS + pos + s, novo, atual[pos + s]))
    return out


def escritas_do_ritmo(r, x, lidos_por_var, cab):
    """Todas as escritas de pattern de um ritmo no pattern x: os steps de cada
    variacao (lidos_por_var = {v: {track: [131]}}) e o cabecalho (cab = a
    lista lida do bloco 116 a partir de INI_CAB). -> [Escrita]."""
    out = []
    for v, grade in expandir(r).items():
        bloco = ts.bloco_de_steps(v)
        for tr, indice, novo, antigo in escritas_de_steps(grade, lidos_por_var[v]):
            out.append(Escrita(bloco, x, tr, indice, novo, antigo))
    last = last_de(r)
    quer = {campos.CAB_SCALE: scale_de(r), campos.CAB_VARIACOES: chain_de(r)}
    for v in expandir(r):
        quer[campos.CAB_FIRST_VAR + v] = 0
        quer[campos.CAB_LAST_VAR + v] = last - 1
    if "Fill 1" in r["variacoes"]:
        quer[campos.CAB_FILL] = 0
    for t in range(len(TRACKS)):
        if cab[campos.CAB_TRK_SW + t]:
            quer[campos.CAB_TRK_SW + t] = 0     # o FIRST/LAST proprio do track sai
    for pos in sorted(quer):
        if cab[pos] != quer[pos]:
            out.append(Escrita(campos.CAB, x, 0, campos.INI_CAB + pos, quer[pos], cab[pos]))
    return out


def desfazer(escritas):
    """As escritas que devolvem o que estava, na ordem inversa. Um slot que
    estava 00 (vazio) volta como FF: o portao recusa 00, e as duas pausas
    soam iguais (o step toca se algum slot nao e 0 nem FF)."""
    out = []
    for e in reversed(escritas):
        antigo = e.antigo
        rel = e.indice - ts.INDICE_STEPS
        if e.bloco != campos.CAB and 0 <= rel < 4 * campos.N_STEPS and not _toca(antigo):
            antigo = SLOT_PAUSA
        out.append(Escrita(e.bloco, e.x, e.y, e.indice, antigo, e.valor))
    return out


# ── o que a pagina recebe ─────────────────────────────────
def _char(p):
    if p is None:
        return "."
    c = "X" if p.vel >= 110 else "x" if p.vel >= 70 else "o" if p.vel >= 40 else "g"
    if p.sub or p.prob < 100 or p.cycle or p.alt:
        c = {"X": "R", "x": "r", "o": "q", "g": "q"}[c]     # um step com campo
    return c


def para_pagina(r):
    last = last_de(r)
    return {
        "id": r["id"], "nome": r["nome"], "estilo": r["estilo"], "bpm": r["bpm"],
        "kit": r["kit"], "kit_n": KIT_POR_NOME[r["kit"]], "scale": r.get("scale", "16th"),
        "last": last, "fonte": r["fonte"], "obs": r.get("obs", ""),
        "chain": chain_de(r), "mix": bool(r.get("mix")),
        "variacoes": {VARIACOES[v]: ["".join(_char(p) for p in g[tr][:last]) for tr in range(len(TRACKS))]
                      for v, g in expandir(r).items()},
    }


def por_estilo(ritmos):
    out = {}
    for r in ritmos:
        out.setdefault(r["estilo"], []).append(r)
    return out


def preview(r):
    pag = para_pagina(r)
    linhas = [f"{r['nome']}  ({r['estilo']}, {r['bpm']} BPM, {r['kit']}, "
              f"{pag['scale']}, last {pag['last']})"]
    for nome_v, grade in pag["variacoes"].items():
        linhas.append(f"  {nome_v}")
        for tr, s in enumerate(grade):
            if set(s) != {"."}:
                linhas.append(f"    {TRACKS[tr]:2} {s}")
    return "\n".join(linhas)


def _carregar():
    import biblioteca
    return biblioteca.RITMOS


RITMOS = _carregar()
POR_ID = {r["id"]: r for r in RITMOS}


if __name__ == "__main__":
    import sys
    ids = set()
    erros = 0
    for r in RITMOS:
        try:
            validar(r)
            if r["id"] in ids:
                raise ValueError(f"id repetido {r['id']}")
            ids.add(r["id"])
        except ValueError as e:
            erros += 1
            print(f"(!) {e}")
            continue
        if "-q" not in sys.argv:
            print(preview(r))
            print()
    est = por_estilo(RITMOS)
    print(f"{len(RITMOS)} ritmos em {len(est)} estilos; {erros} com erro")
    sys.exit(1 if erros else 0)

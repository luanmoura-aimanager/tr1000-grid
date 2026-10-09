#!/usr/bin/env python3
"""
controladoras.py - as duas controladoras de knobs: MC-24 (efeitos) e CM-MC50 (mixer)

    python3 controladoras.py mapear      # knob a knob: gire o que ele pedir
    python3 controladoras.py escutar     # tudo que as duas mandam, com o rotulo

Nada aqui escreve na TR-1000: so escuta as controladoras (portas MIDI). O mapa
vai para mapas/controladoras.json - a configuracao do hardware do Luan.

Os rotulos vem das fotos das placas que o Luan mandou em 09/10/2026:
  MC-24   REVERB (TYPE TIME PREDELAY LOWCUT HIGHCUT DENSITY) · LFO (RATE
          WAVEFORM) · DELAY (TYPE, RVB SEND, DELAY 1-6) · MASTER FX (TYPE,
          MFX 1-7) = 24
  CM-MC50 10 tracks x GAIN, PAN, RVB SND, DLY SND, LFO DTH = 50

O mapear anda na ordem das placas (MC-24 secao por secao, coluna da esquerda
e da direita alternando como na placa; CM-MC50 linha por linha, da esquerda
para a direita). Para cada knob: girar ate o fim anti-horario, depois todo no
horario, e apertar Enter. Retoma de onde parou (Ctrl+C salva) e recusa um CC
que ja esta mapeado em outro knob.
"""
import json, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
MAPA = os.path.join(AQUI, "mapas", "controladoras.json")

PORTA_MC24 = "MC-24"                       # (medido 09/10: nome da porta)
PORTA_MC50 = "CM-MC50"                     # (medido 09/10)
TRACKS = ["bd", "sd", "lt", "ht", "rs", "hc", "ch", "oh", "cc", "rc"]

ROTULOS_MC24 = (
    [("reverb." + k, "REVERB " + r) for k, r in (
        ("type", "TYPE"), ("time", "TIME"), ("predelay", "PREDELAY"),
        ("lowcut", "LOWCUT"), ("highcut", "HIGHCUT"), ("density", "DENSITY"))]
    + [("lfo.rate", "LFO RATE"), ("lfo.waveform", "LFO WAVEFORM")]
    + [("delay.type", "DELAY TYPE"), ("delay.rvb_send", "DELAY RVB SEND")]
    + [(f"delay.p{i}", f"DELAY {i}") for i in range(1, 7)]
    + [("mfx.type", "MASTER FX TYPE")]
    + [(f"mfx.p{i}", f"MFX {i}") for i in range(1, 8)]
)
LINHAS_MC50 = [("gain", "GAIN"), ("pan", "PAN"), ("rvb", "RVB SND"),
               ("dly", "DLY SND"), ("lfo", "LFO DTH")]
ROTULOS_MC50 = [(f"{t}.{k}", f"{t.upper()} {r}")
                for k, r in LINHAS_MC50 for t in TRACKS]
ROTULOS = {PORTA_MC24: ROTULOS_MC24, PORTA_MC50: ROTULOS_MC50}

# Movimento "de verdade" de um knob: pelo menos MIN_MSGS mensagens no mesmo CC.
# O knob so e dado por mapeado quando o Luan aperta Enter (a 1a versao seguia
# 0,8 s depois do primeiro movimento, no meio do giro - 09/10/2026).
MIN_MSGS = 3


# ─────────────────────────────────────────────────────────────
# funcoes puras (testadas)
# ─────────────────────────────────────────────────────────────
def detectar_tipo(valores):
    """'absoluto' (potenciometro, 0..127) ou 'relativo' (encoder sem fim).
    Encoder manda so incrementos: perto de 0/128 (1, 2, 127, 126...) ou perto
    de 64 (63, 65...). Um potenciometro girando anda por valores seguidos."""
    vs = list(valores)
    if not vs:
        return None
    perto_zero = all(v <= 6 or v >= 122 for v in vs) and any(v not in (0, 127) for v in vs)
    perto_64 = all(57 <= v <= 71 for v in vs) and len(set(vs)) <= 6 and len(vs) >= 6
    if perto_zero or perto_64:
        return "relativo"
    return "absoluto"


def chave_dominante(eventos, ja_mapeados=()):
    """eventos [(porta, canal, cc, valor)] -> (porta, canal, cc) com mais
    mensagens, se tiver pelo menos MIN_MSGS e nao estiver em ja_mapeados."""
    conta = {}
    for porta, canal, cc, _ in eventos:
        k = (porta, canal, cc)
        if k not in ja_mapeados:
            conta[k] = conta.get(k, 0) + 1
    if not conta:
        return None
    k = max(conta, key=conta.get)
    return k if conta[k] >= MIN_MSGS else None


def sequencia(knobs, ids):
    """Os ultimos ids do bloco ja mapeados formam CC seguidos (mesma porta e
    canal)? Devolve (porta, canal, proximo_cc) ou None. Usado para oferecer
    o preenchimento do resto do bloco por palpite."""
    if len(ids) < 4 or any(i not in knobs for i in ids[-4:]):
        return None
    ks = [knobs[i] for i in ids[-4:]]
    if len({(k["porta"], k["canal"]) for k in ks}) != 1:
        return None
    ccs = [k["cc"] for k in ks]
    if all(b - a == 1 for a, b in zip(ccs, ccs[1:])):
        return ks[0]["porta"], ks[0]["canal"], ccs[-1] + 1
    return None


def carregar_mapa(caminho=MAPA):
    try:
        with open(caminho) as f:
            return json.load(f)
    except FileNotFoundError:
        return {"versao": 1, "knobs": {}}


def salvar_mapa(mapa, caminho=MAPA):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as f:
        json.dump(mapa, f, indent=1, sort_keys=True)


def indice_reverso(mapa):
    """{(porta, canal, cc): id} - para traduzir uma mensagem em knob."""
    return {(k["porta"], k["canal"], k["cc"]): i for i, k in mapa["knobs"].items()}


# ─────────────────────────────────────────────────────────────
# MIDI
# ─────────────────────────────────────────────────────────────
def _abrir():
    from portas import EntradaMIDI, porta_exata
    abertas = {}
    for nome in (PORTA_MC24, PORTA_MC50):
        p = porta_exata(nome)
        if p:
            abertas[nome] = EntradaMIDI(*p)
        else:
            print(f"(!) porta {nome!r} nao encontrada - esta ligada na USB?")
    return abertas


def _eventos(abertas):
    out = []
    for nome, p in abertas.items():
        for m in p.iter_pending():
            if m.type == "control_change":
                out.append((nome, m.channel, m.control, m.value))
    return out


def _linha_digitada():
    """Uma linha do teclado, se ja houver (sem bloquear), ou None."""
    import select
    r, _, _ = select.select([sys.stdin], [], [], 0)
    return sys.stdin.readline().strip().lower() if r else None


def _girar_ate_enter(abertas):
    """Junta tudo que as controladoras mandarem ate o Luan apertar Enter.
    -> (eventos, texto digitado). O Luan gira o knob ate o fim anti-horario,
    depois todo no horario, e so entao aperta Enter (pedido de 09/10/2026: os
    knobs estavam em posicoes aleatorias, e o fim da faixa e o que prova que o
    knob certo foi medido inteiro)."""
    for p in abertas.values():
        p.iter_pending()                                  # descarta o velho
    evs = []
    while True:
        evs += _eventos(abertas)
        txt = _linha_digitada()
        if txt is not None:
            return evs, txt
        time.sleep(0.005)


def resumo_do_giro(valores):
    """Texto curto da faixa vista: o fim de faixa (0 e 127) e o que confirma."""
    if not valores:
        return "nada"
    lo, hi = min(valores), max(valores)
    ok = " (faixa inteira)" if (lo, hi) == (0, 127) else ""
    return f"{len(valores)} mensagens, de {lo} a {hi}{ok}"


def cmd_mapear():
    abertas = _abrir()
    if not abertas:
        return 1
    mapa = carregar_mapa()
    knobs = mapa["knobs"]
    print(f"mapa: {os.path.relpath(MAPA, AQUI)} ({len(knobs)} knobs ja mapeados)")
    print("Para cada knob: gire ate o FIM anti-horario, depois TODO no horario, e")
    print("aperte Enter.  [Enter] confirma   [r Enter] refaz   [p Enter] pula")
    print("Ctrl+C salva e sai (depois retoma daqui).\n")
    try:
        for porta, rotulos in ROTULOS.items():
            if porta not in abertas:
                continue
            for i, rotulo in rotulos:
                if i in knobs:
                    continue
                while True:
                    print(f">> {porta}  ·  {rotulo}   (gire e aperte Enter)")
                    evs, txt = _girar_ate_enter(abertas)
                    if txt == "p":
                        print("   pulado")
                        break
                    if txt == "r":
                        continue
                    ocupados = set(indice_reverso(mapa))
                    k = chave_dominante([e for e in evs if e[0] == porta], ocupados)
                    if k is None:
                        outros = chave_dominante(evs)
                        print("   (!) nao vi esse knob mexer" +
                              (f" (veio movimento do {outros[0]}, CC {outros[2]} - "
                               f"ja mapeado ou da outra controladora)" if outros else "")
                              + " - gire de novo")
                        continue
                    valores = [v for (po, ca, cc, v) in evs if (po, ca, cc) == k]
                    tipo = detectar_tipo(valores)
                    knobs[i] = dict(porta=k[0], canal=k[1], cc=k[2], tipo=tipo,
                                    palpite=False, faixa=[min(valores), max(valores)])
                    salvar_mapa(mapa)
                    print(f"   {rotulo}: canal {k[1] + 1}, CC {k[2]}, {tipo}, "
                          f"{resumo_do_giro(valores)}")
                    break
    except KeyboardInterrupt:
        print("\ninterrompido - o que foi mapeado esta salvo.")
    finally:
        for p in abertas.values():
            p.close()
    faltam = [r for rs in ROTULOS.values() for i, r in rs if i not in knobs]
    print(f"\n{len(knobs)} mapeados; faltam {len(faltam)}" +
          (f": {', '.join(faltam[:6])}{' ...' if len(faltam) > 6 else ''}" if faltam else ""))
    return 0


def cmd_escutar():
    abertas = _abrir()
    if not abertas:
        return 1
    rev = indice_reverso(carregar_mapa())
    rotulo = {i: r for rs in ROTULOS.values() for i, r in rs}
    print("Gire os knobs. Ctrl+C sai.\n")
    try:
        while True:
            for po, ca, cc, v in _eventos(abertas):
                i = rev.get((po, ca, cc))
                print(f"{po:8} canal {ca + 1:2} CC {cc:3} = {v:3}   "
                      f"{rotulo.get(i, '(nao mapeado)')}")
            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        for p in abertas.values():
            p.close()
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["mapear"]:
        sys.exit(cmd_mapear())
    if a[:1] == ["escutar"]:
        sys.exit(cmd_escutar())
    print(__doc__)
    sys.exit(1)

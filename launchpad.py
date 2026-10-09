#!/usr/bin/env python3
"""
launchpad.py - os dois Launchpad Mini MK3: programmer mode, LEDs, learn, layout

Portado do tr8s-grid (lp_tr8s.py :461-463, :592-645, :766-847, :968-1254) quase
sem mudanca: o hardware e o mesmo. O que mudou:
  - as portas vem do portas.py (rtmidi cru por INDICE - armadilha 3 do CLAUDE.md)
  - o layout mora em ~/.lp_tr1000_layout.json (o da TR-8S fica intocado)
  - a paleta dos steps espelha o painel da TR-1000, nao o da TR-8S: layer A =
    vermelho, so o layer B = VERDE (conferido pelo Luan em 08/10/2026,
    REFERENCIA 2.1c) - por isso o playhead deixou de ser verde e virou BRANCO

Notas: programmer mode numera os pads linha*10 + coluna (11..88); a geometria
real de cada aparelho (origem, passo de coluna, passo de linha - o esquerdo e
girado 90 graus) vem do `learn`.
"""
import json, os, sys, time

import mido
from portas import EntradaMIDI, SaidaMIDI, listar_portas, achar_portas

LAYOUT_FILE = os.path.expanduser("~/.lp_tr1000_layout.json")

LP_MATCH = "Launchpad"
PROG_ON  = mido.Message('sysex', data=[0x00, 0x20, 0x29, 0x02, 0x0D, 0x0E, 0x01])
PROG_OFF = mido.Message('sysex', data=[0x00, 0x20, 0x29, 0x02, 0x0D, 0x0E, 0x00])

# Botoes, por CC. Em programmer mode:
#   fileira de funcao (▲▼◀▶ Session Drums Keys User) = CC 91..98
#   coluna de cena (>)                                = CC 89,79,69,59,49,39,29,19
FUNC_CCS = [91, 92, 93, 94, 95, 96, 97, 98]
CENA_CCS = [89, 79, 69, 59, 49, 39, 29, 19]
LOGO_CC  = 99            # so LED: nao ha chave embaixo (medido no tr8s-grid)

# ─────────────────────────────────────────────────────────────
# PALETA DOS STEPS - espelha o painel da TR-1000 (REFERENCIA 2.1c)
# Cor int = indice da paleta Novation (note_on); tupla (r,g,b) 0-127 = SysEx.
# ─────────────────────────────────────────────────────────────
COR_OFF        = 0     # apagado
COR_FORTE      = 5     # vermelho        - layer A (ou som normal) tocando
COR_FRACA      = 7     # vermelho escuro - idem, velocity fraca
COR_B          = 21    # verde           - SO o layer B (a cor do painel)
COR_B_FRACA    = 23    # verde escuro
COR_ATIVO      = 3     # branco          - modo/selecao
COR_VAR        = 45    # azul            - variacao mostrada
COR_TEMPO      = 1     # cinza fraco     - cabeca de tempo vazia (1, 5, 9, 13)
STEPS_TEMPO    = 4
COR_SETA       = 1     # cinza escuro    - seta de rolagem disponivel
COR_VEL_OFF    = 1     # cinza escuro    - nivel de velocity nao selecionado
# O playhead era verde no tr8s-grid; aqui verde e "so layer B", entao ele e
# BRANCO: cheio sobre step ligado, cinza claro sobre step vazio.
COR_PLAY_HIT   = 3
COR_PLAY       = (30, 30, 30)

# A paleta indexada nao escurece, entao a borda vai SEMPRE em RGB, escurecida
# por um fator unico (o adesivo dos botoes fica ilegivel com LED forte em baixo
# - pedido do Luan no tr8s-grid, 14/08/2026).
BRILHO_BORDA       = 0.10
BRILHO_BORDA_ATIVO = 0.25
RGB_BORDA = {
    COR_OFF:   (0, 0, 0),
    COR_ATIVO: (127, 127, 127),
    COR_VAR:   (0, 40, 127),
    COR_SETA:  (70, 70, 70),
    COR_FORTE: (127, 0, 0),
    COR_B:     (0, 127, 0),
}


def cor_borda(cor, ativo=False):
    """Escurece uma cor de botao de borda. Aceita indice de paleta ou (r,g,b)."""
    rgb = cor if isinstance(cor, tuple) else RGB_BORDA.get(cor, (70, 70, 70))
    f = BRILHO_BORDA_ATIVO if ativo else BRILHO_BORDA
    if f <= 0:
        return (0, 0, 0)
    return tuple(max(0, min(127, int(round(c * f)))) for c in rgb)


# ─────────────────────────────────────────────────────────────
# LEDs
#   SysEx de LED: F0 00 20 29 02 0D 03 <spec> [<spec> ...] F7
#   spec estatico = 00 <indice> <cor>      spec RGB = 03 <indice> <r> <g> <b>
# Varios specs cabem numa mensagem: o quadro inteiro de um aparelho e UM SysEx.
# ─────────────────────────────────────────────────────────────
LED_SYSEX = [0x00, 0x20, 0x29, 0x02, 0x0D, 0x03]


def _spec_cor(nota, cor):
    if isinstance(cor, tuple):
        r, g, b = cor
        return [0x03, nota, int(r) & 0x7F, int(g) & 0x7F, int(b) & 0x7F]
    return [0x00, nota, int(cor) & 0x7F]


def enviar_cor(out, nota, cor):
    if isinstance(cor, tuple):
        out.send(mido.Message('sysex', data=LED_SYSEX + _spec_cor(nota, cor)))
    else:
        out.send(mido.Message('note_on', channel=0, note=nota, velocity=cor))


def enviar_cor_cc(out, control, cor):
    """LED de um BOTAO (CC). Tupla vai pelo SysEx (o indice do botao e o
    proprio numero do CC); indice de paleta vai como control_change."""
    if isinstance(cor, tuple):
        out.send(mido.Message('sysex', data=LED_SYSEX + _spec_cor(control, cor)))
    else:
        out.send(mido.Message('control_change', channel=0, control=control, value=cor))


def enviar_cores(out, pares):
    """[(nota, cor)] num SysEx so."""
    if not pares:
        return
    dados = []
    for nota, cor in pares:
        dados += _spec_cor(nota, cor)
    out.send(mido.Message('sysex', data=LED_SYSEX + dados))


# ─────────────────────────────────────────────────────────────
# Programmer mode, learn, layout
# ─────────────────────────────────────────────────────────────
def programmer_mode(ligar=True):
    """Manda o SysEx de programmer mode pra todas as saidas Launchpad. Fora
    dele a iluminacao da Session volta - "apagado" e programmer mode com tudo
    em 0 (apagar_luzes.py do tr8s-grid)."""
    msg = PROG_ON if ligar else PROG_OFF
    for i, _ in achar_portas(LP_MATCH, entradas=False):
        try:
            with SaidaMIDI(i) as p:
                p.send(msg)
        except Exception:
            pass
    time.sleep(0.3)


def _esperar_pad(portas):
    """Espera um note_on de qualquer porta. Retorna (indice_porta, nota)."""
    while True:
        for idx, p in portas.items():
            for msg in p.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    return idx, msg.note
        time.sleep(0.005)


def _acender_tudo(out_idx, origem, passo_col, passo_lin, cor):
    """Pinta os 64 pads de um aparelho - para confirmar identidade visual."""
    with SaidaMIDI(out_idx) as out:
        for l in range(8):
            for s in range(8):
                out.send(mido.Message('note_on', channel=0,
                                      note=origem + l * passo_lin + s * passo_col,
                                      velocity=cor))


def _confirmar_saida(lado, candidatos, palpite, geo):
    """Nomes duplicados nao distinguem aparelho: confirma acendendo o grid."""
    ordem = [palpite] + [c for c in candidatos if c != palpite]
    for out_idx in ordem:
        try:
            _acender_tudo(out_idx, geo["origem"], geo["passo_col"],
                          geo["passo_lin"], COR_VAR)
        except Exception as e:
            print(f"   [{out_idx}] nao abriu ({e})"); continue
        r = input(f"   O aparelho {lado.upper()} acendeu de azul? [s/n] ").strip().lower()
        _acender_tudo(out_idx, geo["origem"], geo["passo_col"],
                      geo["passo_lin"], COR_OFF)
        if r.startswith("s"):
            return out_idx
    print(f"   (!) nenhum candidato confirmado; ficando com [{palpite}]")
    return palpite


def grupo_lp(nomes):
    """Indices das portas Launchpad, na ordem em que o CoreMIDI as lista."""
    return [i for i, n in enumerate(nomes) if LP_MATCH.lower() in n.lower()]


def cmd_learn():
    programmer_mode(True)
    entradas = achar_portas(LP_MATCH)
    saidas = achar_portas(LP_MATCH, entradas=False)
    if not entradas:
        print("Nenhum Launchpad encontrado. Rode 'ports'."); return
    if len(entradas) < 4:
        print(f"(!) so {len(entradas)} entradas Launchpad - esperado 4 (2 aparelhos "
              f"x DAW/MIDI). Confira 'ports'.")

    portas = {i: EntradaMIDI(i, n) for i, n in entradas}
    cfg, usadas = {}, set()
    try:
        for lado in ("esquerdo", "direito"):
            print(f"\n=== LAUNCHPAD {lado.upper()} ===")
            pedidos = [
                "pad do CANTO SUPERIOR ESQUERDO deste aparelho",
                "pad IMEDIATAMENTE A DIREITA dele",
                "pad IMEDIATAMENTE ABAIXO do primeiro",
            ]
            notas, porta = [], None
            for texto in pedidos:
                while True:                          # repete ate vir do aparelho certo
                    print(f">> Aperte o {texto}")
                    for p in portas.values():
                        p.iter_pending()             # limpa fila
                    idx, nota = _esperar_pad(portas)
                    if porta is not None and idx != porta:
                        print(f"   (!) veio da porta [{idx}], nao da [{porta}] - "
                              f"aperte no MESMO aparelho")
                        time.sleep(0.35); continue
                    if porta is None and idx in usadas:
                        print(f"   (!) a porta [{idx}] ja foi usada no outro lado - "
                              f"aperte no OUTRO aparelho")
                        time.sleep(0.35); continue
                    porta = idx
                    print(f"   nota {nota}  porta [{idx}] {portas[idx].name}")
                    notas.append(nota)
                    time.sleep(0.35)
                    break
            usadas.add(porta)
            cfg[lado] = dict(in_idx=porta, in_nome=portas[porta].name,
                             origem=notas[0],
                             passo_col=notas[1] - notas[0],
                             passo_lin=notas[2] - notas[0])
    finally:
        for p in portas.values():
            p.close()

    # Saida correspondente: nomes identicos, entao pareia por POSICAO ordinal
    # entre as portas Launchpad e confirma visualmente.
    idx_in = [i for i, _ in entradas]
    idx_out = [i for i, _ in saidas]
    print("\nConfirmando qual saida e qual aparelho (nomes sao identicos):")
    for lado in cfg:
        pos = idx_in.index(cfg[lado]["in_idx"])
        palpite = idx_out[pos] if pos < len(idx_out) else idx_out[0]
        escolhido = _confirmar_saida(lado, idx_out, palpite, cfg[lado])
        cfg[lado]["out_idx"] = escolhido
        cfg[lado]["out_nome"] = dict(saidas)[escolhido]

    if cfg["esquerdo"]["out_idx"] == cfg["direito"]["out_idx"]:
        print("\n(!) os dois lados ficaram com a MESMA saida - rode 'learn' de novo.")

    # O que identifica o aparelho e a POSICAO dele entre os Launchpad: o indice
    # global muda toda vez que outro aparelho MIDI entra ou sai.
    nomes_in = [n for _, n in listar_portas(True)]
    nomes_out = [n for _, n in listar_portas(False)]
    g_in, g_out = grupo_lp(nomes_in), grupo_lp(nomes_out)
    for lado in ("esquerdo", "direito"):
        if cfg[lado]["in_idx"] in g_in:
            cfg[lado]["in_ord"] = g_in.index(cfg[lado]["in_idx"])
        if cfg[lado]["out_idx"] in g_out:
            cfg[lado]["out_ord"] = g_out.index(cfg[lado]["out_idx"])
    cfg["_portas_in"] = nomes_in
    cfg["_portas_out"] = nomes_out

    with open(LAYOUT_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

    print(f"\nLayout salvo em {LAYOUT_FILE}:")
    for lado in ("esquerdo", "direito"):
        c = cfg[lado]
        print(f"  {lado:9} origem={c['origem']:3}  +coluna={c['passo_col']:+3}  "
              f"+linha={c['passo_lin']:+3}")
        print(f"            in  [{c['in_idx']}] {c['in_nome']}")
        print(f"            out [{c['out_idx']}] {c['out_nome']}")


def resolver_layout(cfg, portas_in, portas_out):
    """Reconfere o layout salvo contra a enumeracao de agora.

    Devolve (cfg_resolvido, [mensagens]) ou (None, [motivos]).

    O que importa e o GRUPO Launchpad: se ele esta igual (mesmo tamanho, mesma
    sequencia de nomes), a k-esima porta Launchpad continua sendo o mesmo
    aparelho, esteja ela no indice 4 ou no 6. Outros aparelhos podem ir e vir
    (tr8s-grid, 16/08/2026: desligar a interface de audio derrubava o app).

    LIMITE HONESTO: os dois Mini MK3 tem nome IDENTICO; se o CoreMIDI trocar os
    dois de posicao entre si, isto aceita e o grid sai espelhado. A prova e o
    olho, no learn."""
    msgs = []
    if "porta_in" in cfg.get("esquerdo", {}):
        return None, ["layout no formato antigo (portas por nome) - rode 'learn'"]

    g_atual_in, g_atual_out = grupo_lp(portas_in), grupo_lp(portas_out)
    snap_in, snap_out = cfg.get("_portas_in"), cfg.get("_portas_out")

    for rot, snap, atual, g_atual in (("entrada", snap_in, portas_in, g_atual_in),
                                      ("saida", snap_out, portas_out, g_atual_out)):
        if snap is None:
            continue
        g_snap = grupo_lp(snap)
        if len(g_snap) != len(g_atual):
            return None, [f"o conjunto de Launchpad mudou na {rot}: o learn viu "
                          f"{len(g_snap)} portas, agora ha {len(g_atual)}. "
                          "Rode 'learn' de novo."]
        if [snap[i] for i in g_snap] != [atual[i] for i in g_atual]:
            return None, [f"a ordem das portas Launchpad mudou na {rot}. "
                          "Rode 'learn' de novo."]

    novo = json.loads(json.dumps(cfg))          # copia funda, nao mexe no salvo
    for lado in ("esquerdo", "direito"):
        c = novo.get(lado)
        if not c:
            return None, [f"layout sem o lado {lado} - rode 'learn'"]
        for chave, ordch, grupo, snap in (("in_idx", "in_ord", g_atual_in, snap_in),
                                          ("out_idx", "out_ord", g_atual_out, snap_out)):
            ordinal = c.get(ordch)
            if ordinal is None:
                if snap is None:
                    return None, ["layout velho demais (sem ordinal e sem "
                                  "snapshot de portas) - rode 'learn' de novo"]
                g_snap = grupo_lp(snap)
                if c[chave] not in g_snap:
                    return None, [f"o {chave} salvo do {lado} nao era uma porta "
                                  "Launchpad - rode 'learn' de novo"]
                ordinal = g_snap.index(c[chave])
            if ordinal >= len(grupo):
                return None, [f"nao ha porta Launchpad numero {ordinal + 1} - "
                              "rode 'learn' de novo"]
            antes = c[chave]
            c[chave], c[ordch] = grupo[ordinal], ordinal
            if antes != c[chave]:
                msgs.append(f"porta do {lado} deslocada desde o learn: "
                            f"{chave} [{antes}] -> [{c[chave]}]")

    if novo["esquerdo"]["out_idx"] == novo["direito"]["out_idx"]:
        return None, ["os dois lados cairam na MESMA saida - rode 'learn'"]
    if msgs:
        msgs.append("(algum aparelho MIDI entrou ou saiu; reresolvi pelo nome "
                    "e pela posicao entre os Launchpad, sem precisar recalibrar)")
    return novo, msgs


def carregar_layout_resolvido(caminho=LAYOUT_FILE):
    """(cfg, mensagens) do layout em disco, ja reresolvido. cfg=None se recusado."""
    if not os.path.exists(caminho):
        return None, ["nenhum layout salvo - rode 'learn'"]
    try:
        with open(caminho) as f:
            cfg = json.load(f)
    except Exception as e:
        return None, [f"layout ilegivel: {e}"]
    return resolver_layout(cfg, [n for _, n in listar_portas(True)],
                           [n for _, n in listar_portas(False)])


def carregar_layout():
    cfg, msgs = carregar_layout_resolvido()
    for m in msgs:
        print(("(!) " if cfg is None else "    ") + m)
    if cfg is None:
        sys.exit(1)
    return cfg


def cmd_probe():
    """Imprime tudo que chega dos Launchpad - para conferir os CCs dos botoes."""
    programmer_mode(True)
    portas = {i: EntradaMIDI(i, n) for i, n in achar_portas(LP_MATCH)}
    if not portas:
        print("Nenhum Launchpad encontrado. Rode 'ports'."); return
    print("Aperte qualquer botao. Ctrl+C pra sair.\n")
    try:
        while True:
            for idx, p in portas.items():
                for msg in p.iter_pending():
                    if msg.type in ('note_on', 'control_change'):
                        if getattr(msg, 'velocity', 1) == 0: continue
                        if getattr(msg, 'value', 1) == 0: continue
                        curto = p.name.split("Launchpad")[-1].strip()[:24]
                        print(f"[{idx}] {curto:26} {msg}")
            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        for p in portas.values():
            p.close()


def cmd_colors():
    """Acende a paleta: indices 0-63 no esquerdo, 64-127 no direito."""
    programmer_mode(True)
    cfg = carregar_layout()
    for base, lado in ((0, "esquerdo"), (64, "direito")):
        c = cfg[lado]
        with SaidaMIDI(c["out_idx"], c["out_nome"]) as out:
            for l in range(8):
                for s in range(8):
                    nota = c["origem"] + l * c["passo_lin"] + s * c["passo_col"]
                    out.send(mido.Message('note_on', channel=0, note=nota,
                                          velocity=base + l * 8 + s))
    print("Esquerdo = indices 0-63 (linha a linha), direito = 64-127.")

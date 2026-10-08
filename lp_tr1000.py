#!/usr/bin/env python3
"""
lp_tr1000.py - dois Launchpad Mini MK3 como grid da TR-1000 (fase 0: captura)

Requisitos:
    mido + python-rtmidi ja instalados em ~/Library/Python/3.9/
    export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages

FASE 0 - nada aqui ESCREVE no mapa de enderecos da maquina. Os comandos so
escutam, ou mandam o Identity Request universal (que nao e RQ1 e nao toca em
endereco nenhum - ver roland.IDENTITY_REQUEST):

    python3 lp_tr1000.py ports                 # portas MIDI com indice
    python3 lp_tr1000.py escutar [--segundos N] [--arquivo log.txt]
                                               # TUDO que a maquina manda, em
                                               # todas as portas dela
    python3 lp_tr1000.py identidade            # Identity Request na CTRL e na
                                               # comum; mostra quem responde
    python3 lp_tr1000.py sniff [--arquivo x.txt]
                                               # SysEx da porta CTRL, com
                                               # autoteste antes

O grid (learn/run/standby) entra na fase 1, depois do portao da fase 0
(REFERENCIA 3, "criterio de saida").
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mido
import roland
import tr1000
from portas import EntradaMIDI, SaidaMIDI, listar_portas, porta_exata

AUTOTESTE_S = 1.5


# ─────────────────────────────────────────────────────────────
# ports
# ─────────────────────────────────────────────────────────────
def cmd_ports():
    for rotulo, ent in (("ENTRADAS", True), ("SAIDAS", False)):
        portas = listar_portas(ent)
        vistos = {}
        for _, n in portas:
            vistos[n] = vistos.get(n, 0) + 1
        print(f"{rotulo}:")
        for i, n in portas:
            dup = "   <- nome duplicado" if vistos[n] > 1 else ""
            print(f"   [{i}] {n}{dup}")
        print()
    n_mido = len(mido.get_input_names()), len(mido.get_output_names())
    n_real = len(listar_portas(True)), len(listar_portas(False))
    if n_mido != n_real:
        print(f"(mido enxerga {n_mido[0]} in / {n_mido[1]} out por deduplicar "
              f"nomes; o real e {n_real[0]} / {n_real[1]}. Este script usa os "
              "indices reais.)")


def _entradas_tr1000():
    """[(indice, nome)] de toda entrada cujo nome comeca com TR-1000."""
    return [(i, n) for i, n in listar_portas(True) if n.startswith("TR-1000")]


def _descrever(msg):
    """Uma linha legivel, com o nome do instrumento/CC quando o manual da."""
    if msg.type in ("note_on", "note_off"):
        nome = tr1000.nome_da_nota(msg.note)
        return f"{msg}" + (f"   <- {nome}" if nome else "")
    if msg.type == "control_change":
        nome = tr1000.CC.get(msg.control)
        return f"{msg}" + (f"   <- {nome}" if nome else "   <- fora da chart")
    if msg.type == "sysex":
        d = roland.decodificar(msg.data)
        if d:
            return (f"SysEx Roland cab {roland.hexs(d['cabecalho'])}  "
                    f"{roland.CMDS[d['cmd']]} {roland.hexs(d['addr'])}  "
                    f"{len(d['data'])}B {roland.hexs(d['data'][:16])}"
                    + ("" if d["chk_ok"] else "  <-- CHECKSUM RUIM")
                    + ("  <-- model ID ambiguo" if d["ambiguo"] else ""))
        ident = roland.decodificar_identidade(msg.data)
        if ident:
            return f"Identity Reply {roland.hexs(ident['bruto'])}"
        return f"SysEx {roland.hexs(msg.data[:24])}"
    return str(msg)


# ─────────────────────────────────────────────────────────────
# escutar: a sessao C0 (REFERENCIA 7.1)
# ─────────────────────────────────────────────────────────────
TEMPO_REAL = ("clock", "start", "stop", "continue", "active_sensing",
              "songpos")


def cmd_escutar(argv):
    """Abre TODAS as entradas TR-1000 e conta/imprime o que chega.

    Responde as perguntas da C0:
      - a maquina manda clock PARADA? (a TR-8S mandava - armadilha 2 do
        CLAUDE.md do tr8s-grid). O resumo mostra o clock por segundo e os
        start/stop/continue, com horario
      - o painel transmite nota, CC, program change? (a TR-8S nao transmitia
        CC nenhum, mesmo com a chart dizendo que sim)
      - a maquina empurra SysEx sozinha? (a TR-8S empurrava o step atual)

    --segundos existe porque um escutar sem fim, morto a forca, deixa a porta
    aberta - e no tr8s-grid a CTRL emudeceu logo depois de um desses."""
    segundos = float(argv[argv.index("--segundos") + 1]) \
        if "--segundos" in argv else None
    arquivo = argv[argv.index("--arquivo") + 1] if "--arquivo" in argv else None

    entradas = _entradas_tr1000()
    if not entradas:
        print("Nenhuma porta TR-1000. A maquina esta ligada e na USB?"); return
    # Tudo que abre porta ou arquivo fica DENTRO do try: um Ctrl+C no meio do
    # autoteste (ate ~4,5 s) ou uma porta que falha ao abrir deixava as ja
    # abertas sem close - exatamente o "escutar morto deixando a porta aberta"
    # que precedeu a CTRL muda no tr8s-grid (revisao de 07/10/2026)
    abertas, f = [], None
    contagem = {}             # (porta, tipo) -> n
    clock_por_s = {}          # segundo inteiro -> pulsos, SO na porta comum
    t0 = time.time()
    try:
        for i, n in entradas:
            abertas.append(EntradaMIDI(i, n, ignorar_sense=False, callback=True))
        f = open(arquivo, "w") if arquivo else None
        print("Escutando: " + ", ".join(f"[{p.idx}] {p.name}" for p in abertas))

        # AUTOTESTE: sem ele, "nao chegou nada" e ambiguo entre maquina calada
        # e listener surdo (Metodo, regra 1). Primeiro o que vier sozinho; se
        # nada vier, o Identity Request - que nao e RQ1 e nao arrisca a porta.
        vivo = _autoteste(abertas)
        print("autoteste: " + (
            f"chegou {vivo} - o listener esta bom, silencio daqui pra frente e "
            "silencio de verdade." if vivo else
            "(!) nada chegou, nem resposta ao Identity Request. Nao da pra "
            "distinguir maquina calada de listener surdo - o App esta aberto "
            "segurando as portas?"))
        print(f"\nMexa na maquina (pare, toque, knobs, pads, botoes). "
              f"{'Ctrl+C pra sair.' if segundos is None else f'{segundos:.0f} s.'}\n")

        t0 = time.time()
        fim = None if segundos is None else t0 + segundos
        while fim is None or time.time() < fim:
            for p in abertas:
                for msg in p.iter_pending():
                    k = (p.name, msg.type)
                    contagem[k] = contagem.get(k, 0) + 1
                    agora = time.time()
                    if msg.type == "clock":
                        # a pergunta da C0 e sobre o clock da porta COMUM; clock
                        # na CTRL ou vindo de fora pela MIDI IN dobraria a conta
                        # (o resumo por porta, abaixo, mostra cada um)
                        if p.name == tr1000.PORTA_COMUM:
                            s = int(agora - t0)
                            clock_por_s[s] = clock_por_s.get(s, 0) + 1
                        continue
                    if msg.type == "active_sensing":
                        continue
                    # hora e milissegundo do MESMO instante: dois relogios
                    # lidos em momentos diferentes trocavam a ordem dos eventos
                    # na virada do segundo
                    linha = (f"{time.strftime('%H:%M:%S', time.localtime(agora))}"
                             f".{int(agora % 1 * 1000):03d}"
                             f"  [{p.name}]  {_descrever(msg)}")
                    print(linha)
                    if f:
                        f.write(linha + "\n"); f.flush()
            time.sleep(0.002)
    except KeyboardInterrupt:
        pass
    finally:
        for p in abertas:
            p.close()
        if f:
            f.close()

    print("\n── resumo ──")
    for (porta, tipo), n in sorted(contagem.items()):
        print(f"   {porta:18} {tipo:16} {n}")
    # so segundos INTEIROS: o ultimo pedaco (3,002 s de uma janela de 3 s)
    # aparecia como um "0" no fim, que se le como "o clock parou"
    duracao = max(1, int(time.time() - t0))
    if clock_por_s:
        seq = [clock_por_s.get(s, 0) for s in range(duracao)]
        print(f"   clock por segundo em {tr1000.PORTA_COMUM}: "
              + " ".join(str(x) for x in seq))
        print("   (24 por seminima: 48/s = 120 bpm. Clock com a maquina "
              "PARADA e o que a C0 quer saber - anote quando parou/tocou)")
    else:
        print(f"   nenhum clock em {tr1000.PORTA_COMUM}")


def _autoteste(abertas):
    """O nome do primeiro tipo de mensagem que chegar, ou None."""
    limite = time.time() + AUTOTESTE_S
    while time.time() < limite:
        for p in abertas:
            for msg in p.iter_pending():
                return f"{msg.type} em {p.name}"
        time.sleep(0.005)
    respostas = _identidade(abertas)
    if respostas:
        return "Identity Reply em " + ", ".join(sorted({r[0] for r in respostas}))
    return None


# ─────────────────────────────────────────────────────────────
# identidade
# ─────────────────────────────────────────────────────────────
def _identidade(abertas, saidas=(tr1000.PORTA_CTRL, tr1000.PORTA_COMUM)):
    """Manda o Identity Request em cada saida e colhe [(porta_in, dict)]."""
    for p in abertas:
        p.iter_pending()                                  # drena o velho
    respostas = []
    for nome in saidas:
        po = porta_exata(nome, entradas=False)
        if not po:
            continue
        with SaidaMIDI(*po) as out:
            out.send_bytes(roland.IDENTITY_REQUEST)
        limite = time.time() + AUTOTESTE_S
        while time.time() < limite:
            for p in abertas:
                for msg in p.iter_pending():
                    if msg.type != "sysex":
                        continue
                    ident = roland.decodificar_identidade(msg.data)
                    if ident:
                        respostas.append((p.name, dict(ident, pedido_em=nome)))
            time.sleep(0.005)
    return respostas


def cmd_identidade():
    entradas = _entradas_tr1000()
    if not entradas:
        print("Nenhuma porta TR-1000."); return
    abertas = []
    try:
        for i, n in entradas:
            abertas.append(EntradaMIDI(i, n))
        respostas = _identidade(abertas)
    finally:
        for p in abertas:
            p.close()
    if not respostas:
        print("Ninguem respondeu ao Identity Request (nem na CTRL, nem na "
              "comum). Isso NAO prova que a maquina nao tem SysEx - so que nao "
              "responde a este pedido universal. O App aberto pode estar "
              "segurando a CTRL.")
        return
    for porta, r in respostas:
        print(f"pedido em {r['pedido_em']!r}, resposta em {porta!r}:")
        print(f"   bruto       {roland.hexs(r['bruto'])}")
        print(f"   dev         {r['dev']:02X}")
        print(f"   fabricante  {roland.hexs(r['fabricante'])}"
              + ("  (Roland)" if r['fabricante'] == [0x41] else ""))
        print(f"   familia     {roland.hexs(r['familia'])}")
        print(f"   membro      {roland.hexs(r['membro'])}")
        print(f"   versao      {roland.hexs(r['versao'])}")
    print("\nAnote na REFERENCIA 2.1 como (medido). O model ID do DT1/RQ1 NAO "
          "sai daqui - sai do sniff do App (sessao C1).")


# ─────────────────────────────────────────────────────────────
# sniff: o SysEx da CTRL
# ─────────────────────────────────────────────────────────────
def cmd_sniff(argv):
    """Escuta a CTRL e decodifica o que for Roland.

    Nao enxerga o que o App MANDA (o rtmidi nao espiona outros processos): para
    isso e o MIDI Monitor em modo spy, sessao C1. Isto serve para ver o que a
    maquina empurra sozinha - a TR-8S empurrava o step atual tocando (tr8s
    REFERENCIA 7.7) - e para conferir respostas nas sessoes C2/C3."""
    arquivo = argv[argv.index("--arquivo") + 1] if "--arquivo" in argv else None
    pi = porta_exata(tr1000.PORTA_CTRL)
    if not pi:
        print(f"Porta {tr1000.PORTA_CTRL!r} nao encontrada."); return
    f, tin, vistos = None, None, 0
    try:
        tin = EntradaMIDI(*pi, callback=True)
        f = open(arquivo, "w") if arquivo else None
        r = _identidade([tin], saidas=(tr1000.PORTA_CTRL,))
        print("autoteste: " + ("a CTRL respondeu ao Identity Request - o "
              "listener esta bom." if r else "(!) a CTRL nao respondeu ao "
              "Identity Request. Silencio daqui pra frente NAO prova nada."))
        print("\nMexa na maquina. Ctrl+C pra sair.\n")
        while True:
            for msg in tin.iter_pending():
                if msg.type != "sysex":
                    continue
                vistos += 1
                print(f"{time.strftime('%H:%M:%S')}  {_descrever(msg)}")
                if f:
                    # formato que o tr1000_sysex.py parse le
                    f.write("  " + time.strftime('%H:%M:%S')
                            + f"   From {tr1000.PORTA_CTRL}   "
                            + roland.hexs([0xF0] + list(msg.data) + [0xF7])
                            + "\n")
                    f.flush()
            time.sleep(0.003)
    except KeyboardInterrupt:
        print(f"\n{vistos} mensagens SysEx.")
    finally:
        if tin:
            tin.close()
        if f:
            f.close()


COMANDOS = {
    "ports":      lambda a: cmd_ports(),
    "escutar":    cmd_escutar,
    "identidade": lambda a: cmd_identidade(),
    "sniff":      cmd_sniff,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__); sys.exit(1)
    COMANDOS[sys.argv[1]](sys.argv[2:])

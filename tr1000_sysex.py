#!/usr/bin/env python3
"""
tr1000_sysex.py - parser, diff e resumo de capturas SysEx da TR-1000 (MIDI Monitor)

Uso:
    python3 tr1000_sysex.py parse  captura.mmon
    python3 tr1000_sysex.py diff   a.mmon b.mmon
    python3 tr1000_sysex.py fx     um-knob.mmon
    python3 tr1000_sysex.py resumo boot-app.mmon [--json enderecos.json]

Herdado do tr8s_sysex.py (tr8s-grid), com duas mudancas:
  - o cabecalho NAO e fixo. O model ID da TR-1000 e desconhecido ate a sessao
    C1 (REFERENCIA 3); o roland.decodificar descobre o tamanho dele pelo
    checksum, e o `resumo` diz qual cabecalho apareceu na captura
  - o `resumo` existe para a sessao C1: do boot do TR-1000 App ele tira a
    tabela de enderecos que o PROPRIO App le, com o tamanho de cada leitura.
    Essa tabela e a lista branca de RQ1 (REFERENCIA 2.1) - perguntar por
    endereco que nao existe derrubava a porta CTRL da TR-8S, e nao vamos
    descobrir se a TR-1000 faz o mesmo do jeito caro

Aceita dois formatos:
  - o arquivo .mmon salvo pelo proprio MIDI Monitor (binary plist /
    NSKeyedArchiver), o formato recomendado
  - texto colado do MIDI Monitor (Cmd+A, Cmd+C, colar em .txt)
"""
import json, os, plistlib, re, sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roland
from roland import RQ1, DT1, CMDS, hexs

# Enderecos de keep-alive: o TR-EDITOR da TR-8S perguntava a cada 3 s. O da
# TR-1000 nao e conhecido - o `resumo` aponta CANDIDATOS (mesmo RQ1 repetido em
# intervalo regular), e so depois de confirmados eles entram aqui.
KEEPALIVE = set()


# Uma SysEx crua de uma linha de texto: comeca em F0 que NAO e o fim de outro
# numero hexa. Sem o lookbehind, em "From TR-1000\tF0 41 ..." o casamento mais
# a esquerda comecava no "00" de "1000" e a linha inteira era descartada
# (revisao de 07/10/2026). So "TR-1000 CTRL" escapava, porque "CT" quebra a
# sequencia.
_SYSEX_TEXTO = re.compile(r'(?<![0-9A-Fa-f])(F0(?:\s+[0-9A-Fa-f]{2}){9,})')


def _bruto_da_linha(line):
    """(direcao, bytes sem F0/F7) de uma linha de texto, ou None."""
    m = _SYSEX_TEXTO.search(line)
    if not m:
        return None
    b = [int(x, 16) for x in m.group(1).split()]
    if b[-1] != 0xF7:
        return None
    return ("TX" if "To " in line else "RX"), b[1:-1]


def decodificar_lista(brutos, keep_alive=False, outros=None):
    """[(direcao, bytes, t, endpoint)] -> [dict], em DUAS passadas.

    A primeira acha o cabecalho dominante da captura (as mensagens que
    decodificam sem ambiguidade e com checksum certo). A segunda decodifica
    TUDO com ele - inclusive as de checksum ruim, que assim aparecem como
    ruins em vez de sumirem (roland.decodificar). O que nao casa com o
    dominante e decodificado sozinho e conta como outro cabecalho."""
    cab = roland.cabecalho_dominante(b for _, b, _, _ in brutos)
    msgs = []
    for direcao, b, t, ep in brutos:
        r = (roland.decodificar(b, cabecalho=cab) if cab else None) \
            or roland.decodificar(b)
        if r is None:
            if outros is not None:
                outros["sysex-nao-roland"] = outros.get("sysex-nao-roland", 0) + 1
            continue
        if not keep_alive and r["addr"] in KEEPALIVE:
            continue
        r.update(dir=direcao, t=t, endpoint=ep)
        msgs.append(r)
    return msgs


def parse_line(line):
    """Uma mensagem SysEx Roland de uma linha do log do MIDI Monitor, ou None.
    Linha solta nao tem captura em volta: decodifica sem cabecalho dominante."""
    bruto = _bruto_da_linha(line)
    if bruto is None:
        return None
    r = decodificar_lista([(bruto[0], bruto[1], None, "")], keep_alive=True)
    return r[0] if r else None


def load_mmon(path, keep_alive=False, outros=None):
    """Le o .mmon do MIDI Monitor: plist externo com 'messageData', que e um
    NSKeyedArchiver; cada mensagem tem statusByte, data (payload SEM F0/F7,
    checksum incluso), originatingEndpoint ('To ...' = TX = o App falando com a
    maquina, 'From ...' = RX = a maquina respondendo) e clockTimeStamp.
    Formato conferido nas capturas do tr8s-grid em 15/08/2026.

    `outros`, se for um dict, recebe a contagem das mensagens que NAO sao
    SysEx Roland (clock, nota, CC...) por statusByte - util para ver o que mais
    passou pela porta sem poluir a lista."""
    with open(path, "rb") as f:
        externo = plistlib.load(f)
    if outros is not None:
        # o que estava sendo monitorado: e o que torna uma captura VAZIA uma
        # prova ("o App nao mandou nada") em vez de um defeito do observador
        cfg = externo.get("streamSettings", {})
        outros["fontes"] = ", ".join(x.get("name", "?") for x in
                                     cfg.get("portInputStream", [])) or "-"
        outros["espionando"] = ", ".join(x.get("name", "?") for x in
                                         cfg.get("spyingInputStream", [])) or "-"
    if "messageData" not in externo:
        # o MIDI Monitor salva sem a chave quando nada chegou (medido em
        # 08/10/2026, boot do App com ctrlPort = 0). Antes: KeyError
        return []
    inner = plistlib.loads(externo["messageData"])
    objs = inner["$objects"]

    def deref(u):
        return objs[u.data] if isinstance(u, plistlib.UID) else u

    brutos = []
    for o in objs:
        if not (isinstance(o, dict) and "statusByte" in o):
            continue
        if o["statusByte"] != 0xF0:
            if outros is not None:
                outros[o["statusByte"]] = outros.get(o["statusByte"], 0) + 1
            continue
        bruto = deref(o["data"])
        b = list(bruto["NS.data"] if isinstance(bruto, dict) else bruto)
        ep = str(deref(o.get("originatingEndpoint", "")))
        brutos.append(("TX" if ep.startswith("To ") else "RX", b,
                       o.get("clockTimeStamp"), ep))
    brutos.sort(key=lambda x: x[2] or 0)
    return decodificar_lista(brutos, keep_alive, outros)


def load(path, keep_alive=False, outros=None):
    if path.lower().endswith(".mmon"):
        return load_mmon(path, keep_alive, outros)
    brutos = []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            bruto = _bruto_da_linha(line)
            if bruto:
                brutos.append((bruto[0], bruto[1], None, ""))
    return decodificar_lista(brutos, keep_alive, outros)


fmt_addr = hexs          # um formatador so: as chaves "20 00 00 00" do JSON e
                         # dos testes dependem dele nao divergir do roland.hexs


def cmd_parse(path):
    outros = {}
    msgs = load(path, outros=outros)
    bad = sum(1 for m in msgs if not m["chk_ok"])
    amb = sum(1 for m in msgs if m["ambiguo"])
    cabs = sorted({tuple(m["cabecalho"]) for m in msgs})
    print(f"{path}: {len(msgs)} mensagens Roland, {bad} com checksum invalido, "
          f"{amb} com model ID ambiguo")
    print(f"cabecalhos vistos: {', '.join(hexs(c) for c in cabs) or '-'}")
    if outros:
        print("outras mensagens (nao listadas): " + ", ".join(
            f"{k if isinstance(k, str) else hex(k)}={v}"
            for k, v in sorted(outros.items(), key=str)))
    print()
    for m in msgs:
        n = len(m["data"])
        if m["cmd"] == RQ1:
            preview = f"pede {roland.de_7bits(m['data'][:4])} B"
        else:
            preview = hexs(m["data"][:12]) + ("..." if n > 12 else "")
        flag = ("" if m["chk_ok"] else "  <-- CHECKSUM RUIM") + \
               ("  <-- model ID ambiguo" if m["ambiguo"] else "")
        print(f"{m['dir']} {CMDS.get(m['cmd'], hex(m['cmd'])):4} "
              f"addr {fmt_addr(m['addr'])}  {n:5}B  {preview}{flag}")


def index_by_addr(msgs, cmd=DT1):
    """Junta os dados por endereco (ultima ocorrencia vence)."""
    out = OrderedDict()
    for m in msgs:
        if cmd and m["cmd"] != cmd:
            continue
        if not m["data"]:
            continue
        out[m["addr"]] = m["data"]
    return out


def cmd_diff(p1, p2):
    a = index_by_addr(load(p1))
    b = index_by_addr(load(p2))

    only_a = [k for k in a if k not in b]
    only_b = [k for k in b if k not in a]
    if only_a:
        print(f"So em {p1}: {', '.join(fmt_addr(k) for k in only_a)}")
    if only_b:
        print(f"So em {p2}: {', '.join(fmt_addr(k) for k in only_b)}")

    achou = False
    for addr in a:
        if addr not in b:
            continue
        d1, d2 = a[addr], b[addr]
        if d1 == d2:
            continue
        achou = True
        print(f"\n### addr {fmt_addr(addr)}  ({len(d1)} bytes)")
        for i, (x, y) in enumerate(zip(d1, d2)):
            if x != y:
                print(f"  offset {i:4} (0x{i:03X}): {x:02X} -> {y:02X}")
        if len(d2) != len(d1):
            print(f"  (tamanhos diferentes: {len(d1)} vs {len(d2)})")

    if not achou:
        print("\nNenhuma diferenca de dados entre enderecos comuns.")


def cmd_fx(path):
    """Decodifica uma sessao de sniff do App, um controle por vez (o M2 do
    tr8s-grid, REFERENCIA 3.2 regra 3).

    O App manda um DT1 a cada mexida. Mexendo UM controle por vez, a ordem
    cronologica das mudancas casa com a ordem em que voce mexeu. Parametro de
    2 bytes aparece como DOIS offsets vizinhos mexendo juntos."""
    msgs = [m for m in load(path) if m["cmd"] == DT1 and m["dir"] == "TX"]
    if not msgs:
        print("nenhum DT1 saindo do App na captura"); return

    anterior, eventos = {}, []
    for m in msgs:
        chave = m["addr"]
        antes = anterior.get(chave)
        if antes is not None and len(antes) == len(m["data"]):
            difs = [(i, a, b) for i, (a, b) in enumerate(zip(antes, m["data"]))
                    if a != b]
            if difs and len(difs) <= 4:
                eventos.append((chave, difs))
        elif 0 < len(m["data"]) <= 4:
            # escrita curta: o proprio endereco ja aponta o offset. TODOS os
            # bytes, nao so o primeiro - um parametro de 2 bytes escrito num
            # DT1 curto mostrava so o MSB (revisao de 07/10/2026). DT1 sem
            # dados nao vira evento (antes era IndexError)
            eventos.append((chave, [(i, None, v)
                                    for i, v in enumerate(m["data"])]))
        anterior[chave] = list(m["data"])

    if not eventos:
        print(f"{len(msgs)} DT1, mas nenhuma MUDANCA de valor detectada.\n"
              "Dica: limpe o MIDI Monitor DEPOIS que o App terminar de ler a "
              "maquina, senao a leitura inicial domina a captura.")
        return

    print(f"{len(msgs)} DT1, {len(eventos)} mudancas, na ordem em que voce "
          "mexeu:\n")
    print(f"{'#':>3}  {'endereco':<12} {'offset':>6}  valor")
    for n, (addr, difs) in enumerate(eventos, 1):
        offs = ", ".join(str(o) for o, _, _ in difs)
        vals = ", ".join(f"{b:02X}" for _, _, b in difs)
        marca = "  (2 bytes)" if len(difs) == 2 and \
            difs[1][0] == difs[0][0] + 1 else ""
        print(f"{n:>3}  {fmt_addr(addr):<12} {offs:>6}  {vals}{marca}")


# ─────────────────────────────────────────────────────────────
# resumo: a lista branca de enderecos (sessao C1)
# ─────────────────────────────────────────────────────────────
def _uniao(intervalos):
    """[(ini, fim)] -> uniao ordenada, juntando os que encostam."""
    out = []
    for ini, fim in sorted(intervalos):
        if out and ini <= out[-1][1]:
            out[-1][1] = max(out[-1][1], fim)
        else:
            out.append([ini, fim])
    return [tuple(x) for x in out]


def resumir(msgs):
    """O que uma captura diz sobre o mapa de enderecos.

    - leituras: cada (endereco, tamanho) que o App pediu por RQ1, quantas
      vezes, e se veio resposta naquele endereco. E a lista branca.
    - respostas: as regioes cobertas pelos DT1 que a MAQUINA mandou (RX),
      unidas - uma resposta grande pode vir quebrada em varios DT1 seguidos
    - escritas: os DT1 que o App mandou (TX), por endereco
    - keepalive: RQ1 repetido >= 3 vezes em intervalo quase constante -
      CANDIDATO, nao fato (regra 6 do Metodo: pergunte antes de virar ruido)
    """
    cabecalhos = defaultdict(int)
    leituras = OrderedDict()
    tempos = defaultdict(list)
    escritas = OrderedDict()
    respondidos = set()
    intervalos = []
    for m in msgs:
        cabecalhos[tuple(m["cabecalho"])] += 1
        if m["cmd"] == RQ1 and m["dir"] == "TX":
            tam = roland.de_7bits(m["data"][:4])
            k = (m["addr"], tam)
            leituras[k] = leituras.get(k, 0) + 1
            if m["t"] is not None:
                tempos[k].append(m["t"])
        elif m["cmd"] == DT1 and m["dir"] == "RX":
            respondidos.add(m["addr"])
            ini = roland.addr_para_int(m["addr"])
            intervalos.append((ini, ini + len(m["data"])))
        elif m["cmd"] == DT1 and m["dir"] == "TX":
            escritas[m["addr"]] = escritas.get(m["addr"], 0) + 1

    keepalive = []
    for k, ts in tempos.items():
        if len(ts) < 3:
            continue
        # mediana e nao media/extremos: durante a leitura em massa do boot o
        # keep-alive atrasa algumas vezes, e um so passo torto derrubava o
        # criterio de "max - min" (testado contra o boot da TR-8S, 73 repeticoes)
        passos = sorted(b - a for a, b in zip(ts, ts[1:]))
        mediana = passos[len(passos) // 2]
        regulares = sum(1 for p in passos if abs(p - mediana) < 0.25 * mediana)
        if mediana > 0.2 and regulares >= 0.7 * len(passos):
            keepalive.append((k, round(mediana, 2)))

    return dict(
        cabecalhos=dict(cabecalhos),
        leituras=[dict(addr=fmt_addr(a), tamanho=t, vezes=n,
                       respondeu=a in respondidos)
                  for (a, t), n in leituras.items()],
        regioes=[dict(ini=fmt_addr(roland.int_para_addr(i)),
                      fim=fmt_addr(roland.int_para_addr(f)), bytes=f - i)
                 for i, f in _uniao(intervalos)],
        escritas=[dict(addr=fmt_addr(a), vezes=n) for a, n in escritas.items()],
        keepalive=[dict(addr=fmt_addr(a), tamanho=t, periodo_s=p)
                   for (a, t), p in keepalive],
    )


def cmd_resumo(path, destino=None):
    outros = {}
    r = resumir(load(path, keep_alive=True, outros=outros))
    print(f"{path}")
    print("cabecalhos (41 dev model...):")
    for c, n in sorted(r["cabecalhos"].items(), key=lambda x: -x[1]):
        print(f"   {hexs(c):24} {n} mensagens")
    if outros:
        print("outras mensagens: " + ", ".join(
            f"{k if isinstance(k, str) else hex(k)}={v}"
            for k, v in sorted(outros.items(), key=str)))
    print(f"\nleituras do App ({len(r['leituras'])} pares endereco/tamanho):")
    for x in r["leituras"]:
        sem = "" if x["respondeu"] else "   <- SEM resposta no endereco"
        print(f"   {x['addr']}  {x['tamanho']:6} B  x{x['vezes']}{sem}")
    print(f"\nregioes cobertas pelas respostas ({len(r['regioes'])}):")
    for x in r["regioes"]:
        print(f"   {x['ini']} .. {x['fim']}  {x['bytes']:6} B")
    if r["escritas"]:
        print(f"\nescritas do App ({len(r['escritas'])} enderecos):")
        for x in r["escritas"]:
            print(f"   {x['addr']}  x{x['vezes']}")
    if r["keepalive"]:
        print("\nCANDIDATOS a keep-alive (confirmar antes de filtrar):")
        for x in r["keepalive"]:
            print(f"   {x['addr']}  {x['tamanho']} B  a cada ~{x['periodo_s']} s")
    if destino:
        with open(destino, "w") as f:
            json.dump(dict(fonte=os.path.basename(path), **{
                k: ({hexs(c): n for c, n in v.items()}
                    if k == "cabecalhos" else v)
                for k, v in r.items()}), f, indent=2)
        print(f"\ngravado em {destino}")


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    if a[1] == "parse":
        cmd_parse(a[2])
    elif a[1] == "fx":
        cmd_fx(a[2])
    elif a[1] == "diff" and len(a) >= 4:
        cmd_diff(a[2], a[3])
    elif a[1] == "resumo":
        cmd_resumo(a[2], a[a.index("--json") + 1] if "--json" in a else None)
    else:
        print(__doc__)

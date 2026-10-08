#!/usr/bin/env python3
"""
tr1000_serial.py - le as capturas .serlog do espiao (a serial USB do App)

Uso:
    python3 tr1000_serial.py bruto        captura.serlog [--max N]
    python3 tr1000_serial.py estatisticas captura.serlog

E, se a serial carregar SysEx Roland (hipotese H1, REFERENCIA 2.1b), todos os
comandos do tr1000_sysex.py aceitam o .serlog direto:
    python3 tr1000_sysex.py resumo captura.serlog [--json enderecos.json]
    python3 tr1000_sysex.py parse|diff|fx ...

O .serlog e gravado pelo espiao/espiao_serial.c dentro de uma copia do App
(espiao.py). Formato, little-endian:
    cabecalho: "TR1KSER1" + versao u32
    registro:  t_ns u64 | tipo u8 | fd u32 | n u32 | n bytes
    tipos:     S inicio  O open  C close  R read  W write  I ioctl  T tcsetattr

Direcao: W = o App escrevendo para a maquina = "TX" (como o "To ..." do MIDI
Monitor); R = o App lendo o que a maquina mandou = "RX".
"""
import os, struct, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roland
from roland import hexs

MAGICO = b"TR1KSER1"
CABECALHO = struct.Struct("<8sI")
REGISTRO = struct.Struct("<QBII")
TIPOS = {"S": "inicio", "O": "open", "C": "close", "R": "read", "W": "write",
         "I": "ioctl", "T": "tcsetattr"}
DIRECAO = {"W": "TX", "R": "RX"}


def serializar(registros, versao=1):
    """[(t_ns, tipo, fd, bytes)] -> bytes de um .serlog. Existe para os testes
    escreverem capturas sinteticas no MESMO formato do espiao."""
    out = [CABECALHO.pack(MAGICO, versao)]
    for t, tipo, fd, dados in registros:
        out.append(REGISTRO.pack(t, ord(tipo), fd, len(dados)) + bytes(dados))
    return b"".join(out)


def ler_serlog(caminho):
    """-> [dict(t, tipo, fd, dados)], t em segundos (float, relogio de parede).

    Um registro cortado no fim (o App morto no meio de uma escrita do log) e
    descartado com aviso em vez de derrubar a leitura do resto."""
    with open(caminho, "rb") as f:
        bruto = f.read()
    if len(bruto) < CABECALHO.size:
        raise ValueError(f"{caminho}: curto demais para ser .serlog")
    magico, versao = CABECALHO.unpack_from(bruto)
    if magico != MAGICO:
        raise ValueError(f"{caminho}: nao e .serlog (magico {magico!r})")
    regs, pos = [], CABECALHO.size
    while pos + REGISTRO.size <= len(bruto):
        t, tipo, fd, n = REGISTRO.unpack_from(bruto, pos)
        pos += REGISTRO.size
        if pos + n > len(bruto):
            print(f"(!) registro cortado no fim de {caminho}", file=sys.stderr)
            break
        regs.append(dict(t=t / 1e9, tipo=chr(tipo), fd=fd,
                         dados=bruto[pos:pos + n]))
        pos += n
    return regs


def autoteste(regs):
    """(carregou, abriu_serial): o espiao entrou no processo? E viu a porta?

    Sem o 'S' o espiao nem carregou (dyld ignorou o DYLD_INSERT_LIBRARIES); sem
    o 'O' de usbmodem ele carregou mas o App nao abriu a serial. Nos dois casos
    uma captura vazia NAO prova nada (Metodo, regra 1)."""
    carregou = any(r["tipo"] == "S" for r in regs)
    abriu = any(r["tipo"] == "O" and b"usbmodem" in r["dados"] for r in regs)
    return carregou, abriu


def quadros_sysex(regs):
    """Remonta os quadros F0..F7 de cada DIRECAO como um fluxo continuo.

    read() corta onde quiser: um quadro pode vir em tres leituras, e uma
    leitura pode trazer dois quadros. Por isso nada aqui e por chamada.

    -> (quadros, sobra) com quadros = [(direcao, bytes sem F0/F7, t)] e
    sobra = {direcao: bytes que caiu FORA de qualquer quadro}. Muita sobra e o
    sinal de que a hipotese H1 (serial = SysEx Roland) esta errada."""
    quadros, sobra = [], Counter()
    aberto = {"TX": None, "RX": None}
    for r in regs:
        direcao = DIRECAO.get(r["tipo"])
        if not direcao:
            continue
        for b in r["dados"]:
            if b >= 0xF8:                       # tempo real pode vir no meio
                continue
            if b == 0xF0:
                if aberto[direcao] is not None:
                    sobra[direcao] += len(aberto[direcao]) + 1   # quadro sem F7
                aberto[direcao] = []
            elif aberto[direcao] is not None:
                if b == 0xF7:
                    quadros.append((direcao, aberto[direcao], r["t"]))
                    aberto[direcao] = None
                else:
                    aberto[direcao].append(b)
            else:
                sobra[direcao] += 1
    return quadros, dict(sobra)


def carregar(caminho, keep_alive=False, outros=None):
    """O .serlog no formato do tr1000_sysex (dicts com dir, cmd, addr, data,
    t, chk_ok...) - e o que deixa parse/diff/fx/resumo de la funcionarem aqui.
    `outros` recebe o autoteste e quanto byte ficou fora de quadro."""
    import tr1000_sysex                      # tardio: tr1000_sysex importa este
    regs = ler_serlog(caminho)
    quadros, sobra = quadros_sysex(regs)
    if outros is not None:
        carregou, abriu = autoteste(regs)
        outros["espiao-carregou"] = "sim" if carregou else "NAO"
        outros["abriu-serial"] = "sim" if abriu else "NAO"
        for d, n in sobra.items():
            outros[f"bytes-fora-de-quadro-{d}"] = n
    brutos = [(d, q, t, "serial") for d, q, t in quadros]
    return tr1000_sysex.decodificar_lista(brutos, keep_alive, outros)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def _ascii(b):
    return "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in b)


def cmd_bruto(caminho, maximo=None):
    regs = ler_serlog(caminho)
    if not regs:
        print("captura vazia"); return
    t0 = regs[0]["t"]
    for i, r in enumerate(regs):
        if maximo is not None and i >= maximo:
            print(f"... (+{len(regs) - maximo} registros)"); break
        d = r["dados"]
        if r["tipo"] in "SO":
            corpo = d.decode("utf-8", "replace")
        elif r["tipo"] == "I":
            corpo = f"request 0x{struct.unpack('<Q', d)[0]:X}" if len(d) == 8 else hexs(d)
        elif r["tipo"] == "T":
            corpo = _termios(d)
        else:
            corpo = hexs(d[:48]) + (" ..." if len(d) > 48 else "") + \
                    "   |" + _ascii(d[:48]) + "|"
        quem = f"pid{r['fd']}" if r["tipo"] == "S" else f"fd{r['fd']}"
        print(f"{r['t'] - t0:9.4f}  {r['tipo']} {TIPOS.get(r['tipo'], '?'):9} "
              f"{quem:<8} {len(d):6}B  {corpo}")


def _termios(d):
    """struct termios do macOS (arm64/x86_64): 4 x tcflag_t (unsigned long, 8B),
    cc_t c_cc[20], depois ispeed/ospeed (speed_t = unsigned long). So a
    velocidade interessa: e o baud da serial."""
    if len(d) < 4 * 8 + 20:
        return hexs(d)
    deslocamento = 4 * 8 + 20
    deslocamento += (-deslocamento) % 8            # alinhamento do speed_t
    if len(d) >= deslocamento + 16:
        isp, osp = struct.unpack_from("<QQ", d, deslocamento)
        return f"ispeed {isp}  ospeed {osp}"
    return hexs(d)


def cmd_estatisticas(caminho):
    regs = ler_serlog(caminho)
    carregou, abriu = autoteste(regs)
    print(f"{caminho}: {len(regs)} registros")
    print(f"autoteste: espiao carregou = {'sim' if carregou else 'NAO'}, "
          f"abriu a serial = {'sim' if abriu else 'NAO'}")
    for r in regs:
        if r["tipo"] == "O":
            print(f"   open fd{r['fd']}: {r['dados'].decode('utf-8', 'replace')}")
        if r["tipo"] == "T":
            print(f"   tcsetattr fd{r['fd']}: {_termios(r['dados'])}")
    quadros, sobra = quadros_sysex(regs)
    for tipo, direcao in (("W", "TX"), ("R", "RX")):
        rs = [r for r in regs if r["tipo"] == tipo]
        total = sum(len(r["dados"]) for r in rs)
        print(f"\n## {direcao} ({'App -> maquina' if tipo == 'W' else 'maquina -> App'})")
        print(f"   {len(rs)} chamadas, {total} bytes")
        if not rs:
            continue
        nq = sum(1 for q in quadros if q[0] == direcao)
        dentro = sum(len(q[1]) + 2 for q in quadros if q[0] == direcao)
        print(f"   quadros F0..F7: {nq}  ({100 * dentro / max(total, 1):.1f}% dos "
              f"bytes; fora de quadro: {sobra.get(direcao, 0)})")
        primeiros = Counter(r["dados"][0] for r in rs)
        print("   primeiro byte das chamadas: " + "  ".join(
            f"{b:02X}x{n}" for b, n in primeiros.most_common(8)))
        tamanhos = Counter(len(r["dados"]) for r in rs)
        print("   tamanhos mais comuns: " + "  ".join(
            f"{t}Bx{n}" for t, n in tamanhos.most_common(8)))
        fluxo = b"".join(r["dados"] for r in rs)
        quads = Counter(fluxo[i:i + 4] for i in range(0, max(len(fluxo) - 3, 0)))
        print("   4-gramas frequentes: " + "  ".join(
            f"[{hexs(g)}]x{n}" for g, n in quads.most_common(6)))


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    if a[1] == "bruto":
        cmd_bruto(a[2], int(a[a.index("--max") + 1]) if "--max" in a else None)
    elif a[1] == "estatisticas":
        cmd_estatisticas(a[2])
    else:
        print(__doc__)

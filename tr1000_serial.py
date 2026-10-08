#!/usr/bin/env python3
"""
tr1000_serial.py - le as capturas .serlog do espiao (a serial USB do App)

Uso:
    python3 tr1000_serial.py bruto        captura.serlog [--max N]
    python3 tr1000_serial.py estatisticas captura.serlog
    python3 tr1000_serial.py pacotes      captura.serlog [--max N]
    python3 tr1000_serial.py blocos       captura.serlog
    python3 tr1000_serial.py pattern      captura.serlog   # a grade
    python3 tr1000_serial.py escritas     captura.serlog   # os 01 do App
    python3 tr1000_serial.py diffblocos   a.serlog b.serlog

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


# ─────────────────────────────────────────────────────────────
# O protocolo de pacotes da serial (medido 08/10/2026, REFERENCIA 2.1c)
#
# A hipotese H1 (SysEx Roland) caiu na C1-S0: 0,2% dos bytes em quadros F0..F7.
# O que passa e um protocolo binario proprio, little-endian, em pacotes:
#   tipo & 0x7F == 0x14: 12 bytes fixos  [tipo][canal][orig][dest][u32][u32]
#   tipo & 0x7F == 0x15: 16 de cabecalho [tipo][canal][orig][dest][u32][u32]
#                        [u32 n] + n bytes de carga
# Essa regra enquadrou a captura inteira, nas duas direcoes, com ZERO byte
# sobrando (86 KB do App, 1,43 MB da maquina).
# ─────────────────────────────────────────────────────────────
PAC_CURTO, PAC_DADOS = 0x14, 0x15
# Maior carga vista: 1195 B (S0). Um "tamanho" muito acima disso e lixo -
# um byte desalinhado que por acaso vale 0x15 - e nao pode travar o fluxo
# esperando megabytes que nunca vem (revisao do PR #2).
MAX_CARGA = 1 << 16
# Cargas (todas: <cmd u8> <bloco u16> <x u16> <y u16> <indice u16> ...):
LER_BLOCO = 0x82            # App:     82 ... <n u16>              (medido 08/10)
BLOCO_LIDO = 0x02           # maquina: 02 ... <n u16> + n x u32    (medido 08/10)
ESCREVER = 0x01             # App:     01 ... <valor u32>          (medido 08/10, knob-bd-tune)
ESCRITO = 0x03              # maquina: 03 ... <indice u16>         (o "ok" de cada 01)
# x e y sao os dois indices de instancia: y = track (0..9 = BD..RC) ou layer
# (0/1); x = slot de sample (0..499) no bloco 156.


def enquadrar(buf):
    """bytes -> (pacotes completos, resto que ainda nao fecha um pacote).

    Byte que nao comeca pacote conhecido sai como pacote de 1 byte - nao foi
    visto em nenhuma captura, e se aparecer e o sinal de que o enquadramento
    nao e o que achamos. Usado sobre as capturas (pacotes) e ao vivo
    (conexao_serial), que le a porta em pedacos."""
    out = []
    while buf:
        t = buf[0] & 0x7F
        if t == PAC_CURTO:
            n = 12
        elif t == PAC_DADOS:
            if len(buf) < 16:
                break
            n = 16 + struct.unpack_from("<I", buf, 12)[0]
            if n - 16 > MAX_CARGA:
                n = None                     # tamanho absurdo: nao e cabecalho
        else:
            n = None
        if n is None:
            out.append(buf[:1])              # byte solto; tenta realinhar no proximo
            buf = buf[1:]
            continue
        if len(buf) < n:
            break
        out.append(buf[:n])
        buf = buf[n:]
    return out, buf


def pacotes(regs):
    """-> [(direcao, t, bytes do pacote)], remontados sobre o fluxo de cada
    direcao (read() corta onde quiser). t e a hora do registro em que o
    pacote TERMINOU de chegar."""
    out = []
    for tipo_reg, direcao in (("W", "TX"), ("R", "RX")):
        buf = b""
        for r in regs:
            if r["tipo"] != tipo_reg:
                continue
            prontos, buf = enquadrar(buf + r["dados"])
            out.extend((direcao, r["t"], p) for p in prontos)
    out.sort(key=lambda x: x[1])
    return out


def carga(pac):
    return pac[16:] if pac and (pac[0] & 0x7F) == PAC_DADOS else b""


def _endereco(c):
    """<bloco u16> <x u16> <y u16> <indice u16> da carga (depois do cmd)."""
    return struct.unpack_from("<HHHH", c, 1)


# ─────────────────────────────────────────────────────────────
# Montar pacotes (C3, a primeira escrita nossa - REFERENCIA 3.1)
#
# Os cabecalhos sao COPIADOS byte a byte de pacotes que o App mandou e a
# maquina aceitou (knob-bd-tune, 08/10/2026). Os bytes 4..11 variam no App
# (parecem ponteiro e nao voltam na resposta: a maquina os ignora - deduzido);
# usar exatamente um valor visto e o jeito de nao inventar nada.
# ─────────────────────────────────────────────────────────────
APERTO = bytes.fromhex("94 02 40 F0 FE C0 00 00 00 84 03 03")       # (medido 08/10)
POLL = bytes.fromhex("14 08 40 F0 9B 00 00 00 00 00 00 05")         # (medido 08/10)
CAB_ESCRITA = bytes.fromhex("15 08 41 F2 01 00 00 00 C0 88 06 2D")  # o do 1o 01 do knob
CAB_LEITURA = bytes.fromhex("15 08 41 F2 00 00 00 00 40 87 06 2D")  # o do 82 de n = 1


def pacote_dados(cabecalho12, carga_):
    """Cabecalho de 12 + u32 tamanho + carga: um pacote 0x15."""
    return bytes(cabecalho12) + struct.pack("<I", len(carga_)) + bytes(carga_)


def carga_ler(bloco, x, y, indice, n=1):
    return struct.pack("<BHHHHH", LER_BLOCO, bloco, x, y, indice, n)


def carga_escrever(bloco, x, y, indice, valor):
    return struct.pack("<BHHHHI", ESCREVER, bloco, x, y, indice, valor)


def resposta_02(pac):
    """-> (bloco, x, y, indice, [u32...]) de uma resposta de leitura, ou None."""
    c = carga(pac)
    if c[:1] != bytes([BLOCO_LIDO]) or len(c) < 11:
        return None
    bloco, x, y, indice = _endereco(c)
    n = struct.unpack_from("<H", c, 9)[0]
    if len(c) != 11 + 4 * n:
        return None
    return bloco, x, y, indice, list(struct.unpack_from(f"<{n}I", c, 11))


def ack_03(pac):
    """-> (bloco, x, y, indice) da confirmacao de uma escrita, ou None.
    Forma medida: 03 <bloco> <x> <y> <indice> <indice de novo>."""
    c = carga(pac)
    if c[:1] != bytes([ESCRITO]) or len(c) < 9:
        return None
    return _endereco(c)


def versao_95(pac):
    """A versao em ASCII no fim da resposta ao aperto ('1.22'), ou None."""
    if not pac or pac[0] != 0x95:
        return None
    c = carga(pac)
    fim = len(c)
    while fim > 0 and 0x20 <= c[fim - 1] < 0x7F:
        fim -= 1
    texto = c[fim:].decode("ascii")
    return texto or None


def leituras_de_bloco(pacs):
    """Os pedidos 82 do App -> {(bloco, x, y): (indice, n)}."""
    out = {}
    for direcao, t, p in pacs:
        c = carga(p)
        if direcao == "TX" and c[:1] == bytes([LER_BLOCO]) and len(c) >= 11:
            bloco, x, y, indice = _endereco(c)
            out[(bloco, x, y)] = (indice, struct.unpack_from("<H", c, 9)[0])
    return out


def escritas(pacs):
    """Os 01 do App -> [(t, bloco, x, y, indice, valor)], na ordem."""
    out = []
    for direcao, t, p in pacs:
        c = carga(p)
        if direcao == "TX" and c[:1] == bytes([ESCREVER]) and len(c) >= 13:
            bloco, x, y, indice = _endereco(c)
            out.append((t, bloco, x, y, indice, struct.unpack_from("<I", c, 9)[0]))
    return out


def valores_de_bloco(pacs):
    """As respostas 02 da maquina -> [(t, bloco, x, y, indice, [u32...])].
    So as que fecham: n x 4 bytes depois do cabecalho de 11 da carga."""
    out = []
    for direcao, t, p in pacs:
        c = carga(p)
        if direcao == "RX" and c[:1] == bytes([BLOCO_LIDO]) and len(c) >= 11:
            bloco, x, y, indice = _endereco(c)
            n = struct.unpack_from("<H", c, 9)[0]
            if len(c) == 11 + 4 * n:
                out.append((t, bloco, x, y, indice,
                            list(struct.unpack_from(f"<{n}I", c, 11))))
    return out


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


# A leitura do pattern a partir dos blocos (DEDUCAO de 08/10/2026 sobre a S0,
# a confirmar com o Luan olhando o painel - REFERENCIA 2.1c):
#   bloco 116            cabecalho: nome em ASCII (1 char por u32), tempo x100
#   bloco 117 + 3*v      cabecalho da variacao v (0..7 = A..H, 8..11 = Fill 1..4)
#   bloco 118 + 3*v      os steps do track (instancia 0..9 = BD..RC): note0..63
#                        = 16 steps x 4 slots (slot 0 = layer A, 1 = layer B);
#                        o step toca se algum slot nao e 0 nem FF
#   bloco 119 + 3*v      motion (96 + 48, vazio na S0)
VARIACOES_SERIAL = ["A", "B", "C", "D", "E", "F", "G", "H",
                    "Fill 1", "Fill 2", "Fill 3", "Fill 4"]
TRACKS_SERIAL = ["BD", "SD", "LT", "HT", "RS", "HC", "CH", "OH", "CC", "RC"]
BLOCO_CAB_PATTERN, BLOCO_VAR0, BLOCOS_POR_VAR = 116, 117, 3


def ultimos_valores(pacs):
    """{(bloco, x, y): [u32...]} - a ultima resposta de cada um."""
    return {(b, x, y): v for _, b, x, y, _, v in valores_de_bloco(pacs)}


def nome_e_tempo(cab):
    """Do bloco 116: o nome (u32 por caractere, ate o primeiro valor > 0x7F)
    e o tempo em BPM (o u32 seguinte / 100)."""
    nome = []
    for i, v in enumerate(cab):
        if v > 0x7F:
            return "".join(nome).rstrip(), v / 100
        nome.append(chr(v))
    return "".join(nome).rstrip(), None


SLOT_VAZIO, SLOT_PAUSA = 0x00, 0xFF
SLOT_LAYER_A, SLOT_LAYER_B = 0, 1


def slot_toca(v):
    """Um slot com nota. 0 = vazio, 0xFF = pausa (step ligado e desligado de
    novo vira FF, nao 0 - visto na var H do BD, ruido-1 de 08/10/2026)."""
    return v not in (SLOT_VAZIO, SLOT_PAUSA)


def grade_de_steps(valores):
    """note0..63 = 16 steps x 4 slots -> uma letra por step.

    Os slots NAO sao sub-steps: sao layers (medido 08/10/2026, REFERENCIA
    2.1c). Nos 12 bancos do Dub Techno os tracks de layer (BD SD LT HT) so
    usam os slots 0 e 1, e os simples (RS..RC) so o slot 0. Slot 0 = layer A
    (ou o som normal), slot 1 = layer B; 2 e 3 sem uso visto (ALT?).
      'x' toca o layer A (com ou sem o B): LED VERMELHO no painel
      'b' so o layer B:                    LED VERDE no painel
      '.' nada toca
    As cores foram conferidas pelo Luan no SD da var A."""
    out = []
    for s in range(16):
        slots = valores[s * 4:s * 4 + 4]
        if slot_toca(slots[SLOT_LAYER_A]):
            out.append("x")
        elif any(slot_toca(v) for v in slots[1:]):
            out.append("b")
        else:
            out.append(".")
    return "".join(out)


# Bloco 3 (sistema/performance), medido em 08/10/2026 em 1-01, 1-02 e 2-01:
OFF_PATTERN_GLOBAL = 2      # indice global 0..127 = o x dos blocos de pattern
                            # (medido: 0, 1, 16; [3] e [4] repetem o mesmo valor)
OFF_PATTERN_NO_BANCO = 21   # 1..16 dentro do banco (medido: 1, 2, 1)
OFF_TEMPO_ATUAL = 36        # tempo x 100 (medido: 12800, 12200, 16500)


def nome_do_pattern(indice_global):
    """0 -> '1-01', 1 -> '1-02', 16 -> '2-01' (8 bancos x 16, manual RM p.13)."""
    return f"{indice_global // 16 + 1}-{indice_global % 16 + 1:02d}"


def x_presente(vals):
    """O x em que ha cabecalho de pattern numa captura (o App le um so)."""
    xs = sorted({x for (b, x, y) in vals if b == BLOCO_CAB_PATTERN})
    return xs[0] if xs else 0


def linhas_do_pattern(vals, x=None):
    """{(bloco, x, y): [u32...]} -> as linhas de texto da grade. Serve as
    capturas (cmd_pattern) e a leitura ao vivo (sessao_c4.py). x = o indice
    global do pattern (bloco 3 [2]); sem ele, o que a captura tiver."""
    out = []
    x = x_presente(vals) if x is None else x
    cab = vals.get((BLOCO_CAB_PATTERN, x, 0))
    if cab:
        nome, bpm = nome_e_tempo(cab)
        out.append(f"pattern {nome!r}, tempo {bpm}")
    for v, nome_var in enumerate(VARIACOES_SERIAL):
        bloco = BLOCO_VAR0 + 1 + BLOCOS_POR_VAR * v
        linhas = []
        for tr, nome_tr in enumerate(TRACKS_SERIAL):
            vv = vals.get((bloco, x, tr))
            if vv and len(vv) >= 64:
                g = grade_de_steps(vv)
                if g.strip("."):
                    linhas.append(f"   {nome_tr:3} {g[:4]} {g[4:8]} {g[8:12]} {g[12:]}")
        out.append(f"{nome_var:7}" + ("" if linhas else " vazia"))
        out.extend(linhas)
    return out


def cmd_pattern(caminho):
    for l in linhas_do_pattern(ultimos_valores(pacotes(ler_serlog(caminho)))):
        print(l)


def cmd_diffblocos(a, b):
    """O que mudou nos valores entre duas capturas, bloco a bloco - o
    snapdiff da serial: abre a copia, fecha, faz UM gesto no painel, abre de
    novo (o boot rele tudo), e compara. Metodo, regra 2: rode antes com duas
    capturas SEM gesto no meio para medir o piso de ruido."""
    va = ultimos_valores(pacotes(ler_serlog(a)))
    vb = ultimos_valores(pacotes(ler_serlog(b)))
    so_a = sorted(set(va) - set(vb)); so_b = sorted(set(vb) - set(va))
    if so_a: print(f"so em {a}: {so_a}")
    if so_b: print(f"so em {b}: {so_b}")
    mudou = 0
    for k in sorted(set(va) & set(vb)):
        x, y = va[k], vb[k]
        difs = [(i, p, q) for i, (p, q) in enumerate(zip(x, y)) if p != q]
        if not difs and len(x) == len(y):
            continue
        mudou += 1
        print(f"bloco {k[0]:3d} x {k[1]} y {k[2]}:")
        for i, p, q in difs[:40]:
            eh_steps = (BLOCO_VAR0 <= k[0] < BLOCO_VAR0 + BLOCOS_POR_VAR * len(VARIACOES_SERIAL)
                        and (k[0] - BLOCO_VAR0) % BLOCOS_POR_VAR == 1 and i < 64)
            extra = f"  (step {i // 4 + 1}, slot {i % 4}{' = layer ' + 'AB'[i % 4] if i % 4 < 2 else ''})" \
                if eh_steps else ""
            print(f"   [{i:3d}] {p:X} -> {q:X}{extra}")
        if len(difs) > 40:
            print(f"   ... +{len(difs) - 40}")
    print(f"\n{mudou} blocos com diferenca")


def cmd_pacotes(caminho, maximo=None):
    pacs = pacotes(ler_serlog(caminho))
    if not pacs:
        print("nenhum pacote"); return
    t0 = pacs[0][1]
    for i, (d, t, p) in enumerate(pacs):
        if maximo is not None and i >= maximo:
            print(f"... (+{len(pacs) - maximo} pacotes)"); break
        c = carga(p)
        print(f"{t - t0:9.3f} {d} {len(p):5}B  {hexs(p[:12 if not c else 16])}"
              + (f"  | {hexs(c[:32])}{' ...' if len(c) > 32 else ''}" if c else ""))


def cmd_blocos(caminho):
    """O mapa de blocos que o App leu - o equivalente da lista branca."""
    pacs = pacotes(ler_serlog(caminho))
    ruins = sum(1 for _, _, p in pacs if len(p) == 1)
    print(f"{len(pacs)} pacotes, {ruins} bytes fora de pacote")
    lidos = leituras_de_bloco(pacs)
    por_bloco = {}
    for (bloco, x, y), (indice, n) in lidos.items():
        b = por_bloco.setdefault((bloco, indice, n), [set(), set()])
        b[0].add(x); b[1].add(y)
    print(f"{len(por_bloco)} blocos, {len(lidos)} leituras (bloco x instancia)\n")

    def faixa(v):
        v = sorted(v)
        return f"{v[0]}..{v[-1]} ({len(v)})" if len(v) > 1 else str(v[0])
    for (bloco, indice, n), (xs, ys) in sorted(por_bloco.items()):
        print(f"   bloco {bloco:3d}  indice {indice:4d}  n {n:3d}  x {faixa(xs):12} y {faixa(ys)}")


def cmd_escritas(caminho):
    """Os 01 do App, agrupados por endereco, com a faixa de valores vista."""
    ws = escritas(pacotes(ler_serlog(caminho)))
    if not ws:
        print("nenhuma escrita (01) do App nesta captura"); return
    grupos = {}
    for t, b, x, y, i, v in ws:
        grupos.setdefault((b, x, y, i), []).append((t, v))
    t0 = ws[0][0]
    print(f"{len(ws)} escritas em {len(grupos)} enderecos\n")
    for (b, x, y, i), tv in grupos.items():
        vs = [v for _, v in tv]
        print(f"   bloco {b:3d} x {x:3d} y {y} indice {i:4d}: {len(vs)} escritas "
              f"de {tv[0][0] - t0:.1f} a {tv[-1][0] - t0:.1f} s, valores "
              f"{vs[0]} -> min {min(vs)} / max {max(vs)} -> {vs[-1]}")


if __name__ == "__main__":
    a = sys.argv
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    if a[1] == "bruto":
        cmd_bruto(a[2], int(a[a.index("--max") + 1]) if "--max" in a else None)
    elif a[1] == "estatisticas":
        cmd_estatisticas(a[2])
    elif a[1] == "pacotes":
        cmd_pacotes(a[2], int(a[a.index("--max") + 1]) if "--max" in a else None)
    elif a[1] == "blocos":
        cmd_blocos(a[2])
    elif a[1] == "pattern":
        cmd_pattern(a[2])
    elif a[1] == "escritas":
        cmd_escritas(a[2])
    elif a[1] == "diffblocos" and len(a) >= 4:
        cmd_diffblocos(a[2], a[3])
    else:
        print(__doc__)

#!/usr/bin/env python3
"""
roland.py - a camada SysEx Roland, sem nada de TR-1000 dentro

Herdado do tr8s-grid (lp_tr8s.py :61-75, :131, :453), com uma diferenca de
fundo: la o cabecalho era constante (`41 10 00 00 00 45`, provado contra o
TR-EDITOR). Aqui o MODEL ID da TR-1000 ainda NAO e conhecido (REFERENCIA 3),
entao tudo recebe o cabecalho como parametro e o decodificador descobre o
tamanho do model ID sozinho - pelo checksum, que e a unica coisa que se
auto-valida numa mensagem Roland.

Formato (Roland, "exclusive messages" de toda a linha moderna):
    F0 41 <dev> <model: 1-4 bytes> <cmd> <addr: 4 bytes> <dados> <chk> F7
    cmd 0x11 = RQ1 (pedido de leitura, dados = tamanho em 4 bytes de 7 bits)
    cmd 0x12 = DT1 (dados, numa escrita ou numa resposta)
    chk      = (128 - soma(addr + dados) % 128) % 128
"""

ROLAND   = 0x41
RQ1, DT1 = 0x11, 0x12
CMDS     = {RQ1: "RQ1", DT1: "DT1"}

# Universal Non-Realtime Identity Request (MIDI 1.0, nao e Roland-especifico).
# Nao e RQ1: nao toca no mapa de enderecos, entao nao corre o risco do
# envenenamento da porta CTRL (tr8s-grid REFERENCIA 3.1). E por isso que ele
# serve de AUTOTESTE antes de conhecermos qualquer endereco valido.
IDENTITY_REQUEST = [0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]


def checksum(payload):
    """Checksum Roland sobre endereco + dados."""
    return (128 - sum(payload) % 128) % 128


def tamanho_7bits(n):
    """Tamanho de leitura em 4 bytes de 7 bits (o corpo do RQ1)."""
    return [(n >> 21) & 0x7F, (n >> 14) & 0x7F, (n >> 7) & 0x7F, n & 0x7F]


def de_7bits(b):
    """Inverso de tamanho_7bits: 4 bytes de 7 bits -> inteiro."""
    v = 0
    for x in b:
        v = (v << 7) | (x & 0x7F)
    return v


def addr_soma(addr, offset):
    """Soma com carry de 7 bits (enderecamento Roland)."""
    a = list(addr)
    for i in range(3, -1, -1):
        v = a[i] + (offset & 0x7F)
        offset >>= 7
        a[i] = v & 0x7F
        offset += v >> 7
    return tuple(a)


def addr_para_int(addr):
    """Endereco de 4 bytes de 7 bits -> inteiro linear (para ordenar/medir)."""
    return de_7bits(addr)


def int_para_addr(n):
    return tuple(tamanho_7bits(n))


def mascara_para_nibbles(m):
    """Mascara de 16 bits -> 4 nibbles, o formato que a TR-8S usava para
    ACCENT, mute e variacoes habilitadas. Na TR-1000 e HIPOTESE ate medir."""
    return [(m >> 12) & 0xF, (m >> 8) & 0xF, (m >> 4) & 0xF, m & 0xF]


def nibbles_para_mascara(n):
    return ((n[0] & 0xF) << 12) | ((n[1] & 0xF) << 8) | \
           ((n[2] & 0xF) << 4) | (n[3] & 0xF)


def montar_dt1(cabecalho, addr, data):
    """Bytes crus (com F0/F7) de um DT1. cabecalho = [41, dev, model...]"""
    body = list(addr) + list(data)
    return [0xF0] + list(cabecalho) + [DT1] + body + [checksum(body), 0xF7]


def montar_rq1(cabecalho, addr, tamanho):
    body = list(addr) + tamanho_7bits(tamanho)
    return [0xF0] + list(cabecalho) + [RQ1] + body + [checksum(body), 0xF7]


def decodificar(msg, cabecalho=None):
    """Uma mensagem SysEx Roland -> dict, ou None se nao for uma.

    `msg` pode vir com ou sem F0/F7. Com `cabecalho` conhecido, so aceita esse.
    Sem ele, tenta model IDs de 1 a 4 bytes e fica com o tamanho em que o
    comando e RQ1/DT1 E o checksum fecha. Ambiguidade (dois tamanhos fechando)
    volta como None em vez de chute: preferimos nao decodificar a decodificar
    errado sem aviso - a regra 7 do Metodo (REFERENCIA 3.2) vale para codigo.

    Retorna dict(cabecalho, dev, modelo, cmd, addr, data, chk_ok)."""
    b = list(msg)
    if b and b[0] == 0xF0:
        b = b[1:]
    if b and b[-1] == 0xF7:
        b = b[:-1]
    if len(b) < 2 + 1 + 1 + 4 + 1 or b[0] != ROLAND:
        return None

    def tentar(n_modelo):
        i_cmd = 2 + n_modelo
        if len(b) < i_cmd + 1 + 4 + 1:
            return None
        cmd = b[i_cmd]
        if cmd not in CMDS:
            return None
        addr = tuple(b[i_cmd + 1:i_cmd + 5])
        data = b[i_cmd + 5:-1]
        chk = b[-1]
        return dict(cabecalho=b[:i_cmd], dev=b[1], modelo=tuple(b[2:i_cmd]),
                    cmd=cmd, addr=addr, data=data,
                    chk_ok=chk == checksum(list(addr) + data))

    if cabecalho is not None:
        n = len(cabecalho) - 2
        if b[:len(cabecalho)] != list(cabecalho):
            return None
        return tentar(n)

    bons = [r for r in (tentar(n) for n in (4, 3, 2, 1)) if r and r["chk_ok"]]
    if len(bons) == 1:
        return bons[0]
    return None


def decodificar_identidade(msg):
    """Resposta de Identity Request -> dict, ou None.

    F0 7E <dev> 06 02 <fab> <familia 2B> <membro 2B> <versao 4B> F7
    Roland: fab = 41. Os bytes de familia/membro sao o que a Roland chama de
    "device family code" e "device family number code"."""
    b = list(msg)
    if b and b[0] == 0xF0:
        b = b[1:]
    if b and b[-1] == 0xF7:
        b = b[:-1]
    if len(b) < 4 or b[0] != 0x7E or b[2] != 0x06 or b[3] != 0x02:
        return None
    resto = b[4:]
    return dict(dev=b[1], fabricante=resto[:1], familia=resto[1:3],
                membro=resto[3:5], versao=resto[5:9], bruto=b)


def hexs(b):
    return " ".join(f"{x:02X}" for x in b)

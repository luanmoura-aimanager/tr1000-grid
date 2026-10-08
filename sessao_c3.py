#!/usr/bin/env python3
"""
sessao_c3.py - a sessao C3: a primeira escrita NOSSA na TR-1000 (o portao da fase 0)

    python3 sessao_c3.py ler                  # so le: versao, step 2 do BD, TUNE
    python3 sessao_c3.py step2 desligar       # BD var A step 2 -> FF FF (pausa)
    python3 sessao_c3.py step2 ligar          # BD var A step 2 -> A503C A503C
    python3 sessao_c3.py tune 509             # TUNE do sample do BD (0..1000)

Roteiro passo a passo: ROTEIRO-C0-C3.md, C3. O TR-1000 App (original e copia)
tem que estar FECHADO. Cada escrita: le o valor atual, mostra os bytes que vao
sair, pede "sim" digitado, escreve UMA vez, espera a confirmacao (03) e rele.

Os valores nao saem do nada:
  - FF FF e o que o painel deixa num step ligado e desligado (REFERENCIA 2.1c)
  - A503C A503C e o que o painel pos no step 2 do BD na captura step-bd2
  - o TUNE original do BD era 509 (knob-bd-tune; o App deixou em 1000)

Nada disto e WRITE: fica no buffer de edicao. Religar a maquina descarta.
"""
import sys

import conexao_serial as cs
import tr1000_serial as ts

STEP2 = [(118, 0, 0, 1253), (118, 0, 0, 1254)]      # layers A e B
TUNE = (156, 126, 0, 962)
NOTA_DO_PAINEL = 0xA503C
PAUSA = ts.SLOT_PAUSA


def _hex(v):
    return " ".join(f"{x:X}" for x in v)


def cmd_ler():
    with cs.ConexaoTR1000(nome_captura="c3-ler") as c:
        print(f"aperto de mao: versao {c.aperto()!r}  (esperado '1.22')")
        s2 = [c.ler(*e)[0] for e in STEP2]
        print(f"BD var A step 2, slots A/B: {_hex(s2)}  (esperado A503C A503C)")
        print(f"TUNE do BD: {c.ler(*TUNE)[0]}  (esperado 1000)")
    print(f"\ncaptura: {c.captura}")


def _confirmar(c, enderecos, valores):
    print("\nvai sair, um pacote por endereco:")
    for e, v in zip(enderecos, valores):
        print(f"   {cs.ESCRITAS_PERMITIDAS[e]:34} {ts.hexs(c.pacote_escrita(*e, v))}")
    resp = input('\ndigite "sim" para mandar: ').strip().lower()
    return resp == "sim"


def _escrever(nome, enderecos, valores):
    with cs.ConexaoTR1000(nome_captura=f"c3-{nome}") as c:
        print(f"aperto de mao: versao {c.aperto()!r}")
        antes = [c.ler(*e)[0] for e in enderecos]
        print(f"antes:  {_hex(antes)}")
        if not _confirmar(c, enderecos, valores):
            print("nada mandado.")
            return 1
        for e, v in zip(enderecos, valores):
            c.escrever(*e, v)
            print(f"   ok (03) {cs.ESCRITAS_PERMITIDAS[e]}")
        depois = [c.ler(*e)[0] for e in enderecos]
        print(f"depois: {_hex(depois)}  (esperado {_hex(valores)})")
    print(f"\ncaptura: {c.captura}")
    print("Agora o que importa: o que voce OUVIU e VIU (REFERENCIA 3.2, regra 9).")
    return 0 if depois == list(valores) else 1


def main(a):
    try:
        if a[:1] == ["ler"]:
            cmd_ler(); return 0
        if a[:1] == ["step2"] and a[1:2] in (["desligar"], ["ligar"]):
            v = PAUSA if a[1] == "desligar" else NOTA_DO_PAINEL
            return _escrever(f"step2-{a[1]}", STEP2, [v, v])
        if a[:1] == ["tune"] and len(a) == 2 and a[1].isdigit() and 0 <= int(a[1]) <= 1000:
            return _escrever(f"tune-{a[1]}", [TUNE], [int(a[1])])
    except cs.ErroConexao as e:
        print(f"(!) {e}")
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

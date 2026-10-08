#!/usr/bin/env python3
"""
espiao.py - roda uma COPIA do TR-1000 App gravando a conversa serial com a maquina

    python3 espiao.py preparar          # copia, re-assina a copia, compila o espiao
    python3 espiao.py rodar <nome>      # abre a copia; ao fechar, grava
                                        # capturas/AAAA-MM-DD-<nome>.serlog
    python3 espiao.py limpar            # apaga a copia

POR QUE (REFERENCIA 2.1b): o App fala com a TR-1000 por uma serial USB, nao por
MIDI, e o MIDI Monitor nao ve nada. O espiao (espiao/espiao_serial.c) entra no
processo por DYLD_INSERT_LIBRARIES e grava cada byte da serial. O App original
tem hardened runtime, que faz o dyld ignorar essa variavel - por isso a copia,
re-assinada ad hoc SEM hardened runtime.

O ORIGINAL EM /Applications NUNCA E TOCADO. Todo caminho de escrita mora em
~/Library/Caches/tr1000-grid (o TesteEspiaoPreparo confere a lista de
comandos), e o `preparar` termina conferindo que a assinatura do original
continua valida.

Regras das sessoes (ROTEIRO-C0-C3.md, C1): o App original FECHADO enquanto a
copia roda - dois Apps na mesma serial cruzariam as respostas, como o
TR-EDITOR e o grid na CTRL da TR-8S. E nada de WRITE, OVERWRITE, Write Inst,
Transfer Backup "To TR-1000", Transfer Project nem Import Sample.
"""
import datetime, os, plistlib, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGINAL = "/Applications/Roland/TR-1000 App.app"
EXECUTAVEL = "Contents/MacOS/TR-1000 App"
NOME_PROCESSO = "TR-1000 App"            # o da copia e o mesmo: pgrep pega os dois
CACHE = os.path.expanduser("~/Library/Caches/tr1000-grid")
COPIA = os.path.join(CACHE, "TR-1000 App (espiao).app")
FONTE_C = os.path.join(AQUI, "espiao", "espiao_serial.c")
DYLIB = os.path.join(AQUI, "espiao", "libespiao_serial.dylib")


def versao(app):
    try:
        with open(os.path.join(app, "Contents/Info.plist"), "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString")
    except Exception:
        return None


def comandos_preparar():
    """A lista de comandos do `preparar`, separada para o teste poder conferir
    que nenhum deles escreve fora de CACHE (ou de espiao/, onde fica o .dylib)."""
    return [
        ["ditto", ORIGINAL, COPIA],
        # o .appex (plugin de audio) nao interessa e teria que ser re-assinado
        ["rm", "-rf", os.path.join(COPIA, "Contents", "PlugIns")],
        ["xattr", "-cr", COPIA],
        # --force sem --preserve-metadata: a assinatura nova NAO herda as
        # flags da antiga, entao o hardened runtime cai junto
        ["codesign", "--force", "--deep", "--sign", "-", COPIA],
        ["clang", "-dynamiclib", "-arch", "arm64", "-arch", "x86_64", "-O2",
         "-Wall", "-o", DYLIB, FONTE_C],
    ]


def _rodar_cmd(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"(!) falhou: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r


def _flags_assinatura(app):
    r = subprocess.run(["codesign", "-dv", "--verbose=2", app],
                       capture_output=True, text=True)
    linha = [l for l in r.stderr.splitlines() if "flags=" in l]
    return linha[0].strip() if linha else "?"


def cmd_preparar():
    if not os.path.isdir(ORIGINAL):
        raise SystemExit(f"(!) nao achei {ORIGINAL}")
    v_orig = versao(ORIGINAL)
    if os.path.isdir(COPIA):
        v_copia = versao(COPIA)
        if v_copia != v_orig:
            raise SystemExit(f"(!) a copia e da versao {v_copia}, o original e {v_orig}. "
                             "Rode `python3 espiao.py limpar` e prepare de novo.")
        print(f"copia ja existe ({v_copia}); so recompilando o espiao")
        _rodar_cmd(comandos_preparar()[-1])
    else:
        os.makedirs(CACHE, exist_ok=True)
        for cmd in comandos_preparar():
            print("  $ " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
            _rodar_cmd(cmd)

    flags = _flags_assinatura(COPIA)
    print(f"\ncopia:    {COPIA}\n          {flags}")
    if "runtime" in flags:
        raise SystemExit("(!) a copia AINDA tem hardened runtime - o espiao nao "
                         "vai carregar. Nao rode.")
    r = subprocess.run(["codesign", "--verify", "--deep", ORIGINAL],
                       capture_output=True, text=True)
    print(f"original: assinatura {'VALIDA (intocado)' if r.returncode == 0 else 'COM PROBLEMA: ' + r.stderr.strip()}")
    print(f"espiao:   {DYLIB}")
    print("\nPronto. Feche o App original e rode: python3 espiao.py rodar <nome>")


def _app_aberto():
    r = subprocess.run(["pgrep", "-x", NOME_PROCESSO], capture_output=True, text=True)
    return r.stdout.split()


def caminho_captura(nome, hoje=None):
    hoje = hoje or datetime.date.today()
    return os.path.join(AQUI, "capturas", f"{hoje:%Y-%m-%d}-{nome}.serlog")


def cmd_rodar(nome):
    if not os.path.isdir(COPIA) or not os.path.exists(DYLIB):
        raise SystemExit("(!) rode `python3 espiao.py preparar` antes")
    if versao(COPIA) != versao(ORIGINAL):
        raise SystemExit("(!) o App foi atualizado desde o preparar: limpar + preparar")
    abertos = _app_aberto()
    if abertos:
        raise SystemExit(f"(!) o TR-1000 App esta aberto (pid {', '.join(abertos)}). "
                         "Feche com Cmd+Q: dois Apps na mesma serial cruzam as "
                         "respostas.")
    destino = caminho_captura(nome)
    if os.path.exists(destino):
        raise SystemExit(f"(!) {destino} ja existe - escolha outro nome")

    env = dict(os.environ, DYLD_INSERT_LIBRARIES=DYLIB, ESPIAO_SAIDA=destino)
    print(f"abrindo a copia do App, gravando em {os.path.relpath(destino, AQUI)}")
    print("Faca o gesto da sessao e FECHE o App (Cmd+Q) para terminar.\n")
    # o executavel direto, nao `open`: o `open` nao repassa o ambiente
    subprocess.run([os.path.join(COPIA, EXECUTAVEL)], env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    import tr1000_serial
    if not os.path.exists(destino):
        print("(!) nenhum arquivo gravado: o espiao NAO carregou (o dyld ignorou "
              "o DYLD_INSERT_LIBRARIES). A captura nao prova nada.")
        return 1
    regs = tr1000_serial.ler_serlog(destino)
    carregou, abriu = tr1000_serial.autoteste(regs)
    tam = os.path.getsize(destino)
    print(f"\n{os.path.relpath(destino, AQUI)}: {tam} bytes, {len(regs)} registros")
    print(f"autoteste: espiao carregou = {'sim' if carregou else 'NAO'}, "
          f"abriu a serial = {'sim' if abriu else 'NAO'}")
    if not abriu:
        print("(!) o App nao abriu /dev/*usbmodem* enquanto gravava. A TR-1000 "
              "estava ligada e na USB? O App mostrou 'Connected'?")
        return 1
    print(f"\nProximo: python3 tr1000_serial.py estatisticas {os.path.relpath(destino, AQUI)}")
    return 0


def cmd_limpar():
    if not os.path.isdir(COPIA):
        print("nao ha copia"); return
    if not os.path.realpath(COPIA).startswith(os.path.realpath(CACHE) + os.sep):
        raise SystemExit("(!) caminho da copia fora do cache - recusando")
    _rodar_cmd(["rm", "-rf", COPIA])
    print(f"copia removida: {COPIA}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("preparar", "rodar", "limpar"):
        print(__doc__); sys.exit(1)
    if a[0] == "preparar":
        cmd_preparar()
    elif a[0] == "rodar":
        if len(a) < 2:
            print("uso: python3 espiao.py rodar <nome>"); sys.exit(1)
        sys.exit(cmd_rodar(a[1]))
    else:
        cmd_limpar()

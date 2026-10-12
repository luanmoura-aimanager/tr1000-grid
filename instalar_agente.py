#!/usr/bin/env python3
"""
instalar_agente.py - deixa o servidor do TR-1000 Controller sempre no ar, para
o app do Dock abrir sozinho. Port do instalar_agente.py do tr8s-grid.

    python3 instalar_agente.py            instala (ou atualiza) e liga
    python3 instalar_agente.py --so-web   so copia web/ (Cmd+R na pagina basta)
    python3 instalar_agente.py --remover  desliga e desinstala
    python3 instalar_agente.py --estado   diz se esta rodando
    python3 instalar_agente.py --se-mudou ORIG HEAD
                                          o hook post-merge: atualiza a copia so
                                          se o merge mexeu no que ela leva

POR QUE E SEGURO DEIXAR NO AR: o servidor NAO abre porta nenhuma sozinho. O
Motor (serial, Launchpads, controladoras) so nasce quando alguem aperta ON na
tela. Desligado, e um servidor HTTP parado em 127.0.0.1 - e o TR-1000 App da
Roland abre normalmente.

POR QUE UMA COPIA: o projeto vive em ~/Documents, e o macOS (TCC) nao deixa
um LaunchAgent ler nada de la ("Operation not permitted", medido no tr8s).
Entao os scripts, a pagina, o mapa das controladoras e as CAPTURAS DE
REFERENCIA do portao de leitura (sem elas nenhuma leitura e permitida) vao
para ~/Library/Application Support/tr1000-grid/. Depois de editar o codigo,
rodar este script de novo - o hook post-merge (.githooks) faz isso sozinho
quando a main recebe um merge ou um pull, se o agente estiver instalado.
"""
import os
import shutil
import subprocess
import sys
import time

ROTULO = "com.luanmoura.tr1000-grid"
AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.expanduser("~/Library/Application Support/tr1000-grid")
PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{ROTULO}.plist")
LOG = os.path.expanduser("~/Library/Logs/tr1000-grid-agente.log")
PYTHONPATH = os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages")

# tudo que o servidor.py importa do projeto (conferido no TesteEmbalagem)
ARQUIVOS = ("servidor.py", "campos.py", "conexao_serial.py", "controladoras.py",
            "espiao.py", "launchpad.py", "motor.py", "parametros.py", "portas.py",
            "roland.py", "tr1000.py", "tr1000_serial.py")


def copiar_projeto(destino, so_web=False):
    """Copia o que o servidor precisa para `destino`. -> o servidor.py la."""
    import conexao_serial as cs
    os.makedirs(destino, exist_ok=True)
    if not so_web:
        for nome in ARQUIVOS:
            shutil.copy2(os.path.join(AQUI, nome), os.path.join(destino, nome))
        os.makedirs(os.path.join(destino, "mapas"), exist_ok=True)
        mapa = os.path.join(AQUI, "mapas", "controladoras.json")
        if os.path.exists(mapa):
            shutil.copy2(mapa, os.path.join(destino, "mapas", "controladoras.json"))
        os.makedirs(os.path.join(destino, "capturas"), exist_ok=True)
        for cap in cs.CAPTURAS_DE_REFERENCIA:
            shutil.copy2(cap, os.path.join(destino, "capturas", os.path.basename(cap)))
    web = os.path.join(destino, "web")
    shutil.rmtree(web, ignore_errors=True)
    shutil.copytree(os.path.join(AQUI, "web"), web)
    return os.path.join(destino, "servidor.py")


def o_que_atualizar(mudados):
    """Os caminhos que um merge mudou -> "tudo" (algum .py da copia, o mapa,
    uma captura de referencia: o agente reinicia), "web" (so a pagina: Cmd+R
    basta, o motor continua ligado) ou None (nada que a copia leve)."""
    import conexao_serial as cs
    copia = set(ARQUIVOS) | {"mapas/controladoras.json"} | {
        os.path.relpath(c, AQUI) for c in cs.CAPTURAS_DE_REFERENCIA}
    mudados = [m.strip() for m in mudados if m.strip()]
    if any(m in copia for m in mudados):
        return "tudo"
    if any(m.startswith("web/") for m in mudados):
        return "web"
    return None


def depois_do_merge(orig, head):
    """O post-merge: so com o agente instalado, e so o que precisa."""
    if not os.path.exists(PLIST):
        return 0
    r = subprocess.run(["git", "-C", AQUI, "diff", "--name-only", orig, head],
                       capture_output=True, text=True)
    if r.returncode:
        return 0                                 # sem ORIG_HEAD (primeiro pull): nada
    oque = o_que_atualizar(r.stdout.splitlines())
    if oque is None:
        return 0
    print(f"[post-merge] atualizando o TR-1000 Controller instalado ({oque})")
    if oque == "tudo":
        print("[post-merge] o agente reinicia: se o Controller estava em ON, aperte ON "
              "de novo e recarregue a pagina (Cmd+R)")
    return instalar(reiniciar=oque == "tudo")


def _comando_python():
    """O rtmidi instalado e arm64: sob Rosetta ele nao carrega (pitfall do
    tr8s-grid). Numa maquina Apple Silicon, forca o arch nativo."""
    r = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.optional.arm64"],
                       capture_output=True, text=True)
    if r.stdout.strip() == "1":
        return ["/usr/bin/arch", "-arm64", "/usr/bin/python3"]
    return ["/usr/bin/python3"]


MODELO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{rotulo}</string>
  <key>ProgramArguments</key>
  <array>
{argumentos}
  </array>
  <key>WorkingDirectory</key><string>{aqui}</string>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHONPATH</key><string>{pypath}</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
  <key>ProcessType</key><string>Interactive</string>
</dict>
</plist>
"""


def instalar(reiniciar=True):
    alvo = copiar_projeto(DESTINO, so_web=not reiniciar)
    print(f"copiado para {DESTINO}")
    if not reiniciar:
        print("agente NAO reiniciado (--so-web): recarregue a pagina (Cmd+R).")
        return 0
    args = _comando_python() + [alvo, "--sem-abrir"]
    os.makedirs(os.path.dirname(PLIST), exist_ok=True)
    with open(PLIST, "w") as f:
        f.write(MODELO.format(rotulo=ROTULO, aqui=DESTINO, pypath=PYTHONPATH, log=LOG,
                              argumentos="\n".join(f"    <string>{a}</string>" for a in args)))
    uid = os.getuid()
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{ROTULO}"], capture_output=True)
    # o bootout volta ANTES de o processo antigo morrer: bootstrap com retry
    # (o tr8s ficou desinstalado por isso em 16/08/2026)
    r = None
    for tentativa in range(5):
        time.sleep(1.0 if tentativa else 0.5)
        r = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", PLIST],
                           capture_output=True, text=True)
        if r.returncode == 0:
            break
    if r is None or r.returncode:
        print(f"(!) launchctl bootstrap falhou: {r.stderr.strip()}")
        return 1
    print(f"agente instalado: {PLIST}")
    print(f"log: {LOG}")
    print("o servidor sobe agora e a cada login, em http://127.0.0.1:8734/")
    print("No Safari: abra esse endereco e use Arquivo > Adicionar ao Dock.")
    print("Desligado (OFF) = a serial livre para o TR-1000 App da Roland.")
    return 0


def remover():
    subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{ROTULO}"], capture_output=True)
    try:
        os.remove(PLIST)
    except OSError:
        pass
    print("agente removido.")
    return 0


def estado():
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{ROTULO}"],
                       capture_output=True, text=True)
    if r.returncode:
        print("agente NAO instalado")
        return 1
    for linha in r.stdout.splitlines():
        if any(k in linha for k in ("state =", "pid =", "last exit")):
            print("  " + linha.strip())
    return 0


if __name__ == "__main__":
    if "--remover" in sys.argv:
        sys.exit(remover())
    if "--estado" in sys.argv:
        sys.exit(estado())
    if "--se-mudou" in sys.argv:
        i = sys.argv.index("--se-mudou")
        sys.exit(depois_do_merge(*sys.argv[i + 1:i + 3]))
    sys.exit(instalar(reiniciar="--so-web" not in sys.argv))

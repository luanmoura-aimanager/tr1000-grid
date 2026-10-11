#!/usr/bin/env python3
"""
criar_app.py - monta o "TR-1000 Controller.app" (Desktop por padrao).

    python3 criar_app.py            # cria/atualiza em ~/Desktop
    python3 criar_app.py --em /pasta

Port do criar_app.py do tr8s-grid. O bundle carrega uma COPIA do projeto (o
TCC do macOS nao deixa um .app nao assinado ler ~/Documents - ele leva
"Operation not permitted" calado). Duplo clique: se o servidor ja esta no ar
(o LaunchAgent), so abre a pagina; senao sobe o servidor da copia e abre.

Depois de editar o codigo, rodar isto de novo.
"""
import os, shutil, subprocess, sys, tempfile

import icone
import instalar_agente

NOME = "TR-1000 Controller"
IDENT = "com.luanmoura.tr1000-controller"
MARCA = "Contents/.tr1000-grid-app"   # so sobrescrevemos bundles com esta marca

PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>                <string>{nome}</string>
  <key>CFBundleDisplayName</key>         <string>{nome}</string>
  <key>CFBundleIdentifier</key>          <string>{ident}</string>
  <key>CFBundleExecutable</key>          <string>tr1000-controller</string>
  <key>CFBundleIconFile</key>            <string>icone</string>
  <key>CFBundlePackageType</key>         <string>APPL</string>
  <key>CFBundleVersion</key>             <string>1.0</string>
  <key>CFBundleShortVersionString</key>  <string>1.0</string>
  <key>NSHighResolutionCapable</key>     <true/>
  <key>LSRequiresNativeExecution</key>   <true/>
</dict>
</plist>
"""

# O Finder lanca app de script como x86_64, e o rtmidi arm64 nao carrega sob
# Rosetta ("have arm64, need x86_64") - forca o arch nativo (pitfall do tr8s).
LANCADOR = """#!/bin/sh
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
LOG="$HOME/Library/Logs/TR1000-Controller-app.log"
export PYTHONPATH="$HOME/Library/Python/3.9/lib/python/site-packages"
if [ "$(/usr/sbin/sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ]; then
    exec /usr/bin/arch -arm64 /usr/bin/python3 "$DIR/servidor.py" >>"$LOG" 2>&1
fi
exec /usr/bin/python3 "$DIR/servidor.py" >>"$LOG" 2>&1
"""


def criar(pasta):
    destino = os.path.join(pasta, NOME + ".app")
    if os.path.exists(destino) and not os.path.exists(os.path.join(destino, MARCA)):
        print(f"(!) Ja existe um {destino} que nao foi criado por este script. Nao mexo nele.")
        return 1
    # monta e assina num tmp: o Desktop e do iCloud, que re-carimba xattrs no
    # meio da assinatura (pitfall do tr8s)
    tmp = tempfile.mkdtemp(prefix="tr1000-app-")
    app = os.path.join(tmp, NOME + ".app")
    macos = os.path.join(app, "Contents", "MacOS")
    recursos = os.path.join(app, "Contents", "Resources")
    os.makedirs(macos)
    with open(os.path.join(app, "Contents", "Info.plist"), "w") as f:
        f.write(PLIST.format(nome=NOME, ident=IDENT))
    exe = os.path.join(macos, "tr1000-controller")
    with open(exe, "w") as f:
        f.write(LANCADOR)
    os.chmod(exe, 0o755)
    instalar_agente.copiar_projeto(recursos)
    open(os.path.join(app, MARCA), "w").close()
    try:
        icone.montar_icns(os.path.join(recursos, "icone.icns"))
        ic = "com icone"
    except Exception as e:
        ic = f"sem icone ({e})"
    subprocess.run(["xattr", "-cr", app], check=False)
    r = subprocess.run(["codesign", "--force", "--deep", "--sign", "-", app],
                       capture_output=True, text=True)
    assinado = "assinado" if r.returncode == 0 else f"sem assinatura ({r.stderr.strip()[:60]})"
    if os.path.exists(destino):
        shutil.rmtree(destino)
    shutil.move(app, destino)
    shutil.rmtree(tmp, ignore_errors=True)
    subprocess.run(["touch", destino], check=False)
    print(f"Criado: {destino}  ({ic} · {assinado})")
    print("Duplo clique abre a pagina (e sobe o servidor, se o agente nao estiver no ar).")
    print("Log: ~/Library/Logs/TR1000-Controller-app.log")
    return 0


if __name__ == "__main__":
    pasta = os.path.expanduser("~/Desktop")
    if "--em" in sys.argv:
        pasta = os.path.abspath(sys.argv[sys.argv.index("--em") + 1])
    sys.exit(criar(pasta))

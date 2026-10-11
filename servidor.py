#!/usr/bin/env python3
"""
servidor.py - o TR-1000 Controller: a tela do grid como pagina web local.

    python3 servidor.py            sobe e abre o navegador
    python3 servidor.py --sem-abrir

Port do servidor.py do tr8s-grid (o TR-8S Controller), com a mesma armadura:
so em 127.0.0.1, cookie HttpOnly + SameSite=Strict, POST so com o header
proprio + Host + Origin, CSP fechada, lista FECHADA de acoes. Zero
dependencia nova: http.server da stdlib.

UM PROCESSO SO E DONO DA SERIAL (decisao do Luan, 10/10/2026): o ON liga a
TR-1000, os Launchpads (layout A) e as controladoras, num Motor so; o OFF
solta tudo - e so com OFF o TR-1000 App da Roland, o espiao e as sessoes C5
conseguem abrir a serial. O ON recusa com o App aberto (conexao_serial).

Toda escrita sai pelo portao de sempre (conexao_serial.conferir_pacote).
"""
import http.server
import json
import mimetypes
import os
import posixpath
import secrets
import socket
import sys
import threading
import time
import urllib.parse
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import campos
import launchpad
import motor as M
import parametros as P
import tr1000_serial as ts

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(AQUI, "web")
APP = "tr1000-controller"
PORTA = 8734                     # a 8733 e do TR-8S Controller, que pode coexistir
LOG_PATH = os.path.expanduser("~/Library/Logs/TR1000-Controller.log")
ARQ_SERVIDOR = os.path.expanduser("~/.lp_tr1000_servidor.json")

mimetypes.add_type("text/javascript", ".mjs")           # o 3.9 nao conhece
mimetypes.add_type("application/manifest+json", ".webmanifest")

TOKEN = secrets.token_urlsafe(24)
# manifest-src: sem ele o "Adicionar ao Dock" do Safari recusa o manifest calado
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
       "img-src 'self' data:; connect-src 'self'; manifest-src 'self'; "
       "base-uri 'none'; form-action 'none'")
LIMITE_CORPO = 64 * 1024


class Log:
    """Arquivo + as ultimas linhas para o rodape da pagina."""

    def __init__(self, caminho=LOG_PATH, memoria=60):
        self.memoria, self.linhas, self.lock = memoria, [], threading.Lock()
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            if os.path.exists(caminho) and os.path.getsize(caminho) > 1_000_000:
                os.replace(caminho, caminho + ".old")
            self.f = open(caminho, "a", encoding="utf-8")
        except OSError:
            self.f = None

    def __call__(self, texto):
        linha = f"{time.strftime('%H:%M:%S')} {texto}"
        with self.lock:
            self.linhas = (self.linhas + [linha])[-self.memoria:]
            if self.f:
                self.f.write(linha + "\n"); self.f.flush()
        print(linha, flush=True)

    def ultimas(self, n=20):
        with self.lock:
            return list(self.linhas[-n:])


class Host:
    """Dono do Motor: sobe a thread, atende as acoes, devolve o estado."""

    def __init__(self):
        self.log = Log()
        self.motor = None
        self.thread = None
        self.rodando = False
        self.ultimo = {}

    def ligar(self):
        if self.motor is None:
            cfg, msgs = launchpad.carregar_layout_resolvido()
            for m in msgs:
                self.log(("(sem Launchpads) " if cfg is None else "") + m)
            if cfg is not None:
                launchpad.programmer_mode(True)
            try:
                self.motor = M.Motor(cfg, log=self.log)
            except Exception as e:
                self.log(f"(!) nao consegui abrir os Launchpads: {e} - seguindo so com a tela")
                self.motor = M.Motor(None, log=self.log)
            self.rodando = True
            self.thread = threading.Thread(target=self._laco, daemon=True)
            self.thread.start()
        self.motor.enfileirar(self._ligar_motor)

    def _ligar_motor(self):
        if not self.motor.definir_modo(M.MODO_ON):
            self.log("(!) a TR-1000 nao ligou - veja a linha acima (App da Roland aberto?)")

    def _laco(self):
        while self.rodando:
            try:
                self.motor.tick()
            except Exception as e:
                self.log(f"(!) erro no motor: {e}")
                time.sleep(0.5)
            time.sleep(0.003)

    def desligar(self):
        """Solta TUDO: serial, Launchpads, controladoras. So assim o App da
        Roland consegue abrir a serial."""
        if self.motor is None:
            return
        self.rodando = False
        if self.thread:
            self.thread.join(timeout=2.0)
        try:
            self.motor.fechar()
        except Exception:
            pass
        self.motor, self.thread, self.ultimo = None, None, {}
        self.log("desligado: a serial esta livre para o TR-1000 App")

    def enfileirar(self, fn, *args):
        self.motor.enfileirar(fn, *args)

    def estado(self):
        e, fresco = {}, True
        if self.motor:
            novo = self.motor.estado()
            fresco = novo is not None
            e = novo if fresco else dict(self.ultimo)
            self.ultimo = e
        e = dict(e)
        e["servidor_ligado"] = self.motor is not None
        e.setdefault("ligado", False)
        e["fresco"] = fresco
        e["log"] = self.log.ultimas()
        return e


HOST = Host()


# ─────────────────────────────────────────────────────────────
# As acoes: tudo que a pagina pode pedir. Lista FECHADA de proposito - a
# pagina nao chama metodo arbitrario do Motor.
# ─────────────────────────────────────────────────────────────
EXEC_OK = {"variacao", "velocidade", "banco", "layer"}


def _exec(a):
    if a.get("tipo") not in EXEC_OK:
        raise ValueError(f"exec '{a.get('tipo')}' nao permitido")
    HOST.enfileirar(HOST.motor.executar, a["tipo"], a["arg"])


def _int_ou_none(v):
    return None if v is None else int(v)


ACOES = {
    "exec": _exec,
    "step": lambda a: HOST.enfileirar(HOST.motor.alternar_step, int(a["track"]), int(a["step"])),
    "campo_step": lambda a: HOST.enfileirar(HOST.motor.definir_campo_step, int(a["track"]),
                                            int(a["step"]), str(a["nome"]), int(a["valor"])),
    "alt": lambda a: HOST.enfileirar(HOST.motor.definir_alt, int(a["track"]), int(a["step"]),
                                     bool(a["ligado"])),
    "mudo": lambda a: HOST.enfileirar(HOST.motor.alternar_mudo, int(a["track"])),
    "variacoes": lambda a: HOST.enfileirar(HOST.motor.definir_variacoes, int(a["mascara"])),
    "scale": lambda a: HOST.enfileirar(HOST.motor.definir_scale, int(a["n"])),
    "fill": lambda a: HOST.enfileirar(HOST.motor.definir_fill, int(a["n"])),
    "extremos_var": lambda a: HOST.enfileirar(HOST.motor.definir_extremos_var, int(a["v"]),
                                              int(a["first"]), int(a["last"])),
    "extremos_track": lambda a: HOST.enfileirar(HOST.motor.definir_extremos_track, int(a["track"]),
                                                _int_ou_none(a.get("first")),
                                                _int_ou_none(a.get("last"))),
    "loop": lambda a: HOST.enfileirar(HOST.motor.definir_loop, bool(a["ligado"]),
                                      _int_ou_none(a.get("step"))),
    "param": lambda a: HOST.enfileirar(HOST.motor.definir_param, str(a["id"]), int(a["valor"])),
    "quer_kit": lambda a: setattr(HOST.motor, "quer_kit", bool(a["sim"])),
    "reler": lambda a: HOST.enfileirar(HOST.motor.reler, True),
}


def dados_estaticos():
    """O que a pagina precisa uma vez so: os catalogos."""
    # por id: a faixa e o nome em cada type ("-" = nao depende de type). Com
    # condicao (o STEP com SYNC), as alternativas tem a mesma faixa
    params = {}
    for p in P.todas_as_entradas():
        d = params.setdefault(p.id, {"por_tipo": {}})
        d["por_tipo"][str(p.tipo[1]) if p.tipo else "-"] = {
            "min": p.minimo, "max": p.maximo, "escala": p.escala}
    return {
        "app": APP,
        "tracks": ts.TRACKS_SERIAL, "variacoes": ts.VARIACOES_SERIAL,
        "velocidades": M.VELOCIDADES, "bancos": {k: v for k, v in M.BANCOS.items()},
        "sub_nomes": campos.SUB_NOMES, "cycle_nomes": campos.CYCLE_NOMES,
        "scales": campos.SCALES, "params": params,
        "nomes": P.NOMES, "mfx_tipos": P.MFX_TIPOS, "delay_tipos": P.DELAY_TIPOS,
        "lfo_syncs": P.LFO_SYNCS, "rotas": P.ROTAS, "sc_fontes": P.SC_FONTES,
        "seletores": {id: P.seletor_de(id) for id in P.POR_TIPO},
        "build": time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(os.path.abspath(__file__)))),
    }


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = APP
    sys_version = ""

    def log_message(self, *a):
        pass

    # ── seguranca (a mesma do tr8s-grid) ───────────────────
    def _host_ok(self):
        """Fecha DNS rebinding: o Host tem que ser o nosso."""
        h = (self.headers.get("Host") or "").lower()
        return h in (f"127.0.0.1:{self.server.server_port}",
                     f"localhost:{self.server.server_port}")

    def _origem_ok(self):
        o = self.headers.get("Origin")
        return o is None or o.lower() in (f"http://127.0.0.1:{self.server.server_port}",
                                          f"http://localhost:{self.server.server_port}")

    def _tem_cookie(self):
        for parte in (self.headers.get("Cookie") or "").split(";"):
            nome, _, valor = parte.strip().partition("=")
            if nome == "tr1000" and secrets.compare_digest(valor, TOKEN):
                return True
        return False

    def _autorizado_post(self):
        if not self._host_ok():
            return False, "host nao autorizado"
        if not self._origem_ok():
            return False, "origem nao autorizada"
        if not secrets.compare_digest(self.headers.get("X-TR1000-Token") or "", TOKEN):
            return False, ("sessao vencida - o servidor reiniciou desde que esta "
                           "pagina abriu. Recarregue (Cmd+R)")
        return True, ""

    def _responder(self, corpo, tipo="application/json; charset=utf-8", codigo=200, extra=None):
        if isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, msg, codigo=400):
        self._responder(json.dumps({"erro": msg}), codigo=codigo)

    # ── GET ─────────────────────────────────────────────────
    def _servir_pagina(self):
        """A pagina, e a sessao para quem abriu esta URL (o app do Dock guarda
        uma URL fixa; o token muda a cada boot). Seguro pelos mesmos motivos
        do tr8s-grid: so 127.0.0.1, HttpOnly, SameSite=Strict, Host conferido."""
        extra = {"Content-Security-Policy": CSP}
        if self._host_ok():
            extra["Set-Cookie"] = f"tr1000={TOKEN}; Path=/; SameSite=Strict; HttpOnly; Max-Age=86400"
        try:
            with open(os.path.join(WEB, "index.html"), "rb") as f:
                return self._responder(f.read(), "text/html; charset=utf-8", extra=extra)
        except OSError:
            return self._responder("pagina nao encontrada", "text/plain", 500)

    def _servir_estatico(self, rota):
        rel = posixpath.normpath(urllib.parse.unquote(rota[len("/web/"):]))
        if rel.startswith(("..", "/")):
            return self._erro("caminho invalido", 403)
        alvo = os.path.realpath(os.path.join(WEB, rel))
        if os.path.commonpath([alvo, os.path.realpath(WEB)]) != os.path.realpath(WEB):
            return self._erro("fora do diretorio web", 403)
        if os.path.splitext(alvo)[1] not in (".css", ".mjs", ".js", ".svg", ".png",
                                             ".html", ".webmanifest"):
            return self._erro("extensao nao servida", 403)
        try:
            with open(alvo, "rb") as f:
                dados = f.read()
        except OSError:
            return self._erro("nao encontrado", 404)
        tipo = mimetypes.guess_type(alvo)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo.endswith("javascript"):
            tipo += "; charset=utf-8"
        return self._responder(dados, tipo)

    def do_GET(self):
        if not self._host_ok():
            return self._erro("host nao autorizado", 403)
        rota = urllib.parse.urlparse(self.path).path
        if rota in ("/", "/index.html"):
            return self._servir_pagina()
        if rota == "/ping":
            return self._responder(json.dumps({"app": APP, "pid": os.getpid()}))
        if rota.startswith("/web/"):
            return self._servir_estatico(rota)
        if rota == "/token":
            if not self._tem_cookie():
                return self._erro("sem cookie de sessao", 403)
            return self._responder(json.dumps({"token": TOKEN}))
        if rota == "/estado":
            return self._responder(json.dumps(HOST.estado(), default=str))
        if rota == "/dados":
            return self._responder(json.dumps(dados_estaticos(), default=str))
        return self._erro("nao encontrado", 404)

    def do_OPTIONS(self):
        self._responder(b"", "text/plain", 204)     # sem Allow-*: o preflight morre aqui

    # ── POST ────────────────────────────────────────────────
    def do_POST(self):
        ok, motivo = self._autorizado_post()
        if not ok:
            HOST.log(f"(!) POST recusado em {self.path}: {motivo}")
            return self._erro(motivo, 403)
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return self._erro("tamanho invalido")
        if n > LIMITE_CORPO:
            return self._erro("corpo grande demais", 413)
        try:
            corpo = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._erro("json invalido")
        if not isinstance(corpo, dict):
            return self._erro("json invalido")
        if self.path == "/ligar":
            HOST.ligar() if corpo.get("ligar") else HOST.desligar()
            return self._responder(json.dumps({"ok": True}))
        if self.path != "/acao":
            return self._erro("nao encontrado", 404)
        nome = corpo.get("acao")
        fn = ACOES.get(nome)
        if not fn:
            return self._erro(f"acao desconhecida: {nome}")
        if not HOST.motor:
            return self._erro("desligado - aperte ON", 409)
        try:
            fn(corpo)
        except Exception as e:
            HOST.log(f"(!) acao '{nome}' falhou: {e}")
            return self._erro(f"{nome}: {e}", 500)
        return self._responder(json.dumps({"ok": True}))


def _instancia_viva():
    """Ja existe um Controller rodando? Confirma pelo /ping, nao supoe."""
    try:
        with open(ARQ_SERVIDOR) as f:
            info = json.load(f)
        porta = int(info["porta"])
    except (OSError, ValueError, KeyError):
        return None
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/ping", timeout=1.0) as r:
            if json.loads(r.read()).get("app") != APP:
                return None
    except Exception:
        return None
    return f"http://127.0.0.1:{porta}/"


def _porta_livre(base=PORTA):
    for p in range(base, base + 12):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return None


def _anotar_instancia(porta):
    try:
        with open(ARQ_SERVIDOR, "w") as f:
            json.dump({"porta": porta, "pid": os.getpid()}, f)
        os.chmod(ARQ_SERVIDOR, 0o600)
    except OSError:
        pass


def main():
    ja = _instancia_viva()
    if ja:
        print("O TR-1000 Controller ja esta rodando - abrindo a pagina.")
        webbrowser.open(ja)
        return
    porta = _porta_livre()
    if porta is None:
        print(f"Nenhuma porta livre entre {PORTA} e {PORTA + 11}.")
        return
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    _anotar_instancia(porta)
    url = f"http://127.0.0.1:{porta}/"
    HOST.log(f"servidor no ar em {url}")
    if "--sem-abrir" not in sys.argv:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nsaindo...")
    finally:
        HOST.desligar()
        try:
            os.remove(ARQ_SERVIDOR)
        except OSError:
            pass


if __name__ == "__main__":
    main()

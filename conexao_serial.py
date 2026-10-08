#!/usr/bin/env python3
"""
conexao_serial.py - falar com a TR-1000 pela serial USB, como o TR-1000 App fala

Por que existe (REFERENCIA 2.1b/2.1c): a maquina nao edita parametros por
MIDI; o App usa uma porta serial CDC (/dev/cu.usbmodem*) com um protocolo de
pacotes proprio, decodificado das capturas do espiao. Este modulo repete o que
o App faz - a abertura da porta, o aperto de mao, a leitura 82 e a escrita 01 -
copiando os bytes das capturas, sem inventar campo nenhum.

ESCRITA E RESTRITA (portao da fase 0, REFERENCIA 3.1): so os enderecos de
ESCRITAS_PERMITIDAS, checados ANTES de qualquer byte sair. Ampliar essa lista e
uma decisao que passa pelo Luan, nao um detalhe de codigo.

Uso direto: ver sessao_c3.py. Aqui so a conexao.
"""
import datetime, fcntl, os, select, struct, subprocess, termios, time

AQUI = os.path.dirname(os.path.abspath(__file__))
import tr1000_serial as ts

NOME_USB = "Roland TR-1000"              # o no do ioreg (medido 08/10/2026)
NOME_PROCESSO_APP = "TR-1000 App"        # original e copia do espiao: o mesmo nome
TIOCEXCL = 0x2000740D                    # o 1o ioctl do App (espiao, 08/10/2026)
IOSSIOSPEED = 0x80085402                 # o ultimo, com 230400
BAUD = 230400
ESPERA = 1.0                             # s: a maquina respondeu em ~2-30 ms

# (bloco, x, y, indice) - REFERENCIA 2.1c
ESCRITAS_PERMITIDAS = {
    (118, 0, 0, 1253): "BD var A step 2, layer A",      # 1249 + 4*1 + 0
    (118, 0, 0, 1254): "BD var A step 2, layer B",      # 1249 + 4*1 + 1
    (156, 126, 0, 962): "TUNE do sample do BD (slot 126)",
}


class ErroConexao(Exception):
    pass


def porta_da_tr1000():
    """O /dev/cu.* que o ioreg pendura debaixo do 'Roland TR-1000'.
    Exatamente um, senao ErroConexao."""
    r = subprocess.run(["ioreg", "-r", "-n", NOME_USB, "-l", "-w0"],
                       capture_output=True, text=True)
    portas = [l.split("=", 1)[1].strip().strip('"') for l in r.stdout.splitlines()
              if '"IOCalloutDevice"' in l]
    if len(portas) != 1:
        raise ErroConexao(f"esperava UMA porta serial da TR-1000, achei {portas or 'nenhuma'}"
                          " - a maquina esta ligada e na USB?")
    return portas[0]


def app_aberto():
    r = subprocess.run(["pgrep", "-x", NOME_PROCESSO_APP], capture_output=True, text=True)
    return r.stdout.split()


class PortaSerial:
    """A porta de verdade, com a mesma sequencia de abertura do App."""

    def __init__(self, caminho):
        self.fd = os.open(caminho, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            fcntl.ioctl(self.fd, TIOCEXCL)            # ninguem mais abre enquanto isso
            a = termios.tcgetattr(self.fd)
            a[0] = termios.IGNBRK                     # iflag
            a[1] = 0                                  # oflag
            a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            a[3] = 0                                  # lflag
            a[4] = a[5] = termios.B230400
            a[6] = [0] * len(a[6])                    # c_cc todo zero, como o App
            termios.tcsetattr(self.fd, termios.TCSANOW, a)
            fcntl.ioctl(self.fd, IOSSIOSPEED, struct.pack("<Q", BAUD))
        except Exception:
            os.close(self.fd)
            raise

    def escrever(self, b):
        total = 0
        while total < len(b):
            try:
                total += os.write(self.fd, b[total:])
            except BlockingIOError:
                select.select([], [self.fd], [], 0.1)

    def ler(self, limite):
        r, _, _ = select.select([self.fd], [], [], limite)
        if not r:
            return b""
        try:
            return os.read(self.fd, 4096)
        except BlockingIOError:
            return b""

    def fechar(self):
        try:
            os.close(self.fd)
        except OSError:
            pass


class ConexaoTR1000:
    """Uso:
        with ConexaoTR1000(nome_captura="c3-ler") as c:
            versao = c.aperto()
            valor = c.ler(118, 0, 0, 1253)[0]

    `porta` existe para os testes (uma porta falsa); sem ela, abre a de verdade
    e RECUSA se o TR-1000 App estiver aberto - dois programas na mesma serial
    cruzariam as respostas."""

    def __init__(self, nome_captura=None, porta=None, relogio=time.time):
        self._porta_injetada = porta
        self.porta = None
        self.relogio = relogio
        self.buf = b""
        self.registros = []
        self.captura = None
        if nome_captura:
            self.captura = os.path.join(
                AQUI, "capturas", f"{datetime.date.today():%Y-%m-%d}-{nome_captura}.serlog")

    # ── abrir / fechar ──────────────────────────────────────
    def __enter__(self):
        if self._porta_injetada is not None:
            self.porta = self._porta_injetada
            caminho = "(porta de teste)"
        else:
            abertos = app_aberto()
            if abertos:
                raise ErroConexao(f"o TR-1000 App esta aberto (pid {', '.join(abertos)}): "
                                  "feche com Cmd+Q antes")
            caminho = porta_da_tr1000()
            self.porta = PortaSerial(caminho)
        self._registrar("O", caminho.encode())
        return self

    def __exit__(self, *e):
        if self.porta is not None:
            self._registrar("C", b"")
            self.porta.fechar()
        self._gravar_captura()

    # ── log no formato do espiao (.serlog) ──────────────────
    def _registrar(self, tipo, dados):
        self.registros.append((int(self.relogio() * 1e9), tipo, 0, bytes(dados)))

    def _gravar_captura(self):
        if not self.captura or not self.registros:
            return
        os.makedirs(os.path.dirname(self.captura), exist_ok=True)
        with open(self.captura, "wb") as f:
            f.write(ts.serializar([(int(time.time() * 1e9), "S", os.getpid(),
                                    b"conexao_serial.py")] + self.registros))

    # ── troca de pacotes ────────────────────────────────────
    def _mandar(self, pac):
        self._registrar("W", pac)
        self.porta.escrever(pac)

    def _esperar(self, aceita, espera=ESPERA):
        """Le ate um pacote para o qual aceita(pac) nao e None; devolve esse
        valor. Os outros pacotes que chegarem (o poll de resposta, por
        exemplo) ficam registrados e sao descartados."""
        limite = self.relogio() + espera
        while True:
            prontos, self.buf = ts.enquadrar(self.buf)
            for p in prontos:
                r = aceita(p)
                if r is not None:
                    return r
            falta = limite - self.relogio()
            if falta <= 0:
                return None
            chegou = self.porta.ler(min(falta, 0.05))
            if chegou:
                self._registrar("R", chegou)
                self.buf += chegou

    def aperto(self):
        """O aperto de mao do App. E o AUTOTESTE: sem a versao, nada roda."""
        self._mandar(ts.APERTO)
        v = self._esperar(ts.versao_95)
        if v is None:
            raise ErroConexao("a maquina nao respondeu ao aperto de mao em 1 s")
        return v

    def ler(self, bloco, x, y, indice, n=1):
        self._mandar(ts.pacote_dados(ts.CAB_LEITURA, ts.carga_ler(bloco, x, y, indice, n)))

        def casa(p):
            r = ts.resposta_02(p)
            return r[4] if r and r[:4] == (bloco, x, y, indice) else None
        v = self._esperar(casa)
        if v is None:
            raise ErroConexao(f"sem resposta a leitura de {(bloco, x, y, indice)}")
        return v

    def pacote_escrita(self, bloco, x, y, indice, valor):
        """Os bytes exatos que escrever() mandaria - para mostrar antes."""
        if (bloco, x, y, indice) not in ESCRITAS_PERMITIDAS:
            raise PermissionError(f"escrita fora da lista permitida: {(bloco, x, y, indice)}")
        if not 0 <= valor <= 0xFFFFFFFF:
            raise ValueError(valor)
        return ts.pacote_dados(ts.CAB_ESCRITA, ts.carga_escrever(bloco, x, y, indice, valor))

    def escrever(self, bloco, x, y, indice, valor):
        """Um 01, uma vez, e espera o 03. Nunca repete sozinho."""
        pac = self.pacote_escrita(bloco, x, y, indice, valor)   # a guarda vem primeiro
        self._mandar(pac)
        ok = self._esperar(lambda p: ts.ack_03(p) == (bloco, x, y, indice) or None)
        if ok is None:
            raise ErroConexao(f"a maquina nao confirmou (03) a escrita em "
                              f"{(bloco, x, y, indice)} - parando, sem repetir")
        return True

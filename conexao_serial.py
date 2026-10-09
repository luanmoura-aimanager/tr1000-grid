#!/usr/bin/env python3
"""
conexao_serial.py - falar com a TR-1000 pela serial USB, como o TR-1000 App fala

Por que existe (REFERENCIA 2.1b/2.1c): a maquina nao edita parametros por
MIDI; o App usa uma porta serial CDC (/dev/cu.usbmodem*) com um protocolo de
pacotes proprio, decodificado das capturas do espiao. Este modulo repete o que
o App faz - a abertura da porta, o aperto de mao, a leitura 82 e a escrita 01 -
copiando os bytes das capturas, sem inventar campo nenhum.

TODO PACOTE QUE SAI PASSA POR UM PONTO SO (_mandar), que recusa antes de
qualquer byte sair:
  - escrita (01) fora de ESCRITAS_PERMITIDAS - o portao da fase 0,
    REFERENCIA 3.1. Ampliar essa lista e decisao do Luan, nao de codigo;
  - leitura (82) fora das faixas que o PROPRIO App leu no boot
    (CAPTURAS_DE_REFERENCIA) - a armadilha 1 do CLAUDE.md: na TR-8S, leitura
    em endereco invalido derrubava a porta;
  - qualquer outro pacote que nao seja o aperto de mao.

Uso direto: ver sessao_c3.py. Aqui so a conexao.
"""
import fcntl, os, select, struct, subprocess, termios, time

AQUI = os.path.dirname(os.path.abspath(__file__))
import espiao
import tr1000_serial as ts

NOME_USB = "Roland TR-1000"              # o no do ioreg (medido 08/10/2026)
TIOCEXCL = 0x2000740D                    # o 1o ioctl do App (espiao, 08/10/2026)
IOSSIOSPEED = 0x80085402                 # o ultimo, com 230400
BAUD = 230400
ESPERA = 1.0                             # s: a maquina respondeu em ~2-30 ms

# A ESCRITA DO GRID (fase 1, decisao do Luan de 08/10/2026): so STEPS -
# os slots 0 e 1 (layer A e B) dos 16 steps dos 10 tracks, nas 12 variacoes,
# de qualquer pattern; valor so nota (A··3C, velocity 1..127) ou pausa (FF).
# Nada de cabecalho, kit, mixer, probability. Ver escrita_permitida.
N_VARIACOES, N_TRACKS, N_PATTERNS = 12, 10, 128


def escrita_permitida(bloco, x, y, indice, valor):
    """A regra da escrita do grid. Tudo que nao casa e recusado no portao."""
    if (bloco, x, y, indice) in ESCRITAS_PERMITIDAS:          # as 3 da C3
        return True
    blocos = {ts.bloco_de_steps(v) for v in range(N_VARIACOES)}
    if bloco not in blocos or not 0 <= x < N_PATTERNS or not 0 <= y < N_TRACKS:
        return False
    rel = indice - ts.INDICE_STEPS
    if not 0 <= rel < 64 or rel % 4 not in (0, 1):            # slots 0 e 1
        return False
    return valor == ts.SLOT_PAUSA or ts.eh_nota(valor)


# As 3 escritas da C3 (historicas; sessao_c3.py continua funcionando)
# (bloco, x, y, indice) - REFERENCIA 2.1c
ESCRITAS_PERMITIDAS = {
    (118, 0, 0, 1253): "BD var A step 2, layer A",      # 1249 + 4*1 + 0
    (118, 0, 0, 1254): "BD var A step 2, layer B",      # 1249 + 4*1 + 1
    (156, 126, 0, 962): "TUNE do sample do BD (slot 126)",
}

# As leituras que o App fez no boot, com o pattern 1-01 (C1-S0), o 1-02 e o
# 2-01 selecionados (os blocos de pattern vieram com x = 0, 1 e 16). Uma leitura
# nossa so sai se cair DENTRO de uma delas. Para liberar o pattern N, a regra
# e capturar o boot do App com ele selecionado - nao chutar o x.
CAPTURAS_DE_REFERENCIA = [os.path.join(AQUI, "capturas", n) for n in (
    "2026-10-08-s0-autoteste.serlog",
    "2026-10-08-boot-1-02.serlog",
    "2026-10-08-boot-2-01.serlog",          # x = 16: banco 2, pattern 1
)]
_leituras_do_app = None


class ErroConexao(Exception):
    pass


def leituras_do_app():
    """{(bloco, x, y): {(indice, n), ...}} - TODAS as faixas que o App pediu,
    somadas de todas as capturas de referencia (nenhuma apaga a outra).
    Carregado uma vez."""
    global _leituras_do_app
    if _leituras_do_app is None:
        todas = {}
        for cap in CAPTURAS_DE_REFERENCIA:
            if not os.path.exists(cap):
                raise ErroConexao(f"sem a captura de referencia {cap}: "
                                  "nenhuma leitura e permitida sem ela")
            for k, fs in ts.todas_as_leituras(ts.pacotes(ts.ler_serlog(cap))).items():
                todas.setdefault(k, set()).update(fs)
        _leituras_do_app = todas
    return _leituras_do_app


def faixa_do_bloco(bloco, x, y):
    """(indice, n) da maior faixa que o App leu nessa chave - o bloco inteiro.
    PermissionError se o App nunca leu a chave: o mesmo erro do portao."""
    fs = _faixas(bloco, x, y)
    if not fs:
        raise PermissionError(f"o App nunca leu {(bloco, x, y)} numa captura de referencia")
    return max(fs, key=lambda f: f[1])


# Os blocos de pattern (cabecalho e as 12 variacoes): o App os leu com x = 0,
# 1 e 16 (tres patterns de dois bancos), e o x e o indice global do pattern.
# Decisao do Luan (08/10/2026): a MESMA faixa vale para qualquer x de 0..127.
BLOCOS_DE_PATTERN = range(ts.BLOCO_CAB_PATTERN, ts.BLOCO_VAR0 + ts.BLOCOS_POR_VAR * 12)


def _faixas(bloco, x, y):
    fs = leituras_do_app().get((bloco, x, y))
    if not fs and bloco in BLOCOS_DE_PATTERN and 0 <= x < N_PATTERNS:
        fs = leituras_do_app().get((bloco, 0, y))      # a do pattern 1-01
    return fs or ()


def chave_lida(bloco, x, y):
    """A chave tem alguma faixa permitida (lida pelo App, ou pattern x 0..127)."""
    return bool(_faixas(bloco, x, y))


def leitura_permitida(bloco, x, y, indice, n):
    return any(i <= indice and indice + n <= i + m for i, m in _faixas(bloco, x, y))


def conferir_pacote(pac):
    """PermissionError se o pacote nao pode sair. O UNICO portao de saida."""
    if pac == ts.APERTO:
        return
    c = ts.carga(pac)
    if c[:1] == bytes([ts.ESCREVER]) and len(c) == 13:
        e = struct.unpack_from("<HHHH", c, 1)
        v = struct.unpack_from("<I", c, 9)[0]
        if not escrita_permitida(*e, v):
            raise PermissionError(f"escrita fora do permitido: {e} = {v:X}")
        return
    if c[:1] == bytes([ts.LER_BLOCO]) and len(c) == 11:
        b, x, y, i, n = struct.unpack_from("<HHHHH", c, 1)
        if not leitura_permitida(b, x, y, i, n):
            raise PermissionError(f"leitura fora do que o App leu no boot: "
                                  f"{(b, x, y, i)} n={n}")
        return
    raise PermissionError(f"pacote que esta conexao nao manda: {ts.hexs(pac[:20])}")


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
            # sobra de uma sessao anterior no buffer do sistema desalinharia o
            # enquadramento (na C3 a 1a leitura ja trouxe dois 03 velhos)
            termios.tcflush(self.fd, termios.TCIFLUSH)
        except Exception:
            os.close(self.fd)
            raise

    def escrever(self, b, prazo=ESPERA):
        limite, total = time.time() + prazo, 0
        while total < len(b):
            if time.time() > limite:
                raise ErroConexao(f"a porta nao aceitou os bytes em {prazo} s")
            try:
                total += os.write(self.fd, b[total:])
            except BlockingIOError:
                select.select([], [self.fd], [], 0.05)

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
        # nunca por cima de uma captura que ja existe (espiao.caminho_livre)
        self.captura = espiao.caminho_livre(nome_captura) if nome_captura else None

    # ── abrir / fechar ──────────────────────────────────────
    def __enter__(self):
        # o 'S' primeiro e na hora de ABRIR: e o t0 da captura
        self._registrar("S", b"conexao_serial.py", fd=os.getpid())
        try:
            if self._porta_injetada is not None:
                self.porta = self._porta_injetada
                caminho = "(porta de teste)"
            else:
                abertos = espiao.app_aberto()
                if abertos:
                    raise ErroConexao(f"o TR-1000 App esta aberto (pid {', '.join(abertos)}): "
                                      "feche com Cmd+Q antes")
                caminho = porta_da_tr1000()
                try:
                    self.porta = PortaSerial(caminho)
                except OSError as e:
                    raise ErroConexao(f"nao abri {caminho}: {e}")
        except Exception:
            self.captura = None          # porta nem abriu: nao ha conversa para gravar
            raise
        self._registrar("O", caminho.encode())
        return self

    def __exit__(self, *e):
        if self.porta is not None:
            self._registrar("C", b"")
            self.porta.fechar()
        self._gravar_captura()

    # ── log no formato do espiao (.serlog) ──────────────────
    def _registrar(self, tipo, dados, fd=0):
        self.registros.append((int(self.relogio() * 1e9), tipo, fd, bytes(dados)))

    def _gravar_captura(self):
        if not self.captura or not self.registros:
            return
        os.makedirs(os.path.dirname(self.captura), exist_ok=True)
        with open(self.captura, "xb") as f:                  # "x": nunca sobrescreve
            f.write(ts.serializar(self.registros))

    # ── troca de pacotes ────────────────────────────────────
    def _mandar(self, pac):
        conferir_pacote(pac)                                 # o portao, antes de tudo
        self._registrar("W", pac)
        try:
            self.porta.escrever(pac)
        except OSError as e:
            raise ErroConexao(f"a porta falhou ao escrever: {e}")

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
            try:
                chegou = self.porta.ler(min(falta, 0.05))
            except OSError as e:                             # USB puxado, maquina desligada
                raise ErroConexao(f"a porta falhou ao ler: {e}")
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
        """Os bytes exatos que escrever() mandaria - para mostrar antes.
        Passa pelo portao ja aqui: o que nao pode sair nem e montado."""
        if not 0 <= valor <= 0xFFFFFFFF:
            raise ValueError(valor)
        pac = ts.pacote_dados(ts.CAB_ESCRITA, ts.carga_escrever(bloco, x, y, indice, valor))
        conferir_pacote(pac)                                 # recusa ja na hora de mostrar
        return pac

    def escrever(self, bloco, x, y, indice, valor):
        """Um 01, uma vez, e espera o 03. Nunca repete sozinho."""
        self._mandar(self.pacote_escrita(bloco, x, y, indice, valor))
        ok = self._esperar(lambda p: ts.ack_03(p) == (bloco, x, y, indice) or None)
        if ok is None:
            raise ErroConexao(f"a maquina nao confirmou (03) a escrita em "
                              f"{(bloco, x, y, indice)} - parando, sem repetir")
        return True

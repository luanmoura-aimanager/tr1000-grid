#!/usr/bin/env python3
"""
motor.py - o grid ao vivo: dois Launchpad editando o pattern interno da TR-1000

O esqueleto e o Motor do tr8s-grid (lp_tr8s.py :2021-5115) - geometria, fila
de comandos, pintura em lote, pads, clock -, mas a maquina e outra:
  - LER e ESCREVER passam pela serial (conexao_serial.ConexaoTR1000), com o
    portao de saida conferir_pacote: o grid so escreve STEPS (REFERENCIA 3.1,
    decisao do Luan de 08/10/2026)
  - o step atual vem da porta MIDI comum: start/stop + clock (REFERENCIA 7.3).
    A maquina manda clock MESMO PARADA - so o start liga o playhead

As duas controladoras de knobs (MC-24 e CM-MC50, controladoras.py), se
estiverem na USB: cada knob escreve o parametro decifrado dele
(parametros.py), com pickup e as escritas juntadas a cada ~30 ms. Sem elas, o
grid roda igual.

O que o grid mostra (fase 1): os 10 tracks BD..RC (8 por vez, com rolagem) x 16
steps de UMA variacao do pattern selecionado no painel. Le de novo a cada
~0,5 s, entao edicao no painel e troca de pattern aparecem sozinhas.

O playhead (fase 2b, F3 de 12/10/2026): os pulsos por step vem da Scale do
cabecalho, e ele da a volta no FIRST/LAST da variacao mostrada; um track com
FIRST/LAST proprio anda sozinho (polimetria).

As paginas do layout A (fase 2d): PAR (96), PERF (97) e ROUT (98) no topo do
direito; o mesmo botao volta para os steps.

A variacao que TOCA (fase 2f, tocando.py): as notas que a maquina manda na
porta 'TR-1000' contra os steps de cada variacao da chain. So a que bate, e
so ela; empate fica "?". As mesmas notas dao a fase quando o Controller liga
com a maquina ja tocando (sem START).

O que NAO faz ainda (documentado na REFERENCIA):
  - linhas de ACC e TRG: o accent e pelo painel; o TRG ficou de fora
  - gravar: o WRITE continua no painel (criterio 6 adiado)
"""
import colorsys, json, math, os, queue, random, threading, time

import campos
import conexao_serial as cs
import controladoras
import parametros
import launchpad as lp
import ritmos
import tocando as toc
import tr1000
import tr1000_serial as ts
from portas import EntradaMIDI, SaidaMIDI, porta_exata

MODO_ON, MODO_OFF, MODO_STANDBY = "on", "off", "standby"

# Ondinha (port do lp_tr8s.py, onde ja rodou em hardware): o toque no pad em
# standby, e as ondas que nascem sozinhas. Cada estilo e uma tabela de faixas
# (min, max) sorteadas por onda - acertar o gosto e mexer em numero.
ONDA_VEL     = 9.0    # celulas por segundo
ONDA_LARGURA = 2.2    # espessura do anel, em celulas
ONDA_ALCANCE = 15.0   # celulas ate morrer (a diagonal do 16x8 e ~17)
ONDA_FPS     = 30
ESTILO_CHUVA, ESTILO_AMBIENTE = "chuva", "ambiente"
STANDBY_ESTILOS = {
    # chuva: variacao larga, uma onda a cada meio segundo mais ou menos
    ESTILO_CHUVA:    {"intervalo": (0.35, 1.10), "vel": (6.0, 13.0),
                      "larg": (1.4, 3.0), "alc": (9.0, 17.0),
                      "brilho": 1.00, "fps": 30},
    # ambiente: grandes, raras, lentas e fracas - respiracao, nao chuva
    ESTILO_AMBIENTE: {"intervalo": (2.50, 5.00), "vel": (1.6, 3.2),
                      "larg": (3.5, 6.0), "alc": (14.0, 20.0),
                      "brilho": 0.45, "fps": 15},
}

N_TRACKS = len(ts.TRACKS_SERIAL)                    # 10: BD..RC
TRACKS_LAYER = 4                                    # BD SD LT HT tem layer A/B
LINHAS = 8
# Os dois bancos do layout A (ideia do Luan, 10/10/2026, 22:30): o CC divide a
# linha do RS e o RC a do HC; BD e SD (e LT HT CH OH) ficam sempre no lugar.
# Linha -> track. Sem linha de accent: o accent e pelo painel.
BANCOS = {1: [0, 1, 2, 3, 4, 5, 6, 7],              # BD SD LT HT RS HC CH OH
          2: [0, 1, 2, 3, 8, 9, 6, 7]}              # BD SD LT HT CC RC CH OH
PULSOS_P_STEP = 6                                   # 24 ppqn, scale 16th
# pulsos de clock (24 ppqn) por step, pela Scale do cabecalho (campos.SCALES):
# 8th(T) = 1/12 de compasso, 16th(T) = 1/24, 16th = 1/16, 32nd = 1/32. A 32nd
# correu no dobro no F3.4.4 (12/10/2026)
PULSOS_POR_SCALE = (8, 4, 6, 3)
PASSOS = 16
# a foto da sessao (pedido do Luan, 12/10/2026): fica SO no app, nunca na maquina
DIR_SESSOES = os.path.expanduser("~/Library/Application Support/tr1000-sessoes")
MAX_SESSOES = 200
RELER_A_CADA = 0.5                                  # s
# O x do KIT: nas capturas do App, bloco 3 [2] (pattern), [3] e [4] vieram
# sempre iguais - e o x dos blocos de kit foi o mesmo. Qual deles e o kit e
# DEDUCAO ([3]); com eles diferentes, os knobs de kit ficam parados em vez de
# escrever num kit que talvez nao seja o que toca.
OFFS_DO_KIT = (2, 3, 4)
# O bloco de steps inteiro: os 64 slots e PROB/SUB/CYCLE/START (campos.py)
N_SLOTS = ts.N_STEPS_BLOCO                          # 131
ERROS_DE_LEITURA = (cs.ErroConexao, PermissionError)

# Velocity: 80 e o "normal" do painel (Normal Velocity, e o A503C que o
# painel escreve); 66 o painel mostrou FRACO (SD do 1-02, 08/10/2026).
VELOCIDADES = [127, 110, 100, 80, 66, 50, 30, 10]
VEL_PADRAO = 3
VEL_FRACA_ABAIXO = 80          # abaixo disso, a cor fraca (o painel: 66/74 fracos)

MODOS_LAYER = ("AB", "A", "B")

# Botoes (ver o mapa fisico em launchpad.py / tr8s-grid): o aparelho ESQUERDO
# esta girado 90 graus, entao a coluna de cena dele vai para o TOPO.
BOTOES = {}
for _i, _cc in enumerate(lp.CENA_CCS):
    BOTOES[("E", _cc)] = ("variacao", _i)       # topo esquerdo: A..H
    BOTOES[("D", _cc)] = ("velocidade", _i)     # borda direita: 127..10
for _i in range(LINHAS):
    BOTOES[("E", lp.FUNC_CCS[-1 - _i])] = ("mudo", _i)   # lateral do esquerdo: 98 em cima
for _cc, _acao in ((91, ("banco", 1)),          # ▲ RS·HC
                   (92, ("banco", 2)),          # ▼ CC·RC
                   (93, ("layer", "AB")),
                   (94, ("layer", "A")),
                   (95, ("layer", "B")),
                   (96, ("pagina", "par")),
                   (97, ("pagina", "perf")),
                   (98, ("pagina", "rout"))):
    BOTOES[("D", _cc)] = _acao                  # topo direito
del _i, _cc, _acao


bloco_de_steps = ts.bloco_de_steps


# As paginas do layout A (fase 2d; desenho no artefato da REFERENCIA 7.7). O
# mesmo botao volta para os steps. Tudo o que elas escrevem chama as MESMAS
# acoes da tela - o mesmo portao.
PAGINAS = ("steps", "par", "perf", "rout")
# PERF: a linha de cada coisa
PERF_MUTE, PERF_CHAIN, PERF_LOOP, PERF_LAST, PERF_SCALE = 0, 1, 2, 3, 4
PERF_FILLS = (12, 13)                       # colunas do FILL 1 e 2, na linha do mute
# ROUT: as 13 fontes da Routing Matrix, na ordem da tela
FONTES_ROTA = ("bd", "sd", "lt", "ht", "rs", "hc", "ch", "oh", "cc", "rc", "rvb", "dly", "ext")
ROUT_SC1, ROUT_SC2, ROUT_CHAVES = 4, 5, 7   # SC SOURCE em duas linhas; POLARITY e HLD MODE
ROUT_POLARITY, ROUT_HLD = (0, 1), (3, 4)    # colunas
# o que a pagina le do kit (e so isso, a cada 2 s: o kit inteiro e ~440 pedidos)
IDS_ROUT = tuple(f"rota.{f}" for f in FONTES_ROTA) + ("sc.source", "sc.polarity", "sc.hld_mode")
# as cores das paginas (RGB 0..127)
COR_PAR = {"prob": (127, 50, 0), "sub": (0, 80, 127), "cycle": (110, 100, 0),
           "start": (110, 0, 80), "vel": (127, 0, 0), "alt": (80, 0, 127)}
COR_ROTA = ((60, 60, 60), (127, 50, 0), (0, 90, 110))      # THROUGH, MASTER, ANALOG


def _fraca(cor, f=0.12):
    return tuple(int(c * f) for c in cor)


def indice_do_slot(step, slot):
    return ts.INDICE_STEPS + 4 * step + slot


class Motor:
    # defaults na CLASSE: um Motor feito com object.__new__ (os testes) ja
    # funciona sem __init__ - o padrao do motor_cru() do tr8s-grid
    modo_geral = MODO_OFF
    conexao = None
    clk = None
    x_pattern = None
    variacao = 0
    vel_idx = VEL_PADRAO
    modo_layer = "AB"
    banco = 1                                   # BANCOS: 1 = RS HC, 2 = CC RC
    passo = -1
    passos_trk = None                           # [step] por track, ou None parado
    pulsos = 0                                  # pulsos dentro do step atual
    n_steps = -1                                # steps desde o START
    pps_step = PULSOS_P_STEP                    # pulsos do step atual (a Scale dele)
    n_parado = -1                               # o step do STOP, para o CONTINUE
    tocando = False
    pagina = "steps"                            # PAGINAS
    par_track = 0                               # o track da pagina PAR
    par_param = 0                               # campos.PAR_PARAMS
    segurados = frozenset()                     # (linha, step) segurados na pagina
    estilo_standby = ESTILO_CHUVA
    ondas = ()                                  # as ondas no ar (standby)
    onda_suja = False                           # ha um quadro de onda para apagar
    proxima_onda = 0.0
    ultimo_quadro = 0.0
    ao_passo = None                             # callback da tela (o /passo)
    tocando_var = None                          # a variacao que toca (None = "?")
    seq = None                                  # (variacao, coluna) do step atual
    n_extremos = 0                              # step em que os FIRST/LAST mudaram por ultimo
    ultimo_extremos = None                      # os FIRST/LAST do step anterior
    resync_tentado = -99                        # step da ultima busca sem resposta
    seq_trk = None                              # coluna propria de cada track (ou None)
    hist = None                                 # {n: (variacao, coluna)} para conferir
    adotado = False                             # tocando sem ter visto o START
    sem_adocao = False                          # desistiu da fase: espera START/STOP
    sem_nota_n = 0                              # steps seguidos sem nota (adotado)
    fase_incerta = False                        # tocando, mas sem saber o step (adotado)
    ouvidos = None                              # {n: {tracks}} o que soou em cada step
    adocao = None                               # notas sem START: contando para adotar
    lido_em = None                              # {variacao: hora} das variacoes da chain
    RELER_CHAIN_A_CADA = 5.0                    # s
    pc_out = None                               # a porta 'TR-1000' de saida (Program Change)
    loop_antes = None                           # o [150] antes de segurar um step
    loop_segurados = frozenset()                # os steps segurados agora
    proxima_releitura = 0.0
    x_kit = None
    ctl = None                                  # controladoras.Controladoras
    pickup = None                               # controladoras.Pickup
    cab = None                                  # o cabecalho do pattern (bloco 116)
    acc_mascara = 0                             # o accent da variacao mostrada
    mudo_mascara = 0                            # bloco 3 [12]
    b3 = None                                   # o ultimo bloco 3 lido
    kit_valores = {}                            # id do parametro -> valor lido
    quer_kit = False                            # a tela de Mixer/Efeitos esta aberta
    proximo_kit = 0.0
    LER_KIT_A_CADA = 2.0                        # s
    foto_motivo = None                          # a foto da sessao pedida (ON/pattern/botao)
    foto_em = 0.0                               # quando comecar
    foto_passos = None                          # o gerador, andando um pedaco por tick
    ESPERA_FOTO_PATTERN = 3.0                   # s parado no pattern antes da foto
    ultima_sessao = None                        # o arquivo da ultima foto

    def __init__(self, cfg, log=print):
        """cfg = o layout do learn, ou None: sem Launchpads (o Controller roda
        so com a tela - e com as controladoras, se estiverem na USB)."""
        self.log = log
        self.lock = threading.RLock()
        self.fila_cmd = queue.Queue()
        self.cache = {}                         # (variacao, track) -> [131 u32]
        self.kit_valores = {}
        self.geo, self.lp_in, self.lp_out = {}, {}, {}
        if cfg:
            self.geo = {"E": cfg["esquerdo"], "D": cfg["direito"]}
            for dev, lado in (("E", "esquerdo"), ("D", "direito")):
                c = cfg[lado]
                self.lp_in[dev] = EntradaMIDI(c["in_idx"], c.get("in_nome"))
                self.lp_out[dev] = SaidaMIDI(c["out_idx"], c.get("out_nome"))
        try:
            self.ctl = controladoras.Controladoras(log=log)
            if self.ctl.portas:
                self.pickup = self.novo_pickup(self.ctl.mapa)
                self.log(f"controladoras: {', '.join(self.ctl.portas)}")
        except (ValueError, KeyError, TypeError, OSError) as e:
            # mapa corrompido ou editado a mao: o grid roda sem os knobs
            # (revisao do PR #5)
            self.log(f"(!) controladoras desligadas - {controladoras.MAPA}: {e!r}")
            if self.ctl is not None:
                self.ctl.fechar()
            self.ctl = self.pickup = None

    def novo_pickup(self, mapa):
        return controladoras.Pickup(
            mapa,
            ler=lambda b, x, y, i: self._ler(b, x, y, i, 1)[0],
            escrever=lambda b, x, y, i, v: self.conexao.escrever(b, x, y, i, v),
            erros=ERROS_DE_LEITURA, log=self.log)

    # ── geometria (do tr8s-grid, sem mudanca) ───────────────
    def nota_de(self, dev, linha, col):
        c = self.geo[dev]
        return c["origem"] + linha * c["passo_lin"] + col * c["passo_col"]

    def _decodificar(self, dev, nota):
        """nota -> (linha, col) ou None. O teste 0 <= col < 8 e o que separa
        as linhas no aparelho de passo_col = 1 (tr8s REFERENCIA 5)."""
        c = self.geo[dev]
        d = nota - c["origem"]
        for linha in range(8):
            resto = d - linha * c["passo_lin"]
            if c["passo_col"] and resto % c["passo_col"] == 0:
                col = resto // c["passo_col"]
                if 0 <= col < 8:
                    return linha, col
        return None

    def track_da_linha(self, linha):
        return BANCOS[self.banco][linha]

    # ── fila de comandos (a tela do Controller usa) ─────────
    def enfileirar(self, fn, *args, **kw):
        self.fila_cmd.put((fn, args, kw))

    def _drenar_fila(self):
        for _ in range(4):
            try:
                fn, args, kw = self.fila_cmd.get_nowait()
            except queue.Empty:
                return
            try:
                fn(*args, **kw)
            except Exception as exc:
                self.log(f"(!) comando falhou: {exc}")

    # ── a maquina: abrir, ler ───────────────────────────────
    def definir_modo(self, modo, estilo=None):
        """ON: abre a serial, le o pattern selecionado e pinta. STANDBY: solta a
        serial (o App da Roland pode abrir) e os Launchpads viram ondas, no
        estilo pedido. OFF: apaga."""
        if modo == MODO_STANDBY:
            self.soltar_maquina()
            self.modo_geral = MODO_STANDBY
            self.estilo_standby = estilo if estilo in STANDBY_ESTILOS else self.estilo_standby
            self.ondas, self.onda_suja, self.proxima_onda = [], False, 0.0
            self.pintar()
            self.pintar_botoes()
            self.log(f"standby ({self.estilo_standby}): a serial esta livre; os "
                     "Launchpads fazem ondas e o toque solta mais uma")
            return True
        if modo == MODO_ON:
            try:
                if self.conexao is None:
                    c = cs.ConexaoTR1000()
                    c.__enter__()
                    self.conexao = c
                    self.log(f"TR-1000 conectada, versao {c.aperto()!r}")
                if self.clk is None:
                    self.abrir_clock()
                self.modo_geral = MODO_ON
                self.reler(forcar=True)
            except (cs.ErroConexao, PermissionError, OSError) as e:
                self.log(f"(!) nao deu para ligar: {e}")
                # a serial pode ter aberto antes do erro: solta (revisao do PR #10)
                self.soltar_maquina()
                self.modo_geral = MODO_OFF
                self.pintar()
                return False
        else:
            self.modo_geral = MODO_OFF
        self.pintar()
        self.pintar_botoes()
        return True

    def soltar_maquina(self):
        """Fecha a serial e as portas MIDI da TR-1000; os Launchpads e as
        controladoras ficam (o standby usa os Launchpads). Antes, solta os
        steps de STEP LOOP segurados: o note_off que viria depois e ignorado
        fora do ON, e a maquina ficaria presa no loop (revisao do PR #11)."""
        if self.conexao is not None:
            for step in sorted(self.loop_segurados):
                self.definir_loop(False, step)
        if self.conexao is not None:
            self.conexao.__exit__(None, None, None)
            self.conexao = None
        if self.clk is not None:
            self.clk.close()
            self.clk = None
        if self.pc_out is not None:
            self.pc_out.close()
            self.pc_out = None
        self.tocando = False
        self.passo, self.passos_trk, self.n_steps = -1, None, -1
        # o detector tambem (revisao do PR #13: sobrevivia ate o proximo ON)
        self.adocao, self.ouvidos, self.tocando_var, self.n_parado = None, None, None, -1
        self.fase_incerta = self.adotado = self.sem_adocao = False
        self.seq = self.seq_trk = self.hist = None
        self.x_pattern = self.x_kit = None
        self.b3 = self.cab = None                    # sem maquina, nada velho na tela
        self.cache.clear()
        self.foto_motivo = self.foto_passos = None
        if self.ritmo_passos is not None:
            # largado no meio: o diario tem o que ja foi confirmado
            self.ritmo_passos = None
            self._ritmo_falhou("desligado no meio da escrita")
        # o STEP LOOP segurado e da sessao que acabou: soltar um dedo depois
        # nao pode devolver um [150] velho a outro pattern (revisao do PR #10)
        self.loop_antes, self.loop_segurados = None, frozenset()
        self.segurados = frozenset()
        self._avisar_passo()

    def abrir_clock(self):
        """A porta comum 'TR-1000' em modo callback: o rtmidi descarta em
        silencio o que passar de 1024 mensagens na fila (tr8s pitfall 1)."""
        p = porta_exata(tr1000.PORTA_COMUM)
        if p:
            self.clk = EntradaMIDI(*p, callback=True)
        else:
            self.log("(!) porta MIDI 'TR-1000' nao achada - sem playhead")

    def _ler(self, bloco, x, y, indice, n):
        self._ler_clock()                        # antes do pedido, nunca no meio
        return self.conexao.ler(bloco, x, y, indice, n)

    def _ler_variacao(self, x, variacao):
        """Os 10 tracks de uma variacao, SEM tocar no estado: ou volta tudo, ou
        a excecao sobe e o cache continua o de antes (revisao do PR #4: uma
        falha no meio deixava metade do cache novo e metade velho)."""
        b = bloco_de_steps(variacao)
        return {(variacao, tr): self._ler(b, x, tr, ts.INDICE_STEPS, N_SLOTS)
                for tr in range(N_TRACKS)}

    def ler_variacao(self, variacao):
        self.cache.update(self._ler_variacao(self.x_pattern, variacao))

    def reler(self, forcar=False):
        """O pattern selecionado no painel (bloco 3 [2]) e a variacao mostrada.
        Devolve True se algo mudou (e entao ja repintou). Le tudo antes de
        trocar qualquer coisa: o x e o cache so mudam juntos, e so se as 11
        leituras deram certo."""
        b3 = self._ler(3, 0, 0, *cs.faixa_do_bloco(3, 0, 0))
        x = b3[ts.OFF_PATTERN_GLOBAL]
        if not 0 <= x < cs.N_PATTERNS:
            self.log(f"(!) bloco 3 trouxe pattern {x}, fora de 0..127 - ignorado")
            return False
        novo = self._ler_variacao(x, self.variacao)
        cab = self._ler(ts.BLOCO_CAB_PATTERN, x, 0, *cs.faixa_do_bloco(ts.BLOCO_CAB_PATTERN, x, 0))
        acc = self._ler(ts.BLOCO_VAR0 + ts.BLOCOS_POR_VAR * self.variacao, x, 0, campos.INI_ACC, 1)[0]
        kits = {b3[o] for o in OFFS_DO_KIT}
        x_kit = kits.pop() if len(kits) == 1 else None
        if self.pickup is not None:
            if x != self.x_pattern or x_kit != self.x_kit:
                self.pickup.soltar()                 # outro pattern/kit: pickup de novo
            else:
                self.pickup.reconferir()             # o painel pode ter mexido
        if x_kit != self.x_kit and x_kit is None:
            self.log(f"(!) bloco 3 [2..4] = {[b3[o] for o in OFFS_DO_KIT]}: kit incerto, "
                     "knobs de kit parados")
        if x_kit != self.x_kit:
            self.kit_valores = {}                    # outro kit: lido de novo
            self.proximo_kit = 0.0
        self.x_kit = x_kit
        mudo_antes, cab_antes = self.mudo_mascara, self.cab
        self.b3, self.cab, self.acc_mascara = b3, cab, acc
        self.mudo_mascara = b3[campos.B3_MUTE]
        trocou = x != self.x_pattern
        if trocou:
            self.log(f"pattern {ts.nome_do_pattern(x)} (x {x})")
            self.x_pattern = x
            self.cache.clear()
            self.lido_em, self.tocando_var = {}, None
            self.pedir_foto("ON" if self.ultima_sessao is None else "pattern",
                            0.0 if self.ultima_sessao is None else self.ESPERA_FOTO_PATTERN)
        antes = [self.cache.get(k) for k in novo]
        self.cache.update(novo)
        if forcar or trocou or antes != list(novo.values()):
            self.pintar()
            self.pintar_botoes()
            return True
        if self.mudo_mascara != mudo_antes:
            self.pintar_botoes()                     # o mute mudou no painel
        if self.pagina == "perf" and (cab != cab_antes or self.mudo_mascara != mudo_antes):
            self.pintar()                            # chain, LAST, Scale, mute no painel
        return False

    # ── o que um step e ─────────────────────────────────────
    def slots(self, tr, step):
        v = self.cache.get((self.variacao, tr))
        return v[step * 4:step * 4 + 4] if v else [0, 0, 0, 0]

    def slots_alvo(self, tr):
        """Que slots um toque escreve: layer A = 0, layer B = 1. Track simples
        so tem o slot 0 (medido nos 12 bancos do Dub Techno)."""
        if tr >= TRACKS_LAYER:
            return [0]
        return {"AB": [0, 1], "A": [0], "B": [1]}[self.modo_layer]

    def cor_do_step(self, linha, step):
        tr = self.track_da_linha(linha)
        s = self.slots(tr, step)
        a, b = ts.slot_toca(s[0]), ts.slot_toca(s[1])
        no_playhead = self.tocando and step == self.passo_do_track(tr)
        if no_playhead:
            return lp.COR_PLAY_HIT if (a or b) else lp.COR_PLAY
        if a and campos.eh_alt(s[0]):                 # o ALT: roxo, como o painel
            fraca = ts.velocidade(s[0] & ~campos.BIT_ALT) < VEL_FRACA_ABAIXO
            return lp.COR_ALT_FRACA if fraca else lp.COR_ALT
        if a:
            return lp.COR_FRACA if ts.velocidade(s[0]) < VEL_FRACA_ABAIXO else lp.COR_FORTE
        if b:
            return lp.COR_B_FRACA if ts.velocidade(s[1]) < VEL_FRACA_ABAIXO else lp.COR_B
        return lp.COR_TEMPO if step % lp.STEPS_TEMPO == 0 else lp.COR_OFF

    # ── escrever (o toque no pad) ───────────────────────────
    def alternar(self, linha, step):
        """O toque no pad da linha (o banco diz qual track)."""
        self.alternar_track(self.track_da_linha(linha), step)

    def alternar_track(self, tr, step):
        """O toque: se os slots-alvo ja tem a nota na velocity atual, desliga
        (FF, como o painel); senao escreve a nota. Uma escrita por slot, cada
        uma com o 03 de volta; o cache so muda depois da confirmacao. Erro:
        rele o track e segue - nunca repete sozinho."""
        if self.conexao is None or self.x_pattern is None:
            return
        alvo = self.slots_alvo(tr)
        nota = ts.nota(VELOCIDADES[self.vel_idx])
        atuais = [self.slots(tr, step)[s] for s in alvo]
        novo = ts.SLOT_PAUSA if all(v == nota for v in atuais) else nota
        bloco = bloco_de_steps(self.variacao)
        cache = self.cache.get((self.variacao, tr))
        try:
            for s in alvo:
                i = indice_do_slot(step, s)
                self.conexao.escrever(bloco, self.x_pattern, tr, i, novo)
                if cache is not None:
                    cache[i - ts.INDICE_STEPS] = novo
        except ERROS_DE_LEITURA as e:
            self.log(f"(!) escrita recusada/sem resposta: {e} - relendo o track")
            try:
                self.cache[(self.variacao, tr)] = self._ler(
                    bloco, self.x_pattern, tr, ts.INDICE_STEPS, N_SLOTS)
            except ERROS_DE_LEITURA:
                pass

    # ── botoes ──────────────────────────────────────────────
    def executar(self, tipo, arg):
        if tipo == "variacao":
            if arg != self.variacao:
                # le primeiro, troca depois: com a leitura falhando, o grid
                # fica na variacao de antes em vez de mostrar uma vazia que o
                # toque trataria como vazia (revisao do PR #4)
                if self.conexao is not None and self.x_pattern is not None:
                    try:
                        self.cache.update(self._ler_variacao(self.x_pattern, arg))
                    except ERROS_DE_LEITURA as e:
                        self.log(f"(!) nao li a variacao {ts.VARIACOES_SERIAL[arg]}: {e}")
                        return
                self.variacao = arg
        elif tipo == "velocidade":
            if self.pagina == "par":                 # a borda direita escolhe o parametro
                if arg < len(campos.PAR_PARAMS):
                    self.par_param = arg
            else:
                self.vel_idx = arg
        elif tipo == "banco":
            self.banco = arg
        elif tipo == "pagina":
            self._soltar_segurados()                 # um step do loop nao fica preso
            self.pagina = "steps" if self.pagina == arg else arg
            if self.pagina == "rout":
                self.proximo_kit = 0.0               # le o kit ja
        elif tipo == "mudo":
            if self.pagina == "par":                 # a coluna lateral escolhe o track
                self.par_track = self.track_da_linha(arg)
            else:
                self.alternar_mudo(self.track_da_linha(arg))
                return
        elif tipo == "layer":
            self.modo_layer = arg
        self.pintar()
        self.pintar_botoes()

    # ── LEDs ────────────────────────────────────────────────
    def _luz(self, out, control, cor):
        lp.enviar_cor_cc(out, control, cor)

    def pintar_botoes(self):
        if not self.lp_out:
            return
        ligado = self.modo_geral == MODO_ON
        e, d = self.lp_out["E"], self.lp_out["D"]
        for i, cc in enumerate(lp.CENA_CCS):
            # azul = a editada; branco = a que toca (tocando.py)
            if ligado and self.tocando and i == self.tocando_var:
                cor = (127, 127, 127) if i != self.variacao else (60, 100, 127)
            elif ligado:
                cor = lp.cor_borda(lp.COR_VAR, i == self.variacao)
            else:
                cor = (0, 0, 0)
            self._luz(e, cc, cor)
            cor_vel = (lp.COR_ATIVO if i == self.vel_idx else lp.COR_VEL_OFF)
            self._luz(d, cc, lp.cor_borda(cor_vel, i == self.vel_idx) if ligado
                      else (0, 0, 0))
        for cc, b in ((91, 1), (92, 2)):
            self._luz(d, cc, lp.cor_borda(lp.COR_ATIVO, b == self.banco) if ligado
                      else (0, 0, 0))
        # a coluna lateral do esquerdo: o MUTE do track de cada linha
        for linha in range(LINHAS):
            mudo = self.mudo_mascara >> self.track_da_linha(linha) & 1
            self._luz(e, lp.FUNC_CCS[-1 - linha],
                      lp.cor_borda(lp.COR_MUDO if mudo else lp.COR_SOANDO, bool(mudo))
                      if ligado else (0, 0, 0))
        for cc, modo, cor in ((93, "AB", lp.COR_ATIVO), (94, "A", lp.COR_FORTE),
                              (95, "B", lp.COR_B)):
            self._luz(d, cc, lp.cor_borda(cor, modo == self.modo_layer) if ligado
                      else (0, 0, 0))
        for cc, pag in ((96, "par"), (97, "perf"), (98, "rout")):
            self._luz(d, cc, lp.cor_borda(lp.COR_ATIVO, pag == self.pagina) if ligado
                      else (0, 0, 0))
        if ligado and self.pagina == "par":
            # a coluna lateral: o track escolhido; a borda direita: o parametro
            for linha in range(LINHAS):
                # o escolhido bem branco; os outros quase apagados (F4.6c: com o
                # brilho de borda de sempre, nao se via qual estava escolhido)
                self._luz(e, lp.FUNC_CCS[-1 - linha],
                          (127, 127, 127) if self.track_da_linha(linha) == self.par_track
                          else (4, 4, 4))
            for i, cc in enumerate(lp.CENA_CCS):
                if i < len(campos.PAR_PARAMS):
                    cor = COR_PAR[campos.PAR_PARAMS[i]]
                    self._luz(d, cc, cor if i == self.par_param else _fraca(cor, 0.2))
                else:
                    self._luz(d, cc, (0, 0, 0))

    def cor_pad(self, linha, step):
        """A cor de um pad na pagina atual."""
        if self.pagina == "par":
            return self.cor_par(linha, step)
        if self.pagina == "perf":
            return self.cor_perf(linha, step)
        if self.pagina == "rout":
            return self.cor_rout(linha, step)
        return self.cor_do_step(linha, step)

    def pintar_coluna(self, step):
        if step < 0 or self.modo_geral != MODO_ON or not self.lp_out:
            return
        dev = "E" if step < 8 else "D"
        col = step if step < 8 else step - 8
        lp.enviar_cores(self.lp_out[dev],
                        [(self.nota_de(dev, l, col), self.cor_pad(l, step))
                         for l in range(LINHAS)])

    def pintar(self):
        """O grid inteiro: um SysEx por Launchpad. Fora do ON, tudo apagado
        (e nao le cache nenhum)."""
        if not self.lp_out:
            return
        for dev, off in (("E", 0), ("D", 8)):
            if self.modo_geral != MODO_ON:
                pares = [(self.nota_de(dev, l, c), lp.COR_OFF)
                         for l in range(LINHAS) for c in range(8)]
            else:
                pares = [(self.nota_de(dev, l, c), self.cor_pad(l, off + c))
                         for l in range(LINHAS) for c in range(8)]
            lp.enviar_cores(self.lp_out[dev], pares)

    # ── o playhead ──────────────────────────────────────────
    def _c(self, pos, padrao):
        cab = self.cab
        return cab[pos] if cab is not None and pos < len(cab) else padrao

    def pulsos_por_step(self):
        n = self._c(campos.CAB_SCALE, 2)
        return PULSOS_POR_SCALE[n] if 0 <= n < len(PULSOS_POR_SCALE) else PULSOS_P_STEP

    def _extremos(self):
        """{variacao: (FIRST, LAST)} do cabecalho, lidos agora (a regra de
        quando um LAST trocado tocando vale esta em tocando.proximo)."""
        return {v: (self._c(campos.CAB_FIRST_VAR + v, 0),
                    self._c(campos.CAB_LAST_VAR + v, PASSOS - 1))
                for v in range(campos.N_VARS)}

    def _chain(self):
        return toc.chain_de(self._c(campos.CAB_VARIACOES, 1))

    def _extremos_trk(self, t):
        """(FIRST, LAST) proprios do track, ou None se ele segue a variacao."""
        if not self._c(campos.CAB_TRK_SW + t, 0):
            return None
        return self._c(campos.CAB_FIRST_TRK + t, 0), self._c(campos.CAB_LAST_TRK + t, PASSOS - 1)

    def _iniciar_seq(self, estado=None, n=0, manter_trk=False):
        """O primeiro step (START), ou um estado achado pelas notas. Numa
        ressincronizacao, as colunas proprias dos tracks continuam (andaram
        certas desde o START; revisao do PR #14)."""
        self.seq = estado or toc.inicio(self._chain(), self._extremos())
        if not (manter_trk and self.seq_trk):
            trk = []
            for t in range(N_TRACKS):
                e = self._extremos_trk(t)
                # START: o FIRST; adotado no meio: uma estimativa
                trk.append(None if e is None else
                           (e[0] if estado is None else toc.volta(n, *e, PASSOS)))
            self.seq_trk = trk
        self.hist = {n: self.seq}
        self.n_extremos = n

    def _colunas_tocadas(self):
        """A coluna que cada track toca agora: a posicao (da variacao, ou a
        propria do track) passada pelo DIRECTION dele (R-L toca 2 1 4 3...).
        -1 quando nao da para saber (RND, DNK, P-P): sem playhead naquela
        linha, em vez de um no lugar errado."""
        v, pos = self.seq
        out = []
        for t, c in enumerate(self.seq_trk or [None] * N_TRACKS):
            e = self._extremos_trk(t)
            first, last = e if e else self._extremos()[v]
            base = pos if c is None else c
            col = toc.coluna_tocada(toc.direcao_de(self.cache.get((v, t))), base, first, last)
            out.append(-1 if col is None else col)
        return out

    def direcoes(self):
        """O DIRECTION de cada track na variacao mostrada (0 = FWD)."""
        return [toc.direcao_de(self.cache.get((self.variacao, t))) for t in range(N_TRACKS)]

    def _avancar_seq(self):
        """Um step: a variacao/coluna e as colunas proprias dos tracks."""
        if self.seq is None:
            return
        extremos = self._extremos()
        if extremos != self.ultimo_extremos:
            # os steps de antes foram tocados com outros extremos: a busca de
            # ressincronizacao so olha dai em diante (revisao do PR #14)
            if self.ultimo_extremos is not None:
                self.n_extremos = self.n_steps
            self.ultimo_extremos = extremos
        self.seq = toc.proximo(self.seq, self._chain(), extremos)
        trk = []
        for t, c in enumerate(self.seq_trk or [None] * N_TRACKS):
            e = self._extremos_trk(t)
            trk.append(None if e is None else
                       toc.proximo_trk(e[0] - 1 if c is None else c, *e, PASSOS))
        self.seq_trk = trk
        if self.hist is None:
            self.hist = {}
        self.hist[self.n_steps] = self.seq
        for k in [k for k in self.hist if k < self.n_steps - 64]:
            del self.hist[k]

    def passo_do_track(self, tr):
        return self.passos_trk[tr] if self.passos_trk else self.passo

    def mover_playhead(self, n):
        """Vai para o step n desde o START (-1 = parado) e repinta so as
        colunas que mudaram, em qualquer linha (polimetria)."""
        self.n_steps = n
        antes = {self.passo} | set(self.passos_trk or [])
        if n < 0 or self.fase_incerta or self.seq is None:
            self.passo, self.passos_trk = -1, None    # sem fase: nada, nao um chute
        else:
            self.passo = self.seq[1]
            self.passos_trk = self._colunas_tocadas()
        depois = {self.passo} | set(self.passos_trk or [])
        if antes != depois and self.pagina == "steps":
            for c in sorted((antes | depois) - {-1}):
                self.pintar_coluna(c)
        self._avisar_passo()

    def _avisar_passo(self):
        if self.ao_passo is not None:
            try:
                self.ao_passo(self.info_passo())
            except Exception:
                pass

    def info_passo(self):
        return {"tocando": self.tocando, "passo": self.passo,
                "passos_trk": list(self.passos_trk) if self.passos_trk else None}

    # ── a variacao que toca (tocando.py) ────────────────────
    def _nota(self, nota):
        """Uma nota da maquina: o track dela entra no step em que caiu. Nota
        que chega no fim de um step (depois do ultimo pulso dele) e do
        proximo: a maquina manda a nota um pouco antes do pulso que o abre."""
        tr = toc.track_da_nota(nota)
        if tr is None:
            return
        if not self.tocando:
            # sem START: conta para adotar (o Controller ligou com a maquina
            # ja tocando - ou alguem tocou um pad parado; a adocao decide)
            if self.sem_adocao:
                return                               # desistiu: so o START/STOP volta
            if self.adocao is None:
                self.adocao = {"pulsos": 0, "n": 0, "pps": self.pulsos_por_step(),
                               "ouvidos": {}, "sem_nota": 0, "fora": 0}
            a = self.adocao
            # so nota na virada do step conta: a maquina tocando manda tudo
            # junto do pulso que abre o step; um pad tocado com ela parada cai
            # em qualquer lugar (revisao do PR #13: dois pads viravam "tocando")
            if 0 < a["pulsos"] < a["pps"]:
                a["fora"] += 1
                return
            n = a["n"] + (1 if a["pulsos"] >= a["pps"] else 0)
            a["ouvidos"].setdefault(n, set()).add(tr)
            a["sem_nota"] = 0
            return
        if self.ouvidos is None:
            self.ouvidos = {}
        n = self.n_steps + (1 if self.pulsos >= self.pps_step else 0)
        self.ouvidos.setdefault(n, set()).add(tr)

    def _pulso_de_adocao(self):
        """Um pulso de clock durante a adocao. Duas viradas de step com notas
        = a maquina esta tocando: o motor assume, com a fase a descobrir.
        32 steps sem nota = era um pad tocado parado: desiste."""
        a = self.adocao
        a["pulsos"] += 1
        if a["pulsos"] <= a["pps"]:
            return
        a["pulsos"] = 1
        a["n"] += 1
        a["sem_nota"] += 1
        if a["sem_nota"] > 32:
            self.adocao = None
            return
        com_notas = [k for k in a["ouvidos"] if k < a["n"]]
        if 2 * a["fora"] > len(com_notas):           # nota fora da grade demais: pad, nao a maquina
            self.adocao = None
            return
        if len(com_notas) >= 3:
            self.ouvidos = dict(a["ouvidos"])
            self.n_steps, self.pulsos, self.pps_step = a["n"], a["pulsos"], a["pps"]
            self.tocando, self.fase_incerta, self.adocao = True, True, None
            self.adotado, self.sem_nota_n = True, 0
            self.seq = self.seq_trk = self.hist = None   # nada da sessao de antes
            self.log("a TR-1000 ja estava tocando: procurando a fase pelas notas")
            self._avisar_passo()

    def _vars_da_chain(self):
        """{v: {track: [131]}} das variacoes da chain que o cache ja tem."""
        out = {}
        for v in self._chain():
            steps = {tr: self.cache.get((v, tr)) for tr in range(N_TRACKS)}
            if all(x is not None for x in steps.values()):
                out[v] = steps
        return out

    def _avaliar_tocando(self):
        """Depois de cada step. Com a sequencia conhecida (START), as notas
        CONFEREM: o estado do modelo com mais de toc.MAX_ERROS erros (fora
        os tracks que nenhum estado explica) -> procura o estado que explica
        o que soou; achou um so, ressincroniza; senao mostra "?" e segue a
        sequencia. Sem START (adotado), procura o estado ate achar."""
        if not self.tocando:
            return
        n = self.n_steps
        ouvidos = self.ouvidos or {}
        for k in [k for k in ouvidos if k < n - 64]:
            del ouvidos[k]
        janela = [(k, frozenset(ouvidos.get(k, ()))) for k in range(max(0, n - toc.JANELA), n)]
        vars_steps = self._vars_da_chain()
        chain, extremos = self._chain(), self._extremos()
        mudos = {t for t in range(N_TRACKS) if self.mudo_mascara >> t & 1}
        if self.adotado:
            # adotado sem START: 32 steps sem nota = a maquina parou (ou nunca
            # tocou) - o playhead nao segue andando sozinho
            self.sem_nota_n = 0 if ouvidos.get(n - 1) else self.sem_nota_n + 1
            if self.sem_nota_n > 32:
                self.tocando = self.adotado = self.fase_incerta = False
                self.tocando_var, self.ouvidos, self.seq = None, None, None
                self.mover_playhead(-1)
                self.pintar_botoes()
                return
        if any(v not in vars_steps for v in chain):
            return                                   # a chain ainda nao foi lida toda
        if self.fase_incerta:
            achado = toc.achar_estado(janela, vars_steps, chain, extremos, mudos)
            if achado is None:
                if n > 64:                           # 4 compassos sem estado unico
                    # desiste de vez ate um START/STOP (revisao do PR #13)
                    self.log("(!) nao achei a fase pelas notas - de STOP e START na maquina")
                    self.tocando = self.fase_incerta = self.adotado = False
                    self.ouvidos, self.sem_adocao, self.seq = None, True, None
                    self._avisar_passo()
                return
            self._iniciar_seq(toc.proximo(achado, chain, extremos), n)
            self.fase_incerta, self.tocando_var = False, self.seq[0]
            self.log(f"fase achada pelas notas: variacao {ts.VARIACOES_SERIAL[self.seq[0]]}, "
                     f"step {self.seq[1] + 1}")
            self.mover_playhead(n)
            self.pintar_botoes()
            return
        if self.seq is None:
            return
        # o modelo contra todos os pontos de partida, com os steps tocados
        # depois da ultima troca de FIRST/LAST: um track que nenhum estado
        # explica (o SD do F4.1b) fica de fora; os outros contam inteiros
        recente = [(k, o) for k, o in janela if k >= self.n_extremos]
        nova = self.seq[0]
        cands = (toc.analisar(recente, vars_steps, chain, extremos, mudos)
                 if len(recente) >= toc.MIN_STEPS_FASE else None)
        modelo = self.hist.get(n - 1) if self.hist else None
        if cands is not None and modelo is not None:
            if not toc.modelo_bate(cands, modelo):
                achado = toc.decidir(cands)
                if achado is not None:
                    estado = toc.proximo(achado, chain, extremos)
                    if estado != self.seq:
                        self.log(f"ressincronizei pelas notas: variacao "
                                 f"{ts.VARIACOES_SERIAL[estado[0]]}, step {estado[1] + 1}")
                        self._iniciar_seq(estado, n, manter_trk=True)
                        self.mover_playhead(n)
                    nova = self.seq[0]
                else:
                    nova = None                      # nao bate e nao da para saber: "?"
        if nova != self.tocando_var:
            self.tocando_var = nova
            self.pintar_botoes()

    def _ler_chain(self):
        """Uma variacao da chain por vez (a mais velha no cache), a cada
        releitura: o detector precisa dos steps de todas. Parada, nao le
        (revisao do PR #13: 14 leituras/s a toa com a chain inteira)."""
        if self.x_pattern is None or not (self.tocando or self.adocao is not None):
            return
        if self.lido_em is None:
            self.lido_em = {}
        mascara = self._c(campos.CAB_VARIACOES, 1)
        agora = time.time()
        velhas = [(self.lido_em.get(v, 0.0), v) for v in range(8)
                  if mascara >> v & 1 and v != self.variacao
                  and agora - self.lido_em.get(v, 0.0) > self.RELER_CHAIN_A_CADA]
        if not velhas:
            return
        _t, v = min(velhas)
        self.cache.update(self._ler_variacao(self.x_pattern, v))
        self.lido_em[v] = agora

    # ── clock (a porta MIDI comum) ──────────────────────────
    def _ler_clock(self):
        if not self.clk:
            return
        if self.modo_geral != MODO_ON:
            self.clk.iter_pending()          # drena e descarta
            return
        lote = 0
        for msg in self.clk.iter_pending():
            t = msg.type
            if t == "clock":
                if self.adocao is not None and not self.tocando:
                    self._pulso_de_adocao()
                    continue
                lote += 1
                continue
            lote = self._aplicar_pulsos(lote)  # transporte fecha o lote
            if (t == "note_on" and msg.velocity > 0
                    and msg.channel == tr1000.CANAL_PATTERN_PADRAO - 1):
                self._nota(msg.note)
                continue
            if t == "start":
                # start sem stop antes (recomeco): as colunas velhas sao
                # repintadas pelo mover_playhead (revisao do PR #4)
                # as notas do step 1 chegam ~3 ms ANTES do start (REFERENCIA
                # 7.3): ficaram na adocao, e sao do step 0
                antes = (self.adocao or {}).get("ouvidos", {})
                ultimo = max(antes) if antes else None
                pre = antes.get(ultimo, set()) if (self.adocao or {}).get("pulsos") == 0 else set()
                self.adocao, self.fase_incerta = None, False
                self.adotado = self.sem_adocao = False
                self.ouvidos = {0: set(pre)}
                self.pulsos, self.tocando = 0, True
                self.pps_step = self.pulsos_por_step()
                self._iniciar_seq()
                self.tocando_var = self.seq[0]
                self.mover_playhead(0)
                self.pintar_botoes()
            elif t == "continue":
                # retoma de onde parou: os pulsos do step ficaram guardados
                # (revisao do PR #8). Sem saber onde parou (parou procurando a
                # fase): procura de novo, em vez de por no step 1 (PR #13)
                self.tocando = True
                if self.n_parado < 0 or self.seq is None:
                    self.fase_incerta, self.adotado, self.ouvidos = True, True, {}
                    self.mover_playhead(0)
                else:
                    self.mover_playhead(self.n_parado)
            elif t == "stop":
                self.tocando = False
                self.n_parado = -1 if self.fase_incerta else self.n_steps
                self.fase_incerta, self.adocao, self.tocando_var = False, None, None
                self.adotado = self.sem_adocao = False
                self.mover_playhead(-1)
                self.pintar_botoes()
        self._aplicar_pulsos(lote)

    def _aplicar_pulsos(self, lote):
        """Os pulsos 1..p depois do start sao o step 0: o p-esimo ainda e dele,
        o p+1 abre o step 1 (revisao do PR #4). Contado step a step, e nao do
        total desde o start: a Scale trocada tocando vale a partir do proximo
        step, sem o playhead pular para um lugar calculado com a Scale nova."""
        if not (lote and self.tocando):
            return 0
        andou = False
        for _ in range(lote):
            self.pulsos += 1
            if self.pulsos > self.pps_step:
                self.pulsos = 1
                self.pps_step = self.pulsos_por_step()    # a Scale do step que abre
                # o detector olha cada step, mesmo num lote grande; a pintura e
                # o /passo, so o ultimo (revisao do PR #13)
                self.n_steps += 1
                andou = True
                self._avancar_seq()
                self._avaliar_tocando()
        if andou:
            self.mover_playhead(self.n_steps)
        return 0

    # ── as paginas PAR / PERF / ROUT ────────────────────────
    def valor_par(self, nome, tr, step):
        """O valor do parametro `nome` no step, do cache (None sem leitura)."""
        cache = self.cache.get((self.variacao, tr))
        if cache is None:
            return None
        if nome == "vel":
            for v in self.slots(tr, step)[:2]:
                if ts.slot_toca(v):
                    return ts.velocidade(v & ~campos.BIT_ALT)
            return None
        pos, mn, _mx = campos.CAMPOS_STEP[nome]
        v = cache[pos + step]
        return campos.com_sinal(v) if mn < 0 else v

    def cor_par(self, linha, step):
        """16 colunas x 8 niveis: a barra (ou o nivel, nos de escolha) do
        parametro do track escolhido, so nos steps que TOCAM (F4.6c: com as
        barras cheias tambem nos vazios, a pagina ficava toda amarela e trocar
        de track nao mudava nada). Step vazio: apagado; o toque nele ainda
        escreve (a VEL liga a nota)."""
        tr = self.par_track
        nome = campos.PAR_PARAMS[self.par_param]
        nivel = LINHAS - 1 - linha                       # de baixo para cima
        s = self.slots(tr, step)
        toca = ts.slot_toca(s[0]) or ts.slot_toca(s[1])
        cor = COR_PAR[nome]
        vazio = (2, 2, 2) if step % lp.STEPS_TEMPO == 0 and nivel == 0 else (0, 0, 0)
        if not toca:
            return vazio
        if nome == "alt":
            if tr < TRACKS_LAYER:
                return (0, 0, 0)                         # layer A/B nao tem ALT
            return cor if campos.eh_alt(s[0]) else _fraca(cor)
        n = campos.nivel_par(nome, self.valor_par(nome, tr, step))
        aceso = nivel == n if nome in campos.PAR_ESCOLHA else 0 <= nivel <= n
        return cor if aceso else vazio

    def definir_vel(self, tr, step, vel):
        """A velocity de um step pela pagina PAR: reescreve os slots que tocam
        (o ALT fica); num step vazio, liga os slots-alvo com ela."""
        if self.x_pattern is None:
            return
        cache = self.cache.get((self.variacao, tr))
        s = self.slots(tr, step)
        alvo = [i for i in (0, 1) if ts.slot_toca(s[i])] or self.slots_alvo(tr)
        for slot in alvo:
            alt = s[slot] & campos.BIT_ALT if ts.slot_toca(s[slot]) else 0
            novo = ts.nota(vel) | alt
            i = indice_do_slot(step, slot)
            if not self._escrever(bloco_de_steps(self.variacao), self.x_pattern, tr, i, novo):
                # o estado do slot na maquina e incerto: rele o track, como o
                # toque faz (revisao do PR #11)
                try:
                    self.cache[(self.variacao, tr)] = self._ler(
                        bloco_de_steps(self.variacao), self.x_pattern, tr, ts.INDICE_STEPS, N_SLOTS)
                except ERROS_DE_LEITURA:
                    pass
                return
            if cache is not None:
                cache[i - ts.INDICE_STEPS] = novo

    def tocar_par(self, linha, step):
        tr = self.par_track
        nome = campos.PAR_PARAMS[self.par_param]
        if nome == "alt":
            self.definir_alt(tr, step, not campos.eh_alt(self.slots(tr, step)[0]))
            return                                       # o definir_alt ja repinta
        else:
            valor = campos.NIVEIS_PAR[nome][LINHAS - 1 - linha]
            if nome == "vel":
                self.definir_vel(tr, step, valor)
            else:
                self.definir_campo_step(tr, step, nome, valor)
        self.pintar_coluna(step)

    def _c_var(self, pos, padrao):
        return self._c(pos + self.variacao, padrao)

    def cor_perf(self, linha, step):
        if linha == PERF_MUTE:
            if step < N_TRACKS:
                return (lp.COR_MUDO if self.mudo_mascara >> step & 1
                        else _fraca(lp.COR_SOANDO, 0.25))
            if step in PERF_FILLS:
                n = PERF_FILLS.index(step)
                return (127, 127, 127) if self._c(campos.CAB_FILL, 0) == n else (12, 12, 12)
            return (0, 0, 0)
        if linha == PERF_CHAIN and step < 8:
            na_chain = self._c(campos.CAB_VARIACOES, 1) >> step & 1
            return (0, 40, 127) if na_chain else (0, 4, 14)
        if linha == PERF_LOOP:                           # da tela tambem (loop_segurados)
            return (127, 127, 127) if step in self.loop_segurados else (6, 6, 6)
        if linha == PERF_LAST:
            first = self._c_var(campos.CAB_FIRST_VAR, 0)
            last = self._c_var(campos.CAB_LAST_VAR, PASSOS - 1)
            if step == last:
                return (127, 60, 0)
            return (30, 12, 0) if first <= step < last else (0, 0, 0)
        if linha == PERF_SCALE and step < len(campos.SCALES):
            return (127, 127, 127) if self._c(campos.CAB_SCALE, 2) == step else (12, 12, 12)
        return (0, 0, 0)

    def tocar_perf(self, linha, step):
        if linha == PERF_MUTE:
            if step < N_TRACKS:
                self.alternar_mudo(step)
            elif step in PERF_FILLS:
                self.definir_fill(PERF_FILLS.index(step))
        elif linha == PERF_CHAIN and step < 8:
            # segurando outra variacao: soma/tira da chain (como no painel);
            # sozinha: toca so ela
            outra = any(l == PERF_CHAIN for l, _s in self.segurados)
            nova = 1 << step
            if outra:
                # a mascara FRESCA: o painel pode ter mudado a chain (o mesmo
                # cuidado do alternar_mudo; revisao do PR #11)
                try:
                    nova ^= self._ler(campos.CAB, self.x_pattern, 0,
                                      campos.INI_CAB + campos.CAB_VARIACOES, 1)[0]
                except ERROS_DE_LEITURA as e:
                    self.log(f"(!) nao li a chain: {e}")
                    nova = 0
            if nova:
                self.definir_variacoes(nova)
            self.segurados = self.segurados | {(linha, step)}
        elif linha == PERF_LOOP:
            self.segurados = self.segurados | {(linha, step)}
            self.definir_loop(True, step)
        elif linha == PERF_LAST:
            if step >= self._c_var(campos.CAB_FIRST_VAR, 0):   # FIRST depois do LAST: nao
                self._cab(campos.CAB_LAST_VAR + self.variacao, step)    # so o LAST (revisao do PR #11)
        elif linha == PERF_SCALE and step < len(campos.SCALES):
            self.definir_scale(step)
        self.pintar()

    def alvo_rout(self, linha, step):
        """(id do parametro, valor) do pad da pagina ROUT, ou None - um lugar
        so para o desenho da pagina (revisao do PR #11)."""
        if linha < len(COR_ROTA) and step < len(FONTES_ROTA):
            return f"rota.{FONTES_ROTA[step]}", linha
        if linha in (ROUT_SC1, ROUT_SC2):
            n = step + (16 if linha == ROUT_SC2 else 0)
            return ("sc.source", n) if n < len(parametros.SC_FONTES) else None
        if linha == ROUT_CHAVES:
            for cols, id in ((ROUT_POLARITY, "sc.polarity"), (ROUT_HLD, "sc.hld_mode")):
                if step in cols:
                    return id, cols.index(step)
        return None

    def cor_rout(self, linha, step):
        alvo = self.alvo_rout(linha, step)
        if alvo is None:
            return (0, 0, 0)
        id, valor = alvo
        aceso = self.kit_valores.get(id) == valor
        if id.startswith("rota."):
            return COR_ROTA[linha] if aceso else _fraca(COR_ROTA[linha], 0.1)
        if id == "sc.source":
            return (127, 127, 127) if aceso else (10, 10, 10)
        return (127, 60, 0) if aceso else (14, 6, 0)

    def tocar_rout(self, linha, step):
        alvo = self.alvo_rout(linha, step)
        if alvo is not None:
            self.definir_param(*alvo)
        self.pintar()

    def tocar_pad(self, linha, step):
        {"par": self.tocar_par, "perf": self.tocar_perf,
         "rout": self.tocar_rout}[self.pagina](linha, step)

    def _soltar_segurados(self):
        for linha, step in sorted(self.segurados):
            if linha == PERF_LOOP and self.pagina == "perf":
                self.definir_loop(False, step)
        self.segurados = frozenset()

    def soltar_pad(self, linha, step):
        if (linha, step) not in self.segurados:
            return
        self.segurados = self.segurados - {(linha, step)}
        if self.pagina == "perf" and linha == PERF_LOOP:
            self.definir_loop(False, step)
            self.pintar()

    # ── o que a tela (e o layout A) escreve ─────────────────
    # Tudo passa pela conexao e pelo portao (campos.py / parametros.py). Uma
    # falha loga e rele - nunca repete sozinha.
    def _escrever(self, bloco, x, y, indice, valor):
        if self.conexao is None:
            self.log("(!) ligue (ON) antes")
            return False
        try:
            self.conexao.escrever(bloco, x, y, indice, valor)
            return True
        except ERROS_DE_LEITURA as e:
            self.log(f"(!) escrita recusada/sem resposta: {e}")
            return False

    def alternar_step(self, track, step):
        """O clique na grade da tela: o mesmo toque do pad, num track qualquer,
        e a coluna repintada no Launchpad (revisao do PR #7: o pad ficava
        apagado, e a releitura nao via mudanca no cache para repintar)."""
        self.alternar_track(track, step)
        self.pintar_coluna(step)

    def definir_campo_step(self, track, step, nome, valor):
        """PROB / SUB / CYCLE / START de um step da variacao mostrada."""
        c = campos.campo_step(nome, self.variacao, track, step)
        v = campos.u32(valor) if c.minimo < 0 else valor
        if self.x_pattern is not None and self._escrever(c.bloco, self.x_pattern, c.y, c.indice, v):
            cache = self.cache.get((self.variacao, track))
            if cache is not None and c.indice - ts.INDICE_STEPS < len(cache):
                cache[c.indice - ts.INDICE_STEPS] = v

    def definir_alt(self, track, step, ligado):
        """O som ALT no slot 0 de um track simples (RS..RC): bit 23 da nota."""
        if track < TRACKS_LAYER or self.x_pattern is None:
            return
        atual = self.slots(track, step)[0]
        if not ligado and not ts.slot_toca(atual):
            return                                   # nada a tirar: nao liga uma nota
        base = atual & ~campos.BIT_ALT if ts.slot_toca(atual) else ts.nota(VELOCIDADES[self.vel_idx])
        novo = base | campos.BIT_ALT if ligado else base
        i = indice_do_slot(step, 0)
        if self._escrever(bloco_de_steps(self.variacao), self.x_pattern, track, i, novo):
            cache = self.cache.get((self.variacao, track))
            if cache is not None:
                cache[i - ts.INDICE_STEPS] = novo
            self.pintar_coluna(step)

    def alternar_mudo(self, track):
        """Le a mascara fresca antes de inverter (corrida com o painel - o
        mesmo cuidado do alternar_mudo do tr8s-grid)."""
        if self.conexao is None:
            return
        try:
            atual = self._ler(campos.B3, 0, 0, campos.INI_B3 + campos.B3_MUTE, 1)[0]
        except ERROS_DE_LEITURA as e:
            self.log(f"(!) nao li o mute: {e}")
            return
        novo = atual ^ (1 << track)
        if self._escrever(campos.B3, 0, 0, campos.INI_B3 + campos.B3_MUTE, novo):
            self.mudo_mascara = novo
            self.pintar_botoes()

    def _cab(self, pos, valor):
        if self.x_pattern is not None and self._escrever(
                campos.CAB, self.x_pattern, 0, campos.INI_CAB + pos, valor):
            if self.cab is not None:
                self.cab[pos] = valor

    def definir_variacoes(self, mascara):
        """A chain: a mascara de variacoes do cabecalho (A = 1, B = 2...)."""
        self._cab(campos.CAB_VARIACOES, mascara)

    def definir_tempo(self, x100):
        """O BPM x 100 (12450 = 124,50): o tempo do pattern (cabecalho [16]) e
        o atual (bloco 3 [36]), os dois que o knob TEMPO muda (c5d)."""
        self._cab(campos.CAB_TEMPO, x100)
        if self._escrever(campos.B3, 0, 0, campos.INI_B3 + campos.B3_TEMPO, x100):
            if self.b3 is not None:
                self.b3[campos.B3_TEMPO] = x100

    def definir_scale(self, n):
        self._cab(campos.CAB_SCALE, n)

    def definir_fill(self, n):
        self._cab(campos.CAB_FILL, n)

    def definir_extremos_var(self, v, first, last):
        self._cab(campos.CAB_FIRST_VAR + v, first)
        self._cab(campos.CAB_LAST_VAR + v, last)

    def definir_extremos_track(self, track, first, last):
        """FIRST/LAST proprios do track; None, None limpa (volta ao da variacao)."""
        if first is None:
            self._cab(campos.CAB_TRK_SW + track, 0)
            return
        self._cab(campos.CAB_FIRST_TRK + track, first)
        self._cab(campos.CAB_LAST_TRK + track, last)
        self._cab(campos.CAB_TRK_SW + track, 1)

    def definir_loop(self, ligado, step=None):
        """STEP LOOP: o modo, e um step 'segurado' (a tela segura por clique).

        F3.4.6 (12/10/2026): o [150] AGE - com ele em 0, segurar um step deixa a
        maquina em silencio -, mas o LED do painel nao acende. Entao segurar
        um step liga o modo antes, e soltar devolve o [150] de antes."""
        modo = campos.INI_B3 + campos.B3_LOOP
        if step is None:
            self._escrever(campos.B3, 0, 0, modo, int(bool(ligado)))
            self.loop_antes = None                   # o modo e do Luan agora
            return
        i = campos.INI_B3 + campos.B3_LOOP_STEP + step
        if ligado:
            if self.conexao is None:
                self.log("(!) ligue (ON) antes")
                return
            if not self.loop_segurados:
                try:
                    atual = self._ler(campos.B3, 0, 0, modo, 1)[0]
                except ERROS_DE_LEITURA as e:
                    self.log(f"(!) nao li o STEP LOOP: {e}")
                    return
                if not atual and not self._escrever(campos.B3, 0, 0, modo, 1):
                    return
                self.loop_antes = atual
            if self._escrever(campos.B3, 0, 0, i, 1):
                self.loop_segurados = self.loop_segurados | {step}
        else:
            if not self._escrever(campos.B3, 0, 0, i, 0):
                return                               # segue segurado: o modo fica (revisao do PR #8)
            self.loop_segurados = self.loop_segurados - {step}
            if not self.loop_segurados and self.loop_antes is not None:
                if not self.loop_antes:
                    self._escrever(campos.B3, 0, 0, modo, 0)
                self.loop_antes = None

    def _resolver(self, id, seletores=None):
        """(Parametro, endereco) de um parametro agora (type/sync lidos), ou None.
        A MESMA regra dos knobs (controladoras.resolver); `seletores` e o cache
        de uma passada do ler_kit, para ler cada TYPE/SYNC uma vez so."""
        cache = {} if seletores is None else seletores

        def ler_seletor(sid):
            if sid not in cache:
                cache[sid] = self._ler(*parametros.endereco(parametros.SELETORES[sid], self.x_kit), 1)[0]
            return cache[sid]
        return controladoras.resolver(id, self.x_pattern, self.x_kit, ler_seletor)

    def definir_param(self, id, valor):
        """Um parametro do mixer/efeitos pela tela - o mesmo id dos knobs. Solta
        o pickup daquele knob: ele volta a 'pegar no caminho' do valor novo."""
        try:
            e = self._resolver(id)
        except ERROS_DE_LEITURA as exc:
            self.log(f"(!) {id}: nao li o type ({exc})")
            return
        if e is None:
            self.log(f"(!) {id}: inativo agora (type sem esse parametro, ou kit incerto)")
            return
        p, end = e
        if not p.minimo <= valor <= p.maximo:
            self.log(f"(!) {id}: {valor} fora de {p.minimo}..{p.maximo}")
            return
        if self._escrever(*end, valor):
            self.kit_valores[id] = valor
            if self.pickup is not None:
                self.pickup.estado.pop(id, None)
                if id in parametros.SELETORES:
                    self.pickup.seletores[id] = valor

    def ids_do_kit(self):
        return (list(parametros.TABELA) + list(parametros.POR_TIPO)
                + list(parametros.EXTRAS))

    def ler_kit(self, ids=None):
        """Todos os parametros da tabela (ou so `ids`), um pedido cada (~0,25 ms
        cada: uma foto de 439 levou 0,1 s). Os dependentes de type no type
        atual. So `ids`: atualiza esses e mantem o resto."""
        if self.conexao is None or self.x_pattern is None:
            return
        novos, sels = ({}, {}) if ids is None else (dict(self.kit_valores), {})
        for id in (self.ids_do_kit() if ids is None else ids):
            try:
                e = self._resolver(id, sels)
                if e is not None:
                    novos[id] = self._ler(*e[1], 1)[0]
            except cs.ErroConexao as exc:
                # a serial caiu: parar JA (revisao do PR #7 - seguir dava 1 s de
                # espera por id, minutos com o motor travado)
                self.log(f"(!) leitura do kit interrompida: {exc}")
                return
            except PermissionError:
                continue
        # os seletores (o SYNC do LFO, do FLANGER e do PHASER): a tela usa para
        # dar o nome certo ao knob que depende deles
        if self.x_kit is not None and ids is None:
            for sid, p in parametros.SELETORES.items():
                if sid not in novos:
                    try:
                        novos[sid] = sels[sid] if sid in sels else \
                            self._ler(*parametros.endereco(p, self.x_kit), 1)[0]
                    except ERROS_DE_LEITURA:
                        pass
        self.kit_valores = novos

    # ── a foto da sessao (so no app) ────────────────────────
    def foto_sessao(self, motivo):
        """A foto inteira de uma vez (os testes e quem precisar dela ja). No
        motor ao vivo ela anda aos pedacos: pedir_foto + o tick."""
        nome = None
        for nome in self._passos_da_foto(motivo):
            pass
        return nome

    def pedir_foto(self, motivo, atraso=0.0):
        """A foto aos pedacos, uma variacao por tick (revisao do PR #8: de uma
        vez so, ~130 leituras travavam pads e knobs). A da troca de pattern
        espera o pattern parar de mudar (folhear nao enfileira uma foto por
        pattern)."""
        self.foto_em = time.time() + atraso
        self.foto_motivo = motivo
        self.foto_passos = None

    def _andar_foto(self, agora):
        if self.foto_motivo is None or agora < self.foto_em:
            return
        if self.foto_passos is None:
            self.foto_passos = self._passos_da_foto(self.foto_motivo)
        try:
            nome = next(self.foto_passos)
        except StopIteration:
            nome = ""
        if nome is not None:                         # acabou (bem ou mal)
            self.foto_motivo = self.foto_passos = None

    def _passos_da_foto(self, motivo):
        """Tudo o que o Controller sabe ler do pattern e do kit, num JSON em
        DIR_SESSOES (pedido do Luan, 12/10/2026: 'salvar sessao' fica SO no
        app; o reload e no painel). So LEITURAS, dentro das faixas do portao.
        Os valores vao CRUS (u32), com o indice do primeiro de cada lista: e o
        que uma restauracao futura (decisao do Luan) precisaria. Gerador: None
        a cada variacao lida; no fim, o nome do arquivo ("" se falhou)."""
        if self.conexao is None or self.x_pattern is None:
            yield ""
            return
        x = self.x_pattern
        steps, acentos = {}, {}
        try:
            for v, nome_v in enumerate(ts.VARIACOES_SERIAL):
                if self.x_pattern != x:              # trocou no meio: foto velha
                    yield ""
                    return
                lido = self._ler_variacao(x, v)
                steps[nome_v] = {ts.TRACKS_SERIAL[tr]: lido[(v, tr)] for tr in range(N_TRACKS)}
                try:
                    acentos[nome_v] = self._ler(ts.BLOCO_VAR0 + ts.BLOCOS_POR_VAR * v, x, 0,
                                                campos.INI_ACC, 1)[0]
                except PermissionError:
                    pass                             # fora das faixas: fica sem
                yield None
            if not self.kit_valores:
                self.ler_kit()
        except ERROS_DE_LEITURA as e:
            self.log(f"(!) a foto da sessao falhou: {e}")
            yield ""
            return
        foto = {
            "versao": 1, "quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "motivo": motivo,
            "pattern": ts.nome_do_pattern(x), "x_pattern": x, "x_kit": self.x_kit,
            "tempo": (self.b3[ts.OFF_TEMPO_ATUAL] / 100) if self.b3 else None,
            "cabecalho": {"bloco": campos.CAB, "indice": campos.INI_CAB, "valores": list(self.cab or [])},
            "bloco3": {"bloco": campos.B3, "indice": campos.INI_B3, "valores": list(self.b3 or [])},
            "steps": {"indice": ts.INDICE_STEPS, "por_variacao": steps},
            "acentos": {"indice": campos.INI_ACC, "por_variacao": acentos},
            "kit": dict(self.kit_valores),
        }
        # o motivo no nome: as do botao nunca saem na limpeza, e duas fotos no
        # mesmo segundo nao se sobrescrevem (revisao do PR #8)
        # milissegundos no nome, somando 1 se ja existe: a ordem alfabetica
        # continua a do tempo (a limpeza apaga as primeiras)
        agora = time.time()
        ms = int(agora * 1000) % 1000
        try:
            os.makedirs(DIR_SESSOES, exist_ok=True)
            while True:
                nome = (f"{time.strftime('%Y-%m-%d-%H%M%S', time.localtime(agora))}{ms:03d}"
                        f"-{foto['pattern']}-{motivo}.json")
                if not os.path.exists(os.path.join(DIR_SESSOES, nome)) or ms >= 999:
                    break
                ms += 1
            with open(os.path.join(DIR_SESSOES, nome), "w", encoding="utf-8") as f:
                json.dump(foto, f)
            autos = sorted(a for a in os.listdir(DIR_SESSOES)
                           if a.endswith(".json") and "-botao" not in a)
            for a in autos[:-MAX_SESSOES]:
                os.remove(os.path.join(DIR_SESSOES, a))
        except OSError as e:
            self.log(f"(!) nao gravei a foto da sessao: {e}")
            yield ""
            return
        self.ultima_sessao = nome
        self.log(f"sessao salva no app: {nome} ({motivo})")
        yield nome

    # ── trocar de pattern (Program Change) ──────────────────
    def trocar_pattern(self, x):
        """Pede o pattern x a maquina por Program Change no Pattern Ch., na
        porta 'TR-1000' (MIDI chart, REFERENCIA 2.3 - nao medido ate o F4).
        Nao passa pela serial: e o pedido do Luan de 12/10/2026. O motor
        segue o pattern sozinho, pelo bloco 3 [2] (a releitura)."""
        if not 0 <= x < cs.N_PATTERNS:
            return
        if not self._program_change(tr1000.CANAL_PATTERN_PADRAO, x, "troca de pattern"):
            return
        self.log(f"pattern {ts.nome_do_pattern(x)} pedido (Program Change {x}, "
                 f"canal {tr1000.CANAL_PATTERN_PADRAO})")
        self.proxima_releitura = 0.0

    def _program_change(self, canal, n, para_que):
        """Um Program Change na porta 'TR-1000' (canal 1..16). As DUAS unicas
        escritas fora da serial: o PTN e o KIT, ambas so com o Luan pedindo."""
        if self.pc_out is None:
            p = porta_exata(tr1000.PORTA_COMUM, entradas=False)
            if not p:
                self.log(f"(!) porta MIDI 'TR-1000' de saida nao achada - sem {para_que}")
                return False
            self.pc_out = SaidaMIDI(*p)
        self.pc_out.send_bytes([0xC0 | (canal - 1), n])
        return True

    def trocar_kit(self, n):
        """Pede o kit n (0-based, a ordem da lista 0c = ritmos.KITS) por Program
        Change no Kit Ch. (MIDI chart: 'Only KIT switches'). Aprovado pelo
        Luan em 13/10/2026; NAO MEDIDO: o numero do kit = o PC, o canal 1 e o
        efeito no bloco 3 [2..4] sao o ROTEIRO-F5. So kit com nome."""
        if not 0 <= n < len(ritmos.KITS) or not ritmos.KITS[n]:
            self.log(f"(!) kit {n} fora da lista - nada enviado")
            return
        if not self._program_change(tr1000.CANAL_KIT_PADRAO, n, "troca de kit"):
            return
        self.log(f"kit {n + 1} {ritmos.KITS[n]} pedido (Program Change {n}, "
                 f"canal {tr1000.CANAL_KIT_PADRAO})")
        self.proxima_releitura = 0.0

    # ── os ritmos prontos (a aba Ritmos) ────────────────────
    # A escrita de um ritmo anda aos pedacos, como a foto: ate
    # ESCRITAS_POR_TICK passos do gerador por tick, para os pads e os knobs
    # seguirem respondendo. Cada passo e uma leitura ou uma escrita, e cada
    # escrita passa pelo portao. Antes de escrever: a foto da sessao (so
    # leitura). Depois: o diario para o Desfazer (decisao do Luan, 13/10/2026).
    ESCRITAS_POR_TICK = 12
    ESPERA_KIT = 0.6                            # s depois do PC do kit, antes do mix
    ritmo_passos = None                         # o gerador
    ritmo_estado = None                         # o que a tela mostra
    ritmo_diario = None                         # o que o Desfazer reescreve

    def escrever_ritmo(self, id, auto_bpm=False, auto_kit=False, mix=False):
        if self.conexao is None or self.x_pattern is None:
            self.log("(!) ligue (ON) antes de escrever um ritmo")
            return
        if self.ritmo_passos is not None:
            self.log("(!) ja tem um ritmo sendo escrito")
            return
        r = ritmos.POR_ID[id]
        self.ritmo_estado = {"id": id, "nome": r["nome"], "fase": "foto", "feito": 0,
                             "total": 0, "avisos": []}
        self.ritmo_passos = self._passos_do_ritmo(r, auto_bpm, auto_kit, mix)

    def desfazer_ritmo(self):
        if self.conexao is None:
            self.log("(!) ligue (ON) antes")
            return
        if self.ritmo_passos is not None or not self.ritmo_diario:
            return
        d = self.ritmo_diario
        self.ritmo_estado = {"id": d["id"], "nome": d["nome"], "fase": "desfazendo",
                             "feito": 0, "total": 0, "avisos": []}
        self.ritmo_passos = self._passos_do_desfazer(d)

    def _andar_ritmo(self):
        if self.ritmo_passos is None:
            return
        for _ in range(self.ESCRITAS_POR_TICK):
            try:
                next(self.ritmo_passos)
            except StopIteration:
                self.ritmo_passos = None
                return

    def _ritmo_falhou(self, msg):
        self.ritmo_estado["fase"] = "falhou"
        self.ritmo_estado["avisos"].append(msg)
        self.log(f"(!) ritmo: {msg}")

    def _avisos_do_ritmo(self, lidos, acentos):
        out = []
        for v in sorted(lidos):
            nome_v = ts.VARIACOES_SERIAL[v]
            for tr in range(N_TRACKS):
                d = toc.direcao_de(lidos[v][tr])
                if d:
                    out.append(f"{ts.TRACKS_SERIAL[tr]} em {campos.DIRECOES[d]} na {nome_v}: "
                               "toca diferente (o DIRECTION e so leitura; mude no painel)")
            if acentos.get(v):
                out.append(f"a {nome_v} tem accent: ele continua (o accent e pelo painel)")
        return out

    def _escrever_diario(self, escritas, est, feitas, x=None):
        """Escreve uma lista de ritmos.Escrita, um passo do gerador cada (use
        com yield from), anotando em `feitas` as que a maquina confirmou - na
        hora, para o Desfazer valer mesmo se o gerador for largado no meio
        (OFF). -> True se foram todas. Para na primeira falha ou se o pattern
        x saiu da tela: nunca repete."""
        for e in escritas:
            if x is not None and self.x_pattern != x:
                self._ritmo_falhou("o pattern mudou no meio - parei")
                return False
            if not self._escrever(e.bloco, e.x, e.y, e.indice, e.valor):
                self._ritmo_falhou(f"escrita recusada/sem resposta em {e.bloco}/{e.y}/{e.indice}")
                return False
            feitas.append(e)
            est["feito"] += 1
            yield
        return True

    def _passos_do_ritmo(self, r, auto_bpm, auto_kit, mix):
        est = self.ritmo_estado
        x = self.x_pattern
        # 1. a foto (so leitura, um JSON no app). Sem foto, nada e escrito
        foto = None
        for foto in self._passos_da_foto("ritmo"):
            if foto is None:
                yield
        if not foto:
            self._ritmo_falhou("a foto da sessao falhou - nada escrito")
            return
        if self.x_pattern != x:
            self._ritmo_falhou("o pattern mudou durante a foto - nada escrito")
            return
        # 2. o kit, antes: o mix e um parametro do kit que vai tocar
        kit_antes = self.x_kit
        if auto_kit:
            est["fase"] = "kit"
            self.trocar_kit(ritmos.KIT_POR_NOME[r["kit"]])
            ate = time.time() + self.ESPERA_KIT
            while time.time() < ate:
                yield
            try:
                self.reler()
            except ERROS_DE_LEITURA as e:
                self._ritmo_falhou(f"nao reli depois do kit: {e}")
                return
        # 3. o que a maquina tem agora: as variacoes, o accent, o cabecalho
        est["fase"] = "lendo"
        lidos, acentos = {}, {}
        try:
            for v in ritmos.expandir(r):
                lido = self._ler_variacao(x, v)
                lidos[v] = {tr: lido[(v, tr)] for tr in range(N_TRACKS)}
                try:
                    acentos[v] = self._ler(ts.BLOCO_VAR0 + ts.BLOCOS_POR_VAR * v, x, 0,
                                           campos.INI_ACC, 1)[0]
                except PermissionError:
                    pass
                yield
            cab = self._ler(campos.CAB, x, 0, *cs.faixa_do_bloco(campos.CAB, x, 0))
            escritas = ritmos.escritas_do_ritmo(r, x, lidos, cab)
            if auto_bpm:
                x100 = round(r["bpm"] * 100)
                tempo_b3 = self._ler(campos.B3, 0, 0, campos.INI_B3 + campos.B3_TEMPO, 1)[0]
                for bloco, xx, i, antigo in ((campos.CAB, x, campos.INI_CAB + campos.CAB_TEMPO,
                                              cab[campos.CAB_TEMPO]),
                                             (campos.B3, 0, campos.INI_B3 + campos.B3_TEMPO,
                                              tempo_b3)):
                    if antigo != x100:
                        escritas.append(ritmos.Escrita(bloco, xx, 0, i, x100, antigo))
        except ERROS_DE_LEITURA as e:
            self._ritmo_falhou(f"leitura falhou: {e} - nada escrito")
            return
        est["avisos"] = self._avisos_do_ritmo(lidos, acentos)
        com_mix = bool(mix and r.get("mix"))
        est["total"] = len(escritas) + (len(r["mix"]) if com_mix else 0)
        # 4. as escritas do pattern, so a diferenca
        est["fase"] = "escrevendo"
        self.ritmo_diario = {"id": r["id"], "nome": r["nome"], "x": x, "escritas": [],
                             "params": [], "kit": kit_antes if auto_kit else None}
        feitas = self.ritmo_diario["escritas"]
        ok = yield from self._escrever_diario(escritas, est, feitas, x)
        # o cache: as variacoes mudaram - a releitura e a chain releem
        for v in lidos:
            for tr in range(N_TRACKS):
                if v != self.variacao:
                    self.cache.pop((v, tr), None)
        self.lido_em = {}
        self.proxima_releitura = 0.0
        if not ok:
            return
        # 5. o mix (os sends), com o valor de antes lido na hora
        if com_mix:
            if self.x_kit is None:
                est["avisos"].append("kit incerto (bloco 3 [2..4] diferentes): o mix nao foi escrito")
            for id, valor in r["mix"].items():
                if self.x_kit is None:
                    break
                try:
                    e = self._resolver(id)
                    if e is None:
                        est["avisos"].append(f"{id}: inativo agora - nao escrito")
                        continue
                    _p, end = e
                    antigo = self._ler(*end, 1)[0]
                except ERROS_DE_LEITURA as exc:
                    est["avisos"].append(f"{id}: nao li ({exc}) - nao escrito")
                    continue
                if self._escrever(*end, valor):
                    self.ritmo_diario["params"].append((id, end, antigo))
                    self.kit_valores[id] = valor
                est["feito"] += 1
                yield
        est["fase"] = "pronto"
        self.log(f"ritmo {r['nome']} escrito no {ts.nome_do_pattern(x)}: "
                 f"{len(feitas)} escritas ({est['total'] - len(feitas)} de mix)")

    def _passos_do_desfazer(self, d):
        est = self.ritmo_estado
        escritas = ritmos.desfazer(d["escritas"])
        if self.x_pattern != d["x"]:
            # o tempo atual (bloco 3) e do pattern que esta na tela agora
            escritas = [e for e in escritas if e.bloco != campos.B3]
        # um valor antigo que o portao nao aceita (fora da faixa medida) nao
        # volta - avisa, em vez de parar o resto no meio
        fora = [e for e in escritas if not cs.escrita_permitida(e.bloco, e.x, e.y, e.indice, e.valor)]
        if fora:
            escritas = [e for e in escritas if e not in fora]
            est["avisos"].append(f"{len(fora)} valor(es) antigo(s) fora do portao nao voltaram: "
                                 + ", ".join(f"{e.bloco}/{e.y}/{e.indice}={e.valor}" for e in fora[:4]))
        est["total"] = len(escritas) + len(d["params"])
        for id, end, antigo in reversed(d["params"]):
            if self._escrever(*end, antigo):
                self.kit_valores[id] = antigo
            est["feito"] += 1
            yield
        ok = yield from self._escrever_diario(escritas, est, [])
        if ok and d["kit"] is not None:
            self.trocar_kit(d["kit"])
        self.cache = {k: v for k, v in self.cache.items() if k[0] == self.variacao}
        self.lido_em = {}
        self.proxima_releitura = 0.0
        if ok:
            self.ritmo_diario = None
            est["fase"] = "desfeito"
            self.log(f"ritmo {d['nome']} desfeito")

    # ── o espelho para a tela ───────────────────────────────
    def estado(self):
        """Uma foto do motor para a tela, so com tipos de JSON. None se o motor
        esta ocupado (le a maquina): a tela pula um quadro em vez de esperar."""
        if not self.lock.acquire(blocking=False):
            return None
        try:
            v = self.variacao
            grade = []
            for tr in range(N_TRACKS):
                c = self.cache.get((v, tr))
                lido = c is not None
                cheio = list(c or []) + [0] * (ts.N_STEPS_BLOCO - len(c or []))
                linha = []
                for s in range(16):
                    a, b = cheio[s * 4], cheio[s * 4 + 1]
                    cel = {"a": ts.slot_toca(a), "b": ts.slot_toca(b),
                           "vel": ts.velocidade(a & ~campos.BIT_ALT if ts.slot_toca(a) else b),
                           "alt": campos.eh_alt(a)}
                    for nome, (pos, mn, _mx) in campos.CAMPOS_STEP.items():
                        x = cheio[pos + s]
                        cel[nome] = None if not lido else (campos.com_sinal(x) if mn < 0 else x)
                    linha.append(cel)
                grade.append(linha)
            cab = self.cab or []

            def c(pos, padrao=None):
                return cab[pos] if pos < len(cab) else padrao
            return {
                "ligado": self.modo_geral == MODO_ON,
                "modo": (self.estilo_standby if self.modo_geral == MODO_STANDBY
                         else self.modo_geral),
                "pattern": ts.nome_do_pattern(self.x_pattern) if self.x_pattern is not None else None,
                "x_pattern": self.x_pattern, "x_kit": self.x_kit,
                "tempo": (self.b3[ts.OFF_TEMPO_ATUAL] / 100) if self.b3 else None,
                "variacao": v, "velocidade_idx": self.vel_idx, "modo_layer": self.modo_layer,
                "banco": self.banco, "passo": self.passo, "tocando": self.tocando,
                "pagina": self.pagina,
                "direcoes": self.direcoes(),
                "tocando_var": self.tocando_var, "fase_incerta": self.fase_incerta,
                "passos_trk": list(self.passos_trk) if self.passos_trk else None,
                "loop_segurados": sorted(self.loop_segurados),
                "ultima_sessao": self.ultima_sessao,
                "ritmo": dict(self.ritmo_estado, avisos=list(self.ritmo_estado["avisos"]))
                if self.ritmo_estado else None,
                "ritmo_desfazer": self.ritmo_diario["nome"]
                if self.ritmo_diario and self.ritmo_passos is None else None,
                "grade": grade,
                "acentos": campos.acentos(self.acc_mascara),
                "mudos": campos.mudos(self.mudo_mascara),
                "variacoes": c(campos.CAB_VARIACOES, 1),
                "scale": c(campos.CAB_SCALE, 2), "fill": c(campos.CAB_FILL, 0),
                "first_var": [c(campos.CAB_FIRST_VAR + i, 0) for i in range(campos.N_VARS)],
                "last_var": [c(campos.CAB_LAST_VAR + i, 15) for i in range(campos.N_VARS)],
                "first_trk": [c(campos.CAB_FIRST_TRK + t, 0) for t in range(N_TRACKS)],
                "last_trk": [c(campos.CAB_LAST_TRK + t, 15) for t in range(N_TRACKS)],
                "trk_sw": [c(campos.CAB_TRK_SW + t, 0) for t in range(N_TRACKS)],
                "loop": bool(self.b3[campos.B3_LOOP]) if self.b3 else False,
                "kit": dict(self.kit_valores),
                "launchpads": bool(self.lp_out),
                "controladoras": sorted(self.ctl.portas) if self.ctl else [],
            }
        finally:
            self.lock.release()

    def campos_do_step(self, track, step):
        """PROB/SUB/CYCLE/START de um step (para o editor da tela)."""
        cache = self.cache.get((self.variacao, track)) or []
        out = {}
        for nome, (pos, mn, _mx) in campos.CAMPOS_STEP.items():
            i = pos + step
            v = cache[i] if i < len(cache) else None
            out[nome] = campos.com_sinal(v) if (v is not None and mn < 0) else v
        return out

    # ── as controladoras de knobs ───────────────────────────
    def _ler_controladoras(self, agora):
        if self.ctl is None:
            return
        knobs = self.ctl.ler()
        if self.pickup is None or self.modo_geral != MODO_ON or self.conexao is None:
            return
        if knobs and self.x_pattern is not None:
            self.pickup.mover(knobs, self.x_pattern, self.x_kit, agora)
        self.pickup.escrever_pendentes(agora)

    # ── a ondinha do standby (port do lp_tr8s.py) ───────────
    @staticmethod
    def _cor_aleatoria():
        return tuple(c * 127 for c in colorsys.hsv_to_rgb(random.random(), 1.0, 1.0))

    def _nova_onda(self, lin, col, estilo=None, agora=None):
        """Uma onda no grid, com os parametros dela: sem estilo, os ONDA_*
        fixos (o toque); com estilo, sorteados nas faixas dele."""
        rgb = self._cor_aleatoria()
        if estilo is None:
            vel, larg, alc = ONDA_VEL, ONDA_LARGURA, ONDA_ALCANCE
        else:
            e = STANDBY_ESTILOS[estilo]
            vel, larg, alc = (random.uniform(*e["vel"]), random.uniform(*e["larg"]),
                              random.uniform(*e["alc"]))
            rgb = tuple(c * e["brilho"] for c in rgb)
        self.ondas.append({"lin": lin, "col": col, "t0": time.time() if agora is None else agora,
                           "rgb": rgb, "vel": vel, "larg": larg, "alc": alc})

    def _semear(self, agora):
        if agora < self.proxima_onda:
            return
        e = STANDBY_ESTILOS[self.estilo_standby]
        self.proxima_onda = agora + random.uniform(*e["intervalo"])
        self._nova_onda(random.randrange(LINHAS), random.randrange(PASSOS),
                        self.estilo_standby, agora)

    def quadro_de_ondas(self, agora):
        """{dev: [(nota, (r, g, b))]} do instante `agora` (os aneis somados), ou
        None sem onda nenhuma no ar. Tira as ondas que ja morreram."""
        self.ondas = [o for o in self.ondas if (agora - o["t0"]) * o["vel"] < o["alc"]]
        if not self.ondas:
            return None
        # o raio e o desbotamento de cada onda, uma vez por quadro (revisao do PR #10)
        ondas = [(o, (agora - o["t0"]) * o["vel"]) for o in self.ondas]
        ondas = [(o, vt, 1.0 - vt / o["alc"]) for o, vt in ondas]
        quadro = {}
        for dev, off in (("E", 0), ("D", 8)):
            pares = []
            for l in range(LINHAS):
                for c in range(8):
                    step, r, g, b = off + c, 0.0, 0.0, 0.0
                    for o, vt, desbota in ondas:
                        anel = 1.0 - abs(math.hypot(l - o["lin"], step - o["col"]) - vt) / o["larg"]
                        if anel <= 0:
                            continue
                        k = anel * desbota
                        r, g, b = r + o["rgb"][0] * k, g + o["rgb"][1] * k, b + o["rgb"][2] * k
                    pares.append((self.nota_de(dev, l, c),
                                  (int(min(127, r)), int(min(127, g)), int(min(127, b)))))
            quadro[dev] = pares
        return quadro

    def _animar(self, agora):
        if not self.lp_out:
            return
        fps = STANDBY_ESTILOS[self.estilo_standby]["fps"]
        if agora - self.ultimo_quadro < 1.0 / fps:
            return
        self.ultimo_quadro = agora
        quadro = self.quadro_de_ondas(agora)
        if quadro is None:
            if self.onda_suja:                       # um ultimo quadro, para apagar
                self.pintar()
                self.onda_suja = False
            return
        self.onda_suja = True
        for dev, pares in quadro.items():
            lp.enviar_cores(self.lp_out[dev], pares)

    # ── pads e o laco ───────────────────────────────────────
    def _ler_pads(self):
        for dev, off in (("E", 0), ("D", 8)):
            if dev not in self.lp_in:
                continue
            for msg in self.lp_in[dev].iter_pending():
                if msg.type == "control_change":
                    if msg.value == 0:
                        continue
                    acao = BOTOES.get((dev, msg.control))
                    if acao and self.modo_geral == MODO_ON:
                        self.executar(*acao)
                    continue
                if msg.type not in ("note_on", "note_off"):
                    continue
                solto = msg.type == "note_off" or msg.velocity == 0
                pos = self._decodificar(dev, msg.note)
                if pos is None:
                    continue
                linha, col = pos
                if solto:
                    if self.modo_geral == MODO_ON and self.pagina != "steps":
                        self.soltar_pad(linha, off + col)
                    continue
                if self.modo_geral == MODO_STANDBY:
                    # o toque entra no estilo da vez (um dedo nao joga chuva
                    # no meio do ambiente)
                    self._nova_onda(linha, off + col, self.estilo_standby)
                    continue
                if self.modo_geral != MODO_ON:
                    continue
                if self.pagina != "steps":
                    self.tocar_pad(linha, off + col)
                    continue
                self.alternar(linha, off + col)
                self.pintar_coluna(off + col)           # so a coluna mudou

    def tick(self):
        with self.lock:
            self._drenar_fila()
            self._ler_clock()
            self._ler_pads()
            agora = time.time()
            if self.modo_geral == MODO_STANDBY:
                self._semear(agora)
                self._animar(agora)
            self._ler_controladoras(agora)
            if self.modo_geral == MODO_ON and agora >= self.proxima_releitura:
                self.proxima_releitura = agora + RELER_A_CADA
                try:
                    self.reler()
                    self._ler_chain()
                except ERROS_DE_LEITURA as e:
                    self.log(f"(!) releitura falhou: {e}")
            if self.modo_geral == MODO_ON:
                self._andar_foto(agora)
                self._andar_ritmo()
            if (self.modo_geral == MODO_ON and (self.quer_kit or self.pagina == "rout")
                    and agora >= self.proximo_kit):
                self.proximo_kit = agora + self.LER_KIT_A_CADA
                antes = dict(self.kit_valores)
                self.ler_kit(None if self.quer_kit else IDS_ROUT)
                if self.pagina == "rout" and self.kit_valores != antes:
                    self.pintar()                    # o App/painel mexeu na rota

    def fechar(self):
        with self.lock:
            self.modo_geral = MODO_OFF
            try:
                self.pintar()
                self.pintar_botoes()
            except Exception:
                pass
            self.soltar_maquina()
            if self.ctl is not None:
                self.ctl.fechar()
                self.ctl = None
            for p in list(self.lp_in.values()) + list(self.lp_out.values()):
                try:
                    p.close()
                except Exception:
                    pass

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

O que NAO faz ainda (documentado na REFERENCIA):
  - saber qual variacao esta TOCANDO (nao ha de onde ler): o playhead anda
    sobre a variacao mostrada
  - scale e last step: assume 16th e 16 steps
  - linhas de ACC e TRG: os enderecos nao foram decifrados
  - gravar: o WRITE continua no painel (criterio 6 adiado)
"""
import queue, threading, time

import campos
import conexao_serial as cs
import controladoras
import parametros
import launchpad as lp
import tr1000
import tr1000_serial as ts
from portas import EntradaMIDI, SaidaMIDI, porta_exata

MODO_ON, MODO_OFF = "on", "off"

N_TRACKS = len(ts.TRACKS_SERIAL)                    # 10: BD..RC
TRACKS_LAYER = 4                                    # BD SD LT HT tem layer A/B
LINHAS = 8
# Os dois bancos do layout A (ideia do Luan, 10/10/2026, 22:30): o CC divide a
# linha do RS e o RC a do HC; BD e SD (e LT HT CH OH) ficam sempre no lugar.
# Linha -> track. Sem linha de accent: o accent e pelo painel.
BANCOS = {1: [0, 1, 2, 3, 4, 5, 6, 7],              # BD SD LT HT RS HC CH OH
          2: [0, 1, 2, 3, 8, 9, 6, 7]}              # BD SD LT HT CC RC CH OH
PULSOS_P_STEP = 6                                   # 24 ppqn, scale 16th (assumido)
PASSOS = 16                                         # last step (assumido)
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
                   (95, ("layer", "B"))):
    BOTOES[("D", _cc)] = _acao                  # topo direito
del _i, _cc, _acao


bloco_de_steps = ts.bloco_de_steps


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
    pulsos = 0
    tocando = False
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
    def definir_modo(self, modo):
        """ON: abre a serial, le o pattern selecionado e pinta. OFF: apaga."""
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
                self.modo_geral = MODO_OFF
                self.pintar()
                return False
        else:
            self.modo_geral = MODO_OFF
        self.pintar()
        self.pintar_botoes()
        return True

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
        mudo_antes = self.mudo_mascara
        self.b3, self.cab, self.acc_mascara = b3, cab, acc
        self.mudo_mascara = b3[campos.B3_MUTE]
        trocou = x != self.x_pattern
        if trocou:
            self.log(f"pattern {ts.nome_do_pattern(x)} (x {x})")
            self.x_pattern = x
            self.cache.clear()
        antes = [self.cache.get(k) for k in novo]
        self.cache.update(novo)
        if forcar or trocou or antes != list(novo.values()):
            self.pintar()
            self.pintar_botoes()
            return True
        if self.mudo_mascara != mudo_antes:
            self.pintar_botoes()                     # o mute mudou no painel
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
        no_playhead = self.tocando and step == self.passo
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
        """O toque: se os slots-alvo ja tem a nota na velocity atual, desliga
        (FF, como o painel); senao escreve a nota. Uma escrita por slot, cada
        uma com o 03 de volta; o cache so muda depois da confirmacao. Erro:
        rele o track e segue - nunca repete sozinho."""
        tr = self.track_da_linha(linha)
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
            self.vel_idx = arg
        elif tipo == "banco":
            self.banco = arg
        elif tipo == "mudo":
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
            self._luz(e, cc, lp.cor_borda(lp.COR_VAR, i == self.variacao) if ligado
                      else (0, 0, 0))
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

    def pintar_coluna(self, step):
        if step < 0 or self.modo_geral != MODO_ON or not self.lp_out:
            return
        dev = "E" if step < 8 else "D"
        col = step if step < 8 else step - 8
        lp.enviar_cores(self.lp_out[dev],
                        [(self.nota_de(dev, l, col), self.cor_do_step(l, step))
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
                pares = [(self.nota_de(dev, l, c), self.cor_do_step(l, off + c))
                         for l in range(LINHAS) for c in range(8)]
            lp.enviar_cores(self.lp_out[dev], pares)

    def mover_playhead(self, novo):
        if novo == self.passo:
            return
        antigo, self.passo = self.passo, novo
        self.pintar_coluna(antigo)
        self.pintar_coluna(novo)

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
                lote += 1
                continue
            lote = self._aplicar_pulsos(lote)  # transporte fecha o lote
            if t == "start":
                # start sem stop antes (recomeco): a coluna velha precisa ser
                # repintada, senao o branco fica preso nela (revisao do PR #4)
                antigo = self.passo
                self.pulsos, self.tocando = 0, True
                self.passo = -1
                self.mover_playhead(0)
                self.pintar_coluna(antigo)
            elif t == "continue":
                self.tocando = True
            elif t == "stop":
                antigo = self.passo
                self.tocando, self.passo = False, -1
                self.pintar_coluna(antigo)
        self._aplicar_pulsos(lote)

    def _aplicar_pulsos(self, lote):
        if lote and self.tocando:
            self.pulsos += lote
            # os pulsos 1..6 depois do start sao o step 0: o 6o ainda e dele,
            # o 7o abre o step 1 (pulsos // 6 adiantava um pulso a cada step -
            # revisao do PR #4)
            self.mover_playhead(((self.pulsos - 1) // PULSOS_P_STEP) % PASSOS)
        return 0

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
        """O clique na grade da tela: o mesmo toque do pad, num track qualquer."""
        if track in BANCOS[self.banco]:
            return self.alternar(BANCOS[self.banco].index(track), step)
        banco_antes = self.banco
        self.banco = 1 if track in BANCOS[1] else 2
        try:
            self.alternar(BANCOS[self.banco].index(track), step)
        finally:
            self.banco = banco_antes

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
        """STEP LOOP: o modo, e um step 'segurado' (a tela segura por clique)."""
        if step is None:
            self._escrever(campos.B3, 0, 0, campos.INI_B3 + campos.B3_LOOP, int(bool(ligado)))
        else:
            self._escrever(campos.B3, 0, 0, campos.INI_B3 + campos.B3_LOOP_STEP + step,
                           int(bool(ligado)))

    def _resolver(self, id):
        """(Parametro, endereco) de um parametro agora (type/sync lidos), ou None."""
        if self.pickup is not None:
            return self.pickup.entrada(id, self.x_pattern, self.x_kit)
        p = parametros.entrada_para(id)
        if p is None:
            sel = parametros.seletor_de(id)
            if not sel or self.x_kit is None:
                return None
            tipo = self._ler(*parametros.endereco(parametros.SELETORES[sel], self.x_kit), 1)[0]
            conds = {c: self._ler(*parametros.endereco(parametros.SELETORES[c], self.x_kit), 1)[0]
                     for c in parametros.condicoes_de(id, tipo)}
            p = parametros.entrada_para(id, tipo, conds)
            if p is None:
                return None
        x = self.x_pattern if p.escopo == "pattern" else self.x_kit
        if x is None:
            return None
        return p, parametros.endereco(p, x, parametros.track_do_id(id))

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

    def ler_kit(self):
        """Todos os parametros da tabela, um pedido cada (~0,25 ms cada: uma
        foto de 439 levou 0,1 s). Os dependentes de type no type atual."""
        if self.conexao is None or self.x_pattern is None:
            return
        novos = {}
        for id in self.ids_do_kit():
            try:
                e = self._resolver(id)
                if e is not None:
                    novos[id] = self._ler(*e[1], 1)[0]
            except ERROS_DE_LEITURA:
                continue
        self.kit_valores = novos

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
                c = self.cache.get((v, tr)) or [0] * N_SLOTS
                cheio = list(c) + [0] * (ts.N_STEPS_BLOCO - len(c))
                linha = []
                for s in range(16):
                    a, b = cheio[s * 4], cheio[s * 4 + 1]
                    linha.append({
                        "a": ts.slot_toca(a), "b": ts.slot_toca(b),
                        "vel": ts.velocidade(a & ~campos.BIT_ALT if ts.slot_toca(a) else b),
                        "alt": campos.eh_alt(a)})
                grade.append(linha)
            cab = self.cab or []

            def c(pos, padrao=None):
                return cab[pos] if pos < len(cab) else padrao
            return {
                "ligado": self.modo_geral == MODO_ON,
                "pattern": ts.nome_do_pattern(self.x_pattern) if self.x_pattern is not None else None,
                "x_pattern": self.x_pattern, "x_kit": self.x_kit,
                "tempo": (self.b3[ts.OFF_TEMPO_ATUAL] / 100) if self.b3 else None,
                "variacao": v, "velocidade_idx": self.vel_idx, "modo_layer": self.modo_layer,
                "banco": self.banco, "passo": self.passo, "tocando": self.tocando,
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
                if msg.type != "note_on" or msg.velocity == 0:
                    continue
                pos = self._decodificar(dev, msg.note)
                if pos is None or self.modo_geral != MODO_ON:
                    continue
                linha, col = pos
                self.alternar(linha, off + col)
                self.pintar_coluna(off + col)           # so a coluna mudou

    def tick(self):
        with self.lock:
            self._drenar_fila()
            self._ler_clock()
            self._ler_pads()
            agora = time.time()
            self._ler_controladoras(agora)
            if self.modo_geral == MODO_ON and agora >= self.proxima_releitura:
                self.proxima_releitura = agora + RELER_A_CADA
                try:
                    self.reler()
                except ERROS_DE_LEITURA as e:
                    self.log(f"(!) releitura falhou: {e}")
            if (self.modo_geral == MODO_ON and self.quer_kit
                    and agora >= self.proximo_kit):
                self.proximo_kit = agora + self.LER_KIT_A_CADA
                self.ler_kit()

    def fechar(self):
        with self.lock:
            self.modo_geral = MODO_OFF
            try:
                self.pintar()
                self.pintar_botoes()
            except Exception:
                pass
            if self.conexao is not None:
                self.conexao.__exit__(None, None, None)
                self.conexao = None
            if self.clk is not None:
                self.clk.close()
                self.clk = None
            if self.ctl is not None:
                self.ctl.fechar()
                self.ctl = None
            for p in list(self.lp_in.values()) + list(self.lp_out.values()):
                try:
                    p.close()
                except Exception:
                    pass

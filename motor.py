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

import conexao_serial as cs
import launchpad as lp
import tr1000
import tr1000_serial as ts
from portas import EntradaMIDI, SaidaMIDI, porta_exata

MODO_ON, MODO_OFF = "on", "off"

N_TRACKS = len(ts.TRACKS_SERIAL)                    # 10: BD..RC
TRACKS_LAYER = 4                                    # BD SD LT HT tem layer A/B
LINHAS = 8
BASE_MAX = N_TRACKS - LINHAS                        # rolagem: 0..2
PULSOS_P_STEP = 6                                   # 24 ppqn, scale 16th (assumido)
PASSOS = 16                                         # last step (assumido)
RELER_A_CADA = 0.5                                  # s

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
for _cc, _acao in ((91, ("rolar", -1)),         # ▲
                   (92, ("rolar", +1)),         # ▼
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
    base_inst = 0
    passo = -1
    pulsos = 0
    tocando = False
    proxima_releitura = 0.0

    def __init__(self, cfg, log=print):
        self.log = log
        self.lock = threading.RLock()
        self.fila_cmd = queue.Queue()
        self.cache = {}                         # (variacao, track) -> [131 u32]
        self.geo = {"E": cfg["esquerdo"], "D": cfg["direito"]}
        self.lp_in, self.lp_out = {}, {}
        for dev, lado in (("E", "esquerdo"), ("D", "direito")):
            c = cfg[lado]
            self.lp_in[dev] = EntradaMIDI(c["in_idx"], c.get("in_nome"))
            self.lp_out[dev] = SaidaMIDI(c["out_idx"], c.get("out_nome"))

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

    # ── fila de comandos (para uma tela futura) ─────────────
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

    def ler_variacao(self, variacao):
        b = bloco_de_steps(variacao)
        for tr in range(N_TRACKS):
            self.cache[(variacao, tr)] = self._ler(b, self.x_pattern, tr,
                                                   ts.INDICE_STEPS, ts.N_STEPS_BLOCO)

    def reler(self, forcar=False):
        """O pattern selecionado no painel (bloco 3 [2]) e a variacao mostrada.
        Devolve True se algo mudou (e entao ja repintou)."""
        b3 = self._ler(3, 0, 0, *cs.faixa_do_bloco(3, 0, 0))
        x = b3[ts.OFF_PATTERN_GLOBAL]
        mudou = forcar or x != self.x_pattern
        if x != self.x_pattern:
            self.log(f"pattern {ts.nome_do_pattern(x)} (x {x})")
            self.x_pattern = x
            self.cache.clear()
        antes = [self.cache.get((self.variacao, tr)) for tr in range(N_TRACKS)]
        self.ler_variacao(self.variacao)
        depois = [self.cache.get((self.variacao, tr)) for tr in range(N_TRACKS)]
        if mudou or antes != depois:
            self.pintar()
            self.pintar_botoes()
            return True
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
        tr = self.base_inst + linha
        if tr >= N_TRACKS:
            return lp.COR_OFF
        s = self.slots(tr, step)
        a, b = ts.slot_toca(s[0]), ts.slot_toca(s[1])
        no_playhead = self.tocando and step == self.passo
        if no_playhead:
            return lp.COR_PLAY_HIT if (a or b) else lp.COR_PLAY
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
        relê o track e segue - nunca repete sozinho."""
        tr = self.base_inst + linha
        if tr >= N_TRACKS or self.conexao is None or self.x_pattern is None:
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
        except (cs.ErroConexao, PermissionError) as e:
            self.log(f"(!) escrita recusada/sem resposta: {e} - relendo o track")
            try:
                self.cache[(self.variacao, tr)] = self._ler(
                    bloco, self.x_pattern, tr, ts.INDICE_STEPS, ts.N_STEPS_BLOCO)
            except cs.ErroConexao:
                pass

    # ── botoes ──────────────────────────────────────────────
    def executar(self, tipo, arg):
        if tipo == "variacao":
            if arg != self.variacao:
                self.variacao = arg
                if self.conexao is not None and self.x_pattern is not None:
                    try:
                        self.ler_variacao(arg)
                    except cs.ErroConexao as e:
                        self.log(f"(!) {e}")
        elif tipo == "velocidade":
            self.vel_idx = arg
        elif tipo == "rolar":
            self.base_inst = max(0, min(BASE_MAX, self.base_inst + arg))
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
        setas = {91: self.base_inst > 0, 92: self.base_inst < BASE_MAX}
        for cc, ok in setas.items():
            self._luz(d, cc, lp.cor_borda(lp.COR_SETA) if ligado and ok else (0, 0, 0))
        for cc, modo, cor in ((93, "AB", lp.COR_ATIVO), (94, "A", lp.COR_FORTE),
                              (95, "B", lp.COR_B)):
            self._luz(d, cc, lp.cor_borda(cor, modo == self.modo_layer) if ligado
                      else (0, 0, 0))

    def pintar_coluna(self, step):
        if step < 0 or self.modo_geral != MODO_ON:
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
                self.pulsos, self.tocando = 0, True
                self.passo = -1
                self.mover_playhead(0)
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
            self.mover_playhead((self.pulsos // PULSOS_P_STEP) % PASSOS)
        return 0

    # ── pads e o laco ───────────────────────────────────────
    def _ler_pads(self):
        for dev, off in (("E", 0), ("D", 8)):
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
                self.pintar()

    def tick(self):
        with self.lock:
            self._drenar_fila()
            self._ler_clock()
            self._ler_pads()
            agora = time.time()
            if self.modo_geral == MODO_ON and agora >= self.proxima_releitura:
                self.proxima_releitura = agora + RELER_A_CADA
                try:
                    self.reler()
                except cs.ErroConexao as e:
                    self.log(f"(!) releitura falhou: {e}")

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
            for p in list(self.lp_in.values()) + list(self.lp_out.values()):
                try:
                    p.close()
                except Exception:
                    pass

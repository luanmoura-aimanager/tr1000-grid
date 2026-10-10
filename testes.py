#!/usr/bin/env python3
"""
testes.py - testes de mesa (unittest), sem porta MIDI e sem hardware

    python3 testes.py

Verde aqui NAO significa "funciona": significa "nao quebrou o que ja estava
provado". Quem diz que funciona e o Luan, na frente da maquina (CLAUDE.md).

Na fase 0 o que se prova de mesa e pouco e e de proposito:
  - a camada Roland (checksum, enderecos, decodificador que acha o model ID)
    contra uma mensagem REAL da TR-8S, que e o unico parente medido
  - o parser/resumo das capturas, que vai ler o boot do App na sessao C1
  - o extrator do catalogo, contra um binario de mentira
  - o portao da fase 0: cada comando do lp_tr1000.py roda contra portas
    falsas, e o unico SysEx que pode sair e o Identity Request
"""
import os, py_compile, sys, tempfile, unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import roland
import tr1000
import tr1000_sysex
import tr1000_serial
import catalogo_app
import espiao
import conexao_serial
import motor
import controladoras
import parametros

# Mensagem real, capturada do site ARIA falando com uma TR-8S (tr8s-grid
# REFERENCIA 2.9): "pattern atual -> 127". E o unico SysEx Roland medido que
# temos; serve para provar a aritmetica, nao o mapa da TR-1000.
TR8S_REAL = [0xF0, 0x41, 0x10, 0x00, 0x00, 0x00, 0x45, 0x12,
             0x01, 0x00, 0x00, 0x01, 0x7F, 0x7F, 0xF7]
TR8S_CAB = [0x41, 0x10, 0x00, 0x00, 0x00, 0x45]


class TesteRoland(unittest.TestCase):
    def test_checksum_da_mensagem_real(self):
        self.assertEqual(roland.checksum([0x01, 0x00, 0x00, 0x01, 0x7F]), 0x7F)

    def test_montar_dt1_reproduz_a_real(self):
        self.assertEqual(roland.montar_dt1(TR8S_CAB, (1, 0, 0, 1), [0x7F]),
                         TR8S_REAL)

    def test_decodificar_acha_o_model_id_sozinho(self):
        d = roland.decodificar(TR8S_REAL)
        self.assertIsNotNone(d)
        self.assertEqual(d["cabecalho"], TR8S_CAB)
        self.assertEqual(d["modelo"], (0, 0, 0, 0x45))
        self.assertEqual(d["cmd"], roland.DT1)
        self.assertEqual(d["addr"], (1, 0, 0, 1))
        self.assertEqual(d["data"], [0x7F])
        self.assertTrue(d["chk_ok"])

    def test_decodificar_sem_f0_f7(self):
        self.assertIsNotNone(roland.decodificar(TR8S_REAL[1:-1]))

    def test_cabecalho_errado_recusa(self):
        outro = [0x41, 0x10, 0x00, 0x00, 0x00, 0x46]
        self.assertIsNone(roland.decodificar(TR8S_REAL, cabecalho=outro))
        self.assertIsNotNone(roland.decodificar(TR8S_REAL, cabecalho=TR8S_CAB))

    def test_checksum_ruim_aparece_como_ruim(self):
        # mensagem estragada NAO some: volta marcada, para quem le a captura
        # ver o byte corrompido (revisao de 07/10/2026)
        ruim = list(TR8S_REAL); ruim[-2] = 0x00
        d = roland.decodificar(ruim)
        self.assertIsNotNone(d)
        self.assertFalse(d["chk_ok"])
        self.assertEqual(d["cabecalho"], TR8S_CAB)
        self.assertFalse(roland.decodificar(ruim, cabecalho=TR8S_CAB)["chk_ok"])

    def test_dois_tamanhos_fechando_e_ambiguo(self):
        # model de 1 byte (0x6F) com endereco comecando em 0x11: lido como
        # model de 3 bytes, o "cmd" vira o 0x11 do endereco - e o checksum
        # tambem pode fechar. Tem que voltar marcado, nao sumir
        cab1 = [0x41, 0x10, 0x6F]
        m = roland.montar_dt1(cab1, (0x11, 0x00, 0x00, 0x00), [0x00, 0x00])
        d = roland.decodificar(m)
        self.assertIsNotNone(d)
        com_cab = roland.decodificar(m, cabecalho=cab1)
        self.assertTrue(com_cab["chk_ok"])
        self.assertFalse(com_cab["ambiguo"])

    def test_cabecalho_dominante(self):
        outra = roland.montar_dt1(TR8S_CAB, (0x10, 0, 0, 0), [5])
        ruim = list(TR8S_REAL); ruim[-2] = 0
        self.assertEqual(roland.cabecalho_dominante([TR8S_REAL, outra, ruim]),
                         TR8S_CAB)
        self.assertIsNone(roland.cabecalho_dominante([]))

    def test_model_id_de_outro_tamanho(self):
        # model de 3 bytes, como o de varias maquinas Roland antigas
        cab3 = [0x41, 0x10, 0x00, 0x00, 0x3B]
        m = roland.montar_dt1(cab3, (0x10, 0, 0, 0), [1, 2, 3])
        d = roland.decodificar(m)
        self.assertEqual(d["modelo"], (0, 0, 0x3B))
        self.assertEqual(d["data"], [1, 2, 3])

    def test_rq1_tamanho_em_7_bits(self):
        m = roland.montar_rq1(TR8S_CAB, (0x20, 0, 0, 0), 24504)
        d = roland.decodificar(m)
        self.assertEqual(d["cmd"], roland.RQ1)
        self.assertEqual(roland.de_7bits(d["data"]), 24504)

    def test_addr_soma_com_carry(self):
        self.assertEqual(roland.addr_soma((0x10, 0, 0, 0x7F), 1), (0x10, 0, 1, 0))
        self.assertEqual(roland.addr_soma((0x20, 0, 0, 0), 16384), (0x20, 1, 0, 0))

    def test_endereco_linear_ida_e_volta(self):
        for a in [(0, 0, 0, 0), (0x20, 0x10, 0x7F, 0x01), (0x7F,) * 4]:
            self.assertEqual(roland.int_para_addr(roland.addr_para_int(a)), a)

    def test_nibbles_ida_e_volta(self):
        for m in (0, 1, 0x8001, 0xFFFF, 0x1234):
            self.assertEqual(
                roland.nibbles_para_mascara(roland.mascara_para_nibbles(m)), m)


class TesteIdentidade(unittest.TestCase):
    def test_resposta_roland(self):
        r = roland.decodificar_identidade(
            [0xF0, 0x7E, 0x10, 0x06, 0x02, 0x41, 0x01, 0x02, 0x03, 0x04,
             0x00, 0x01, 0x02, 0x00, 0xF7])
        self.assertEqual(r["fabricante"], [0x41])
        self.assertEqual(r["familia"], [0x01, 0x02])
        self.assertEqual(r["membro"], [0x03, 0x04])

    def test_pedido_nao_e_resposta(self):
        self.assertIsNone(roland.decodificar_identidade(roland.IDENTITY_REQUEST))


def _m(direcao, cmd, addr, data, t):
    return dict(dir=direcao, cmd=cmd, addr=tuple(addr), data=list(data), t=t,
                cabecalho=TR8S_CAB, chk_ok=True)


class TesteCapturas(unittest.TestCase):
    def test_linha_de_texto_do_midi_monitor(self):
        linha = ("  22:01:02.123   To TR-1000 CTRL   SysEx   Roland   "
                 + roland.hexs(TR8S_REAL))
        m = tr1000_sysex.parse_line(linha)
        self.assertEqual(m["dir"], "TX")
        self.assertEqual(m["addr"], (1, 0, 0, 1))

    def test_porta_comum_colada_no_hexa(self):
        # "TR-1000" termina em digitos hexa: sem o lookbehind, o casamento
        # comecava no "00" de "1000" e a linha sumia (revisao de 07/10/2026)
        linha = "22:01:02.123\tFrom TR-1000\t" + roland.hexs(TR8S_REAL)
        m = tr1000_sysex.parse_line(linha)
        self.assertIsNotNone(m)
        self.assertEqual(m["addr"], (1, 0, 0, 1))

    def test_captura_de_texto_marca_o_checksum_ruim(self):
        ruim = list(TR8S_REAL); ruim[-2] = 0
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            for b in (TR8S_REAL, TR8S_REAL, ruim):
                f.write("  10:00:00   From TR-1000 CTRL   " + roland.hexs(b) + "\n")
        try:
            msgs = tr1000_sysex.load(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual([m["chk_ok"] for m in msgs], [True, True, False])

    def test_mmon_vazio_nao_quebra_e_diz_o_que_monitorava(self):
        # o MIDI Monitor salva sem "messageData" quando nada chegou - foi o
        # boot do App com ctrlPort = 0 (medido 08/10/2026)
        import plistlib
        vazio = {"version": 1, "streamSettings": {
            "portInputStream": [{"name": "TR-1000 CTRL", "uniqueID": 1}],
            "spyingInputStream": [{"name": "TR-1000 CTRL", "uniqueID": 2}]}}
        with tempfile.NamedTemporaryFile(suffix=".mmon", delete=False) as f:
            plistlib.dump(vazio, f, fmt=plistlib.FMT_BINARY)
        try:
            outros = {}
            self.assertEqual(tr1000_sysex.load(f.name, outros=outros), [])
        finally:
            os.unlink(f.name)
        self.assertEqual(outros["espionando"], "TR-1000 CTRL")

    def test_o_formato_que_o_sniff_grava_e_lido(self):
        # o lp_tr1000 sniff --arquivo escreve "From TR-1000 CTRL" + hex
        linha = "  22:01:02   From TR-1000 CTRL   " + roland.hexs(TR8S_REAL)
        self.assertEqual(tr1000_sysex.parse_line(linha)["dir"], "RX")

    def test_resumo_lista_branca_regioes_e_keepalive(self):
        msgs = []
        # keep-alive a cada 3 s, com um atraso no meio (o boot da TR-8S fazia)
        for t in (0, 3, 6, 9.9, 12.9, 15.9):
            msgs.append(_m("TX", roland.RQ1, (0, 3, 0, 0x3B),
                           roland.tamanho_7bits(1), t))
        # leitura de 256 B respondida em dois DT1 de 128 seguidos
        msgs.append(_m("TX", roland.RQ1, (0x20, 0, 0, 0),
                       roland.tamanho_7bits(256), 1.0))
        msgs.append(_m("RX", roland.DT1, (0x20, 0, 0, 0), [0] * 128, 1.01))
        msgs.append(_m("RX", roland.DT1, (0x20, 0, 1, 0), [0] * 128, 1.02))
        # leitura sem resposta
        msgs.append(_m("TX", roland.RQ1, (0x30, 0, 0, 0),
                       roland.tamanho_7bits(8), 2.0))
        # escrita do App
        msgs.append(_m("TX", roland.DT1, (0x50, 0, 0, 0x13), [1], 4.0))
        r = tr1000_sysex.resumir(msgs)

        leit = {(x["addr"], x["tamanho"]): x for x in r["leituras"]}
        self.assertEqual(leit[("20 00 00 00", 256)]["vezes"], 1)
        self.assertTrue(leit[("20 00 00 00", 256)]["respondeu"])
        self.assertFalse(leit[("30 00 00 00", 8)]["respondeu"])
        self.assertIn(dict(ini="20 00 00 00", fim="20 00 02 00", bytes=256),
                      r["regioes"])
        self.assertEqual([k["addr"] for k in r["keepalive"]], ["00 03 00 3B"])
        self.assertEqual(r["escritas"], [dict(addr="50 00 00 13", vezes=1)])

    def test_leitura_unica_nao_e_keepalive(self):
        msgs = [_m("TX", roland.RQ1, (0x10, 0, 0, 0),
                   roland.tamanho_7bits(16), t) for t in (0, 0.01)]
        self.assertEqual(tr1000_sysex.resumir(msgs)["keepalive"], [])


class TesteSerlog(unittest.TestCase):
    """O leitor do .serlog contra capturas sinteticas no MESMO formato que o
    espiao/espiao_serial.c grava (tr1000_serial.serializar). O espiao em si foi
    conferido de ponta a ponta numa pty em 08/10/2026 (REFERENCIA 2.1b); o
    teste de verdade dele e a sessao C1-S0, com o App."""

    def _gravar(self, registros):
        f = tempfile.NamedTemporaryFile(suffix=".serlog", delete=False)
        f.write(tr1000_serial.serializar(registros)); f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_le_os_registros(self):
        c = self._gravar([(1_000_000_000, "S", 42, b"/app"),
                          (1_500_000_000, "O", 7, b"/dev/tty.usbmodem31101"),
                          (2_000_000_000, "W", 7, b"\x01\x02")])
        regs = tr1000_serial.ler_serlog(c)
        self.assertEqual([r["tipo"] for r in regs], ["S", "O", "W"])
        self.assertEqual(regs[2]["dados"], b"\x01\x02")
        self.assertAlmostEqual(regs[1]["t"], 1.5)
        self.assertEqual(tr1000_serial.autoteste(regs), (True, True))

    def test_sem_o_open_o_autoteste_reprova(self):
        c = self._gravar([(0, "S", 1, b"/app")])
        self.assertEqual(tr1000_serial.autoteste(tr1000_serial.ler_serlog(c)),
                         (True, False))

    def test_magico_errado_recusa(self):
        f = tempfile.NamedTemporaryFile(suffix=".serlog", delete=False)
        f.write(b"XXXXXXXX\x01\x00\x00\x00"); f.close()
        self.addCleanup(os.unlink, f.name)
        with self.assertRaises(ValueError):
            tr1000_serial.ler_serlog(f.name)

    def test_quadro_quebrado_em_tres_reads_e_dois_num_read(self):
        q = bytes(TR8S_REAL)
        c = self._gravar([(0, "O", 3, b"/dev/tty.usbmodem1"),
                          (1, "R", 3, q[:4]), (2, "R", 3, q[4:9]),
                          (3, "R", 3, q[9:]),
                          (4, "R", 3, q + q)])
        quadros, sobra = tr1000_serial.quadros_sysex(tr1000_serial.ler_serlog(c))
        self.assertEqual(len(quadros), 3)
        self.assertTrue(all(d == "RX" and b == TR8S_REAL[1:-1]
                            for d, b, _ in quadros))
        self.assertEqual(sobra, {})

    def test_bytes_fora_de_quadro_contam(self):
        # muita sobra = a hipotese H1 (serial = SysEx Roland) esta errada
        c = self._gravar([(0, "W", 3, b"\xAA\x55\x01" + bytes(TR8S_REAL))])
        quadros, sobra = tr1000_serial.quadros_sysex(tr1000_serial.ler_serlog(c))
        self.assertEqual(len(quadros), 1)
        self.assertEqual(sobra, {"TX": 3})

    def test_resumo_pelo_tr1000_sysex(self):
        # o .serlog passa pelo MESMO caminho do .mmon: lista branca de graca
        rq = roland.montar_rq1(TR8S_CAB, (0x20, 0, 0, 0), 128)
        dt = roland.montar_dt1(TR8S_CAB, (0x20, 0, 0, 0), [0] * 128)
        c = self._gravar([(0, "O", 3, b"/dev/tty.usbmodem1"),
                          (1_000_000, "W", 3, bytes(rq)),
                          (2_000_000, "R", 3, bytes(dt))])
        outros = {}
        msgs = tr1000_sysex.load(c, outros=outros)
        r = tr1000_sysex.resumir(msgs)
        self.assertEqual(r["leituras"], [dict(addr="20 00 00 00", tamanho=128,
                                              vezes=1, respondeu=True)])
        self.assertEqual(outros["abriu-serial"], "sim")


class TestePacotesSerial(unittest.TestCase):
    """O enquadramento medido na C1-S0 (REFERENCIA 2.1c), contra pacotes
    copiados da captura real: o pedido 82 do bloco 3 e a resposta 02 dele."""

    PEDIDO = bytes.fromhex("15 08 41 F2 01 00 00 00 C0 17 92 21 0B 00 00 00"
                           "82 03 00 00 00 00 00 70 00 24 01")
    POLL = bytes.fromhex("14 08 40 F0 9B 00 00 00 00 00 00 05")

    def _resposta(self, valores):
        import struct
        c = bytes.fromhex("02 03 00 00 00 00 00 70 00") + struct.pack(
            "<H", len(valores)) + struct.pack(f"<{len(valores)}I", *valores)
        return bytes.fromhex("15 08 F0 00 38 73 84 86 00 00 00 00") + \
            struct.pack("<I", len(c)) + c

    def _regs(self, *pares):
        return [dict(t=i * 0.001, tipo=t, fd=3, dados=d)
                for i, (t, d) in enumerate(pares)]

    def test_enquadra_pacote_cortado_e_colado(self):
        resp = self._resposta([1, 2, 3])
        regs = self._regs(("W", self.PEDIDO[:5]), ("W", self.PEDIDO[5:] + self.POLL),
                          ("R", resp[:20]), ("R", resp[20:]))
        pacs = tr1000_serial.pacotes(regs)
        self.assertEqual([(d, len(p)) for d, _, p in pacs],
                         [("TX", 27), ("TX", 12), ("RX", len(resp))])

    def test_pedido_e_resposta_de_bloco(self):
        pacs = tr1000_serial.pacotes(self._regs(("W", self.PEDIDO),
                                                ("R", self._resposta([7, 8]))))
        self.assertEqual(tr1000_serial.leituras_de_bloco(pacs),
                         {(3, 0, 0): (112, 292)})
        self.assertEqual(tr1000_serial.valores_de_bloco(pacs)[0][1:],
                         (3, 0, 0, 112, [7, 8]))

    def test_x_e_y_sao_dois_u16(self):
        # bloco 13 da S0: y = 0..9 (o track); bloco 156: x = 0..499 (o slot)
        import struct
        ped = bytearray(self.PEDIDO)
        struct.pack_into("<HH", ped, 16 + 3, 126, 9)
        pacs = tr1000_serial.pacotes(self._regs(("W", bytes(ped))))
        self.assertEqual(list(tr1000_serial.leituras_de_bloco(pacs)), [(3, 126, 9)])

    def test_escrita_real_do_knob(self):
        # knob-bd-tune (08/10/2026): o TUNE do BD, primeiro valor escrito
        esc = bytes.fromhex("15 08 41 F2 01 00 00 00 E0 52 AF 2F 0D 00 00 00"
                            "01 9C 00 7E 00 00 00 C2 03 FD 01 00 00")
        pacs = tr1000_serial.pacotes(self._regs(("W", esc)))
        self.assertEqual([w[1:] for w in tr1000_serial.escritas(pacs)],
                         [(156, 126, 0, 962, 0x1FD)])

    def test_byte_estranho_vira_pacote_de_um(self):
        pacs = tr1000_serial.pacotes(self._regs(("R", b"\x42" + self.POLL)))
        self.assertEqual([len(p) for _, _, p in pacs], [1, 12])


class TesteGradeDeSteps(unittest.TestCase):
    """Os slots reais da S0 contra o que o Luan viu no painel (08/10/2026):
    SD var A e BD var H."""

    def test_sd_var_a_bate_com_os_leds(self):
        F, n, m = 0xFF, 0xA503C, 0xA5A3C
        slots = [F, F, F, F,  F, n, 0, 0,  0, 0, 0, 0,  m, m, F, F,
                 F, F, F, F,  F, F, F, F,  F, n, 0, 0,  0, 0, 0, 0,
                 F, n, F, F,  F, n, 0, 0,  0, 0, 0, 0,  m, m, F, F,
                 F, n, F, F,  0, 0, 0, 0,  F, m, 0, 0,  F, n, 0, 0]
        # vermelho 4 e 12 (layers A+B); verde 2 7 9 10 13 15 16 (so o B)
        self.assertEqual(tr1000_serial.grade_de_steps(slots),
                         ".b.x..b.bb.xb.bb")

    def test_step_ligado_no_painel(self):
        # step-bd2 (08/10/2026): o step 2 do BD ligado no painel virou
        # A503C nos slots 0 e 1 - os dois layers, como os outros BD
        v = [0] * 64
        v[4] = v[5] = 0xA503C
        self.assertEqual(tr1000_serial.grade_de_steps(v)[:3], ".x.")

    def test_so_pausas_e_apagado(self):
        self.assertEqual(tr1000_serial.grade_de_steps([0xFF] * 64), "." * 16)


# Pacotes REAIS da captura knob-bd-tune (08/10/2026)
R95_REAL = bytes.fromhex("95 02 f0 00 58 db 7b 86 f4 d1 1e 00 1b 00 00 00 7e 00 00 03 00"
                         "00 00 03 00 5a 01 00 00 5a 01 e0 f8 f1 00 00 00 00 00 31 2e 32 32")
R03_REAL = bytes.fromhex("15 08 f0 00 78 d6 82 86 f4 a0 87 00 0b 00 00 00 03 9c 00 7e 00"
                         "00 00 c2 03 c2 03")
R02_REAL = bytes.fromhex("15 08 f0 00 68 d7 82 86 01 00 00 00 0f 00 00 00 02 9c 00 7e 00"
                         "00 00 c2 03 01 00 fd 01 00 00")
W01_REAL = bytes.fromhex("15 08 41 f2 01 00 00 00 c0 88 06 2d 0d 00 00 00 01 9c 00 7e 00"
                         "00 00 c2 03 fd 01 00 00")
R82_REAL = bytes.fromhex("15 08 41 f2 00 00 00 00 40 87 06 2d 0b 00 00 00 82 9c 00 7e 00"
                         "00 00 c2 03 01 00")


class _MaquinaFalsa:
    """Uma TR-1000 de mentira atras da 'porta': responde ao aperto com o 95
    real, a leitura com um 02 do valor guardado, a escrita com um 03 - em
    pedacos de 5 bytes, porque a porta de verdade entrega cortado.
    calada=True nao confirma escrita nenhuma."""

    def __init__(self, calada=False, confirma_ate=None):
        import struct
        self.st = struct
        self.confirma_ate = confirma_ate          # quantos 03 ela da antes de calar
        self.valores = {(156, 126, 0, 962): 1000, (118, 0, 0, 1253): 0xA503C,
                        (118, 0, 0, 1254): 0xA503C}
        self.recebido, self.saida, self.calada, self.fechada = [], b"", calada, False

    def escrever(self, b):
        st = self.st
        self.recebido.append(bytes(b))
        if b == tr1000_serial.APERTO:
            self.saida += R95_REAL + tr1000_serial.POLL
            return
        c = tr1000_serial.carga(b)
        bloco, x, y, i = st.unpack_from("<HHHH", c, 1)
        if c[0] == tr1000_serial.LER_BLOCO:
            n = st.unpack_from("<H", c, 9)[0]
            blocos = getattr(self, "blocos", {})
            if n == 1 and (bloco, x, y, i) in self.valores:
                vs = [self.valores[(bloco, x, y, i)]]
            elif (bloco, x, y) in blocos or getattr(self, "zeros_ok", False):
                vs = list(blocos.get((bloco, x, y), [0] * n))[:n]
                vs += [0] * (n - len(vs))
            else:
                # endereco que o teste nao previu: falha alto, nao responde
                # zero - zero pareceria "step desligado" (revisao do PR #3)
                raise KeyError((bloco, x, y, i, n))
            corpo = bytes([2]) + c[1:9] + st.pack("<H", n) + st.pack(f"<{n}I", *vs)
            self.saida += bytes.fromhex("15 08 F0 00 68 D7 82 86 01 00 00 00") + \
                st.pack("<I", len(corpo)) + corpo
        elif c[0] == tr1000_serial.ESCREVER and not self.calada:
            if self.confirma_ate is not None:
                if self.confirma_ate == 0:
                    return
                self.confirma_ate -= 1
            self.valores[(bloco, x, y, i)] = st.unpack_from("<I", c, 9)[0]
            corpo = bytes([3]) + c[1:9] + c[7:9]
            self.saida += bytes.fromhex("15 08 F0 00 78 D6 82 86 F4 A0 87 00") + \
                st.pack("<I", len(corpo)) + corpo

    def ler(self, limite):
        pedaco, self.saida = self.saida[:5], self.saida[5:]
        return pedaco

    def fechar(self):
        self.fechada = True


class TesteEscritaC3(unittest.TestCase):
    """O cliente da serial da sessao C3 (REFERENCIA 3.1), sem hardware."""

    def test_pacotes_byte_a_byte_iguais_aos_do_app(self):
        ts = tr1000_serial
        self.assertEqual(ts.pacote_dados(ts.CAB_ESCRITA,
                                         ts.carga_escrever(156, 126, 0, 962, 0x1FD)), W01_REAL)
        self.assertEqual(ts.pacote_dados(ts.CAB_LEITURA,
                                         ts.carga_ler(156, 126, 0, 962, 1)), R82_REAL)

    def test_respostas_reais(self):
        ts = tr1000_serial
        self.assertEqual(ts.versao_95(R95_REAL), "1.22")
        self.assertEqual(ts.ack_03(R03_REAL), (156, 126, 0, 962))
        self.assertEqual(ts.resposta_02(R02_REAL), (156, 126, 0, 962, [509]))

    def test_enquadrar_ao_vivo_em_pedacos(self):
        fluxo = R95_REAL + tr1000_serial.POLL + R03_REAL
        buf, todos = b"", []
        for i in range(0, len(fluxo), 7):
            prontos, buf = tr1000_serial.enquadrar(buf + fluxo[i:i + 7])
            todos += prontos
        self.assertEqual(todos, [R95_REAL, tr1000_serial.POLL, R03_REAL])
        self.assertEqual(buf, b"")

    def test_sessao_completa_com_maquina_falsa(self):
        m = _MaquinaFalsa()
        with conexao_serial.ConexaoTR1000(porta=m) as c:
            self.assertEqual(c.aperto(), "1.22")
            self.assertEqual(c.ler(156, 126, 0, 962), [1000])
            self.assertTrue(c.escrever(156, 126, 0, 962, 509))
            self.assertEqual(c.ler(156, 126, 0, 962), [509])
        self.assertTrue(m.fechada)
        self.assertEqual(m.recebido[0], tr1000_serial.APERTO)

    def test_fora_da_lista_nao_manda_nada(self):
        m = _MaquinaFalsa()
        with conexao_serial.ConexaoTR1000(porta=m) as c:
            with self.assertRaises(PermissionError):
                c.escrever(118, 0, 0, 1251, 0xFF)          # slot 2: nao e layer A/B
            with self.assertRaises(PermissionError):
                c.pacote_escrita(116, 0, 0, 988, 0)        # cabecalho do pattern
        self.assertEqual(m.recebido, [])

    def test_sem_confirmacao_para_e_nao_repete(self):
        m = _MaquinaFalsa(calada=True)
        with conexao_serial.ConexaoTR1000(porta=m, relogio=_relogio_rapido()) as c:
            with self.assertRaises(conexao_serial.ErroConexao):
                c.escrever(118, 0, 0, 1253, 0xFF)
        escritas = [p for p in m.recebido if tr1000_serial.carga(p)[:1] == b"\x01"]
        self.assertEqual(len(escritas), 1)

    def test_lista_permitida_e_so_a_da_c3(self):
        self.assertEqual(set(conexao_serial.ESCRITAS_PERMITIDAS),
                         {(118, 0, 0, 1253), (118, 0, 0, 1254), (156, 126, 0, 962)})

    def test_a_captura_da_sessao_e_lida_como_as_do_espiao(self):
        m = _MaquinaFalsa()
        with tempfile.TemporaryDirectory() as tmp:
            with conexao_serial.ConexaoTR1000(porta=m, registrar=True) as c:
                c.captura = os.path.join(tmp, "c3.serlog")
                c.aperto(); c.ler(156, 126, 0, 962)
            regs = tr1000_serial.ler_serlog(c.captura)
            pacs = tr1000_serial.pacotes(regs)
        self.assertIn(tr1000_serial.APERTO, [p for d, _, p in pacs if d == "TX"])
        self.assertIn(R95_REAL, [p for d, _, p in pacs if d == "RX"])


class TesteSessaoC3(unittest.TestCase):
    """A confirmacao: sem teclado nao manda nada; --sim manda."""

    def _rodar(self, argv, entrada=None):
        import io, contextlib, builtins
        import sessao_c3
        m = _MaquinaFalsa()
        orig_cx, orig_input = conexao_serial.ConexaoTR1000, builtins.input

        class CxFalsa(orig_cx):
            def __init__(s, nome_captura=None, **k):
                super().__init__(porta=m)
        conexao_serial.ConexaoTR1000 = CxFalsa

        def falso_input(prompt=""):
            if entrada is None:
                raise EOFError
            return entrada
        builtins.input = falso_input
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                codigo = sessao_c3.main(argv)
        finally:
            conexao_serial.ConexaoTR1000, builtins.input = orig_cx, orig_input
        escritas = [p for p in m.recebido if tr1000_serial.carga(p)[:1] == b"\x01"]
        return codigo, escritas, m

    def test_sem_teclado_nao_manda(self):
        codigo, escritas, _ = self._rodar(["step2", "desligar"])
        self.assertEqual((codigo, escritas), (1, []))

    def test_enter_vazio_nao_manda(self):
        codigo, escritas, _ = self._rodar(["step2", "desligar"], entrada="")
        self.assertEqual((codigo, escritas), (1, []))

    def test_sim_digitado_manda_os_dois_slots(self):
        codigo, escritas, m = self._rodar(["step2", "desligar"], entrada="sim")
        self.assertEqual((codigo, len(escritas)), (0, 2))
        self.assertEqual(m.valores[(118, 0, 0, 1253)], 0xFF)

    def test_flag_sim_manda(self):
        codigo, escritas, m = self._rodar(["tune", "509", "--sim"])
        self.assertEqual((codigo, len(escritas)), (0, 1))
        self.assertEqual(m.valores[(156, 126, 0, 962)], 509)


class TesteRevisaoPR2(unittest.TestCase):
    """Os achados da revisao do PR #2 (08/10/2026), cada um travado."""

    def test_prova_do_boot_vazio_continua_intacta(self):
        # o MIDI Monitor ficou aberto e salvou por cima dela tres vezes
        import plistlib
        with open(os.path.join(AQUI, "capturas",
                               "2026-10-08-boot-app-serial-vazio.mmon"), "rb") as f:
            p = plistlib.load(f)
        self.assertNotIn("messageData", p)
        self.assertEqual(sorted(x["name"] for x in p["streamSettings"]["spyingInputStream"]),
                         ["TR-1000", "TR-1000 CTRL"])

    def test_leitura_fora_do_que_o_app_leu_nao_sai(self):
        m = _MaquinaFalsa()
        with conexao_serial.ConexaoTR1000(porta=m) as c:
            with self.assertRaises(PermissionError):
                c.ler(999, 0, 0, 0, 5000)
            with self.assertRaises(PermissionError):
                c.ler(118, 0, 0, 1249, 200)        # passa do fim do bloco (131)
        self.assertEqual(m.recebido, [])

    def test_leituras_da_c3_estao_dentro_do_boot_do_app(self):
        for e in conexao_serial.ESCRITAS_PERMITIDAS:
            self.assertTrue(conexao_serial.leitura_permitida(*e, 1), e)

    def test_so_aperto_leitura_e_escrita_saem(self):
        with self.assertRaises(PermissionError):
            conexao_serial.conferir_pacote(tr1000_serial.POLL)
        with self.assertRaises(PermissionError):
            conexao_serial.conferir_pacote(b"\x15" * 30)
        conexao_serial.conferir_pacote(tr1000_serial.APERTO)       # nao levanta

    def test_escrita_pela_metade_avisa_o_que_ja_mudou(self):
        import io, contextlib, sessao_c3
        m = _MaquinaFalsa(confirma_ate=1)
        orig = conexao_serial.ConexaoTR1000

        class CxFalsa(orig):
            def __init__(s, nome_captura=None, **k):
                super().__init__(porta=m, relogio=_relogio_rapido(0.005))
        conexao_serial.ConexaoTR1000 = CxFalsa
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                codigo = sessao_c3.main(["step2", "desligar", "--sim"])
        finally:
            conexao_serial.ConexaoTR1000 = orig
        saida = buf.getvalue()
        self.assertEqual(codigo, 1)
        self.assertIn("JA ESCRITO: BD var A step 2, layer A", saida)
        self.assertIn("estado agora: FF A503C", saida)

    def test_tamanho_absurdo_nao_trava_o_fluxo(self):
        lixo = b"\x15" + b"\x00" * 11 + b"\xff\xff\xff\x7f"   # n = 2 GB
        prontos, resto = tr1000_serial.enquadrar(lixo + R95_REAL)
        self.assertIn(R95_REAL, prontos)
        self.assertEqual(resto, b"")

    def test_captura_comeca_pelo_S_e_no_tempo_certo(self):
        m = _MaquinaFalsa()
        with conexao_serial.ConexaoTR1000(porta=m, relogio=_relogio_rapido(0.005),
                                          registrar=True) as c:
            c.aperto()
        tempos = [r[0] for r in c.registros]
        self.assertEqual(c.registros[0][1], "S")
        self.assertEqual(tempos, sorted(tempos))

    def test_captura_do_mesmo_dia_nao_sobrescreve(self):
        import datetime
        orig = espiao.AQUI
        with tempfile.TemporaryDirectory() as tmp:
            espiao.AQUI = tmp
            try:
                os.makedirs(os.path.join(tmp, "capturas"))
                d = datetime.date(2026, 10, 8)
                a = espiao.caminho_livre("c3-x", d)
                open(a, "w").close()
                b = espiao.caminho_livre("c3-x", d)
            finally:
                espiao.AQUI = orig
        self.assertTrue(a.endswith("2026-10-08-c3-x.serlog"))
        self.assertTrue(b.endswith("2026-10-08-c3-x-2.serlog"))

    def test_usb_puxado_vira_erro_tratado(self):
        class PortaQueCai(_MaquinaFalsa):
            def ler(self, limite):
                raise OSError(6, "Device not configured")
        with conexao_serial.ConexaoTR1000(porta=PortaQueCai()) as c:
            with self.assertRaises(conexao_serial.ErroConexao):
                c.aperto()


class TesteRevisaoPR3(unittest.TestCase):
    def test_faixas_somam_e_nao_encolhem(self):
        # o App rele parametros soltos (n = 1) em blocos que ja leu inteiros
        pacs = []
        for i, n in ((112, 292), (130, 1)):
            c = tr1000_serial.carga_ler(3, 0, 0, i, n)
            pacs.append(("TX", 0, tr1000_serial.pacote_dados(tr1000_serial.CAB_LEITURA, c)))
        todas = tr1000_serial.todas_as_leituras(pacs)
        self.assertEqual(todas[(3, 0, 0)], {(112, 292), (130, 1)})
        self.assertEqual(tr1000_serial.leituras_de_bloco(pacs)[(3, 0, 0)], (112, 292))

    def test_bloco_3_inteiro_continua_lido(self):
        self.assertEqual(conexao_serial.faixa_do_bloco(3, 0, 0), (112, 292))
        self.assertTrue(conexao_serial.leitura_permitida(3, 0, 0, 112, 292))

    def test_chave_nunca_lida_e_permission_error(self):
        with self.assertRaises(PermissionError):
            conexao_serial.faixa_do_bloco(118, 130, 0)     # x fora de 0..127
        with self.assertRaises(PermissionError):
            conexao_serial.faixa_do_bloco(999, 0, 0)       # bloco que nao existe

    def test_segundos_invalido_nao_quebra(self):
        import io, contextlib, sessao_c4
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(sessao_c4.main(["estado", "--segundos"]), 1)
            self.assertEqual(sessao_c4.main(["estado", "--segundos", "8s"]), 1)
        self.assertIn("precisa de um numero", buf.getvalue())

    def test_bloco_de_steps_um_lugar_so(self):
        self.assertEqual([tr1000_serial.bloco_de_steps(v) for v in (0, 1, 11)],
                         [118, 121, 151])


class TesteSessaoC4(unittest.TestCase):
    """Leituras ao vivo dos criterios 4 e 5: so le, e le o pattern inteiro."""

    def _com_maquina(self, m, func):
        import io, contextlib
        orig = conexao_serial.ConexaoTR1000

        class CxFalsa(orig):
            def __init__(s, nome_captura=None, **k):
                super().__init__(porta=m)
        conexao_serial.ConexaoTR1000 = CxFalsa
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                func()
        finally:
            conexao_serial.ConexaoTR1000 = orig
        return buf.getvalue()

    def test_pattern_le_nome_e_grade_sem_escrever(self):
        import sessao_c4
        m = _MaquinaFalsa()
        nome = [ord(ch) for ch in "Dub Techno      "] + [12800]
        bd = [0] * 131
        for passo in (0, 4, 8, 12):
            bd[passo * 4] = bd[passo * 4 + 1] = 0xA503C
        b3 = [0] * 292
        b3[2], b3[21], b3[36] = 1, 2, 12200       # 1-02, 122 BPM (medido 08/10)
        m.blocos = {(3, 0, 0): b3, (116, 1, 0): nome, (118, 1, 0): bd}
        m.zeros_ok = True                 # os outros 119 blocos: vazios
        saida = self._com_maquina(m, sessao_c4.cmd_pattern)
        self.assertIn("pattern 1-02 -> x 1, tempo 122.0", saida)
        self.assertIn("pattern 'Dub Techno', tempo 128.0", saida)
        self.assertIn("BD  x... x... x... x...", saida)
        escritas = [p for p in m.recebido if tr1000_serial.carga(p)[:1] == b"\x01"]
        self.assertEqual(escritas, [])
        # 1 aperto + bloco 3 + cabecalho + 12 bancos x 10 tracks
        self.assertEqual(len(m.recebido), 1 + 1 + 1 + 120)

    def test_pattern_fora_de_0_127_nao_e_lido(self):
        import sessao_c4
        m = _MaquinaFalsa()
        b3 = [0] * 292
        b3[2] = 130                               # fora de 0..127: nao existe
        m.blocos = {(3, 0, 0): b3}
        saida = self._com_maquina(m, sessao_c4.cmd_pattern)
        self.assertIn("fora do que se pode ler", saida)
        self.assertEqual(len(m.recebido), 1 + 1)  # aperto + bloco 3, mais nada

    def test_x_do_pattern_medido(self):
        # boot-1-02 e boot-2-01 (08/10/2026): o App leu os blocos de pattern
        # com x = 1 e x = 16, e o bloco 3 [2] trazia o mesmo numero
        self.assertEqual(tr1000_serial.nome_do_pattern(0), "1-01")
        self.assertEqual(tr1000_serial.nome_do_pattern(1), "1-02")
        self.assertEqual(tr1000_serial.nome_do_pattern(16), "2-01")
        for x in (0, 1, 16):
            self.assertIn((116, x, 0), conexao_serial.leituras_do_app())
        for cap, x in (("2026-10-08-boot-1-02.serlog", 1), ("2026-10-08-boot-2-01.serlog", 16)):
            v = tr1000_serial.ultimos_valores(tr1000_serial.pacotes(
                tr1000_serial.ler_serlog(os.path.join(AQUI, "capturas", cap))))
            self.assertEqual(v[(3, 0, 0)][tr1000_serial.OFF_PATTERN_GLOBAL], x)

    def test_mudancas_so_o_que_muda(self):
        import sessao_c4
        amostras = [(0.0, {(3, 7): 0, (3, 8): 5}), (0.1, {(3, 7): 1, (3, 8): 5}),
                    (0.2, {(3, 7): 1, (3, 8): 5}), (0.3, {(3, 7): 2, (3, 8): 5})]
        self.assertEqual(sessao_c4.mudancas(amostras),
                         {(3, 7): [(0.0, 0), (0.1, 1), (0.3, 2)]})

    def test_nao_ha_escrita_no_arquivo(self):
        with open(os.path.join(AQUI, "sessao_c4.py")) as f:
            fonte = f.read()
        self.assertNotIn(".escrever(", fonte)
        self.assertNotIn("pacote_escrita", fonte)


class _PortaLP:
    """Launchpad de mentira: a saida guarda o que foi mandado; a entrada
    entrega uma vez o que o teste enfileirou."""

    def __init__(self, entrada=()):
        self.enviado, self.fila = [], list(entrada)

    def send(self, msg):
        self.enviado.append(msg)

    def iter_pending(self):
        f, self.fila = self.fila, []
        return f

    def close(self):
        pass


# geometria real do learn no tr8s-grid (o mesmo par de aparelhos): o esquerdo
# girado 90 graus, o direito em pe
GEO = {"E": {"origem": 88, "passo_col": -10, "passo_lin": -1},
       "D": {"origem": 81, "passo_col": 1, "passo_lin": -10}}


def motor_cru(maquina=None):
    """Um Motor sem __init__ (sem abrir porta nenhuma), com Launchpad e
    maquina falsos - o padrao motor_cru() do tr8s-grid."""
    import threading, queue
    m = object.__new__(motor.Motor)
    m.log = lambda *a: None
    m.lock = threading.RLock()
    m.fila_cmd = queue.Queue()
    m.cache = {}
    m.geo = GEO
    m.lp_in = {"E": _PortaLP(), "D": _PortaLP()}
    m.lp_out = {"E": _PortaLP(), "D": _PortaLP()}
    m.maquina = maquina or _MaquinaFalsa()
    m.maquina.zeros_ok = True
    m.conexao = conexao_serial.ConexaoTR1000(porta=m.maquina)
    m.conexao.__enter__()
    m.x_pattern = 0
    m.modo_geral = motor.MODO_ON
    for tr in range(10):
        m.cache[(0, tr)] = [0] * 131
    return m


def _escritas(maq):
    import struct
    out = []
    for p in maq.recebido:
        c = tr1000_serial.carga(p)
        if c[:1] == b"\x01":
            out.append(struct.unpack_from("<HHHHI", c, 1))
    return out


class TesteRevisaoPR4(unittest.TestCase):
    def test_conexao_sem_captura_nao_guarda_nada(self):
        m = _MaquinaFalsa()
        with conexao_serial.ConexaoTR1000(porta=m) as c:
            c.aperto()
        self.assertEqual(c.registros, [])

    def test_leitura_recusada_nao_derruba_o_tick(self):
        maq = _MaquinaFalsa()
        b3 = [0] * 292
        b3[2] = 130                                    # fora de 0..127
        maq.blocos = {(3, 0, 0): b3}
        m = motor_cru(maq)
        m.proxima_releitura = 0
        m.tick()                                       # nao pode levantar
        self.assertEqual(m.x_pattern, 0)

    def test_variacao_que_nao_le_nao_troca(self):
        m = motor_cru()
        def falha(*a):
            raise conexao_serial.ErroConexao("sem resposta")
        m._ler = falha
        m.executar("variacao", 2)
        self.assertEqual(m.variacao, 0)

    def test_start_sem_stop_limpa_a_coluna_velha(self):
        import mido
        m = motor_cru()
        m.tocando, m.passo = True, 9
        pintadas = []
        m.pintar_coluna = pintadas.append
        m.clk = _PortaLP([mido.Message("start")])
        m._ler_clock()
        self.assertIn(9, pintadas)
        self.assertEqual(m.passo, 0)

    def test_o_sexto_pulso_ainda_e_do_step_0(self):
        import mido
        m = motor_cru()
        m.clk = _PortaLP([mido.Message("start")] + [mido.Message("clock")] * 6)
        m._ler_clock()
        self.assertEqual(m.passo, 0)
        m.clk.fila = [mido.Message("clock")]
        m._ler_clock()
        self.assertEqual(m.passo, 1)


class TesteNota(unittest.TestCase):
    def test_reproduz_os_valores_lidos(self):
        # lidos na S0 e no boot-1-02 (08/10/2026)
        for vel, valor in ((80, 0xA503C), (90, 0xA5A3C), (66, 0xA423C),
                           (74, 0xA4A3C), (88, 0xA583C)):
            self.assertEqual(tr1000_serial.nota(vel), valor)
            self.assertEqual(tr1000_serial.velocidade(valor), vel)
            self.assertTrue(tr1000_serial.eh_nota(valor))

    def test_fora_da_forma(self):
        for v in (0, 0xFF, 0xA503D, 0xB503C, 0xA003C):
            self.assertFalse(tr1000_serial.eh_nota(v), hex(v))
        with self.assertRaises(ValueError):
            tr1000_serial.nota(0)


class TestePortoesDaFase1(unittest.TestCase):
    """A escrita do grid (decisao do Luan, 08/10/2026): so steps, layers A/B."""

    def test_regra_da_escrita(self):
        ok = conexao_serial.escrita_permitida
        n = tr1000_serial.nota(127)
        self.assertTrue(ok(118, 0, 0, 1253, 0xFF))            # BD var A step 2 A
        self.assertTrue(ok(118, 127, 9, 1249 + 60 + 1, n))    # RC, step 16, B
        self.assertTrue(ok(151, 16, 3, 1249, n))              # Fill 4
        self.assertFalse(ok(118, 0, 0, 1251, n))              # slot 2
        self.assertFalse(ok(118, 0, 10, 1249, n))             # track 11
        self.assertFalse(ok(118, 128, 0, 1249, n))            # pattern 129
        self.assertFalse(ok(118, 0, 0, 1249 + 64, n))         # alem do step 16
        self.assertFalse(ok(119, 0, 0, 1249, n))              # bloco de motion
        self.assertFalse(ok(116, 0, 0, 988, n))               # cabecalho
        self.assertFalse(ok(118, 0, 0, 1249, 0))              # vazio nao: so pausa
        self.assertFalse(ok(118, 0, 0, 1249, 0xA503D))        # forma estranha
        self.assertTrue(ok(156, 126, 0, 962, 509))            # a C3 continua

    def test_leitura_de_qualquer_pattern(self):
        ok = conexao_serial.leitura_permitida
        self.assertTrue(ok(118, 127, 9, 1249, 131))
        self.assertTrue(ok(116, 77, 0, 988, 248))
        self.assertFalse(ok(118, 128, 0, 1249, 131))
        self.assertFalse(ok(3, 5, 0, 112, 292))               # so pattern generaliza


class TesteMotor(unittest.TestCase):
    def test_pads_ida_e_volta_nos_dois_aparelhos(self):
        m = motor_cru()
        for dev in ("E", "D"):
            for l in range(8):
                for c in range(8):
                    self.assertEqual(m._decodificar(dev, m.nota_de(dev, l, c)), (l, c))

    def test_toque_liga_e_desliga_os_dois_layers(self):
        m = motor_cru()
        m.alternar(0, 1)                                   # BD, step 2
        n80 = tr1000_serial.nota(80)
        self.assertEqual(_escritas(m.maquina),
                         [(118, 0, 0, 1253, n80), (118, 0, 0, 1254, n80)])
        self.assertEqual(m.slots(0, 1)[:2], [n80, n80])
        m.maquina.recebido.clear()
        m.alternar(0, 1)                                   # de novo: desliga
        self.assertEqual(_escritas(m.maquina),
                         [(118, 0, 0, 1253, 0xFF), (118, 0, 0, 1254, 0xFF)])

    def test_outra_velocity_reescreve_em_vez_de_desligar(self):
        m = motor_cru()
        m.alternar(0, 0)
        m.vel_idx = 4                                      # 66
        m.maquina.recebido.clear()
        m.alternar(0, 0)
        n66 = tr1000_serial.nota(66)
        self.assertEqual([e[4] for e in _escritas(m.maquina)], [n66, n66])

    def test_track_simples_so_slot_0_e_layer_b(self):
        m = motor_cru()
        m.alternar(6, 3)                                   # CH, step 4
        self.assertEqual([e[3] for e in _escritas(m.maquina)], [1249 + 12])
        m.maquina.recebido.clear()
        m.modo_layer = "B"
        m.alternar(1, 4)                                   # SD, step 5, so B
        self.assertEqual([e[2:4] for e in _escritas(m.maquina)], [(1, 1249 + 16 + 1)])

    def test_rolagem_muda_o_track(self):
        m = motor_cru()
        m.executar("rolar", +5)                            # trava em 2
        self.assertEqual(m.base_inst, 2)
        m.alternar(7, 0)                                   # ultima linha = RC
        self.assertEqual({e[2] for e in _escritas(m.maquina)}, {9})

    def test_linha_alem_dos_tracks_nao_escreve(self):
        m = motor_cru()
        m.base_inst = 3                                    # forcado: linha 7 = track 10
        m.alternar(7, 0)
        self.assertEqual(_escritas(m.maquina), [])

    def test_cores_espelham_o_painel(self):
        m = motor_cru()
        F, n, f = 0xFF, 0xA503C, 0xA423C
        m.cache[(0, 1)][0:4] = [n, n, F, F]                # vermelho
        m.cache[(0, 1)][4:8] = [F, n, 0, 0]                # so B: verde
        m.cache[(0, 1)][8:12] = [f, f, F, F]               # fraco
        m.cache[(0, 1)][12:16] = [F, F, F, F]              # pausa: apagado
        cores = [m.cor_do_step(1, s) for s in range(5)]
        import launchpad as lp
        self.assertEqual(cores, [lp.COR_FORTE, lp.COR_B, lp.COR_FRACA,
                                 lp.COR_OFF, lp.COR_TEMPO])

    def test_clock_so_anda_depois_do_start(self):
        import mido
        m = motor_cru()
        m.clk = _PortaLP([mido.Message("clock")] * 12)
        m._ler_clock()
        self.assertEqual((m.tocando, m.passo), (False, -1))   # parada: ignora
        m.clk.fila = [mido.Message("start")] + [mido.Message("clock")] * 13
        m._ler_clock()
        self.assertEqual((m.tocando, m.passo), (True, 2))     # 13 // 6
        m.clk.fila = [mido.Message("clock")] * (6 * 14)
        m._ler_clock()
        self.assertEqual(m.passo, 0)                          # deu a volta em 16
        m.clk.fila = [mido.Message("stop")]
        m._ler_clock()
        self.assertEqual((m.tocando, m.passo), (False, -1))

    def test_troca_de_pattern_no_painel_rele_com_o_novo_x(self):
        maq = _MaquinaFalsa()
        b3 = [0] * 292
        b3[2] = 16                                            # 2-01
        maq.blocos = {(3, 0, 0): b3}
        m = motor_cru(maq)
        self.assertTrue(m.reler())
        self.assertEqual(m.x_pattern, 16)
        lidos = {tr1000_serial.carga(p)[1:7] for p in maq.recebido
                 if tr1000_serial.carga(p)[:1] == b"\x82"}
        import struct
        self.assertIn(struct.pack("<HHH", 118, 16, 9), lidos)

    def test_pad_no_hardware_vira_escrita(self):
        import mido
        m = motor_cru()
        nota_pad = m.nota_de("D", 0, 3)                       # direito: step 12
        m.lp_in["D"].fila = [mido.Message("note_on", note=nota_pad, velocity=100)]
        m._ler_pads()
        self.assertEqual([e[3] for e in _escritas(m.maquina)], [1249 + 44, 1249 + 45])

    def test_botoes(self):
        import mido
        m = motor_cru()
        m.lp_in["E"].fila = [mido.Message("control_change", control=79, value=127)]
        m.lp_in["D"].fila = [mido.Message("control_change", control=19, value=127),
                             mido.Message("control_change", control=95, value=127)]
        m._ler_pads()
        self.assertEqual((m.variacao, m.vel_idx, m.modo_layer), (1, 7, "B"))


class TesteControladorasMapear(unittest.TestCase):
    def test_rotulos_das_placas(self):
        # fotos de 09/10/2026: 24 + 50 knobs, sem id repetido
        self.assertEqual(len(controladoras.ROTULOS_MC24), 24)
        self.assertEqual(len(controladoras.ROTULOS_MC50), 50)
        ids = [i for rs in controladoras.ROTULOS.values() for i, _ in rs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(controladoras.ROTULOS_MC50[0], ("bd.gain", "BD GAIN"))
        self.assertEqual(controladoras.ROTULOS_MC50[-1], ("rc.lfo", "RC LFO DTH"))

    def test_tipo_do_knob(self):
        d = controladoras.detectar_tipo
        self.assertEqual(d(range(30, 90)), "absoluto")
        self.assertEqual(d([1, 1, 2, 1, 127, 127, 126]), "relativo")
        self.assertEqual(d([65, 65, 66, 65, 63, 63, 62]), "relativo")
        self.assertEqual(d([127, 127, 127]), "absoluto")       # potenciometro no fim

    def test_chave_dominante_e_recusa_o_ja_mapeado(self):
        evs = [("MC-24", 0, 20, v) for v in (10, 11, 12)] + [("MC-24", 0, 21, 5)]
        self.assertEqual(controladoras.chave_dominante(evs), ("MC-24", 0, 20))
        self.assertIsNone(controladoras.chave_dominante(evs, {("MC-24", 0, 20)}))
        self.assertIsNone(controladoras.chave_dominante(evs[:2]))   # pouco: ruido

    def test_sequencia_oferece_o_proximo_cc(self):
        ids = ["a", "b", "c", "d"]
        knobs = {i: dict(porta="MC-24", canal=0, cc=20 + n) for n, i in enumerate(ids)}
        self.assertEqual(controladoras.sequencia(knobs, ids), ("MC-24", 0, 24))
        knobs["d"]["cc"] = 40
        self.assertIsNone(controladoras.sequencia(knobs, ids))
        self.assertIsNone(controladoras.sequencia(knobs, ids[:3]))

    def test_resumo_do_giro(self):
        self.assertIn("faixa inteira", controladoras.resumo_do_giro([60, 0, 127, 30]))
        self.assertNotIn("faixa inteira", controladoras.resumo_do_giro([10, 90]))
        self.assertEqual(controladoras.resumo_do_giro([]), "nada")

    def test_mapa_ida_e_volta(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = os.path.join(tmp, "m", "controladoras.json")
            m = controladoras.carregar_mapa(c)
            m["knobs"]["bd.gain"] = dict(porta="CM-MC50", canal=0, cc=1,
                                         tipo="absoluto", palpite=False)
            controladoras.salvar_mapa(m, c)
            m2 = controladoras.carregar_mapa(c)
        self.assertEqual(controladoras.indice_reverso(m2), {("CM-MC50", 0, 1): "bd.gain"})


def _mapa_falso(faixa=(0, 127)):
    """Um knob por rotulo, canal 1, CC na ordem das placas (o real fica no
    mapas/, que e do hardware do Luan)."""
    knobs = {}
    for porta, rotulos in controladoras.ROTULOS.items():
        for cc, (i, _) in enumerate(rotulos):
            knobs[i] = dict(porta=porta, canal=0, cc=cc, tipo="absoluto",
                            palpite=False, faixa=list(faixa))
    return {"versao": 1, "knobs": knobs}


def motor_com_knobs(maq=None, faixa=(0, 127)):
    m = motor_cru(maq)
    m.x_kit = 0
    mapa = _mapa_falso(faixa)
    m.ctl = object.__new__(controladoras.Controladoras)
    m.ctl.mapa, m.ctl.rev = mapa, controladoras.indice_reverso(mapa)
    m.ctl.portas = {"MC-24": _PortaLP(), "CM-MC50": _PortaLP()}
    m.log_visto = []
    m.log = m.log_visto.append
    m.pickup = m.novo_pickup(mapa)
    m.agora = 100.0
    return m


def girar(m, id, *ccs, num_tick=False):
    """Os CCs de um knob, um por tick do motor (o relogio anda 1 s por tick),
    ou todos num tick so."""
    import mido
    k = m.ctl.mapa["knobs"][id]
    for lote in ([ccs] if num_tick else [[v] for v in ccs]):
        m.ctl.portas[k["porta"]].fila += [
            mido.Message("control_change", channel=k["canal"], control=k["cc"], value=v)
            for v in lote]
        m.agora += 1
        m._ler_controladoras(m.agora)


class TesteControladorasNoMotor(unittest.TestCase):
    """B5: os knobs escrevendo na maquina - pickup, juntar escritas, type."""

    def test_ler_entrega_so_o_ultimo_de_cada_knob(self):
        import mido
        m = motor_com_knobs()
        cc_pan = m.ctl.mapa["knobs"]["bd.pan"]["cc"]
        m.ctl.portas["CM-MC50"].fila = [
            mido.Message("control_change", channel=0, control=cc_pan, value=v)
            for v in (1, 2, 3)] + [
            mido.Message("control_change", channel=9, control=cc_pan, value=9),  # outro canal
            mido.Message("note_on", note=1)]
        self.assertEqual(m.ctl.ler(), {"bd.pan": 3})

    def test_pickup_so_escreve_depois_de_cruzar_o_valor_da_maquina(self):
        maq = _MaquinaFalsa()
        maq.valores[(13, 0, 0, 556)] = 500                 # BD PAN no meio
        m = motor_com_knobs(maq)
        girar(m, "bd.pan", 0)
        girar(m, "bd.pan", 30)                             # 236: ainda longe
        self.assertEqual(_escritas(maq), [])
        girar(m, "bd.pan", 70)                             # 551: passou do 500
        self.assertEqual(_escritas(maq), [(13, 0, 0, 556, 551)])

    def test_perto_do_valor_pega_de_cara(self):
        maq = _MaquinaFalsa()
        maq.valores[(13, 0, 9, 557)] = 500                 # RC RVB SND
        m = motor_com_knobs(maq)
        girar(m, "rc.rvb", 64)                             # 504: a um passo (8)
        self.assertEqual(_escritas(maq), [(13, 0, 9, 557, 504)])

    def test_cinquenta_mensagens_num_tick_viram_uma_escrita(self):
        maq = _MaquinaFalsa()
        m = motor_com_knobs(maq)                           # maquina em 0
        girar(m, "sd.dly", 0)                              # pega no 0, nada a escrever
        girar(m, "sd.dly", *range(50, 100), num_tick=True)
        self.assertEqual(_escritas(maq), [(13, 0, 1, 558, 780)])  # so o 99

    def test_escritas_no_maximo_a_cada_30_ms(self):
        maq = _MaquinaFalsa()
        m = motor_com_knobs(maq)
        girar(m, "bd.gain", 0, 10)
        m.agora += 0.01 - 1                                # o proximo tick: +10 ms
        girar(m, "bd.gain", 20)
        self.assertEqual(len(_escritas(maq)), 1)           # o 20 espera
        m._ler_controladoras(m.agora + 0.05)
        self.assertEqual(_escritas(maq)[-1], (116, 0, 0, 1014, 104))

    def test_troca_de_pattern_solta_os_knobs(self):
        maq = _MaquinaFalsa()
        b3 = [0] * 292
        maq.blocos = {(3, 0, 0): b3}
        m = motor_com_knobs(maq)
        girar(m, "bd.pan", 0, 64)
        self.assertTrue(m.pickup.estado["bd.pan"]["pego"])
        b3[2] = b3[3] = b3[4] = 16                         # o painel foi para 2-01
        m.reler()
        self.assertEqual((m.x_pattern, m.x_kit), (16, 16))
        self.assertEqual(m.pickup.estado, {})
        maq.valores[(13, 16, 0, 556)] = 1000
        n = len(_escritas(maq))
        girar(m, "bd.pan", 10)                             # longe do 1000 do kit novo
        self.assertEqual(len(_escritas(maq)), n)

    def test_kit_incerto_para_os_knobs_de_kit_mas_nao_o_gain(self):
        maq = _MaquinaFalsa()
        b3 = [0] * 292
        b3[3] = 5                                          # [2] 0, [3] 5, [4] 0
        maq.blocos = {(3, 0, 0): b3}
        m = motor_com_knobs(maq)
        m.reler()
        self.assertIsNone(m.x_kit)
        girar(m, "bd.pan", 0, 64)
        girar(m, "reverb.time", 0, 64)
        girar(m, "mfx.p1", 0, 64)
        girar(m, "bd.gain", 0, 64)                         # o gain mora no PATTERN
        self.assertEqual([e[0] for e in _escritas(maq)], [116])

    def test_mfx_segue_o_type_e_o_sync_da_maquina(self):
        maq = _MaquinaFalsa()
        maq.valores[(7, 0, 0, 2512)] = 6                   # FLANGER
        maq.valores[(7, 0, 0, 2561)] = 1                   # SYNC ON
        m = motor_com_knobs(maq)
        girar(m, "mfx.p2", 0, 10)                          # STEP com SYNC ON
        self.assertEqual(_escritas(maq), [(7, 0, 0, 2564, 20)])
        maq.valores[(7, 0, 0, 2561)] = 0                   # SYNC OFF no painel
        m.pickup.esquecer_seletores()                      # (a releitura de 0,5 s)
        girar(m, "mfx.p2", 12)                             # outro indice: pickup de novo
        self.assertEqual(len(_escritas(maq)), 1)
        girar(m, "mfx.p2", 0)                              # cruzou o 0 do 2557
        girar(m, "mfx.p2", 30)
        self.assertEqual(_escritas(maq)[-1], (7, 0, 0, 2557, 60))

    def test_o_knob_de_type_muda_o_que_os_outros_escrevem(self):
        maq = _MaquinaFalsa()
        m = motor_com_knobs(maq)                           # MFX em BYPASS (0)
        girar(m, "mfx.type", 0, 20)                        # 20 * 18 / 127 = 3: LOOPER
        self.assertEqual(_escritas(maq), [(7, 0, 0, 2512, 3)])
        self.assertEqual(m.pickup.seletores["mfx.type"], 3)
        self.assertIn("mfx.type: DJFX LOOPER", m.log_visto)
        girar(m, "mfx.p2", 0, 64)                          # SPEED do LOOPER
        self.assertEqual(_escritas(maq)[-1], (7, 0, 0, 2546, 101))

    def test_type_sem_entrada_deixa_o_knob_parado(self):
        maq = _MaquinaFalsa()
        maq.valores[(7, 0, 0, 2512)] = 1                   # CRUSHER: 3 parametros
        m = motor_com_knobs(maq)
        girar(m, "mfx.p5", 0, 64)
        self.assertEqual(_escritas(maq), [])
        self.assertNotIn("mfx.p5", m.pickup.estado)

    def test_escrita_que_falha_solta_o_knob(self):
        maq = _MaquinaFalsa()
        maq.valores[(22, 0, 0, 606)] = 1000                # LFO DTH do BD no centro
        m = motor_com_knobs(maq)

        def recusa(*a):
            raise PermissionError("teste")
        m.pickup.escrever = recusa
        girar(m, "bd.lfo", 64)                             # 1004: pega, tenta, falha
        self.assertNotIn("bd.lfo", m.pickup.estado)

    def test_faixa_do_knob_que_para_em_125_cobre_a_faixa(self):
        maq = _MaquinaFalsa()
        m = motor_com_knobs(maq, faixa=(0, 125))
        girar(m, "reverb.type", 0, 125)
        self.assertEqual(_escritas(maq)[-1], (5, 0, 0, 2368, 5))

    def test_sem_controladoras_o_tick_roda(self):
        m = motor_cru()
        m.proxima_releitura = float("inf")
        m.tick()                                           # ctl None: nada quebra

    def test_leitura_dos_parametros_em_outro_kit(self):
        ok = conexao_serial.leitura_permitida
        self.assertTrue(ok(7, 5, 0, 2564, 1))              # STEP do FLANGER, kit 6
        self.assertTrue(ok(6, 16, 0, 2429, 1))             # DELAY: SYNC TIME
        self.assertTrue(ok(112, 3, 0, 606, 1))             # LFO DTH do RC
        self.assertFalse(ok(7, 5, 0, 2555, 1))             # o App nunca leu
        self.assertFalse(ok(7, 128, 0, 2564, 1))           # x fora de 0..127


class TesteParametros(unittest.TestCase):
    """A tabela decifrada em 09/10/2026 (mixer-bd/rc, kit-reverb)."""

    def test_enderecos_medidos(self):
        T = parametros.TABELA
        self.assertEqual(parametros.endereco(T["bd.gain"], 0), (116, 0, 0, 1014))
        self.assertEqual(parametros.endereco(T["rc.gain"], 0, 9), (116, 0, 0, 1023))
        self.assertEqual(parametros.endereco(T["rc.pan"], 0, 9), (13, 0, 9, 556))
        self.assertEqual(parametros.endereco(T["bd.dly"], 16, 0), (13, 16, 0, 558))
        self.assertEqual(parametros.endereco(T["reverb.type"], 1), (5, 1, 0, 2368))

    def test_todo_knob_das_placas_esta_na_tabela_ou_pendente(self):
        ids = {i for rs in controladoras.ROTULOS.values() for i, _ in rs}
        tem = set(parametros.TABELA) | set(parametros.POR_TIPO)
        self.assertEqual(ids, tem | set(parametros.PENDENTES))
        self.assertFalse(tem & set(parametros.PENDENTES))

    def test_lfo_dth_e_o_amount_do_lfo_do_inst(self):
        T, ok = parametros.TABELA, conexao_serial.escrita_permitida
        self.assertEqual(parametros.endereco(T["bd.lfo"], 0, 0), (22, 0, 0, 606))
        self.assertEqual(parametros.endereco(T["rc.lfo"], 0, 9), (112, 0, 0, 606))
        self.assertTrue(ok(112, 0, 0, 606, 1500))
        self.assertFalse(ok(112, 0, 0, 606, 499))
        self.assertFalse(ok(122, 0, 0, 606, 1000))              # nao ha track 11
        self.assertFalse(ok(27, 0, 0, 606, 1000))               # fora do passo de 10

    def test_lfo_do_kit(self):
        e = parametros.entrada_para
        self.assertEqual(e("lfo.waveform").indice, 519)
        self.assertEqual(e("lfo.rate", 0).maximo, 180)         # SYNC = TIME
        self.assertEqual(e("lfo.rate", 1).indice, 530)          # STEP
        self.assertEqual(e("lfo.rate", 2).maximo, 24)           # NOTE: 4/1 .. 1/64
        self.assertIsNone(e("lfo.rate", 3))
        self.assertFalse(conexao_serial.escrita_permitida(10, 0, 0, 532, 1))  # SYNC nao e knob

    def test_mfx_por_type(self):
        e, ok = parametros.entrada_para, conexao_serial.escrita_permitida
        self.assertEqual(e("mfx.type").indice, 2512)
        self.assertEqual(e("mfx.p1", 1).indice, 2536)             # CRUSHER: BALANCE
        self.assertEqual(e("mfx.p6", 2).maximo, 48)               # F+DRIVE: LOW GAIN
        self.assertEqual(e("mfx.p7", 6).indice, 2562)             # FLANGER: LOW CUT
        self.assertEqual(e("mfx.p7", 9).maximo, 80)               # COMPRESSOR: GAIN
        self.assertEqual(e("mfx.p4", 11).indice, 2594)            # SDD-320: LEVEL
        self.assertIsNone(e("mfx.p4", 1))                         # CRUSHER so tem 3
        self.assertEqual(e("mfx.p7", 13).indice, 2605)            # TRANSIENT2: BYPASS
        self.assertEqual(e("mfx.p3", 14).maximo, 1)               # NOISE: DIRECTION
        self.assertEqual(e("mfx.p2", 18).indice, 2622)            # DJFX DELAY: TIME
        self.assertIsNone(e("mfx.p6", 18))                        # DJFX DELAY tem 5
        self.assertEqual(len(parametros.MFX_TIPOS), 19)

    def test_step_do_flanger_e_do_phaser_depende_do_sync(self):
        e, ok = parametros.entrada_para, conexao_serial.escrita_permitida
        self.assertEqual(e("mfx.p2", 6, {"mfx.sync.flanger": 1}).indice, 2564)
        self.assertEqual(e("mfx.p2", 6, {"mfx.sync.flanger": 0}).indice, 2557)
        self.assertEqual(e("mfx.p2", 7, {"mfx.sync.phaser": 0}).indice, 2566)
        self.assertEqual(e("mfx.p2", 7, {"mfx.sync.phaser": 1}).indice, 2572)
        self.assertIsNone(e("mfx.p2", 6))                         # SYNC nao lido: inativo
        self.assertIsNone(e("mfx.p2", 6, {"mfx.sync.phaser": 1}))   # o SYNC do outro
        self.assertEqual(e("mfx.p1", 6).indice, 2556)             # DEPTH nao depende
        self.assertTrue(ok(7, 0, 0, 2557, 255))                   # os dois sao escreviveis
        self.assertTrue(ok(7, 0, 0, 2572, 0))
        self.assertFalse(ok(7, 0, 0, 2570, 1))                    # o SYNC em si nao
        self.assertTrue(ok(7, 3, 0, 2546, 200))
        self.assertFalse(ok(7, 0, 0, 2546, 201))                  # SPEED vai a 200
        self.assertFalse(ok(7, 0, 0, 2514, 1))                    # FX ROUTE nao e knob
        self.assertFalse(ok(7, 0, 0, 2561, 1))                    # SYNC do FLANGER
        self.assertTrue(ok(7, 0, 0, 2512, 0))                     # BYPASS (mfx-3)
        self.assertFalse(ok(7, 0, 0, 2512, 19))
        self.assertFalse(ok(7, 0, 0, 2601, 3))                    # Q do TRANSIENT2: fora

    def test_delay_por_type(self):
        e = parametros.entrada_para
        self.assertEqual(e("delay.p1").indice, 2409)              # LEVEL, sempre
        self.assertEqual(e("delay.p3", 1).indice, 2438)           # FEEDBACK no PAN
        self.assertEqual(e("delay.p3", 2).indice, 2447)           # ECHO: INTENSITY
        self.assertEqual(e("delay.p6", 3).indice, 2464)           # PITCH: COARSE
        self.assertEqual(e("delay.p2", 0).indice, 2429)           # DELAY: SYNC TIME
        self.assertIsNone(e("delay.p2", 4))                       # type que nao existe
        ok = conexao_serial.escrita_permitida
        self.assertTrue(ok(6, 0, 0, 2438, 999))
        self.assertFalse(ok(6, 0, 0, 2438, 1000))
        self.assertTrue(ok(6, 0, 0, 2407, 3))                     # PITCH
        self.assertFalse(ok(6, 0, 0, 2444, 50))                   # TAP: fora das placas

    def test_portao_aceita_so_dentro_da_faixa(self):
        ok = conexao_serial.escrita_permitida
        self.assertTrue(ok(116, 0, 0, 1023, 661))             # RC gain, max
        self.assertFalse(ok(116, 0, 0, 1023, 662))            # acima da faixa
        self.assertFalse(ok(116, 0, 0, 1024, 100))            # track 11
        self.assertTrue(ok(13, 5, 9, 556, 500))               # RC pan, kit 6
        self.assertFalse(ok(13, 0, 10, 556, 500))             # y fora
        self.assertFalse(ok(13, 0, 0, 559, 10))               # indice nao decifrado
        self.assertTrue(ok(5, 0, 0, 2368, 5))                 # reverb PLATE..MOD
        self.assertFalse(ok(5, 0, 0, 2368, 6))                # tipo que nao existe
        self.assertFalse(ok(5, 0, 1, 2368, 1))                # reverb nao e por track

    def test_conversao_do_knob(self):
        T = parametros.TABELA
        self.assertEqual(parametros.converter(T["bd.pan"], 0, 0, 125), 0)
        self.assertEqual(parametros.converter(T["bd.pan"], 125, 0, 125), 1000)  # para em 125
        self.assertEqual(parametros.converter(T["reverb.type"], 127), 5)
        self.assertEqual(parametros.converter(T["reverb.lowcut"], 64), 9)

    def test_leitura_dos_blocos_de_kit_para_qualquer_kit(self):
        ok = conexao_serial.leitura_permitida
        self.assertTrue(ok(13, 77, 9, 556, 9))
        self.assertTrue(ok(5, 100, 0, 2368, 14))
        self.assertFalse(ok(13, 128, 0, 556, 9))


def _relogio_rapido(passo=0.3):
    """Relogio que anda `passo` s por consulta: a espera de 1 s acaba logo.
    Passo grande demais estoura o prazo antes de a maquina falsa terminar de
    entregar uma resposta (ela entrega 5 bytes por leitura)."""
    t = [0.0]

    def agora():
        t[0] += passo
        return t[0]
    return agora


class TesteEspiaoPreparo(unittest.TestCase):
    """O App em /Applications nunca e escrito: ele so pode aparecer como
    ORIGEM do ditto. Todo o resto mira o cache (ou espiao/, onde mora o
    .dylib). Confere a lista de comandos sem rodar nada."""

    def test_nada_escreve_no_original(self):
        permitido = (espiao.CACHE, os.path.join(AQUI, "espiao"))
        for cmd in espiao.comandos_preparar():
            caminhos = [a for a in cmd[1:] if a.startswith("/")]
            if cmd[0] == "ditto":
                self.assertEqual(caminhos[0], espiao.ORIGINAL)
                caminhos = caminhos[1:]
            if cmd[0] == "clang":
                caminhos = [cmd[cmd.index("-o") + 1]]      # so a saida
            for c in caminhos:
                self.assertTrue(c.startswith(permitido), f"{cmd[0]} mira {c}")

    def test_copia_mora_no_cache(self):
        self.assertTrue(espiao.COPIA.startswith(espiao.CACHE + os.sep))
        self.assertFalse(espiao.COPIA.startswith("/Applications"))

    def test_assinatura_nova_nao_herda_o_runtime(self):
        cs = [c for c in espiao.comandos_preparar() if c[0] == "codesign"][0]
        self.assertIn("--force", cs)
        self.assertFalse(any(a.startswith("--preserve-metadata") or
                             a == "--options" for a in cs))

    def test_nome_da_captura(self):
        import datetime
        c = espiao.caminho_captura("boot-app", datetime.date(2026, 10, 8))
        self.assertTrue(c.endswith("capturas/2026-10-08-boot-app.serlog"))


class TesteFx(unittest.TestCase):
    def _rodar(self, msgs):
        import io, contextlib
        orig = tr1000_sysex.load
        tr1000_sysex.load = lambda *a, **k: msgs
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                tr1000_sysex.cmd_fx("x.mmon")
            return buf.getvalue()
        finally:
            tr1000_sysex.load = orig

    def test_escrita_curta_mostra_todos_os_bytes(self):
        saida = self._rodar([_m("TX", roland.DT1, (0x10, 0, 0, 0x20),
                                [0x01, 0x7F], 0)])
        self.assertIn("01, 7F", saida)
        self.assertIn("(2 bytes)", saida)

    def test_dt1_sem_dados_nao_quebra(self):
        saida = self._rodar([_m("TX", roland.DT1, (0x10, 0, 0, 0x20), [], 0)])
        self.assertIn("nenhuma MUDANCA", saida)


class TesteCatalogo(unittest.TestCase):
    def test_serie_comprime(self):
        self.assertEqual(catalogo_app.comprimir(["note0", "note1", "note2", "X"]),
                         [{"nome": "note", "de": 0, "ate": 2}, "X"])

    def test_ordem_alfabetica_nao_vira_serie(self):
        # existe no binario: QUANTIZE1, QUANTIZE10, QUANTIZE2... - comprimir
        # esconderia uma ordem que nao e de offset
        c = catalogo_app.comprimir(["QUANTIZE1", "QUANTIZE10", "QUANTIZE2"])
        self.assertEqual(c, ["QUANTIZE1", "QUANTIZE10", "QUANTIZE2"])

    def test_serie_de_um_vira_string(self):
        self.assertEqual(catalogo_app.comprimir(["CTRL3"]), ["CTRL3"])

    def test_segmentar_pelas_ancoras_em_ordem(self):
        nomes = ["lixo", "Bright", "a", "Device ID", "b", "KIT_NUM", "c"]
        blocos = dict(catalogo_app.segmentar(nomes))
        self.assertEqual(blocos["inicio"], ["lixo"])
        self.assertEqual(blocos["sistema"], ["Bright", "a"])
        self.assertEqual(blocos["performance"], ["KIT_NUM", "c"])

    def test_so_a_tabela_contigua_em_volta_da_ancora(self):
        dados = (b"\x00longe\x00" + b"\xff" * 64 +
                 b"\x00Bright\x00Device ID\x00KIT_NUM\x00PTN_NUM\x00\x00\x00"
                 + b"\xff" * 64 + b"\x00depois\x00")
        regiao, blocos = catalogo_app.extrair(dados)
        nomes = [s for _, s in regiao]
        self.assertEqual(nomes, ["Bright", "Device ID", "KIT_NUM", "PTN_NUM"])

    def test_lixo_nas_pontas_sai(self):
        # no App 1.10 a regiao terminava em "... ABS END MSB | 10"
        dados = (b"\xff" * 64 + b"\x009\x00Bright\x00KIT_NUM\x00ABS END MSB"
                 b"\x0010\x00" + b"\xff" * 64)
        nomes = [s for _, s in catalogo_app.extrair(dados)[0]]
        self.assertEqual(nomes, ["Bright", "KIT_NUM", "ABS END MSB"])

    def test_sem_ancora_nao_inventa(self):
        regiao, _ = catalogo_app.extrair(b"\x00nada\x00aqui\x00")
        self.assertEqual(regiao, [])


class TesteModeloDoManual(unittest.TestCase):
    def test_sessenta_e_seis_ccs(self):
        # "66 CCs, todos Tx e Rx" (manual MIC p.1) - se alguem apagar ou
        # duplicar uma linha da tabela, isto pega
        self.assertEqual(len(tr1000.CC), 66)

    def test_notas_padrao_sem_colisao(self):
        todas = [n for t in tr1000.NOTAS_PADRAO.values() for n in t if n]
        self.assertEqual(len(todas), len(set(todas)))

    def test_nome_da_nota(self):
        self.assertEqual(tr1000.nome_da_nota(36), "BD")
        self.assertEqual(tr1000.nome_da_nota(35), "BD (A)")
        self.assertEqual(tr1000.nome_da_nota(99), "BD (B)")
        self.assertEqual(tr1000.nome_da_nota(56), "RS (ALT)")
        self.assertIsNone(tr1000.nome_da_nota(0))

    def test_doze_linhas(self):
        self.assertEqual(len(tr1000.LINHAS), 12)


class _EntradaFalsa:
    """Porta de entrada de mentira: nada chega. Depois de muitas leituras
    levanta KeyboardInterrupt, que e como o Luan sai do sniff."""
    abertas = []

    def __init__(self, idx, nome=None, **k):
        self.idx, self.name, self.fechada, self.leituras = idx, nome, False, 0
        _EntradaFalsa.abertas.append(self)

    def iter_pending(self):
        self.leituras += 1
        if self.leituras > 300:
            raise KeyboardInterrupt
        return []

    def close(self):
        self.fechada = True

    def __enter__(self): return self
    def __exit__(self, *e): self.close()


class _SaidaFalsa:
    enviados = []

    def __init__(self, idx, nome=None):
        self.idx, self.name = idx, nome

    def send(self, msg):
        _SaidaFalsa.enviados.append(list(msg.bytes()))

    def send_bytes(self, b):
        _SaidaFalsa.enviados.append(list(b))

    def close(self): pass
    def __enter__(self): return self
    def __exit__(self, *e): self.close()


class TestePortaoDaFase0(unittest.TestCase):
    """Nada escreve no mapa de enderecos antes de a fase 0 terminar
    (REFERENCIA 3.1). Quando a sessao C3 provar a primeira escrita, este teste
    muda junto com o PR que a usar - nao antes.

    Comportamental, nao textual (revisao de 07/10/2026): procurar a palavra
    "montar_rq1" no fonte deixava passar um RQ1 montado na mao. Aqui as portas
    sao falsas, cada comando da CLI roda, e o que SAIU e conferido byte a byte:
    o unico SysEx permitido e o Identity Request universal."""

    PORTAS_IN = [(4, "TR-1000"), (5, "TR-1000 CTRL"), (6, "TR-1000 MIDI IN")]
    PORTAS_OUT = [(4, "TR-1000"), (5, "TR-1000 CTRL"), (6, "TR-1000 MIDI OUT 1")]

    def setUp(self):
        try:
            import lp_tr1000
        except ImportError as e:            # mido/rtmidi ausentes
            self.skipTest(f"lp_tr1000 nao importa aqui: {e}")
        self.lp = lp_tr1000
        self._orig = {k: getattr(lp_tr1000, k) for k in
                      ("EntradaMIDI", "SaidaMIDI", "listar_portas",
                       "porta_exata", "AUTOTESTE_S")}
        _EntradaFalsa.abertas, _SaidaFalsa.enviados = [], []
        listar = lambda entradas=True: list(
            self.PORTAS_IN if entradas else self.PORTAS_OUT)
        lp_tr1000.EntradaMIDI = _EntradaFalsa
        lp_tr1000.SaidaMIDI = _SaidaFalsa
        lp_tr1000.listar_portas = listar
        lp_tr1000.porta_exata = lambda nome, entradas=True, portas=None: next(
            ((i, n) for i, n in listar(entradas) if n == nome), None)
        lp_tr1000.AUTOTESTE_S = 0.01

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(self.lp, k, v)

    def _rodar(self, comando, argv):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.lp.COMANDOS[comando](argv)

    def _so_identidade(self):
        self.assertTrue(_SaidaFalsa.enviados)          # o autoteste rodou
        for b in _SaidaFalsa.enviados:
            self.assertEqual(b, roland.IDENTITY_REQUEST)

    def _tudo_fechado(self):
        self.assertTrue(_EntradaFalsa.abertas)
        for p in _EntradaFalsa.abertas:
            self.assertTrue(p.fechada, f"porta {p.name} ficou aberta")

    def test_identidade(self):
        self._rodar("identidade", [])
        self._so_identidade(); self._tudo_fechado()

    def test_escutar(self):
        self._rodar("escutar", ["--segundos", "0.05"])
        self._so_identidade(); self._tudo_fechado()

    def test_sniff_sai_no_ctrl_c_fechando_tudo(self):
        self._rodar("sniff", [])
        self._so_identidade(); self._tudo_fechado()

    def test_ports_nao_manda_nada(self):
        import mido
        orig = (mido.get_input_names, mido.get_output_names)
        mido.get_input_names = mido.get_output_names = lambda: []
        try:
            self._rodar("ports", [])
        finally:
            mido.get_input_names, mido.get_output_names = orig
        self.assertEqual(_SaidaFalsa.enviados, [])


class TesteSintaxe(unittest.TestCase):
    def test_todo_py_compila(self):
        with tempfile.TemporaryDirectory() as tmp:
            for nome in sorted(os.listdir(AQUI)):
                if nome.endswith(".py"):
                    py_compile.compile(os.path.join(AQUI, nome),
                                       cfile=os.path.join(tmp, nome + "c"),
                                       doraise=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)

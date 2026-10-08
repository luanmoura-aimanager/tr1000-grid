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
  - o portao da fase 0: o lp_tr1000.py nao monta DT1 nem RQ1
"""
import os, py_compile, sys, tempfile, unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import roland
import tr1000
import tr1000_sysex
import catalogo_app

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

    def test_checksum_ruim_nao_vira_chute(self):
        # sem cabecalho conhecido, so aceita o tamanho de model ID em que o
        # checksum fecha; estragado, nao decodifica - melhor que decodificar
        # errado sem aviso
        ruim = list(TR8S_REAL); ruim[-2] = 0x00
        self.assertIsNone(roland.decodificar(ruim))
        d = roland.decodificar(ruim, cabecalho=TR8S_CAB)
        self.assertFalse(d["chk_ok"])

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


class TestePortaoDaFase0(unittest.TestCase):
    """Nada escreve no mapa de enderecos antes de a fase 0 terminar
    (REFERENCIA 3, criterio de saida). Quando a sessao C3 provar a primeira
    escrita, este teste sai junto com o PR que a usar - nao antes."""

    def test_cli_nao_monta_dt1_nem_rq1(self):
        with open(os.path.join(AQUI, "lp_tr1000.py")) as f:
            fonte = f.read()
        for proibido in ("montar_dt1", "montar_rq1"):
            self.assertNotIn(proibido, fonte)


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

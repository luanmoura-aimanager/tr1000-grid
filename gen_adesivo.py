#!/usr/bin/env python3
"""
gen_adesivo.py - gera adesivo.pdf: as etiquetas do layout A (escolhido pelo Luan
em 10/10/2026) em TAMANHO REAL, para colar nos botoes de borda dos dois
Launchpad Mini MK3 e embaixo de cada coluna de pads (os numeros dos steps).

    python3 gen_adesivo.py               # 100%
    python3 gen_adesivo.py --medido 93   # a impressora do Luan imprimiu a regua
                                         # de 100 mm com 93: sai pre-escalada

Fork do ../tr8s-grid/gen_adesivo.py - as medidas (botao de 15 mm, etiqueta de
13,3), a regua, o --medido e o "uma etiqueta por vez" vem de la, com os porques
nos comentarios de la. O que muda aqui e o CONTEUDO (o layout A da TR-1000) e a
fileira 6, nova: os numeros dos steps, em preto com letra branca como o proprio
Launchpad, recortados um a um (o passo entre pads nao importa).

POR QUE FILEIRAS E UM MAPA: as etiquetas em L ao redor de dois grids nao cabem
num A4. A folha traz as fileiras (o que se recorta) e, embaixo, um mapa fora de
escala dizendo onde cada fileira vai.
"""
import os, sys
import fitz

AQUI = os.path.dirname(os.path.abspath(__file__))

# ── medidas, em mm (as do tr8s-grid, medidas no aparelho) ─────
BOTAO = 15.0                   # lado do botao de borda do Mini MK3
# A etiqueta sai menor que o botao para nao sobrar aba. O tr8s usava 1,7 (13,3
# mm); colada a folha do layout A, o Luan pediu meio mm a menos de cada lado
# (10/10/2026): 2,7, etiqueta de 12,3 mm.
FOLGA = 2.7
LADO = BOTAO - FOLGA           # 12,3 mm
VAO = 4.5                      # branco entre etiquetas, para a tesoura
# Os numeros dos steps vao no bezel embaixo dos pads, que e estreito: etiqueta
# baixa. A largura nao precisa casar com o pad - cada uma e recortada sozinha.
STEP_L, STEP_A, STEP_VAO = 8.0, 6.5, 1.8
GAP_METADES = 8.0              # entre o 1-8 e o 9-16 (sao aparelhos diferentes)

MM = 72 / 25.4
A4_L, A4_A = 210.0, 297.0

ESCALA, MEDIDO = 1.0, None
if "--medido" in sys.argv:
    MEDIDO = float(sys.argv[sys.argv.index("--medido") + 1])
    ESCALA = 100.0 / MEDIDO


def mm(v):
    return v * MM * ESCALA


GAP_FILEIRA = 5.0 if ESCALA == 1.0 else 2.6
CEL_MAPA = 4.2 if ESCALA == 1.0 else 3.4
GAP_RODAPE = 4.2 if ESCALA == 1.0 else 3.8

# ── cores: um grupo, uma cor ──────────────────────────────────
VAR_C = (0.05, 0.40, 0.36)     # teal          variacoes A-H
MUTE_C = (0.68, 0.21, 0.04)    # laranja       mute da linha (e track no PAR)
BANCO_C = (0.11, 0.11, 0.13)   # quase preto   banco de tracks (▲ ▼)
LAYER_C = (0.33, 0.15, 0.68)   # roxo          layer AB / A / B
PAG_C = (0.02, 0.46, 0.21)     # verde         paginas PAR / PERF / ROUT
VEL_C = (0.24, 0.49, 0.83)     # azul          velocity (e parametro no PAR)
VELP_C = (0.05, 0.19, 0.52)    # azul escuro   80, a Normal Velocity da maquina
STEP_C = (0.0, 0.0, 0.0)       # preto         numeros dos steps (como o Launchpad)
BRANCO = (1, 1, 1)
TINTA = (0.10, 0.09, 0.08)
FRACO = (0.55, 0.53, 0.50)
CORTE = (0.76, 0.74, 0.71)
GUIA = (0.86, 0.85, 0.83)

# ── as bordas, na ordem fisica (o layout A) ───────────────────
# (rotulo, cor[, glifo][, nota])
GRUPOS = [
    ("ESQUERDO · borda de cima", "variações, da esquerda para a direita", "topo", "E",
     [(ch, VAR_C) for ch in "ABCDEFGH"]),
    ("ESQUERDO · borda da esquerda", "MUTE da linha ao lado, de cima para baixo "
     "(no banco CC·RC as 3 primeiras são CC, RC e ACC)", "esq", "E",
     [("BD/CC", MUTE_C), ("SD/RC", MUTE_C), ("LT/ACC", MUTE_C), ("HT", MUTE_C),
      ("RS", MUTE_C), ("HC", MUTE_C), ("CH", MUTE_C), ("OH", MUTE_C)]),
    ("DIREITO · borda de cima", "da esquerda para a direita", "topo", "D",
     [("BD-OH", BANCO_C, "cima"), ("CC·RC", BANCO_C, "baixo"),
      ("AB", LAYER_C), ("A", LAYER_C), ("B", LAYER_C),
      ("PAR", PAG_C), ("PERF", PAG_C), ("ROUT", PAG_C)]),
    ("DIREITO · borda da direita", "velocity de cima para baixo; embaixo, o "
     "parâmetro na página PAR", "dir", "D",
     [(v, VELP_C if v == "80" else VEL_C, None, nota) for v, nota in
      (("127", "PROB"), ("110", "SUB"), ("100", "CYCLE"), ("80", "START"),
       ("66", "VEL"), ("50", "ALT"), ("30", None), ("10", None))]),
]
TITULOS = [("VAR", "direita", "E"), ("VEL", "baixo", "D")]

doc = fitz.open()
pg = doc.new_page(width=mm(A4_L), height=mm(A4_A))


def _por(x, y, larg, alt, txt, tam, cor, negrito, alinha):
    """insert_textbox descarta o texto em silencio se a caixa for baixa demais:
    aqui isso vira erro (do tr8s-grid)."""
    sobra = pg.insert_textbox(
        fitz.Rect(mm(x), mm(y), mm(x + larg), mm(y + alt)), txt, fontsize=tam,
        fontname="hebo" if negrito else "helv", color=cor, align=alinha)
    if sobra < 0:
        raise SystemExit(f"caixa baixa demais para {txt[:40]!r}: "
                         f"faltaram {-sobra:.1f} pt em {alt} mm")


def esq(x, y, larg, txt, tam=7.5, cor=TINTA, negrito=False, alt=None):
    _por(x, y, larg, alt or max(5.0, tam * 0.7), txt, tam, cor, negrito,
         fitz.TEXT_ALIGN_LEFT)


def tinta_para(fundo):
    lum = 0.2126 * fundo[0] + 0.7152 * fundo[1] + 0.0722 * fundo[2]
    return TINTA if lum > 0.55 else BRANCO


def triangulo(cx, cy, base, direcao, cor):
    """Vetor: a fonte base do PDF (WinAnsi) nao tem seta."""
    b, h = base / 2, base * 0.80
    if direcao == "cima":
        pts = [(cx - b, cy + h / 2), (cx + b, cy + h / 2), (cx, cy - h / 2)]
    elif direcao == "baixo":
        pts = [(cx - b, cy - h / 2), (cx + b, cy - h / 2), (cx, cy + h / 2)]
    else:
        pts = [(cx - h / 2, cy - b), (cx - h / 2, cy + b), (cx + h / 2, cy)]
    pg.draw_polyline([fitz.Point(mm(a), mm(c)) for a, c in pts + [pts[0]]],
                     color=cor, fill=cor, width=0.2)


# A linha de corte fica a 0,85 mm da cor (a margem da folha que o Luan ja
# colou). Fixa, e nao FOLGA/2: com a folga maior, o recorte tem que encolher
# junto com a etiqueta - senao o adesivo continua com 15 mm, so com mais branco.
MARGEM_CORTE = 0.85


def corte(x, y, larg, alt):
    m = MARGEM_CORTE
    pg.draw_rect(fitz.Rect(mm(x - m), mm(y - m), mm(x + larg + m), mm(y + alt + m)),
                 color=CORTE, width=0.3, dashes="[1.5 1.5] 0")


def etiqueta(x, y, rotulo, cor, glifo=None, nota=None):
    tinta = tinta_para(cor)
    pg.draw_rect(fitz.Rect(mm(x), mm(y), mm(x + LADO), mm(y + LADO)), color=None, fill=cor)
    if glifo or nota:
        tam, dy = (8.2 if len(rotulo) <= 3 else 7.2), 2.6
    elif len(rotulo) <= 3:
        tam, dy = 10.0, 3.6
    elif len(rotulo) <= 5:
        tam, dy = 8.0, 4.3
    else:
        tam, dy = 6.8, 4.5
    _por(x, y + dy, LADO, LADO, rotulo, tam, tinta, True, fitz.TEXT_ALIGN_CENTER)
    if nota:
        _por(x, y + 8.2, LADO, 5.2, nota, 5.6, tinta, True, fitz.TEXT_ALIGN_CENTER)
    elif glifo:
        # relativo a LADO: com 13,3 fixos a ponta saia da etiqueta de 12,3
        triangulo(x + LADO / 2, y + LADO - 3.0, 3.6, glifo, tinta)


def etiqueta_titulo(x, y, texto, direcao):
    """O canto do logo nao e botao: etiqueta BRANCA de cabecalho da borda."""
    pg.draw_rect(fitz.Rect(mm(x), mm(y), mm(x + LADO), mm(y + LADO)),
                 color=CORTE, fill=BRANCO, width=0.5)
    _por(x, y + 2.2, LADO, 7.0, texto, 9.0, TINTA, True, fitz.TEXT_ALIGN_CENTER)
    triangulo(x + LADO / 2, y + LADO - 3.2, 3.8, direcao, TINTA)


def etiqueta_step(x, y, n):
    pg.draw_rect(fitz.Rect(mm(x), mm(y), mm(x + STEP_L), mm(y + STEP_A)), color=None, fill=STEP_C)
    _por(x, y + 1.3, STEP_L, STEP_A, str(n), 9.0, BRANCO, True, fitz.TEXT_ALIGN_CENTER)


# ── cabecalho ─────────────────────────────────────────────────
esq(14.5, 11, 181, "TR-1000 GRID  ·  ETIQUETAS DO LAYOUT A", tam=13, negrito=True)
for k, linha in enumerate([
        ("Imprima em A4 adesivo com escala 100% (tamanho real). Recorte pela linha "
         "tracejada e cole cada etiqueta no seu botão." if ESCALA == 1.0 else
         "Imprima em A4 adesivo com AJUSTAR À PÁGINA (o padrão). Recorte pela linha "
         "tracejada e cole cada etiqueta no seu botão."),
        f"Cada etiqueta tem {LADO:.1f} mm para um botão de {BOTAO:.0f} mm; os números dos "
        f"steps têm {STEP_L:.1f} x {STEP_A:.1f} mm, para o bezel embaixo dos pads.",
        "As fileiras estão na ordem física. O mapa embaixo mostra onde cada uma vai."]):
    esq(14.5, 18.5 + k * 4.4, 181, linha, tam=7.5, cor=FRACO)

if ESCALA != 1.0:
    esq(14.5, 31.4, 181,
        f"PRÉ-ESCALADA {ESCALA * 100:.1f}% - a régua da folha anterior mediu "
        f"{MEDIDO:.0f} mm onde devia dar 100.", tam=7.5, cor=(0.70, 0.15, 0.10), negrito=True)
    esq(14.5, 35.4, 181,
        "Então NÃO peça 100%: deixe o Ajustar à página. Meça a régua no resultado; se "
        "não der 100 mm, gere de novo com a nova medida.", tam=7.5, cor=(0.70, 0.15, 0.10))

RY = 34.0 if ESCALA == 1.0 else 43.0
pg.draw_line(fitz.Point(mm(14.5), mm(RY)), fitz.Point(mm(114.5), mm(RY)), color=TINTA, width=0.8)
for k in range(11):
    x = 14.5 + k * 10
    pg.draw_line(fitz.Point(mm(x), mm(RY)), fitz.Point(mm(x), mm(RY - (3.0 if k % 5 == 0 else 1.8))),
                 color=TINTA, width=0.6)
esq(117, RY - 3.4, 90, "esta linha deve medir exatamente 100 mm", tam=7.5)

# ── as fileiras de botao ──────────────────────────────────────
LARG = 8 * LADO + 7 * VAO
X0 = (A4_L - LARG) / 2
y = 44.0 if ESCALA == 1.0 else 51.0


def cabecalho_fileira(n, titulo, sentido):
    global y
    esq(X0 - 6.5, y + 0.6, 6.5, f"{n}", tam=10, cor=FRACO, negrito=True, alt=6.0)
    esq(X0, y, 160, titulo, tam=8.5, negrito=True)
    esq(X0, y + 4.0, 160, sentido, tam=7, cor=FRACO)
    y += 9.0


n_etiquetas = 0
for n, (titulo, sentido, _borda, _dev, itens) in enumerate(GRUPOS, 1):
    cabecalho_fileira(n, titulo, sentido)
    for k, item in enumerate(itens):
        rotulo, cor = item[0], item[1]
        glifo = item[2] if len(item) > 2 else None
        nota = item[3] if len(item) > 3 else None
        x = X0 + k * (LADO + VAO)
        etiqueta(x, y, rotulo, cor, glifo, nota)
        corte(x, y, LADO, LADO)
        n_etiquetas += 1
    y += LADO + GAP_FILEIRA

cabecalho_fileira(5, "CANTOS · não são botões", "o logo de cada um: VAR no esquerdo, VEL no direito")
for k, (texto, direcao, _dev) in enumerate(TITULOS):
    x = X0 + k * (LADO + VAO)
    etiqueta_titulo(x, y, texto, direcao)
    corte(x, y, LADO, LADO)
y += LADO + GAP_FILEIRA

# ── fileira 6: os numeros dos steps ───────────────────────────
cabecalho_fileira(6, "STEPS · embaixo dos pads", "1-8 no bezel de baixo do esquerdo, "
                  "9-16 no do direito, um embaixo de cada coluna")
# 16 etiquetas nao cabem na largura das fileiras de botao: esta fileira se
# centraliza na largura UTIL da folha (com --medido, o A4 logico encolhe)
LARG_S = 8 * STEP_L + 7 * STEP_VAO
XS = (A4_L / ESCALA - (2 * LARG_S + GAP_METADES)) / 2
for metade in range(2):
    for k in range(8):
        x = XS + metade * (LARG_S + GAP_METADES) + k * (STEP_L + STEP_VAO)
        etiqueta_step(x, y, metade * 8 + k + 1)
        corte(x, y, STEP_L, STEP_A)
if (XS + 2 * LARG_S + GAP_METADES) * ESCALA > A4_L - 8 or XS * ESCALA < 8:
    raise SystemExit("a fileira de steps saiu da largura do A4")
y += STEP_A + 7.0

# ── o mapa ────────────────────────────────────────────────────
esq(14.5, y, 181, "ONDE CADA FILEIRA VAI", tam=8.5, negrito=True)
esq(14.5, y + 4.0, 181, "Fora de escala: cada etiqueta é recortada sozinha. Os dois "
    "aparelhos vistos de cima, como ficam na mesa.", tam=7, cor=FRACO)
y += 13.0

CEL, MINI = CEL_MAPA, CEL_MAPA - 0.6
LARG_AP, ALT_AP = 9 * CEL, 10 * CEL
GAP_AP = 14.0
MX = (A4_L - (2 * LARG_AP + GAP_AP)) / 2
for ap, (nome, logo_esq) in enumerate((("ESQUERDO · girado 90° anti-horário", True),
                                       ("DIREITO · normal", False))):
    ox = MX + ap * (LARG_AP + GAP_AP)
    esq(ox, y - 4.6, LARG_AP + 14, nome, tam=7, negrito=True)
    pg.draw_rect(fitz.Rect(mm(ox), mm(y), mm(ox + LARG_AP), mm(y + ALT_AP)), color=GUIA, width=0.7)
    cols = range(1, 9) if logo_esq else range(0, 8)
    for r in range(1, 9):
        for c in cols:
            px, py = ox + c * CEL + 0.7, y + r * CEL + 0.7
            pg.draw_rect(fitz.Rect(mm(px), mm(py), mm(px + CEL - 1.4), mm(py + CEL - 1.4)),
                         color=GUIA, width=0.4)
    for n, (_t, _s, borda, dev, itens) in enumerate(GRUPOS, 1):
        if dev != ("E" if logo_esq else "D"):
            continue
        for k, item in enumerate(itens):
            if borda == "topo":
                cx, cy = ox + (k + (1 if logo_esq else 0)) * CEL, y
            elif borda == "esq":
                cx, cy = ox, y + (k + 1) * CEL
            else:
                cx, cy = ox + 8 * CEL, y + (k + 1) * CEL
            pg.draw_rect(fitz.Rect(mm(cx + 0.4), mm(cy + 0.4), mm(cx + 0.4 + MINI), mm(cy + 0.4 + MINI)),
                         color=None, fill=item[1])
        if borda == "topo":
            lx, ly = ox + LARG_AP + 1.5, y + 0.6
        elif borda == "esq":
            lx, ly = ox - 5.0, y + 8 * CEL - 6.0
        else:
            lx, ly = ox + LARG_AP + 1.5, y + 8 * CEL - 6.0
        esq(lx, ly, 6, f"{n}", tam=8, cor=FRACO, negrito=True, alt=5.5)
    # fileira 6: os numeros, no bezel de baixo, um por coluna de pad
    for c in cols:
        cx, cy = ox + c * CEL, y + 9 * CEL
        pg.draw_rect(fitz.Rect(mm(cx + 0.6), mm(cy + 1.0), mm(cx + CEL - 0.6), mm(cy + CEL - 1.0)),
                     color=None, fill=STEP_C)
    esq(ox + LARG_AP + 1.5, y + 9 * CEL, 6, "6", tam=8, cor=FRACO, negrito=True, alt=5.5)
    lcx = ox if logo_esq else ox + 8 * CEL
    pg.draw_rect(fitz.Rect(mm(lcx + 0.4), mm(y + 0.4), mm(lcx + 0.4 + MINI), mm(y + 0.4 + MINI)),
                 color=TINTA, fill=BRANCO, width=0.5)
    esq(lcx + 0.6, y + 1.2, MINI, "5", tam=4.5, negrito=True, alt=3.5)
y += ALT_AP + 3.0

# ── rodape ────────────────────────────────────────────────────
RODAPE = [
    "Cores:  teal = variações  ·  laranja = mute da linha  ·  preto = banco de tracks  ·  "
    "roxo = layer  ·  verde = páginas  ·  azul = velocity",
    "Bancos: BD-OH mostra BD SD LT HT RS HC CH OH; CC·RC troca as 3 primeiras linhas por CC, "
    "RC e ACC (accent). As linhas 4-8 não mudam.",
    "Página PAR: a borda esquerda escolhe o track e a direita o parâmetro (PROB, SUB, CYCLE, "
    "START, VEL, ALT). PERF e ROUT usam os pads.",
    "Os logos dos cantos são LEDs, não botões: as etiquetas brancas (5) são o título da borda ao lado.",
]
for k, linha in enumerate(RODAPE):
    esq(14.5, y + k * GAP_RODAPE, 181, linha, tam=7.3, alt=10.0, cor=TINTA if k == 0 else FRACO)

usada = (y + len(RODAPE) * GAP_RODAPE) * ESCALA
if usada > A4_A - 8:
    raise SystemExit(f"conteudo estourou o A4: {usada:.0f} mm de {A4_A:.0f}")

saida = os.path.join(AQUI, "adesivo.pdf")
doc.save(saida)
print(f"escrito: {saida}  (1 pagina)")
print(f"{n_etiquetas} etiquetas de botao + {len(TITULOS)} de canto + 16 de step; "
      f"{LADO:.1f} mm (botao de {BOTAO:.0f} mm)")
print(f"altura usada: {usada:.0f} de {A4_A:.0f} mm"
      f"{'' if ESCALA == 1 else f'  (escala {ESCALA:.4f})'}")

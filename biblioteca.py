#!/usr/bin/env python3
"""
biblioteca.py - os ritmos prontos da aba Ritmos, como DADOS (o formato e a
validacao estao no ritmos.py; `python3 ritmos.py` imprime tudo).

Cada ritmo tem a coluna de FONTE: de onde veio a celula. "conhecimento geral"
quer dizer o padrao canonizado do estilo, como produtores o programam, sem
uma transcricao conferida nesta pesquisa (13/10/2026). O SOM de cada um nao
foi ouvido na TR-1000: e o ROTEIRO-F5.

Convencoes:
  - 10 tracks: BD SD LT HT RS HC CH OH CC RC. Nao ha MT: o que no tr8s-grid
    era MT virou LT ou HT (anotado).
  - O accent nao e gravavel: o acento e a velocity (X = 127).
  - CH e OH se sufocam (o par de chimbal): onde o OH abre, o CH cala - salvo
    quando o abafado e o gesto (anotado).
  - Nao ha SHUFFLE gravavel. O swing de tercina sai da Scale 16th(T) com
    last 12 (12 steps = 2 tempos; a chain AB = 1 compasso), ou 8th(T) com
    last 12 (12 steps = 1 compasso).
  - Kit: o SUGERIDO, que o menu da aba troca. Desde 15/10/2026 (pedido do
    Luan: mais kits que 808/909) sai da lista de 64 pelo NOME e pelo estilo,
    sem ouvir; quem cita uma maquina na fonte (808, 909, 707...) fica com ela.

REGGAE: tudo em MEIO-TEMPO (60..90 BPM), o compasso dos produtores e da
notacao da Wikipedia (One drop rhythm: bd no 2 e no 4 a ♩ = 80). Nessa
contagem o drop/backbeat cai nos steps 5 e 13; o skank (guitarra, fora da
bateria) nos 3, 7, 11 e 15; e o "tempo" da contagem rapida dos textos de
reggae ("o drop no 3") e cada 2 steps. Por isso:
    one drop   BD + RS no 5 e no 13          (o 1 vazio: o "drop")
    rockers    BD no 1 5 9 13, RS no 5 e 13  (Wikipedia: o bumbo em cada tempo)
    steppers   BD em todo step impar         (Wikipedia: o bumbo em cada colcheia)
"""

RITMOS = [
    # ══ REGGAE / DUB ══════════════════════════════════════════════════
    # ── ska ───────────────────────────────────────────────────────────
    {
        "id": "ska_knibb", "nome": "Ska (Lloyd Knibb)", "estilo": "ska",
        "bpm": 120, "kit": "Backline Kit",
        "fonte": "Gil Sharone, Wicked Beats (Hudson Music, 2017), cap. Ska: cross-stick "
                 "com o bumbo no 2 e no 4, chimbal aberto em colcheia, pedal no 2 e no 4, "
                 "'swish' no 'a' do 2 e do 4; q = 110-136",
        "obs": "o ska original e um shuffle de tempo dobrado - sem SHUFFLE gravavel, "
               "aqui vai reto; o bumbo no 2 e no 4 e o que separa do R&B",
        "variacoes": {
            # Ex. 7/8: OH em colcheia, o pedal (CH) fechando no 2 e no 4, e o
            # swish (OH fraco) no 'a' do 2 e do 4
            "A": {"BD": "....|x...|....|x...",
                  "RS": "....|x...|....|x...",
                  "OH": "x.x.|..xo|x.x.|..xo",
                  "CH": "....|x...|....|x..."},
            # Ex. 11 + Ex. 16: chimbal fechado em colcheia e o bumbo que
            # acompanha o baixo
            "B": {"BD": "x...|x...|..x.|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o."},
            # os rolos de rimshot "de timbale" do Knibb (Easy Reader, 2023)
            "Fill 1": {"BD": "x...|x...|....|x...",
                       "SD": "....|....|x.oo|x.xX",
                       "OH": "x.x.|..x.|....|...."},
        },
    },
    {
        "id": "ska_2tone", "nome": "2-Tone (ska de 1979)", "estilo": "ska",
        "bpm": 150, "kit": "Backline Kit",
        "fonte": "conhecimento geral (Specials, Selecter, Madness); Wicked Beats tem o "
                 "capitulo 2-Tone - a celula: o ska com a pegada do punk",
        "obs": "o 2-Tone acelera o ska e poe a caixa cheia do rock no 2 e no 4",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "....|x...|....|x...",
                  "CH": "x...|x...|x...|x...",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "x...|x...|x.x.|x...",
                  "SD": "....|x...|....|x..o",
                  "CH": "x...|x...|x...|x...",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "SD": "....|x...|xoxo|xxXX",
                       "CC": "x...|....|....|...."},
        },
    },
    # ── rocksteady ────────────────────────────────────────────────────
    {
        "id": "rocksteady", "nome": "Rocksteady", "estilo": "rocksteady",
        "bpm": 90, "kit": "Backline Kit",
        "fonte": "Wikipedia, Rocksteady ('rocksteady is really slow ska', Lynn Taitt; "
                 "Joe Isaacs e Winston Grennan); a celula: o ska mais lento, com o "
                 "bumbo migrando para o backbeat - o embriao do one drop (deduzido)",
        "obs": "A: o bumbo ainda no 1 e no 3; B: o bumbo ja junto do rim no 2 e no 4",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "RS": "....|x...|....|x...",
                  "CH": "o.x.|o.x.|o.x.|o.x."},
            "B": {"BD": "....|x...|....|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "o.x.|o.x.|o.x.|o.xo",
                  "OH": "....|....|....|..x."},
            "Fill 1": {"BD": "....|x...|....|....",
                       "RS": "....|x...|....|....",
                       "SD": "....|....|x.x.|xxX."},
        },
    },
    # ── one drop ──────────────────────────────────────────────────────
    {
        "id": "one_drop", "nome": "One drop (reto)", "estilo": "reggae",
        "bpm": 76, "kit": "Backline Kit",
        "fonte": "Wikipedia, One drop rhythm (bumbo e cross-stick juntos, o 1 vazio; "
                 "chimbal em colcheia a q = 80); bonedo.de (Reggae am Schlagzeug: "
                 "chimbal acentuado no 2 e no 4)",
        "variacoes": {
            "A": {"BD": "....|x...|....|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o."},
            # a abertura do chimbal antes do 1 e o 16 quebrado
            "B": {"BD": "....|x...|....|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.oo|x.o.|x.oo|x...",
                  "OH": "....|....|....|..x."},
            # virada de caixa (rimshot) que cai no drop
            "Fill 1": {"BD": "....|x...|....|....",
                       "RS": "....|x...|....|....",
                       "SD": "....|....|o.x.|xxX.",
                       "HT": "....|....|....|...x"},
        },
    },
    {
        "id": "one_drop_barrett", "nome": "One drop (Carlton Barrett, tercina)",
        "estilo": "reggae", "bpm": 72, "kit": "Backline Kit",
        "scale": "16th(T)", "last": 12,
        "fonte": "Wikipedia, Carlton Barrett ('broken triplet' no chimbal; o one drop); "
                 "bonedo.de (colcheias 'geshuffelt'); Wicked Beats, cap. One Drop "
                 "(13 padroes de chimbal + Carly Barrett)",
        "obs": "Scale 16th(T), last 12: cada variacao e MEIO compasso (2 tempos, 6 "
               "steps cada); a chain AB faz o compasso. O drop cai no step 7",
        "variacoes": {
            # 6 steps por tempo: a colcheia no 1 e 4 do grupo, o 'a' de
            # tercina no 3 - o chimbal quebrado do Barrett
            "A": {"BD": "...|...|x..|...",
                  "RS": "...|...|x..|...",
                  "CH": "x.g|x..|x.g|x.."},
            "B": {"BD": "...|...|x..|...",
                  "RS": "...|...|x..|...",
                  "CH": "x.o|x.o|x..|xo.",
                  "OH": "...|...|...|..x"},
            # as entradas de caixa em tercina, que ele fazia antes do drop
            "Fill 1": {"BD": "...|...|x..|...",
                       "RS": "...|...|x..|...",
                       "SD": "...|...|...|oxX",
                       "HT": "...|...|...|x.."},
        },
    },
    {
        "id": "half_drop", "nome": "Half drop", "estilo": "reggae",
        "bpm": 70, "kit": "Backline Kit",
        "fonte": "dubroom.org (tutorial computer dub 05: steppers, one drop, two drop e "
                 "half drop - o bumbo so no 1 da contagem rapida, a caixa no 3); "
                 "dubroom 15 (o bumbo 1 7 8 9 e o chimbal fraco/forte)",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "RS": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            # dubroom 15: o bumbo empurra a volta (7 8) e o ultimo chimbal abre
            "B": {"BD": "x...|..xx|x...|....",
                  "RS": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xox.",
                  "OH": "....|....|....|...x"},
            "Fill 1": {"BD": "x...|....|....|....",
                       "RS": "....|x...|....|....",
                       "SD": "....|....|x.o.|x.x.",
                       "HT": "....|....|....|.x.x"},
        },
    },
    # ── rockers / flying cymbal / steppers (Channel One, Bunny Lee) ───
    {
        "id": "rockers", "nome": "Rockers (Channel One)", "estilo": "reggae",
        "bpm": 78, "kit": "Backline Kit",
        "fonte": "Wikipedia, One drop rhythm (rockers = o backbeat do one drop + bumbo "
                 "em cada tempo); Soundbrenner, Rockers rhythm; The Quietus/Reggaeville "
                 "(Sly Dunbar e os Revolutionaries no Channel One, 1975-76)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.xo|x.xo|x.xo|x.xo"},
            # o rim dobrado do Sly ('doubling rim shots')
            "B": {"BD": "x...|x...|x...|x...",
                  "RS": "....|xx..|....|x.x.",
                  "CH": "x.xo|x.xo|x.xo|x.x.",
                  "OH": "....|....|....|...x"},
            # os toms do Sly (syndrum): rolo descendo
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "RS": "....|x...|....|....",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|x.xX"},
        },
    },
    {
        "id": "flying_cymbal", "nome": "Flying cymbal (Aggrovators)", "estilo": "reggae",
        "bpm": 76, "kit": "Backline Kit",
        "fonte": "Wikipedia, Bunny Lee e Carlton 'Santa' Davis; FACT (2016) e Red Bull "
                 "Music Academy (2013): o chimbal aberto e fechado no contratempo, de "
                 "'None Shall Escape the Judgement' (Johnny Clarke, 1974); a origem no "
                 "'Philly bump' da soul",
        "obs": "o chiado e do CHIMBAL, nao de prato (Santa Davis); o 'e' da contagem "
               "rapida e cada step par aqui",
        "variacoes": {
            # one drop com o chimbal 'voando': fecha no tempo, abre no 'e'
            "A": {"BD": "....|x...|....|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": ".o.o|.o.o|.o.o|.o.o"},
            # o mesmo chimbal sobre o bumbo do rockers
            "B": {"BD": "x...|x...|x...|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": ".o.o|.o.o|.o.o|.x.x"},
            "Fill 1": {"BD": "....|x...|....|....",
                       "RS": "....|x...|....|....",
                       "SD": "....|....|x.xx|x.X.",
                       "OH": ".o.o|.o.o|....|...."},
        },
    },
    {
        "id": "steppers", "nome": "Steppers (Sly Dunbar)", "estilo": "reggae",
        "bpm": 75, "kit": "Backline Kit",
        "fonte": "Wikipedia, One drop rhythm (steppers = o backbeat + bumbo em cada "
                 "colcheia); dubroom.org 05 (o bumbo nos quatro da contagem rapida); "
                 "Soundbrenner, Steppers rhythm; Reggaeville (Sly: o 'straight four')",
        "variacoes": {
            "A": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            # o chimbal abrindo no contratempo da contagem rapida
            "B": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": ".o.o|.o.o|.o.o|.o.x"},
            # timbale/rim no meio-contratempo depois do 2 e do 4 (dubroom 05)
            "C": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "RS": "....|..x.|....|..x.",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            "Fill 1": {"BD": "x.x.|x.x.|x.x.|x.x.",
                       "SD": "....|x...|....|....",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|x.xX"},
        },
        "chain": "AB",
    },
    {
        "id": "uk_steppers", "nome": "UK steppers (sound system)", "estilo": "dub",
        "bpm": 74, "kit": "TR-909-1000",
        "fonte": "conhecimento geral (Jah Shaka, Iration Steppas, Mad Professor, anos "
                 "80-90): o steppers de Channel One acelerado no 4/4 do sound system; "
                 "dubroom 15 (140 na contagem rapida, reto)",
        "obs": "74 aqui = 148 na contagem rapida; o 909 da o peso do sound system",
        "variacoes": {
            "A": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            "B": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": ".o.o|.o.o|.o.o|.o.o"},
            # o rolo de tom 'syndrum' do dub ingles: sub step 1/2
            "Fill 1": {"BD": "x.x.|x.x.|x.x.|x.x.",
                       "SD": "....|x...|....|....",
                       "HT": ("....|....|x.x.|....", {9: {"sub": "1/2"}}),
                       "LT": ("....|....|....|x.x.", {13: {"sub": "1/2"}, 15: {"sub": "1/2"}})},
        },
    },
    # ── dub ───────────────────────────────────────────────────────────
    {
        "id": "dub_roots", "nome": "Dub roots (Tubby / Scientist)", "estilo": "dub",
        "bpm": 72, "kit": "Dub Techno Kit",
        "fonte": "Wicked Beats, cap. Dub; attackmagazine.com (dub-style drum processing: "
                 "delay de fita e mola na caixa e no chimbal, o bumbo seco); MoPOP / "
                 "FACT (King Tubby: baixo e bateria em primeiro plano, eco e reverb)",
        "obs": "o dub mora no MIX: o Play liga delay no rim, delay+reverb na caixa e "
               "um pouco de delay no chimbal aberto (o BD fica seco). B e C sao as "
               "quebras de mesa - o que sai da mixagem, nao o que toca diferente",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "RS": "....|x...|....|x...",
                  "CH": "x.xo|x.xo|x.xo|x.xo",
                  "OH": "....|....|....|..x."},
            # a quebra: so o bumbo e o rim, com o rim ecoando
            "B": {"BD": "x...|x...|x...|x...",
                  "RS": "....|x...|....|x...",
                  "SD": "....|....|....|..o."},
            # a outra quebra: o bumbo some, o chimbal fica
            "C": {"RS": "....|x...|....|x...",
                  "CH": "x.xo|x.xo|x.xo|x.x.",
                  "OH": "....|....|....|...x"},
            "Fill 1": {"BD": "x...|....|....|....",
                       "SD": "....|x...|....|x...",
                       "RS": "....|....|x...|...."},
        },
        "mix": {"rs.dly": 450, "sd.dly": 550, "sd.rvb": 350, "oh.dly": 250},
    },
    {
        "id": "dub_steppers", "nome": "Dub steppers", "estilo": "dub",
        "bpm": 75, "kit": "Dub Techno Kit",
        "fonte": "attackmagazine.com (comeca de um steppers seco e manda delay e mola na "
                 "caixa e nos chimbais, o bumbo seco como ancora); dubroom 05",
        "obs": "o Play manda a caixa e o chimbal aberto para o delay",
        "variacoes": {
            "A": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": "....|...o|....|...o"},
            "B": {"BD": "x.x.|x.x.|x.x.|x.x.",
                  "SD": "....|x...|....|....",
                  "RS": "....|....|....|x..."},
            "Fill 1": {"BD": "x...|....|x...|....",
                       "SD": "....|x...|....|x.o.",
                       "OH": "....|....|....|...x"},
        },
        "mix": {"sd.dly": 600, "sd.rvb": 300, "oh.dly": 400, "rs.dly": 400},
    },
    {
        "id": "lovers_rock", "nome": "Lovers rock", "estilo": "reggae",
        "bpm": 74, "kit": "Backline Kit",
        "fonte": "conhecimento geral (Londres, fim dos anos 70; Dennis Bovell): o one "
                 "drop de dinamica baixa, rim leve e chimbal mais cheio",
        "variacoes": {
            "A": {"BD": "....|x...|....|x...",
                  "RS": "....|o...|....|o...",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            "B": {"BD": "....|x..o|....|x...",
                  "RS": "....|o...|....|o...",
                  "CH": "xoxo|xoxo|xoxo|xox.",
                  "OH": "....|....|....|...o"},
            "Fill 1": {"BD": "....|x...|....|....",
                       "RS": "....|o...|....|....",
                       "HT": "....|....|o.o.|....",
                       "LT": "....|....|....|o.x."},
        },
    },
    # ── nyabinghi ─────────────────────────────────────────────────────
    {
        "id": "nyabinghi", "nome": "Nyabinghi", "estilo": "nyabinghi",
        "bpm": 128, "kit": "Backline Kit",
        "fonte": "Wikipedia, Nyabinghi rhythm (thunder: aberto no 1, abafado no 3; funde: "
                 "o pulso no 2 e no 4; repeater: sincopado em volta do 2 e do 4, "
                 "improvisando); Wicked Beats, cap. Nyabingi",
        "obs": "thunder no BD (afinar grave), funde no LT, repeater (kete) no HT, "
               "shaka no CH. O repeater improvisa: B e C sao duas frases dele",
        "variacoes": {
            "A": {"BD": "X...|....|g...|....",
                  "LT": "...o|x...|...o|x...",
                  "HT": "....|..x.|....|.x.x",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "B": {"BD": "X...|....|g...|....",
                  "LT": "...o|x...|...o|x...",
                  "HT": "..x.|.x.x|..x.|..x.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            # 'occasionally, the thunder player will syncopate'
            "C": {"BD": "X...|...o|g...|....",
                  "LT": "...o|x...|...o|x...",
                  "HT": ".x..|x..x|.x..|x.x.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "X...|....|....|....",
                       "LT": "...o|x...|....|....",
                       "HT": "....|..x.|xxxx|xXxX"},
        },
    },
    # ── dancehall ─────────────────────────────────────────────────────
    {
        "id": "sleng_teng", "nome": "Sleng Teng (digital, 1985)", "estilo": "dancehall",
        "bpm": 98, "kit": "707 Kit 1",
        "fonte": "Wikipedia, Sleng Teng e Casio MT-40 (o preset 'rock' de Hiroko Okuda, "
                 "1980, desacelerado por King Jammy); DancehallMag (2026): Jammy pos "
                 "piano e palmas por cima",
        "obs": "DEDUCAO: a programacao exata do preset nao foi transcrita aqui - a "
               "celula e um rock simples desacelerado, com a palma do Jammy. O MT-40 "
               "tem 5 sons de bateria; o 707 e o mais proximo na lista",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "B": {"BD": "x...|....|x.x.|....",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.xx"},
            "Fill 1": {"BD": "x...|....|x...|....",
                       "SD": "....|x...|xxxx|xxxx"},
        },
    },
    {
        "id": "dancehall_90s", "nome": "Dancehall (anos 90)", "estilo": "dancehall",
        "bpm": 94, "kit": "Hard Perc Kit",
        "fonte": "DancehallMag, 'The Dancehall Drum Pattern, Explained' (2026): bumbo "
                 "1 4 9 12, rim nos contratempos, palma no 'e' do 2 e do 4, colcheias "
                 "no chimbal, 90-95 BPM",
        "obs": "a grade da DancehallMag poe a palma nos steps 6 e 14, mas o texto diz "
               "'o e do 2 e do 4' (7 e 15) - segui o texto",
        "variacoes": {
            "A": {"BD": "x..x|....|x..x|....",
                  "HC": "....|..x.|....|..x.",
                  "RS": "..o.|..o.|..o.|..o.",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "B": {"BD": "x..x|....|x..x|..o.",
                  "HC": "....|..x.|....|..x.",
                  "RS": "..o.|..o.|..o.|....",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": "....|....|....|..x."},
            "Fill 1": {"BD": "x..x|....|x...|....",
                       "HC": "....|..x.|..x.|x.xx"},
        },
    },
    {
        "id": "dem_bow_riddim", "nome": "Dem Bow (Poco Man Jam, 1990)", "estilo": "dancehall",
        "bpm": 100, "kit": "Hard Perc Kit",
        "fonte": "DancehallMag (2026): o loop de dois compassos do Poco Man Jam (Steely "
                 "& Clevie) - bumbo no 1 e no 'e' do 2, caixa no 'e' do 1 e no 3; a "
                 "celula 3-3-2 que o reggaeton herdou (conhecimento geral)",
        "obs": "A: a celula 3-3-2 no 4/4 (a que o reggaeton herdou); B: o desenho da "
               "DancehallMag",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "...x|..x.|...x|..x.",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "B": {"BD": "x...|..x.|....|....",
                  "SD": "..x.|....|x...|....",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "SD": "...x|..x.|...x|xxxx",
                       "HT": "....|....|....|..x."},
        },
    },

    # ══ PORT DO TR8S-GRID (biblioteca.py de la, 54 patterns) ═════════════
    # Cada um auditado (13/10/2026): o que mudou esta no comentario. Todos
    # ganharam uma variacao B (a segunda barra, a abertura, a variacao de
    # bumbo) e um Fill 1. O accent virou X; o MT virou LT ou HT.
    # ── house ─────────────────────────────────────────────────────────
    {
        "id": "house_classico", "nome": "House quatro no chão", "estilo": "house",
        "bpm": 124, "kit": "TR-909-1000",
        "fonte": "tr8s-grid (house_classico); conhecimento geral (o 909 de Chicago/NY: "
                 "bumbo nos 4, palma no 2 e no 4, aberto no contratempo)",
        "obs": "auditoria: no tr8s o CH tocava junto do OH no contratempo (o par se "
               "sufoca); aqui o fechado fica na cabeca do tempo",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "HC": "....|x...|....|x...",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "X...|X...|X...|X...",
                  "HC": "....|x...|....|x...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RS": "....|...o|....|..o."},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": "....|....|o.o.|xxxX",
                       "OH": "..x.|..x.|....|...."},
        },
    },
    {
        "id": "deep_house", "nome": "Deep house", "estilo": "house",
        "bpm": 122, "kit": "Aussie House Kit",
        "fonte": "tr8s-grid (deep_house); conhecimento geral (o rim sincopado do deep)",
        "obs": "auditoria: CH/OH tirados de cima um do outro",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "HC": "....|o...|....|o...",
                  "RS": "...o|....|..o.|...o",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..o.|..o.|..o.|..o."},
            "B": {"BD": "x...|x...|x...|x..o",
                  "HC": "....|o...|....|o...",
                  "RS": "...o|..o.|..o.|...o",
                  "CH": "o..o|o...|o..o|o...",
                  "OH": "..o.|..o.|..o.|..o."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "HC": "....|o...|....|o.oo",
                       "RS": "...o|....|o.o.|...."},
        },
    },
    {
        "id": "acid_house", "nome": "Acid house", "estilo": "house",
        "bpm": 126, "kit": "TR-909-1000",
        "fonte": "tr8s-grid (acid_house); conhecimento geral (Phuture, 1987: 909 seco, "
                 "palma dobrada)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "HC": "....|x...|...o|x...",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..xo",
                  "RS": "....|...o|....|...."},
            "B": {"BD": "x...|x...|x...|x.x.",
                  "HC": "....|x...|...o|x..o",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "SD": "....|....|oooo|xxxX",
                       "HC": "....|x...|....|...."},
        },
    },
    {
        "id": "jackin_house", "nome": "Jackin' house", "estilo": "house",
        "bpm": 126, "kit": "Aussie House Kit",
        "fonte": "tr8s-grid (jackin_house); conhecimento geral (o 'jack' de Chicago: a "
                 "caixa fantasma na colcheia)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "....|x..o|....|x..o",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "x...|x...|x..o|x...",
                  "SD": "....|x..o|..o.|x..o",
                  "HC": "....|x...|....|x...",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "SD": "....|x..o|o.o.|xoxX"},
        },
    },
    # ── techno ────────────────────────────────────────────────────────
    {
        "id": "techno_pancada", "nome": "Techno reto", "estilo": "techno",
        "bpm": 132, "kit": "Deep Techno Kit",
        "fonte": "tr8s-grid (techno_pancada); conhecimento geral",
        "obs": "auditoria: o CH em semicolcheia abre buraco onde o OH toca",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "SD": "....|x...|....|x...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "X...|X...|X...|X..o",
                  "SD": "....|x...|....|x...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": "....|x...|....|x...",
                       "LT": "....|....|....|..oo",
                       "CH": "oooo|oooo|oooo|oo.."},
        },
    },
    {
        "id": "techno_detroit", "nome": "Detroit", "estilo": "techno",
        "bpm": 128, "kit": "TR-909 OG 1",
        "fonte": "tr8s-grid (techno_detroit); conhecimento geral (o 909 com percussao "
                 "de Detroit, Underground Resistance / Jeff Mills)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "HC": "....|x...|....|x...",
                  "RS": ".o..|..o.|....|o.o.",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HT": "....|...o|..o.|...."},
            "B": {"BD": "x...|x...|x...|x...",
                  "HC": "....|x...|....|x...",
                  "RS": ".o..|..o.|.o..|o.o.",
                  "CH": "o...|o...|o...|o...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HT": "....|...o|..o.|....",
                  "LT": "....|....|....|.o.o"},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "HC": "....|x...|....|x.xx",
                       "HT": "....|....|o.o.|....",
                       "LT": "....|....|....|o.o."},
        },
    },
    {
        "id": "techno_hipnotico", "nome": "Techno hipnótico", "estilo": "techno",
        "bpm": 134, "kit": "Deep Techno Kit",
        "fonte": "tr8s-grid (techno_hipnotico); conhecimento geral (rim em ciclo de 3 "
                 "contra o 4 do bumbo)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "RS": "o..o|..o.|.o..|o..o",
                  "CH": "..x.|..x.|..x.|..x.",
                  "CC": "x...|....|....|...."},
            "B": {"BD": "x...|x...|x...|x...",
                  "RS": "..o.|.o..|o..o|..o.",
                  "CH": "..x.|..x.|..x.|..x.",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "RS": "o..o|..o.|.o..|oooo",
                       "CH": "..x.|..x.|..x.|...."},
        },
    },
    {
        "id": "techno_industrial", "nome": "Industrial", "estilo": "techno",
        "bpm": 138, "kit": "Deep Techno Kit",
        "fonte": "tr8s-grid (techno_industrial); conhecimento geral",
        "obs": "port: o MT do tr8s virou HT",
        "variacoes": {
            "A": {"BD": "X...|X..x|x...|X...",
                  "SD": "....|x...|....|x..o",
                  "CH": "oooo|oooo|oooo|oooo",
                  "HT": "....|....|..o.|..o."},
            "B": {"BD": "X...|X..x|x.x.|X...",
                  "SD": "....|x...|....|x.xo",
                  "CH": "oooo|oooo|oooo|oooo",
                  "HT": "....|....|..o.|..o.",
                  "CC": "x...|....|....|...."},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": "....|x...|xxxx|XXXX"},
        },
    },
    {
        "id": "tech_house", "nome": "Tech house", "estilo": "techno",
        "bpm": 126, "kit": "Deep Techno Kit",
        "fonte": "tr8s-grid (tech_house); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "CH": "o...|o.o.|o...|o.o.",
                  "OH": "..x.|....|..x.|....",
                  "RS": "...o|..o.|....|.o..",
                  "HC": "....|x...|....|x...",
                  "LT": "....|....|....|..o."},
            "B": {"BD": "x...|x...|x...|x..o",
                  "CH": "o...|o.o.|o...|o.o.",
                  "OH": "..x.|....|..x.|....",
                  "RS": "...o|..o.|..o.|.o..",
                  "HC": "....|x...|....|x...",
                  "LT": "....|..o.|....|..o."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "HC": "....|x...|....|x.xx",
                       "RS": "...o|..o.|oooo|...."},
        },
    },
    {
        "id": "minimal", "nome": "Minimal", "estilo": "techno",
        "bpm": 128, "kit": "Deep Techno Kit",
        "fonte": "tr8s-grid (minimal); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "CH": "..o.|..o.|..o.|..o.",
                  "RS": "o..o|.o..|o..o|.o.."},
            "B": {"BD": "x...|x...|x...|x...",
                  "CH": "..o.|..o.|..oo|..o.",
                  "RS": "o..o|.o..|o..o|..o."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "CH": "..o.|..o.|..o.|oooo",
                       "RS": "o..o|.o..|o...|...."},
        },
    },
    {
        "id": "dub_techno", "nome": "Dub techno", "estilo": "techno",
        "bpm": 118, "kit": "Dub Techno Kit",
        "fonte": "tr8s-grid (dub_techno); conhecimento geral (Basic Channel / Chain "
                 "Reaction: o acorde e o eco fazem o groove)",
        "obs": "o Play manda o rim e o chimbal para o delay e o reverb - o dub "
               "techno mora nos efeitos",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "CH": "..o.|..o.|..o.|..o.",
                  "RS": "....|...o|....|..o.",
                  "OH": "....|....|....|.o..",
                  "CC": "o...|....|....|...."},
            "B": {"BD": "x...|x...|x...|x...",
                  "CH": "..o.|..o.|..o.|..o.",
                  "RS": "....|...o|...o|..o."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "RS": "....|...o|..o.|o.o.",
                       "OH": "....|....|....|...o"},
        },
        "mix": {"rs.dly": 600, "rs.rvb": 400, "ch.dly": 300, "oh.rvb": 450},
    },
    # ── electro / miami ───────────────────────────────────────────────
    {
        "id": "electro_808", "nome": "Electro (Planet Rock)", "estilo": "electro",
        "bpm": 128, "kit": "TR-808-1000",
        "fonte": "tr8s-grid (electro_808); conhecimento geral (o 808 de 'Planet Rock', "
                 "1982) - nao conferido em transcricao",
        "variacoes": {
            "A": {"BD": "x...|...x|..x.|...o",
                  "SD": "....|x...|....|x...",
                  "HC": "....|....|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o.",
                  "RS": "..o.|....|....|.o.."},
            "B": {"BD": "x...|...x|..x.|x...",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x...",
                  "OH": "....|....|....|..o."},
            "Fill 1": {"BD": "x...|...x|....|....",
                       "SD": "....|x...|....|x...",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|x.x."},
        },
    },
    {
        "id": "miami_bass", "nome": "Miami bass", "estilo": "electro",
        "bpm": 130, "kit": "TR-808 OG 1",
        "fonte": "tr8s-grid (miami_bass); conhecimento geral (2 Live Crew: 808 com "
                 "bumbo longo)",
        "variacoes": {
            "A": {"BD": "x..o|..x.|..x.|..o.",
                  "SD": "....|x...|....|x...",
                  "HC": "....|o...|....|o...",
                  "CH": "oooo|oooo|oooo|oo.o",
                  "OH": "....|....|....|..x."},
            "B": {"BD": "x..o|..x.|x.x.|..o.",
                  "SD": "....|x...|....|x...",
                  "HC": "....|o...|....|o...",
                  "CH": "oooo|oooo|oooo|oooo"},
            "Fill 1": {"BD": "x..o|..x.|....|....",
                       "SD": "....|x...|x.xx|xxxx",
                       "HC": "....|o...|....|...."},
        },
    },
    # ── hip-hop ───────────────────────────────────────────────────────
    {
        "id": "boom_bap", "nome": "Boom bap", "estilo": "hip-hop",
        "bpm": 92, "kit": "TR-808 OG 2",
        "fonte": "tr8s-grid (boom_bap); conhecimento geral",
        "obs": "o boom bap e de sample de break; o 808 OG e a aproximacao analogica",
        "variacoes": {
            "A": {"BD": "x...|..x.|.o..|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o.",
                  "OH": "....|....|....|..o."},
            "B": {"BD": "x...|..x.|.o..|..o.",
                  "SD": "....|x...|....|x..o",
                  "CH": "x.o.|x.o.|x.o.|x.o."},
            "Fill 1": {"BD": "x...|..x.|.o..|....",
                       "SD": "....|x...|..o.|xoxo"},
        },
    },
    {
        "id": "trap_meio_tempo", "nome": "Trap (meio tempo)", "estilo": "hip-hop",
        "bpm": 140, "kit": "Lofi Kit",
        "fonte": "tr8s-grid (trap_meio_tempo); conhecimento geral",
        "obs": "os rolos de chimbal sao o SUB do step (o retrigger da maquina)",
        "variacoes": {
            "A": {"BD": "x...|.o..|..x.|....",
                  "SD": "....|....|x...|....",
                  "CH": ("x.o.|x.o.|x.o.|x.o.", {7: {"sub": "1/2"}, 15: {"sub": "1/4"}}),
                  "OH": "....|....|....|o..."},
            "B": {"BD": "x...|.o..|..x.|..o.",
                  "SD": "....|....|x...|....",
                  "CH": ("x.o.|x.o.|x.o.|x.o.", {3: {"sub": "1/3"}, 11: {"sub": "1/2"},
                                                 15: {"sub": "1/4"}})},
            "Fill 1": {"BD": "x...|.o..|....|....",
                       "SD": ("....|....|x...|x.x.", {15: {"sub": "1/3"}}),
                       "CH": ("x.o.|x.o.|....|....", {7: {"sub": "1/4"}})},
        },
    },
    {
        "id": "trap_808", "nome": "Trap (808 rolando)", "estilo": "hip-hop",
        "bpm": 150, "kit": "TR-808-1000",
        "fonte": "tr8s-grid (trap_808); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|..x.|..x.|....",
                  "SD": "....|....|x...|....",
                  "CH": ("x.o.|x.oo|x.o.|o.o.", {8: {"sub": "1/3"}, 13: {"sub": "1/3"}}),
                  "OH": "....|o...|....|...."},
            "B": {"BD": "x...|..x.|..x.|.x..",
                  "SD": "....|....|x...|....",
                  "CH": ("x.o.|x.o.|x.oo|o.o.", {12: {"sub": "Triplet 1"}, 15: {"sub": "1/4"}})},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": ("....|....|x...|..xx", {15: {"sub": "1/2"}, 16: {"sub": "1/4"}})},
        },
    },
    {
        "id": "dubstep_halftime", "nome": "Dubstep (meio tempo)", "estilo": "hip-hop",
        "bpm": 140, "kit": "Downstep Life",
        "fonte": "tr8s-grid (dubstep_halftime); conhecimento geral (Skream/Benga/Mala: "
                 "140 com a caixa so no 3)",
        "obs": "o groove esta no que NAO toca - resistir a encher os vazios",
        "variacoes": {
            "A": {"BD": "x...|..x.|....|....",
                  "SD": "....|....|x...|....",
                  "CH": "o..o|..o.|.o..|o..o",
                  "OH": "....|....|..x.|....",
                  "RS": "....|....|....|..o."},
            "B": {"BD": "x...|....|....|..x.",
                  "SD": "....|....|x...|....",
                  "CH": "o..o|..o.|.o..|o..o",
                  "RS": "...o|....|....|..o."},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": "....|....|x...|x.xx",
                       "LT": "....|....|....|.x.."},
        },
    },
    # ── drum'n'bass / breakbeat ───────────────────────────────────────
    {
        "id": "dnb_twostep", "nome": "Two-step DnB", "estilo": "drum'n'bass",
        "bpm": 174, "kit": "Glitchy DnB Kit",
        "fonte": "tr8s-grid (dnb_twostep); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|....|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "RC": "x...|x...|x...|x..."},
            "B": {"BD": "x...|....|..x.|.x..",
                  "SD": "....|x...|....|x..o",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "OH": "....|..o.|....|...."},
            "Fill 1": {"BD": "x...|....|..x.|....",
                       "SD": "....|x..o|.o..|xoxx"},
        },
    },
    {
        "id": "jungle_amen", "nome": "Jungle (amen)", "estilo": "drum'n'bass",
        "bpm": 170, "kit": "Jungle Kit",
        "fonte": "Wikipedia, Amen break (4 compassos: os 2 primeiros iguais, o 3o atrasa "
                 "uma caixa, o 4o deixa o 1 vazio e adianta o prato; ~136 BPM no "
                 "original); a celula dos 2 primeiros: conhecimento geral",
        "obs": "auditoria: o tr8s tinha so a barra 1; aqui A = barras 1-2, B = barra 3, "
               "C = barra 4. A chain da maquina e uma mascara (toca A, B, C uma vez "
               "cada): o A A B C do break fica A B C",
        "variacoes": {
            "A": {"BD": "x.x.|....|..xx|....",
                  "SD": "....|x..o|.o..|x..o",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            "B": {"BD": "x.x.|....|..x.|....",
                  "SD": "....|x..o|.o..|..xo",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            "C": {"BD": "..x.|....|..x.|....",
                  "SD": ".o..|x..o|.o..|..xo",
                  "RC": "x.x.|x.x.|x...|x.x.",
                  "CC": "....|....|..x.|...."},
            "Fill 1": {"BD": "x.x.|....|....|....",
                       "SD": "....|x..o|xoxo|xxXX"},
        },
    },
    {
        "id": "jungle_chopped", "nome": "Jungle (chopped)", "estilo": "drum'n'bass",
        "bpm": 172, "kit": "Jungle Kit",
        "fonte": "tr8s-grid (jungle_2); conhecimento geral (o amen refatiado)",
        "variacoes": {
            "A": {"BD": "x...|....|..x.|....",
                  "SD": "....|x..x|.o..|x..o",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "RS": "....|...o|....|...."},
            "B": {"BD": "x...|..x.|..x.|....",
                  "SD": ("....|x..x|.o..|x.xo", {15: {"sub": "1/2"}}),
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "x...|....|....|....",
                       "SD": ("....|x.xx|.xx.|xxxx", {13: {"sub": "1/2"}, 16: {"sub": "1/3"}})},
        },
    },
    {
        "id": "funky_drummer", "nome": "Funky Drummer", "estilo": "breakbeat",
        "bpm": 98, "kit": "TR-909 OG 1",
        "fonte": "tr8s-grid (funky_drummer); conhecimento geral (Clyde Stubblefield, "
                 "1970: o break como todo mundo o programa)",
        "obs": "o original e bateria acustica; o 909 OG e a aproximacao analogica",
        "variacoes": {
            "A": {"BD": "x.x.|..x.|..x.|.x..",
                  "SD": "....|x..o|.o..|x..o",
                  "CH": "xooo|oooo|oooo|oooo",
                  "OH": "....|....|...o|...."},
            "B": {"BD": "x.x.|..x.|..x.|.x..",
                  "SD": "....|x..o|.o..|x..o",
                  "CH": "xooo|oooo|oo.o|oooo",
                  "OH": "....|....|..o.|...."},
            "Fill 1": {"BD": "x.x.|..x.|....|....",
                       "SD": "....|x..o|xoxo|xoxX"},
        },
    },
    {
        "id": "big_beat", "nome": "Big beat", "estilo": "breakbeat",
        "bpm": 120, "kit": "Uncut Rhythm Kit",
        "fonte": "tr8s-grid (big_beat); conhecimento geral (Chemical Brothers / Fatboy "
                 "Slim)",
        "variacoes": {
            "A": {"BD": "X..x|....|X.x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "CC": "x...|....|....|....",
                  "OH": "....|....|....|..o."},
            "B": {"BD": "X..x|....|X.x.|..x.",
                  "SD": "....|x...|....|x..o",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "X..x|....|....|....",
                       "SD": "....|x...|xoxo|xxXX"},
        },
    },
    # ── funk / disco / pop ────────────────────────────────────────────
    {
        "id": "funk_cold_sweat", "nome": "Funk (Cold Sweat)", "estilo": "funk",
        "bpm": 108, "kit": "Uncut Rhythm Kit",
        "fonte": "bonedo.de, 'James Brown Cold Sweat' (Clyde Stubblefield): figura de "
                 "2 compassos - o 1 pesado; no 1o compasso a segunda caixa atrasada "
                 "uma colcheia; no 2o quase sem backbeat; o chimbal aberto por uma "
                 "colcheia levando ao 2 e ao 4",
        "obs": "auditoria: o tr8s tinha uma barra so; aqui A e B sao os dois compassos "
               "da figura",
        "variacoes": {
            "A": {"BD": "X...|....|..x.|....",
                  "SD": "....|x...|....|..x.",
                  "CH": "x...|x.x.|x...|x...",
                  "OH": "..x.|....|..x.|...."},
            "B": {"BD": "x...|....|..o.|....",
                  "SD": "....|..o.|.o..|..o.",
                  "CH": "x...|x.x.|x...|x.x.",
                  "OH": "..x.|....|..x.|...."},
            "Fill 1": {"BD": "X...|....|....|....",
                       "SD": "....|x...|x.ox|.xX."},
        },
    },
    {
        "id": "disco", "nome": "Disco", "estilo": "disco",
        "bpm": 118, "kit": "707 & 727 Kit",
        "fonte": "tr8s-grid (disco); conhecimento geral (o chimbal aberto no contratempo "
                 "da Philadelphia - a mesma raiz do flying cymbal)",
        "obs": "auditoria: CH/OH tirados de cima um do outro",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "SD": "....|x...|....|x...",
                  "HC": "....|o...|....|o...",
                  "CH": "x...|x...|x...|x...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "CC": "o...|....|....|...."},
            "B": {"BD": "X...|X...|X...|X...",
                  "SD": "....|x...|....|x..o",
                  "HC": "....|o...|....|o...",
                  "CH": "xo..|xo..|xo..|xo..",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": "....|x...|....|xoxo",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|..x."},
        },
    },
    {
        "id": "pop_billie", "nome": "Pop reto (Billie Jean)", "estilo": "pop",
        "bpm": 117, "kit": "707 & 727 Kit",
        "fonte": "tr8s-grid (pop_billie); conhecimento geral (LinnDrum, 1982: bumbo no "
                 "1 e no 3, caixa no 2 e no 4, chimbal em colcheia)",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o."},
            "B": {"BD": "x...|....|x...|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.oo"},
            "Fill 1": {"BD": "x...|....|x...|....",
                       "SD": "....|x...|....|x.oo",
                       "CH": "x.o.|x.o.|x.o.|...."},
        },
    },
    {
        "id": "neo_soul", "nome": "Neo-soul", "estilo": "r&b",
        "bpm": 88, "kit": "Lofi Kit",
        "fonte": "tr8s-grid (neo_soul); conhecimento geral (o 'atras do tempo' do Dilla)",
        "obs": "o atraso do Dilla e o START do step: o B empurra a caixa e os fantasmas",
        "variacoes": {
            "A": {"BD": "x...|..x.|..o.|....",
                  "SD": "....|x..o|..o.|x...",
                  "CH": "o.oo|.o.o|o.o.|o.oo",
                  "RS": "....|....|....|..o."},
            "B": {"BD": "x...|..x.|..o.|.o..",
                  "SD": ("....|x..o|..o.|x...", {5: {"start": 20}, 13: {"start": 20}}),
                  "CH": "o.oo|.o.o|o.o.|o.oo"},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": "....|x..o|.oo.|xooo"},
        },
    },
    # ── latino / caribe ───────────────────────────────────────────────
    {
        "id": "reggaeton_dembow", "nome": "Reggaeton (dembow)", "estilo": "reggaeton",
        "bpm": 95, "kit": "Hard Perc Kit",
        "fonte": "tr8s-grid (reggaeton_dembow); DancehallMag (2026): o Dem Bow do "
                 "Poco Man Jam, que o reggaeton herdou; conhecimento geral (bumbo nos "
                 "4, caixa no 3-3-2: 4 e 7 de cada metade)",
        "obs": "auditoria: o 'dancehall' do tr8s saiu daqui - virou o Dancehall (anos "
               "90), com fonte",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "...x|..x.|...x|..x.",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "OH": "....|....|....|..o."},
            "B": {"BD": "x...|x...|x...|x...",
                  "SD": "...x|..x.|...x|..x.",
                  "HC": "...o|..o.|...o|..o.",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "RS": "..o.|....|..o.|...."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "SD": "...x|..x.|..xx|xxxx"},
        },
    },
    {
        "id": "dembow_cru", "nome": "Dembow dominicano", "estilo": "reggaeton",
        "bpm": 115, "kit": "Hard Perc Kit",
        "fonte": "tr8s-grid (dembow_cru); conhecimento geral (o dembow dominicano, mais "
                 "seco e rapido que o reggaeton)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "...x|..x.|...x|..x.",
                  "HC": "...o|..o.|...o|..o.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "B": {"BD": "x...|x...|x..x|x...",
                  "SD": "...x|..x.|...x|..xx",
                  "HC": "...o|..o.|...o|..o.",
                  "CH": "oooo|oooo|oooo|oooo"},
            "Fill 1": {"BD": "x...|x...|....|....",
                       "SD": "...x|..x.|xxxx|xxxx"},
        },
    },
    # ── brasil ────────────────────────────────────────────────────────
    {
        "id": "funk_tamborzao", "nome": "Funk carioca (tamborzão)", "estilo": "funk brasileiro",
        "bpm": 130, "kit": "808 Kit", "scale": "8th(T)", "last": 12,
        "fonte": "tr8s-grid (funk_tamborzao); Caceres & Ferrari (RIEB/USP: Volt Mix nos "
                 "90, tamborzao 2000-2009, beatbox de 2010); Loopcloud (~130 BPM). A "
                 "celula em tercina e do tr8s - NAO conferida em transcricao",
        "obs": "Scale 8th(T), last 12: 12 steps = 1 compasso em tercina de colcheia",
        "variacoes": {
            "A": {"BD": "x.x|x.x|..x|x.x",
                  "SD": "...|...|x..|...",
                  "CH": "o.o|.o.|o.o|.o."},
            "B": {"BD": "x.x|x.x|..x|x..",
                  "SD": "...|...|x..|.xx",
                  "CH": "o.o|.o.|o.o|.o."},
            "Fill 1": {"BD": "x.x|x.x|...|...",
                       "SD": "...|...|xxx|xxX"},
        },
    },
    {
        "id": "funk_volt_mix", "nome": "Funk carioca (Volt Mix)", "estilo": "funk brasileiro",
        "bpm": 130, "kit": "TR-808-1000",
        "fonte": "Billboard Brasil ('como uma faixa obscura virou a base do funk'): o loop "
                 "do Volt Mix veio de uma faixa de TR-808 - bumbo, caixa, chimbal e "
                 "estalinhos metalicos numa celula seca; Caceres & Ferrari (RIEB/USP). "
                 "As posicoes: conhecimento geral (o miami bass por tras do funk dos 90)",
        "variacoes": {
            "A": {"BD": "x..x|..x.|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "RS": "..o.|....|.o..|..o."},
            "B": {"BD": "x..x|..x.|x.x.|..o.",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "RS": "..o.|...o|.o..|...."},
            "Fill 1": {"BD": "x..x|..x.|....|....",
                       "SD": "....|x...|x.x.|xxxx"},
        },
    },
    {
        "id": "samba_batucada", "nome": "Samba (batucada)", "estilo": "samba",
        "bpm": 100, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (samba_batucada); conhecimento geral (surdo de primeira no "
                 "2, de segunda marcando o 1; caixa em semicolcheia)",
        "obs": "port: surdo no BD (marcacao fraca no 1 e 3, resposta forte no 2 e 4), "
               "tamborim/agogo no RS",
        "variacoes": {
            "A": {"BD": "o...|x...|o...|x...",
                  "SD": "ooox|o.ox|o.ox|ooox",
                  "RS": "x..x|..x.|x..x|..x.",
                  "CH": "....|o...|....|o..."},
            # o tamborim 'carreteiro' e o surdo de terceira cortando
            "B": {"BD": "o...|x...|o...|x...",
                  "LT": "..o.|...o|..o.|..o.",
                  "SD": "ooox|o.ox|o.ox|ooox",
                  "RS": "x.xx|.x.x|x.xx|.x.x",
                  "CH": "....|o...|....|o..."},
            "Fill 1": {"BD": "o...|x...|....|....",
                       "SD": "xxxx|xxxx|x.x.|x.X.",
                       "RS": "x..x|..x.|....|...."},
        },
    },
    {
        "id": "samba_reggae", "nome": "Samba-reggae", "estilo": "samba",
        "bpm": 96, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (samba_reggae); conhecimento geral (Neguinho do Samba / "
                 "Olodum, Salvador, anos 80)",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "LT": "....|x...|....|x...",
                  "SD": "..o.|..o.|..o.|..x.",
                  "RS": "x..x|..x.|.x..|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "B": {"BD": "x...|...o|x...|....",
                  "LT": "....|x...|....|x.x.",
                  "SD": "..o.|..o.|..o.|..x.",
                  "RS": "x..x|..x.|.x..|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "x...|....|x...|....",
                       "LT": "....|x...|....|....",
                       "SD": "....|....|xxxx|xxxX"},
        },
    },
    {
        "id": "partido_alto", "nome": "Partido alto", "estilo": "samba",
        "bpm": 100, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (partido_alto); conhecimento geral (a figura do partido alto "
                 "no tamborim/pandeiro, surdo no 2 e no 4, palmas de roda)",
        "variacoes": {
            "A": {"RS": ".x..|x.x.|..x.|.x..",
                  "BD": "o...|x...|o...|x...",
                  "CH": "oooo|oooo|oooo|oooo",
                  "HC": "x...|...x|..x.|...."},
            "B": {"RS": ".x..|x.x.|..x.|.x.x",
                  "BD": "o...|x...|o..o|x...",
                  "CH": "oooo|oooo|oooo|oooo",
                  "HC": "x...|...x|..x.|...."},
            "Fill 1": {"RS": ".x..|x.x.|xxxx|xxxx",
                       "BD": "o...|x...|....|x..."},
        },
    },
    {
        "id": "bossa_nova", "nome": "Bossa nova", "estilo": "bossa nova",
        "bpm": 132, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (bossa_nova); conhecimento geral (a clave da bossa no rim - "
                 "1 4 7 11 14 -, o surdo pontuado no bumbo)",
        "variacoes": {
            "A": {"RS": "x..x|..x.|..x.|.x..",
                  "BD": "x..x|x..x|x..x|x..x",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            # a clave invertida (2-3): a outra metade do ciclo
            "B": {"RS": "..x.|.x..|x..x|..x.",
                  "BD": "x..x|x..x|x..x|x..x",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"RS": "x..x|..x.|..x.|.x..",
                       "BD": "x..x|x..x|....|....",
                       "SD": "....|....|o.o.|o.x."},
        },
    },
    {
        "id": "baiao", "nome": "Baião", "estilo": "forró",
        "bpm": 104, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (baiao); ANPPOM 2018 (o triangulo em semicolcheia "
                 "acentuando o contratempo; zabumba nos graves, celula em 2/4: "
                 "colcheia pontuada + semicolcheia); Soundbrenner, Baião",
        "obs": "triangulo = OH aberto no contratempo + CH fechado no resto (o choke do "
               "par faz o abafado); zabumba no BD (afinar grave), bacalhau no RS",
        "variacoes": {
            "A": {"BD": "x..x|....|x..x|....",
                  "RS": "....|..o.|....|..o.",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "x..x|..o.|x..x|..o.",
                  "RS": "....|o.o.|....|o.o.",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "x..x|....|x.xx|x.x.",
                       "RS": "....|..o.|....|....",
                       "OH": "..x.|..x.|....|...."},
        },
    },
    {
        "id": "xote", "nome": "Xote", "estilo": "forró",
        "bpm": 92, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (xote); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|...o|x...|...o",
                  "RS": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "B": {"BD": "x...|...o|x..o|...o",
                  "RS": "....|x...|....|x.o.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "x...|...o|x.x.|x.x.",
                       "RS": "....|x...|....|...."},
        },
    },
    {
        "id": "maracatu", "nome": "Maracatu (baque virado)", "estilo": "maracatu",
        "bpm": 105, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (maracatu); conhecimento geral (alfaias, caixa e gongue do "
                 "baque virado, simplificados ao que cabe em 16)",
        "obs": "alfaias no BD/LT (tune grave, decay longo), gongue no RS",
        "variacoes": {
            "A": {"BD": "x..x|..x.|x..x|....",
                  "LT": "....|....|....|..xx",
                  "SD": "ooxo|ooxo|ooxo|ooxo",
                  "RS": "x..x|..x.|x..x|..x.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            # a virada das alfaias (o 'repique')
            "B": {"BD": "x..x|..x.|x.xx|.x..",
                  "LT": "....|..x.|....|x.xx",
                  "SD": "ooxo|ooxo|ooxo|ooxo",
                  "RS": "x..x|..x.|x..x|..x.",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "x..x|..x.|xxxx|xxxx",
                       "LT": "....|....|xxxx|xxxX",
                       "SD": "ooxo|ooxo|....|...."},
        },
    },
    {
        "id": "frevo", "nome": "Frevo", "estilo": "frevo",
        "bpm": 152, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (frevo); conhecimento geral (a caixa no 3+3+2 dobrado, o "
                 "surdo empurrando a virada do tempo)",
        "variacoes": {
            "A": {"BD": "x...|...x|x...|....",
                  "SD": "xoox|ooxo|xoox|ooxo",
                  "HC": "....|x...|....|x...",
                  "CC": "x...|....|....|...."},
            "B": {"BD": "x...|...x|x...|...x",
                  "SD": "xoox|ooxo|xoox|ooxo",
                  "HC": "....|x...|....|x..."},
            "Fill 1": {"BD": "x...|...x|....|....",
                       "SD": "xoox|ooxo|xxxx|xxXX"},
        },
    },
    {
        "id": "ijexa", "nome": "Ijexá (afoxé)", "estilo": "afoxé",
        "bpm": 96, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (ijexa); Per Musi/UFMG e ANPPOM 2018 (o agogo/ga e a linha "
                 "guia; rumpi e le repetem a base, o rum improvisa por cima)",
        "obs": "port: o MT do tr8s virou LT (rumpi/le); agogo no RS, xequere no CH, rum "
               "no HT no B",
        "variacoes": {
            "A": {"RS": "x..x|..x.|x.x.|x.x.",
                  "BD": "....|..x.|....|..x.",
                  "LT": "..o.|.o..|..o.|.o..",
                  "CH": "oooo|oooo|oooo|oooo"},
            # o rum (HT) conversando
            "B": {"RS": "x..x|..x.|x.x.|x.x.",
                  "BD": "....|..x.|....|..x.",
                  "LT": "..o.|.o..|..o.|.o..",
                  "HT": "x...|....|..x.|x...",
                  "CH": "oooo|oooo|oooo|oooo"},
            "Fill 1": {"RS": "x..x|..x.|x.x.|x.x.",
                       "HT": "....|x.x.|xxx.|x.X."},
        },
    },
    {
        "id": "coco", "nome": "Coco", "estilo": "coco",
        "bpm": 104, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (coco); conhecimento geral (o ganza carrega o coco)",
        "variacoes": {
            "A": {"BD": "x...|..x.|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "oooo|oooo|oooo|oooo",
                  "RS": "..x.|..x.|..x.|..x."},
            "B": {"BD": "x...|..x.|..x.|..o.",
                  "SD": "....|x...|....|x...",
                  "CH": "oooo|oooo|oooo|oooo",
                  "RS": "..x.|..x.|..x.|..x.",
                  "HC": "....|x...|....|x..."},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": "....|x...|xxxx|x.x."},
        },
    },
    {
        "id": "carimbo", "nome": "Carimbó", "estilo": "carimbó",
        "bpm": 110, "kit": "727 Kit 2",
        "fonte": "tr8s-grid (carimbo); conhecimento geral (curimbo grave pergunta, o "
                 "medio responde; milheiro em semicolcheia)",
        "obs": "port: o MT do tr8s virou HT",
        "variacoes": {
            "A": {"LT": "x.x.|..x.|x.x.|..x.",
                  "BD": "x...|....|x...|....",
                  "HT": "....|o..o|....|.o..",
                  "CH": "oooo|oooo|oooo|oooo",
                  "RS": "....|x...|....|x..."},
            "B": {"LT": "x.x.|..x.|x.x.|x.x.",
                  "BD": "x...|....|x...|....",
                  "HT": "....|o..o|...o|.o..",
                  "CH": "oooo|oooo|oooo|oooo",
                  "RS": "....|x...|....|x..."},
            "Fill 1": {"LT": "x.x.|..x.|xxxx|xxxX",
                       "HT": "....|o..o|....|...."},
        },
    },
    # ── africa ────────────────────────────────────────────────────────
    {
        "id": "afrobeat", "nome": "Afrobeat (Tony Allen)", "estilo": "afrobeat",
        "bpm": 110, "kit": "Hard Perc Kit",
        "fonte": "tr8s-grid (afrobeat); conhecimento geral (Tony Allen simplificado ao "
                 "que cabe em 16: o sino no ride, o bumbo conversando com a caixa)",
        "variacoes": {
            "A": {"BD": "x...|...x|..x.|....",
                  "SD": ".o..|o..x|...o|.o..",
                  "RC": "x..x|..x.|.x.x|..x.",
                  "CH": "..o.|..o.|....|.o.."},
            "B": {"BD": "x...|...x|..x.|..x.",
                  "SD": ".o..|o..x|...o|.o.o",
                  "RC": "x..x|..x.|.x.x|..x.",
                  "OH": "....|....|....|..o."},
            "Fill 1": {"BD": "x...|...x|....|....",
                       "SD": ".o..|o..x|o.oo|xoxo"},
        },
    },
    {
        "id": "gqom", "nome": "Gqom", "estilo": "afro / sul-africano",
        "bpm": 124, "kit": "Hard Perc Kit",
        "fonte": "tr8s-grid (gqom); conhecimento geral (Durban: o vazio no 1, o peso na "
                 "sincopa e nos toms)",
        "variacoes": {
            "A": {"BD": "..x.|..x.|..x.|.x..",
                  "LT": "x...|....|x...|....",
                  "SD": "....|..o.|....|..o.",
                  "CH": "o..o|o..o|o..o|o..o"},
            "B": {"BD": "..x.|..x.|..x.|.x..",
                  "LT": "x...|...x|x...|....",
                  "HT": "....|....|....|..o.",
                  "SD": "....|..o.|....|..o.",
                  "CH": "o..o|o..o|o..o|o..o"},
            "Fill 1": {"BD": "..x.|..x.|....|....",
                       "LT": "x...|....|x.x.|x.x."},
        },
    },
    {
        "id": "amapiano", "nome": "Amapiano", "estilo": "afro / sul-africano",
        "bpm": 112, "kit": "Hard Perc Kit",
        "fonte": "tr8s-grid (amapiano); conhecimento geral (o log drum sincopado; o "
                 "shaker e o rim andando)",
        "obs": "o log drum e um tom de bumbo grave com pitch: afinar o BD (ou usar o LT) "
               "bem grave e com decay",
        "variacoes": {
            "A": {"BD": "..o.|.x..|...o|..x.",
                  "RS": "x...|x...|x...|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "HC": "....|....|..x.|...."},
            "B": {"BD": "..o.|.x..|...o|..x.",
                  "LT": "....|....|....|...o",
                  "RS": "x...|x...|x...|x..o",
                  "CH": "oooo|oooo|oooo|oooo",
                  "HC": "....|....|..x.|...."},
            "Fill 1": {"BD": "..o.|.x..|.o.o|.o.x",
                       "RS": "x...|x...|....|...."},
        },
    },
    # ── garage / footwork ─────────────────────────────────────────────
    {
        "id": "garage_2step", "nome": "UK garage (2-step)", "estilo": "garage",
        "bpm": 132, "kit": "Westend Kit",
        "fonte": "tr8s-grid (garage_2step); conhecimento geral (o bumbo que pula o 3 e o "
                 "chimbal saltado)",
        "variacoes": {
            "A": {"BD": "x...|...x|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|.oo.|o.o.|.oo.",
                  "RS": "....|....|...o|....",
                  "OH": "....|....|....|..o."},
            "B": {"BD": "x...|...x|....|..x.",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|.oo.|o.o.|.oo.",
                  "RS": "...o|....|...o|...."},
            "Fill 1": {"BD": "x...|...x|....|....",
                       "SD": "....|x...|.o.o|xoxX"},
        },
    },
    {
        "id": "footwork", "nome": "Footwork", "estilo": "footwork",
        "bpm": 160, "kit": "808 Kit",
        "fonte": "tr8s-grid (footwork); conhecimento geral (Chicago: os toms em tercina)",
        "obs": "os toms em tercina sao o SUB 1/3",
        "variacoes": {
            "A": {"BD": "x..x|..x.|..x.|.x..",
                  "HC": "....|x...|....|x...",
                  "LT": ("....|..x.|....|..o.", {7: {"sub": "1/3"}, 15: {"sub": "1/3"}}),
                  "CH": "o...|o...|o...|o..."},
            "B": {"BD": "x..x|..x.|..x.|.x.x",
                  "HC": "....|x...|....|x...",
                  "HT": ("..o.|....|..o.|....", {3: {"sub": "1/3"}, 11: {"sub": "1/3"}}),
                  "LT": ("....|..x.|....|..o.", {7: {"sub": "1/3"}}),
                  "CH": "o...|o...|o...|o..."},
            "Fill 1": {"BD": "x..x|..x.|....|....",
                       "LT": ("....|....|x.x.|x.x.", {9: {"sub": "1/3"}, 11: {"sub": "1/3"},
                                                   13: {"sub": "1/3"}, 15: {"sub": "1/3"}})},
        },
    },
    # ── rock ──────────────────────────────────────────────────────────
    {
        "id": "punk_dbeat", "nome": "Punk (d-beat)", "estilo": "rock",
        "bpm": 180, "kit": "Regular Kit",
        "fonte": "Wikipedia, D-beat (Discharge, 1982; a grade de 16 em colcheias: bumbo "
                 "1 4 6, caixa 3 7 - aqui em semicolcheia, 1 compasso = 2 da grade)",
        "obs": "auditoria: o tr8s tinha o bumbo e a caixa juntos no 7 e no 15; a celula "
               "da Wikipedia separa os dois. A e o refrao (prato), B o verso (chimbal)",
        "variacoes": {
            "A": {"BD": "x...|..x.|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CC": "x...|..x.|..x.|...."},
            "B": {"BD": "x...|..x.|..x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": "....|x...|xxxx|xxxx",
                       "CC": "x...|....|....|...."},
        },
    },
    {
        "id": "rock_basico", "nome": "Rock de garagem", "estilo": "rock",
        "bpm": 132, "kit": "Regular Kit",
        "fonte": "tr8s-grid (rock_basico); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|...x|x...|....",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "OH": "....|....|....|..o."},
            "B": {"BD": "x...|...x|x.x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o.",
                  "CC": "x...|....|....|...."},
            "Fill 1": {"BD": "x...|...x|....|....",
                       "SD": "....|x...|xx..|....",
                       "HT": "....|....|..xx|....",
                       "LT": "....|....|....|xxxX"},
        },
    },
    # ── trance / psy ──────────────────────────────────────────────────
    {
        "id": "trance_uplifting", "nome": "Trance (uplifting)", "estilo": "trance",
        "bpm": 138, "kit": "Trance Kit",
        "fonte": "tr8s-grid (trance_uplifting); conhecimento geral",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HC": "....|x...|....|x..."},
            "B": {"BD": "X...|X...|X...|X...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HC": "....|x...|....|x...",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            # o rolo de caixa da virada de 8 em 8 compassos
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": ("o.o.|o.o.|oooo|xxxx", {13: {"sub": "1/2"}, 14: {"sub": "1/2"},
                                                   15: {"sub": "1/4"}, 16: {"sub": "1/4"}})},
        },
    },
    {
        "id": "trance_progressive", "nome": "Trance (progressive)", "estilo": "trance",
        "bpm": 132, "kit": "Trance Kit",
        "fonte": "tr8s-grid (trance_progressive); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "CH": "o..o|o..o|o..o|o..o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RS": "...o|..o.|...o|..o.",
                  "HC": "....|o...|....|o..."},
            "B": {"BD": "x...|x...|x...|x...",
                  "CH": "o..o|o..o|o..o|o..o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RS": "...o|..o.|.o.o|..o.",
                  "HC": "....|o...|....|o..."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "RS": "...o|..o.|oooo|oooo",
                       "HC": "....|o...|....|o..."},
        },
    },
    {
        "id": "psy_fullon", "nome": "Psytrance (full-on)", "estilo": "psytrance",
        "bpm": 145, "kit": "Trance Kit",
        "fonte": "tr8s-grid (psy_fullon); conhecimento geral (o grave no contratempo e "
                 "o baixo, nao a bateria)",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HC": "....|....|....|x..."},
            "B": {"BD": "X...|X...|X...|X...",
                  "CH": "oo.o|oo.o|oo.o|oo.o",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HC": "....|x...|....|x...",
                  "RS": "...o|...o|...o|...o"},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "SD": "....|....|o.o.|xxxx"},
        },
    },
    {
        "id": "psy_prog", "nome": "Psytrance (progressivo)", "estilo": "psytrance",
        "bpm": 140, "kit": "Trance Kit",
        "fonte": "tr8s-grid (psy_prog); conhecimento geral",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "CH": ".o..|.o..|.o..|.o..",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RS": "....|...o|....|...o"},
            "B": {"BD": "x...|x...|x...|x...",
                  "CH": ".o.o|.o..|.o.o|.o..",
                  "OH": "..x.|..x.|..x.|..x.",
                  "RS": "....|...o|..o.|...o"},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "RS": "....|...o|oooo|oooo"},
        },
    },
    # ── ambient ───────────────────────────────────────────────────────
    {
        "id": "ambient_mare", "nome": "Ambient (maré)", "estilo": "ambient",
        "bpm": 76, "kit": "Ground Swell",
        "fonte": "tr8s-grid (ambient_mare)",
        "obs": "reverb e delay altos (o Play faz isso) - o espaco e o instrumento",
        "variacoes": {
            "A": {"BD": "x...|....|..o.|....",
                  "RC": "....|o...|....|o...",
                  "CC": "....|....|o...|....",
                  "RS": "....|..o.|....|....",
                  "CH": "..o.|....|o...|..o."},
            "B": {"BD": "x...|....|....|..o.",
                  "RC": "....|o...|....|o...",
                  "RS": "....|....|..o.|....",
                  "CH": "..o.|....|o...|...."},
            "Fill 1": {"RC": "o...|o...|o.o.|oooo",
                       "CC": "....|....|....|...o"},
        },
        "mix": {"rs.rvb": 800, "ch.rvb": 700, "rc.rvb": 700, "cc.rvb": 800, "rs.dly": 500},
    },
    {
        "id": "ambient_pulso", "nome": "Ambient (pulso)", "estilo": "ambient",
        "bpm": 90, "kit": "Ground Swell",
        "fonte": "tr8s-grid (ambient_pulso)",
        "variacoes": {
            "A": {"BD": "x...|....|x...|....",
                  "CH": "o...|o...|o...|o...",
                  "RC": "..o.|..o.|..o.|..o.",
                  "SD": "....|....|....|o...",
                  "OH": "....|..o.|....|...."},
            "B": {"BD": "x...|....|x..o|....",
                  "CH": "o...|o...|o...|o...",
                  "RC": "..o.|..o.|..o.|..o.",
                  "SD": "....|....|....|o..."},
            "Fill 1": {"BD": "x...|....|x...|....",
                       "SD": "....|....|..o.|o.o."},
        },
    },

    # ══ OS QUE FALTAVAM (pesquisa de 13/10/2026) ═══════════════════════
    # Pesquisados e NAO incluidos, por falta de uma grade com fonte: funk
    # 150 (Polyvox, 2016 - so a historia e o tempo), brega funk e pisadinha.
    {
        "id": "jersey_club", "nome": "Jersey club", "estilo": "club",
        "bpm": 140, "kit": "TR-808-1000",
        "fonte": "Native Instruments blog (Jersey club: bumbo nos steps 1 5 9 12 15, "
                 "velocity 100, 808 com corte de grave); orphiq.com (4-4-3-3-2, a "
                 "metade de tras em tresillo; 130-140 BPM; caixa contra o bumbo, nao "
                 "no backbeat; chimbal esparso no 2 e no 4; o 'bed squeak' de "
                 "Trillville, 2004)",
        "obs": "o bed squeak e um sample: aqui o RS faz o papel dele, entre os bumbos",
        "variacoes": {
            "A": {"BD": "x...|x...|x..x|..x.",
                  "SD": "....|..x.|....|x...",
                  "CH": "....|x...|....|x...",
                  "RS": "..o.|....|.o..|...."},
            # os bumbos em tercina (sub) - a assinatura das viradas de jersey
            "B": {"BD": ("x...|x...|x..x|..x.", {12: {"sub": "1/3"}, 15: {"sub": "1/3"}}),
                  "SD": "....|..x.|....|x...",
                  "CH": "....|x...|....|x...",
                  "RS": "..o.|...o|.o..|...."},
            "Fill 1": {"BD": ("x..x|..x.|x..x|..x.", {9: {"sub": "1/3"}, 12: {"sub": "1/3"},
                                                   15: {"sub": "1/3"}}),
                       "SD": "....|..x.|....|...."},
        },
    },
    {
        "id": "uk_drill", "nome": "UK drill", "estilo": "hip-hop",
        "bpm": 142, "kit": "TR-808-1000",
        "fonte": "attackmagazine.com, Beat Dissected: UK drill (o chimbal 'empresta do "
                 "grime': dois espacos, dois espacos, um espaco na grade de 16, com "
                 "rolos e tercinas; fantasmas de caixa no ultimo compasso); "
                 "violetrecording.com (caixa no 3 de cada compasso, meio tempo)",
        "obs": "o 808 deslizando e o baixo: no BD so a marcacao",
        "variacoes": {
            "A": {"BD": "x...|....|..x.|....",
                  "SD": "....|....|x...|....",
                  "CH": "x..x|..x.|x..x|..x."},
            "B": {"BD": "x...|..x.|....|.x..",
                  "SD": "....|....|x...|..o.",
                  "CH": ("x..x|..x.|x..x|..x.", {7: {"sub": "Triplet 1"}, 15: {"sub": "1/3"}}),
                  "OH": "....|....|....|...o"},
            "Fill 1": {"BD": "x...|....|....|....",
                       "SD": "....|....|x..o|.oo.",
                       "CH": ("x..x|..x.|....|....", {4: {"sub": "1/4"}})},
        },
    },
    {
        "id": "cumbia", "nome": "Cumbia", "estilo": "latino",
        "bpm": 92, "kit": "727 Kit 2",
        "fonte": "Wikipedia, Güira (o 'golpe'/galope da cumbia: escovada no tempo com o "
                 "'e-a' antes; guiro de cabaca ou guira de metal); jamzone.musicwill "
                 "(comecar a 60-70 e subir a 88). Bumbo e conga: conhecimento geral",
        "obs": "guiro no CH (o galope: o 'e' e o 'a' fracos levando ao tempo), tambora no "
               "BD, conga no LT/HT, campana no RS",
        "variacoes": {
            "A": {"CH": "x.oo|x.oo|x.oo|x.oo",
                  "BD": "x...|....|x...|....",
                  "LT": "....|..x.|....|..xx",
                  "HT": "..o.|....|..o.|....",
                  "RS": "x...|x...|x...|x..."},
            "B": {"CH": "x.oo|x.oo|x.oo|x.oo",
                  "BD": "x...|...o|x...|....",
                  "LT": "....|..x.|....|..xx",
                  "HT": "..o.|.o..|..o.|.o..",
                  "RS": "x.x.|x...|x.x.|x..."},
            "Fill 1": {"CH": "x.oo|x.oo|....|....",
                       "LT": "....|..x.|x.x.|xxxx",
                       "HT": "....|....|.x.x|...."},
        },
    },
    {
        "id": "italo_disco", "nome": "Italo disco / hi-NRG", "estilo": "disco",
        "bpm": 124, "kit": "707 & 727 Kit",
        "fonte": "conhecimento geral (anos 80: bumbo nos 4, palma/caixa no 2 e no 4, "
                 "aberto no contratempo, o baixo em oitavas em colcheia faz o resto)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "x.o.|x.o.|x.o.|x.o.",
                  "OH": "..x.|..x.|..x.|..x."},
            "B": {"BD": "x...|x...|x...|x...",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x..o",
                  "CH": "xooo|xooo|xooo|xooo",
                  "OH": "..x.|..x.|..x.|..x."},
            "Fill 1": {"BD": "x...|x...|x...|x...",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|x.x."},
        },
    },
    {
        "id": "ebm", "nome": "EBM", "estilo": "techno",
        "bpm": 124, "kit": "Deep Techno Kit",
        "fonte": "conhecimento geral (DAF, Front 242, Nitzer Ebb: bumbo reto, caixa "
                 "pesada no 2 e no 4; o sequenciador de baixo em semicolcheia e o motor)",
        "variacoes": {
            "A": {"BD": "X...|x...|X...|x...",
                  "SD": "....|X...|....|X...",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "B": {"BD": "X...|x...|X.x.|x...",
                  "SD": "....|X...|....|X..o",
                  "HC": "....|x...|....|x...",
                  "CH": "o.o.|o.o.|o.o.|o.o."},
            "Fill 1": {"BD": "X...|x...|....|....",
                       "SD": "....|X...|xxxx|XXXX"},
        },
    },
    {
        "id": "synthpop_707", "nome": "Synthpop / new wave", "estilo": "pop",
        "bpm": 120, "kit": "707 Kit 1",
        "fonte": "conhecimento geral (a TR-707 dos anos 80: bumbo no 1, no 'e' do 2 e no "
                 "3, caixa e palma juntas no 2 e no 4, chimbal em semicolcheia)",
        "variacoes": {
            "A": {"BD": "x...|..x.|x...|....",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xoxo"},
            "B": {"BD": "x...|..x.|x.x.|....",
                  "SD": "....|x...|....|x...",
                  "HC": "....|x...|....|x...",
                  "CH": "xoxo|xoxo|xoxo|xo..",
                  "OH": "....|....|....|..x."},
            "Fill 1": {"BD": "x...|..x.|....|....",
                       "SD": "....|x...|....|....",
                       "HT": "....|....|x.x.|....",
                       "LT": "....|....|....|x.x."},
        },
    },
    {
        "id": "motorik", "nome": "Motorik (krautrock)", "estilo": "rock",
        "bpm": 148, "kit": "Regular Kit",
        "fonte": "conhecimento geral (Klaus Dinger, Neu! 'Hallogallo', 1972: a batida "
                 "reta e sem fim - colcheias no chimbal, caixa no 2 e no 4, o bumbo "
                 "empurrando o 3)",
        "variacoes": {
            "A": {"BD": "x...|....|x.x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x."},
            "B": {"BD": "x...|....|x.x.|....",
                  "SD": "....|x...|....|x...",
                  "CH": "x.x.|x.x.|x.x.|x.x.",
                  "OH": "....|....|....|..o."},
            "Fill 1": {"BD": "x...|....|x.x.|....",
                       "SD": "....|x...|....|x.x.",
                       "CC": "....|....|....|...x"},
        },
    },
    {
        "id": "new_jack_swing", "nome": "New jack swing", "estilo": "r&b",
        "bpm": 104, "kit": "Lofi Kit", "scale": "16th(T)", "last": 12,
        "fonte": "conhecimento geral (Teddy Riley, fim dos 80: semicolcheias swingadas, "
                 "caixa e palma secas no 2 e no 4, bumbo sincopado)",
        "obs": "Scale 16th(T), last 12: 6 steps por tempo, cada variacao e MEIO "
               "compasso; a semicolcheia swingada e o 3o step de cada grupo de 3",
        "variacoes": {
            "A": {"BD": "x..|..x|...|x..",
                  "SD": "...|...|x..|...",
                  "HC": "...|...|x..|...",
                  "CH": "x.o|x.o|x.o|x.o"},
            "B": {"BD": "x..|...|..x|x.o",
                  "SD": "...|...|x..|..o",
                  "HC": "...|...|x..|...",
                  "CH": "x.o|x.o|x.o|x.o"},
            "Fill 1": {"BD": "x..|...|...|...",
                       "SD": "...|...|x.x|xxX"},
        },
    },
    {
        "id": "afrobeats", "nome": "Afrobeats (Lagos)", "estilo": "afro / sul-africano",
        "bpm": 106, "kit": "Hard Perc Kit",
        "fonte": "conhecimento geral (o afrobeats nigeriano dos anos 2010: bumbo em "
                 "tresillo, rim no contratempo, shaker em semicolcheia, palma no 2 e "
                 "no 4) - nao conferido em transcricao",
        "variacoes": {
            "A": {"BD": "x..x|..x.|..x.|....",
                  "RS": "...x|..x.|...x|..x.",
                  "HC": "....|x...|....|x...",
                  "CH": "xoox|xoox|xoox|xoox"},
            "B": {"BD": "x..x|..x.|..x.|.x..",
                  "RS": "...x|..x.|.x.x|..x.",
                  "HC": "....|x...|....|x...",
                  "CH": "xoox|xoox|xoox|xoox",
                  "LT": "....|....|....|..o."},
            "Fill 1": {"BD": "x..x|..x.|....|....",
                       "RS": "...x|..x.|x.x.|x.x.",
                       "LT": "....|....|.o.o|.o.o"},
        },
    },
    {
        "id": "afro_house", "nome": "Afro house", "estilo": "afro / sul-africano",
        "bpm": 122, "kit": "Hard Perc Kit",
        "fonte": "conhecimento geral (bumbo reto, shaker em semicolcheia, congas "
                 "sincopadas e o rim em tresillo)",
        "variacoes": {
            "A": {"BD": "x...|x...|x...|x...",
                  "RS": "x..x|..x.|x..x|..x.",
                  "CH": "oxoo|oxoo|oxoo|oxoo",
                  "LT": "....|..x.|....|x.x.",
                  "HT": "..o.|....|..o.|...."},
            "B": {"BD": "x...|x...|x...|x...",
                  "RS": "x..x|..x.|x..x|..x.",
                  "CH": "oxoo|oxoo|oxoo|oxoo",
                  "OH": "..x.|..x.|..x.|..x.",
                  "LT": "....|..x.|...x|x.x.",
                  "HT": "..o.|.o..|..o.|...."},
            "Fill 1": {"BD": "x...|x...|x...|....",
                       "LT": "....|..x.|x.x.|xxxx",
                       "HT": "..o.|....|.o.o|...."},
        },
    },
    {
        "id": "gabber", "nome": "Gabber", "estilo": "hardcore",
        "bpm": 185, "kit": "TR-909-1000",
        "fonte": "conhecimento geral (Roterda, anos 90: o bumbo 909 distorcido em todo "
                 "tempo, o aberto no contratempo)",
        "obs": "a distorcao do bumbo e o som do gabber: puxar o drive/tune do BD",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "HC": "....|x...|....|x..."},
            "B": {"BD": "X...|X...|X...|X.x.",
                  "OH": "..x.|..x.|..x.|..x.",
                  "SD": "....|x...|....|x...",
                  "CH": "oo.o|oo.o|oo.o|oo.o"},
            "Fill 1": {"BD": "X...|X...|XXXX|XXXX"},
        },
    },
    {
        "id": "hardstyle", "nome": "Hardstyle", "estilo": "hardcore",
        "bpm": 150, "kit": "HardTechnoKit",
        "fonte": "conhecimento geral (bumbo reto com cauda; a 'reverse bass' no "
                 "contratempo e o sintetizador)",
        "variacoes": {
            "A": {"BD": "X...|X...|X...|X...",
                  "HC": "....|x...|....|x...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "CH": "o...|o...|o...|o..."},
            "B": {"BD": "X...|X...|X...|X...",
                  "HC": "....|x...|....|x...",
                  "OH": "..x.|..x.|..x.|..x.",
                  "CH": "o..o|o..o|o..o|o..o",
                  "RC": "x.x.|x.x.|x.x.|x.x."},
            "Fill 1": {"BD": "X...|X...|X...|X...",
                       "HC": "....|x...|xxxx|xxxX"},
        },
    },
]

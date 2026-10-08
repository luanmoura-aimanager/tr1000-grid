#!/usr/bin/env python3
"""
catalogo_app.py - o catalogo de parametros que o TR-1000 App carrega dentro de si

Uso:
    python3 catalogo_app.py                 # le o App instalado, grava o JSON
    python3 catalogo_app.py --mostrar       # so imprime, nao grava
    python3 catalogo_app.py --app CAMINHO   # outro binario (outra versao)

O QUE ISTO E (REFERENCIA 2.2)
    O binario do App tem, numa tabela contigua de strings, os nomes de todos os
    parametros da maquina NA ORDEM: sistema, MIDI, o bloco de performance
    (KIT_NUM, PTN_NUM, ..., cur_step0..10, cur_vari0..10), o projeto, o kit, o
    cabecalho do pattern (Tempo, Variation, ..., Begin/End Step) e os campos do
    step (note, probability, sub_step, cycle...). Achado em 07/10/2026 com
    `strings`, na versao 1.10 do App.

O QUE ISTO NAO E
    Nao e o layout: e o VOCABULARIO. A tabela vem da secao de strings do
    binario, onde o linker guarda cada string identica UMA vez so. Todo nome
    que se repete na tabela real (o CTRL1 de cada instrumento, PRM1..,
    LEVEL...) aparece so na primeira ocorrencia - no App 1.10 sao 2401 nomes e
    ZERO repetidos, o que ja diz que houve deduplicacao. Um bloco de 10
    instrumentos vira um conjunto de nomes so (revisao de 07/10/2026).

    Nao e mapa de enderecos. A ORDEM dos nomes e uma HIPOTESE de ordem de
    offsets so onde os nomes sao unicos (performance, cabecalho do pattern) -
    e mesmo ali, nao medida. Nenhum endereco sai daqui; eles saem da sessao C1 (sniff do
    App), e o catalogo serve para dar NOME ao que a captura mostrar.

    O JSON gerado vai para capturas/ e fica FORA do git (.gitignore): e
    derivado do binario da Roland. O que se versiona e este extrator.
"""
import json, os, plistlib, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
APP = "/Applications/Roland/TR-1000 App.app"
BINARIO = "Contents/MacOS/TR-1000 App"

# A string que prova que achamos a tabela certa: so existe nela.
ANCORA = b"KIT_NUM"

# Tamanho minimo de uma string da tabela. A tabela tem nomes de 1-2 letras
# ("H", "L", "W/F") nos parametros de efeito; minimo 1 e seguro porque so
# aceitamos o trecho CONTIGUO em volta da ancora (ver _regiao_contigua).
MIN_STR = 1

# Folga entre duas strings vizinhas da mesma tabela: o compilador separa por
# NUL e as vezes alinha. Mais que isso e fim de tabela.
FOLGA_MAX = 8

# Onde cada bloco COMECA, pela primeira string dele. HIPOTESE de leitura, nao
# fato: os nomes dos blocos sao nossos, e a fronteira foi escolhida olhando a
# lista (07/10/2026). O que ficar antes da primeira ancora vira "inicio".
BLOCOS = [
    ("sistema",       "Bright"),
    ("midi",          "Device ID"),
    ("performance",   "KIT_NUM"),          # o 01 00 00 00 da TR-8S tinha kit/pattern/next
    ("projeto",       "Tempo Source"),
    ("kit",           "CUSTOM LED"),
    ("pattern",       "Name1"),            # nome do pattern (16 chars) + Tempo...
    ("step",          "Accent Weak"),
    ("hardware",      "ANA DEBUG"),        # calibracao, deteccao dos analogicos
    ("efeitos_inst",  "PRE DLY"),          # reverb/delay/MFX/IFX e os params dos GEN
]


def versao_do_app(app=APP):
    try:
        with open(os.path.join(app, "Contents/Info.plist"), "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString", "?")
    except Exception:
        return "?"


def strings_com_offset(dados, minimo=MIN_STR):
    """[(offset, texto)] de toda sequencia ASCII imprimivel terminada em NUL."""
    out = []
    for m in re.finditer(rb"[\x20-\x7E]{%d,}(?=\x00)" % minimo, dados):
        out.append((m.start(), m.group().decode("ascii")))
    return out


def _regiao_contigua(strs, ancora=ANCORA.decode()):
    """O trecho de strings coladas (folga <= FOLGA_MAX) que contem a ancora."""
    idx = next((i for i, (_, s) in enumerate(strs) if s == ancora), None)
    if idx is None:
        return []
    ini = fim = idx
    while ini > 0:
        o_ant, s_ant = strs[ini - 1]
        if strs[ini][0] - (o_ant + len(s_ant)) > FOLGA_MAX:
            break
        ini -= 1
    while fim + 1 < len(strs):
        o, s = strs[fim]
        if strs[fim + 1][0] - (o + len(s)) > FOLGA_MAX:
            break
        fim += 1
    regiao = strs[ini:fim + 1]
    # Com MIN_STR = 1, qualquer byte imprimivel seguido de NUL perto da tabela
    # entra nas pontas: no App 1.10 a regiao terminava em "... ABS END MSB | 10"
    # (revisao de 07/10/2026). Nome de parametro comeca com letra ou "_".
    while regiao and not _NOME.match(regiao[0][1]):
        regiao = regiao[1:]
    while regiao and not _NOME.match(regiao[-1][1]):
        regiao = regiao[:-1]
    return regiao


_NOME = re.compile(r"^[A-Za-z_]")


_SERIE = re.compile(r"^(.*?)(\d+)$")


def comprimir(nomes):
    """Series viram um item: note0..note63 -> {"nome": "note", "de": 0,
    "ate": 63}. Nome solto fica string. A serie so continua se o numero
    cresce de 1 em 1 com o mesmo prefixo - "QUANTIZE1, QUANTIZE10, QUANTIZE2"
    (ordem alfabetica, existe no binario) NAO vira serie, e e bom que nao vire:
    seria esconder uma ordem que nao e de offset."""
    out = []
    for n in nomes:
        m = _SERIE.match(n)
        if m and out and isinstance(out[-1], dict):
            ult = out[-1]
            if m.group(1) == ult["nome"] and int(m.group(2)) == ult["ate"] + 1:
                ult["ate"] += 1
                continue
        if m and m.group(1):
            out.append({"nome": m.group(1), "de": int(m.group(2)),
                        "ate": int(m.group(2))})
        else:
            out.append(n)
    # serie de um elemento so volta a ser string
    return [x["nome"] + str(x["de"]) if isinstance(x, dict) and
            x["de"] == x["ate"] else x for x in out]


def segmentar(nomes, blocos=BLOCOS):
    """Corta a lista na primeira ocorrencia de cada ancora, em ordem."""
    cortes, pos = [], 0
    for rotulo, primeira in blocos:
        try:
            i = nomes.index(primeira, pos)
        except ValueError:
            continue
        cortes.append((rotulo, i))
        pos = i + 1
    out = []
    if not cortes or cortes[0][1] > 0:
        out.append(("inicio", nomes[:cortes[0][1] if cortes else len(nomes)]))
    for k, (rotulo, i) in enumerate(cortes):
        fim = cortes[k + 1][1] if k + 1 < len(cortes) else len(nomes)
        out.append((rotulo, nomes[i:fim]))
    return out


def extrair(dados):
    """bytes do binario -> (regiao [(offset, texto)], blocos [(rotulo, nomes)])"""
    regiao = _regiao_contigua(strings_com_offset(dados))
    return regiao, segmentar([s for _, s in regiao])


def _fmt_item(x):
    if isinstance(x, dict):
        return f"{x['nome']}[{x['de']}..{x['ate']}]"
    return x


def main(argv):
    app = APP
    if "--app" in argv:
        app = argv[argv.index("--app") + 1]
    caminho = app if os.path.isfile(app) else os.path.join(app, BINARIO)
    if not os.path.exists(caminho):
        print(f"(!) nao achei o binario do App em {caminho}")
        return 1
    with open(caminho, "rb") as f:
        dados = f.read()
    regiao, blocos = extrair(dados)
    if not regiao:
        print("(!) a ancora KIT_NUM nao esta neste binario - outra versao do "
              "App mudou a tabela? Nada foi gravado.")
        return 1

    versao = versao_do_app(app) if os.path.isdir(app) else "?"
    print(f"TR-1000 App {versao}: {len(regiao)} nomes contiguos em "
          f"0x{regiao[0][0]:X}..0x{regiao[-1][0]:X}\n")
    saida = []
    for rotulo, nomes in blocos:
        comp = comprimir(nomes)
        saida.append({"bloco": rotulo, "n_nomes": len(nomes), "itens": comp})
        print(f"## {rotulo} ({len(nomes)} nomes)")
        print("   " + " | ".join(_fmt_item(x) for x in comp))
        print()

    if "--mostrar" in argv:
        return 0
    destino = os.path.join(AQUI, "capturas", f"catalogo-app-{versao}.json")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w") as f:
        json.dump({"app_versao": versao, "binario": caminho,
                   "offset_ini": regiao[0][0], "offset_fim": regiao[-1][0],
                   "aviso": "vocabulario em ordem de primeira ocorrencia; "
                            "nomes repetidos foram deduplicados pelo linker, "
                            "entao NAO e layout de offsets nem mapa de "
                            "enderecos (REFERENCIA 2.2)",
                   "blocos": saida}, f, indent=1)
    print(f"gravado em {os.path.relpath(destino, AQUI)} (fora do git)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

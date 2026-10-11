#!/usr/bin/env python3
"""
icone.py - o icone do TR-1000 Controller, desenhado aqui mesmo: o PIL nao
esta instalado, entao o PNG sai de um codificador de 20 linhas em zlib puro (o
mesmo do criar_app.py do tr8s-grid). O sips e o iconutil, que vem no macOS,
fazem o .icns.

    python3 icone.py        # gera web/icon-192.png e web/icon-512.png

O desenho e o grid como ele fica na mesa: steps vermelhos (layer A), verdes
(so B), um roxo (ALT), a coluna branca do playhead, e a faixa laranja do
botao ON do App da Roland embaixo.
"""
import os, shutil, struct, subprocess, zlib

AQUI = os.path.dirname(os.path.abspath(__file__))


def escrever_png(caminho, largura, altura, linhas):
    """linhas = lista de listas de (r, g, b)."""
    cru = b"".join(b"\x00" + bytes(v for px in linha for v in px) for linha in linhas)

    def bloco(tipo, dados):
        return (struct.pack(">I", len(dados)) + tipo + dados +
                struct.pack(">I", zlib.crc32(tipo + dados) & 0xFFFFFFFF))

    with open(caminho, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0)))
        f.write(bloco(b"IDAT", zlib.compress(cru, 9)))
        f.write(bloco(b"IEND", b""))


def desenhar(lado):
    FUNDO, VAZIO, TEMPO = (18, 17, 16), (40, 37, 34), (60, 56, 51)
    A, B, ALT, PLAY, ON = (255, 59, 48), (52, 208, 88), (168, 85, 247), (244, 244, 244), (255, 122, 26)
    a = {(0, 0), (0, 4), (0, 8), (0, 12), (1, 3), (1, 11), (3, 14), (5, 4), (5, 12),
         (6, 0), (6, 2), (6, 6), (6, 10), (6, 14), (7, 2), (7, 10)}
    b = {(1, 1), (1, 6), (1, 9), (1, 15), (2, 10)}
    alt = {(4, 2)}
    playhead = 5
    px = [[FUNDO] * lado for _ in range(lado)]
    margem = int(lado * 0.10)
    celula = (lado - 2 * margem) // 16
    topo = int(lado * 0.24)
    folga = max(1, celula // 7)
    for l in range(8):
        for c in range(16):
            if c == playhead:
                cor = PLAY
            elif (l, c) in alt:
                cor = ALT
            elif (l, c) in a:
                cor = A
            elif (l, c) in b:
                cor = B
            else:
                cor = TEMPO if c % 4 == 0 else VAZIO
            x0, y0 = margem + c * celula + folga, topo + l * celula + folga
            for y in range(y0, y0 + celula - 2 * folga):
                linha = px[y]
                for x in range(x0, x0 + celula - 2 * folga):
                    linha[x] = cor
    # a faixa laranja embaixo (o ON)
    y0 = topo + 8 * celula + int(lado * 0.06)
    for y in range(y0, y0 + max(2, int(lado * 0.035))):
        for x in range(margem, lado - margem):
            px[y][x] = ON
    return px


def gerar_web():
    for tam in (192, 512):
        escrever_png(os.path.join(AQUI, "web", f"icon-{tam}.png"), tam, tam, desenhar(tam))


def montar_icns(destino):
    conj = destino + ".iconset"
    shutil.rmtree(conj, ignore_errors=True)
    os.makedirs(conj)
    mestre = os.path.join(conj, "mestre.png")
    escrever_png(mestre, 1024, 1024, desenhar(1024))
    for tam in (16, 32, 128, 256, 512):
        for escala, sufixo in ((1, ""), (2, "@2x")):
            subprocess.run(["sips", "-z", str(tam * escala), str(tam * escala), mestre,
                            "--out", os.path.join(conj, f"icon_{tam}x{tam}{sufixo}.png")],
                           check=True, capture_output=True)
    os.remove(mestre)
    subprocess.run(["iconutil", "-c", "icns", conj, "-o", destino], check=True)
    shutil.rmtree(conj, ignore_errors=True)


if __name__ == "__main__":
    gerar_web()
    print("web/icon-192.png e web/icon-512.png gerados")

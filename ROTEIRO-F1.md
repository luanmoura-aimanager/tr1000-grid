# Fase 1 — o grid na frente da máquina

Roteiro para o Luan. É a primeira vez que os Launchpads editam a TR-1000. Faça um passo, me
diga o que **viu e ouviu**, siga para o próximo.

**O que o grid faz nesta versão:**
- mostra os **10 tracks** (8 por vez, com rolagem) × **16 steps** de **uma variação** do
  pattern que está selecionado no painel
- um toque num pad liga ou desliga o step **direto na máquina**
- a velocity e o layer (A, B ou os dois) escolhidos nos botões da borda
- o playhead anda com o clock da máquina
- a cada ~0,5 s o grid relê a máquina: o que você mudar no painel aparece nele

**O que NÃO faz ainda** (não é defeito, é o limite desta fase):
- não sabe qual variação está **tocando** (o playhead anda sobre a variação mostrada)
- assume scale 16th e 16 steps
- não tem as linhas de ACCENT e TRG
- **não grava**: para guardar, aperte **WRITE no painel**. Religar sem WRITE descarta

**Antes:** TR-1000 App (original e cópia) **fechado**. Os dois Launchpads na USB.

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
```

---

## F1.0 — learn (uma vez)

```bash
python3 lp_tr1000.py learn
```

O mesmo do tr8s-grid: três pads em cada Launchpad, na ordem que ele pede. Depois, cada
aparelho acende azul e você confirma com `s`.

## F1.1 — ligar o grid

No painel: **1-01 Dub Techno**, var **A**, parado. Então:

```bash
python3 lp_tr1000.py run
```

**O que esperar:**
- no terminal, `TR-1000 conectada, versao '1.22'` e `pattern 1-01 (x 0)`
- **no grid:**
  - BD (linha de cima) em **1, 5, 9, 13 vermelhos**
  - SD com vermelho em 4 e 12 e **verde** em 2, 7, 9, 10, 13, 15, 16, como o painel
  - a cada 4 steps, um cinza fraco marcando o tempo
- **na borda:**
  - topo esquerdo: **A** aceso em azul
  - borda direita: a velocity **80** acesa (4ª de cima para baixo)
  - topo direito: as setas e os três botões de layer (`AB`, `A`, `B`)

## F1.2 — um step pelo grid

Num **pad apagado** do BD (o step 2), aperte uma vez.

**O que esperar:**
- o pad acende vermelho
- **no painel**, com BD selecionado, o step 2 acende
- com a máquina tocando (**START**), o bumbo extra soa

Aperte o mesmo pad de novo: apaga no grid e no painel, e o bumbo some.

## F1.3 — velocity

Na borda direita, escolha **66** (5º de cima) e ligue um step vazio do **SD**.

**O que esperar:** no painel, aparece **fraco**. Escolha **127** (o 1º) e ligue outro: forte.

**É a primeira prova da fórmula da velocity** (`0xA·vel·3C`). Se o painel não mostrar fraco
e forte, pare e me conte.

## F1.4 — layer B

**Atenção, há dois "B":** a **variação B** fica no topo do Launchpad **esquerdo**; o **layer
B** é o botão **"Session"** do Launchpad **direito**. A fileira de cima do direito é:

| botão | ação |
|---|---|
| ▲ / ▼ | rolar |
| ◀ | `AB` |
| ▶ | `A` |
| Session | `B` |

Aperte **Session** e ligue um step vazio do **SD** (ou BD, LT, HT).

**O que esperar:** no painel, o step aparece **verde**, e só o layer B soa. Volte para
**`AB`** (o 3º botão).

## F1.5 — o playhead

Aperte **START** no painel.

**O que esperar:**
- uma coluna **branca** anda no grid, no tempo
- **STOP**: ela some

## F1.6 — o grid segue o painel

1. Com o grid ligado, troque para o pattern **1-02** no painel. Em menos de 1 s o grid
   mostra o Groovy Beach (BD em 1, 12, 15).
2. Ligue ou desligue um step **no painel**. Em menos de 1 s o grid acompanha.

## F1.7 — variações e rolagem

- **No topo esquerdo**, os botões **A…H** trocam a variação que o grid mostra. Compare com
  o painel.
- **As setas** (topo direito, 1º e 2º) rolam as linhas: com 10 tracks, a rolagem mostra o
  CC e o RC embaixo.

**Para sair:** Ctrl+C no terminal. Os LEDs apagam.

---

**Resultado em 09/10/2026: todos os passos passaram** (REFERENCIA 7.4). O playhead só
aparece depois de um START com o grid já ligado.

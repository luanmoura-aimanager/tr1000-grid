# C5 — onde moram os parâmetros do step, a performance, o side chain e o routing

Roteiro para o Luan. **Nada aqui escreve na máquina**: a parte 1 só **lê** (fotos), e a
parte 2 é o App escrevendo, como nas capturas dos knobs. O que o painel mudar, você desfaz
no fim com o **Reload**.

**O método** (REFERENCIA 3.2): uma **foto** de tudo que o App lê no boot → **um** gesto no
painel → outra foto → o gesto inverso → mais uma. O diff diz onde o gesto mora. Antes de
tudo, três fotos sem gesto medem o **piso de ruído**, o que muda sozinho, e isso é
descontado.

---

## Parte 1 — a sessão guiada (painel; ~20 min)

**Antes:**
1. **TR-1000 App fechado** (original e cópia) e **grid fechado**: a serial é de um só.
2. No painel:
   - pattern **1-01**, variação **A**, **parado**;
   - aperte **[TR-REC]** (aceso);
   - aperte **[SD]**.

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
python3 sessao_c4.py c5
```

**Como funciona:**
- O programa mostra um gesto por vez. Você faz o gesto no painel e aperta **Enter**.
- Ele tira a foto (~2 s) e **mostra na hora o que mudou**.
- Em seguida, ele pede o gesto **inverso**. Você desfaz e aperta Enter.
- Ele confere se tudo voltou ao que era.
- **[p]** pula um gesto que não deu para fazer. **[q]** encerra e salva o que já foi.

**Os gestos, na ordem** (do manual RM, p. 20–26 e 44). O programa mostra cada um:

| id | o que é | gesto |
|---|---|---|
| velocity | **controle**: já sabemos onde mora | segure STEP 4, gire o C1 |
| start | micro-timing | segure STEP 4, gire o C2 |
| substep | sub step 1/2 | [SUB], STEP 4, [SUB] |
| flam | sub step Flam | segure [SUB], C6 em Flam; [SUB], STEP 4, [SUB] |
| prob | probability 50% | segure STEP 4, gire o C4 |
| cycle | CYCLE 1/3 | segure STEP 4, gire o C5 |
| accent | ACCENT no step 6 | ACCENT [STEP], STEP 6 |
| alt | som ALT no RS | [RS]; segure LAYER [B] + STEP 3 |
| last-var | LAST STEP da var A = 12 | [LAST], [A], STEP 12 |
| last-trk | LAST STEP do SD = 8 | [LAST], [SD], STEP 8 |
| scale | Scale 32nd | [SHIFT]+[PTN SELECT], Scale |
| var-b | selecionar a variação B | [B] |
| chain | chain A+B | [A] e [B] juntos |
| mute | MUTE do SD | [MUTE], [SD] |
| fill | FILL2 no FILL IN | [SHIFT]+[FILL IN TRIG], C1 |
| loop | STEP LOOP ligado (tocando) | [START], [STEP LOOP] |

**O que me mandar:** o resumo vai sozinho para `capturas/<data>-c5.txt`. Mande só
"pronto", mais qualquer gesto em que o visor mostrou algo diferente do esperado.

**O que pode acontecer, e não é erro:** um gesto **não mudar nada** (`0 valores mudaram`).
Isso já é a resposta: aquilo não mora em nenhum bloco que dá para ler. É o que decide se
o mute, o fill e o step loop podem ir para o Launchpad.

---

## Parte 2 — side chain e routing pelo App (espião; ~10 min)

Feche o terminal da parte 1. Duas capturas, como as dos knobs:

```bash
python3 espiao.py rodar sidechain
```
1. Clique em **Side Chain**, no rodapé à direita.
2. Gire cada knob da tela, na ordem da tela: anti-horário → horário → meio, com 2 s
   entre eles.
3. Passe pelos menus e botões e volte.
4. Na tela **KIT**, gire também os três **SC DEPTH**, ponta a ponta: o do REVERB, o do
   DELAY e o do EXTERNAL INPUT.
5. Print da tela Side Chain e de cada menu aberto. **Cmd+Q**, "pronto".

```bash
python3 espiao.py rodar routing
```
1. Na tela **KIT**, na **Routing Matrix**, uma linha de cada vez, da esquerda para a
   direita (**BD, SD … RC, RVB, DLY, EXT**): clique em **THROUGH**, espere 2 s, depois
   **ANALOG FX**, 2 s, e volte para **MASTER FX**.
2. Print da matriz no fim. **Cmd+Q**, "pronto".

---

## No fim — desfazer

**[SHIFT]+[MENU] (RELOAD)** → recarregue o **pattern** e o **kit**. Os dois voltam ao que
estava salvo.

**Não testado:**
- A sessão guiada nunca rodou contra a máquina; os testes são de mesa.
- A primeira foto vai dizer quanto tempo cada uma leva.
- O piso de ruído com a máquina **tocando** (o gesto `loop`) pode ser maior que o medido
  parado. Se o `loop` mostrar muita coisa no bloco 3, eu separo à mão.

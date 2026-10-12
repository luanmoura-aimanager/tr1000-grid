# F4 — a fase 2b na frente da máquina

Roteiro para o Luan. Testa o que a fase 2b mudou na tela depois do F3: o playhead, o STEP
LOOP, o PTN digitado, a foto da sessão e as variações. Faça um passo, me diga o que
**ouviu e viu**, siga para o próximo.

**Antes:**
1. O servidor já se atualiza sozinho depois de cada merge (o hook `post-merge`). Confira
   com `python3 instalar_agente.py --estado`.
2. Feche o TR-1000 App da Roland e aperte **ON** no Controller. No painel: **1-01**, var
   **A**.
3. Recarregue a página do Controller (Cmd+R), para ela pegar os módulos novos.

## F4.1 — O playhead

1. Dê **Play**. **Esperado:** a borda branca da grade anda **um step por vez**, junto com
   o Launchpad, sem pular.
2. **Scale 32nd** (coluna do lado). **Esperado:** a borda anda no dobro, junto com o som.
   Volte para 16th.
3. **LAST = 12**. **Esperado:** a borda volta para o 1 depois do 12, como a máquina. Volte
   para 16.
4. Clique no nome **SD**, marque **próprio**, FIRST 1, LAST 3. **Esperado:** a linha do SD
   tem a borda própria, dando a volta a cada 3 steps. Desmarque.

## F4.2 — STEP LOOP

1. Com o botão STEP LOOP **apagado**, segure o **5** na fila da coluna do lado.
   **Esperado:** repete o step 5 (antes, ficava em silêncio). Solte: volta ao normal.

## F4.3 — Variações

1. **toca B** (clique simples). **Esperado:** a máquina toca só a B; o TOCA mostra `B`.
2. **Shift-clique em A**. **Esperado:** A+B, alternando.
3. **edita C**. **Esperado:** a grade mostra a C, e o som continua A+B.
4. Volte para **edita A** e **toca A**.

## F4.4 — PTN digitado (Program Change)

1. Parada. Clique no **PTN** do topo, digite `1-02` e Enter. **Esperado:** o painel vai
   para 1-02 e a tela segue. **Isto é palpite:** pode não mudar nada (canal, Rx Program
   Change), ou mudar para outro número. Me diga qual pattern apareceu.
2. Tocando, digite `1-01`. **Esperado:** a troca no fim do pattern (como o painel faz).
3. **Se não mudar:** no painel, MENU > SYSTEM > MIDI, veja o **Pattern Ch.** e o **Rx
   Program Change**, e me diga os valores.

## F4.5 — Salvar sessão

1. Clique em **salvar sessão**. **Esperado:** o rodapé diz `sessao salva no app:
   ...json (botao)`. A TR-1000 não muda nada.
2. No Finder, Ir > Ir para a pasta (Cmd+Shift+G): `~/Library/Application Support/tr1000-sessoes`.
   **Esperado:** um arquivo do ON e um do botão.

## F4.6 — PT | EN

1. **EN** no topo. **Esperado:** a página recarrega em inglês; os nomes da máquina (BD,
   PROB, SUB...) ficam iguais. Volte para **PT**.

## F4.6b — Standby

1. Aperte **chuva**. **Esperado:** os Launchpads ganham ondas coloridas nascendo sozinhas,
   e o rodapé diz que a serial está livre. Toque um pad: sai mais uma onda dali.
2. Com a chuva rodando, abra o **App da Roland**. **Esperado:** ele conecta, e as ondas
   continuam. Feche o App.
3. **ambiente**. **Esperado:** ondas maiores, mais lentas e mais fracas.
4. **ON**. **Esperado:** volta o grid, o PTN e os LEDs. **OFF** apaga tudo.

## F4.6c — As páginas do Launchpad

Com **ON**, nos botões do topo do Launchpad direito:
1. **PAR** (o 6º botão). A coluna lateral esquerda escolhe o track (escolha o SD); a borda
   direita, o parâmetro (o 1º = PROB). Toque a **linha de cima** no step 4 do SD: PROB
   100 %. Toque a **4ª linha de baixo**: uns 43 %. **Esperado:** a barra muda e o painel,
   segurando o step, mostra o valor.
2. Na PAR, o **5º da borda (VEL)**: a linha de cima num step aceso → velocity 127 (a cor
   fica forte no grid).
3. **PERF** (o 7º). Linha 1: toque o **HT** (mute). Linha 2: toque **B** (só a B); segure
   **A** e toque **B** (A+B). Linha 3: **segure** o 5 (loop) e solte. Linha 4: toque o 12
   (LAST = 12). Linha 5: o 4º (32nd), depois o 3º (16th).
4. **ROUT** (o 8º). Linha 3, coluna 2: o SD vai para ANALOG FX. Linhas 5–6: SC SOURCE.
   Linha 8: DUCK/GATE e TIME/STEP. **Esperado:** a aba Efeitos mostra o mesmo.
5. O mesmo botão volta para os steps.

## F4.6d — O gráfico e os presets do SIDE CHAIN

1. Aba **Efeitos**, SIDE CHAIN, com a máquina tocando. Arraste o **ponto de baixo** para
   baixo (MSTR DEP maior) e para a direita (HOLD maior). **Esperado:** o bombeado fica mais
   fundo e mais longo, e os sliders seguem.
2. O **ponto de cima** para a direita: a volta fica mais lenta. O **do meio**: muda o
   formato da volta.
3. **PRESET:** passe pelos 9 e diga, para cada um, se soa como o nome promete e o que
   mudar (ex.: "Pump clássico: release mais curto").

## F4.6e — A variação que toca

1. Chain **A+B** (toca A, Shift-clique em B), com A e B **diferentes** (um BD a mais na B
   basta). Play. **Esperado:** o TOCA alterna A → B → A no compasso certo; no Launchpad o
   botão da que toca fica **branco**, o da editada **azul**. Diga se a troca chega atrasada
   (quantos steps).
2. A e B iguais: **Esperado:** `?` (não dá para saber de ouvido) em vez de um chute.
3. Com a máquina **tocando**, aperte **OFF** e depois **ON** no Controller. **Esperado:**
   em até ~1 compasso o rodapé diz "fase achada" e o playhead aparece no step certo, sem
   STOP/START. Com um pattern muito repetitivo (só BD nos tempos), o playhead pode não
   aparecer; isso é esperado.

## F4.7 — c5d: o TEMPO (para o BPM digitável)

Com **OFF** no Controller (a serial livre):

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
python3 sessao_c4.py c5d
```

Siga os gestos do terminal: o TEMPO um clique por vez (digite o BPM do visor), o ajuste
fino e a troca de pattern pelo painel. **Só lê.** Me cole a saída inteira.

**Não testado até este roteiro:** tudo acima. Os testes de mesa (185) só dizem que nada
quebrou o que já estava provado.

## F4.8 — BPM digitado (depois da c5d)

Com **ON**, clique no **BPM** do topo, digite `124.5` e Enter. **Esperado:** o painel mostra
124.5, o som acelera ou desacelera, e o BPM do Controller segue. Volte para `128`.

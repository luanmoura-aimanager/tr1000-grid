# F4 — a fase 2b na frente da máquina

Roteiro para o Luan. Testa o que a fase 2b mudou na tela depois do F3: o playhead, o STEP
LOOP, o PTN digitado, a foto da sessão e as variações. Faça um passo, me diga o que
**ouviu e viu**, siga para o próximo.

**Antes:**
1. Reinstale o servidor e o app com o código novo:
   ```bash
   cd ~/Documents/Claude/Projects/tr1000-grid
   python3 instalar_agente.py
   python3 criar_app.py
   ```
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

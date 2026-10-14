# F5 — a aba Ritmos na frente da máquina

Roteiro para o Luan. Testa a fase 2l: a aba **Ritmos** (escrever um ritmo pronto com
variações, o Desfazer, o Mix dub) e o **Kit por Program Change**, que nunca foi medido.
Faça um passo, me diga o que **ouviu e viu**, e siga para o próximo.

**Nada aqui grava na memória:** o WRITE do painel continua com você. Religar a máquina
descarta tudo.

**Antes:**
1. Confira com `python3 instalar_agente.py --estado` que o servidor já se atualizou.
2. Feche o TR-1000 App da Roland e aperte **ON** no Controller. No painel, escolha um
   pattern que **pode ser sobrescrito** (um vazio é o ideal). Var **A**.
3. Recarregue a página do Controller (Cmd+R) e abra a aba **Ritmos**.

## F5.1 — O Kit por Program Change (o palpite que falta medir)

1. No painel: MENU > SYSTEM > MIDI. Anote o **Kit Ch.**, o **Rx Program Change** (deixe
   em ON, como no F4.4) e o **Kit Select** (Kit ou Pattern).
2. Na aba Ritmos, escolha **One drop (reto)** e clique em **kit → TR-808-1000**.
   **Esperado:** o painel carrega o kit **41 TR-808-1000**. **Isto é palpite:** pode
   não mudar nada (o canal), ou carregar o 40 ou o 42 (o número), ou mudar também o
   pattern (o Kit Select). Me diga **qual kit apareceu**.
3. Veja o rodapé do Controller. Se aparecer `kit incerto, knobs de kit parados`, o PC
   mudou **um só** dos três números do bloco 3. Isso resolve a dedução de qual deles é o
   kit. Os knobs de kit ficam parados até o pattern voltar ao kit dele. Me diga se a frase
   apareceu.
4. Volte ao kit de antes pelo painel.

## F5.2 — Escrever um ritmo (o One drop do Carlton Barrett)

1. Escolha **One drop (Carlton Barrett, tercina)**. **Auto BPM** ligado, **Auto kit**
   desligado.
2. Clique em **Escrever** e, em até 2 s, em **Confirmar?**. Cronometre de cabeça.
   **Esperado:**
   - o quadro "escrita" passa por: tirando a foto da sessão → lendo o pattern →
     escrevendo (n/total) → pronto;
   - o rodapé diz `sessao salva no app: ...-ritmo.json` e depois `ritmo ... escrito`.

   Me diga **quanto tempo levou**.
3. No painel: **Scale 16th(T)**, **LAST 12**, BPM 72, chain **A+B**.
4. Dê **Play**. **Esperado:** o bumbo e o rim **juntos** uma vez a cada meio compasso
   (o "drop"), e o chimbal com **swing de tercina**. **Me diga se soa como reggae** ou
   se o swing ficou estranho.
5. No grid da tela e no Launchpad, **edita B** e **edita Fill 1**. **Esperado:** as
   variações que o preview da aba mostrava.

## F5.3 — Desfazer

1. Clique em **Desfazer**. **Esperado:** "desfazendo… → desfeito"; o pattern volta ao
   que era (os steps, a Scale, o LAST, a chain e o BPM).
2. Me diga se **algo não voltou**. Se o quadro mostrar "valor(es) antigo(s) fora do
   portao nao voltaram", copie a linha para mim.

## F5.4 — Mix dub

1. Escolha **Dub roots (Tubby / Scientist)**. Deixe ligados **Mix dub** e **Auto BPM**,
   e escreva.
2. Play. **Esperado:** o **rim e a caixa com eco** (delay), o chimbal aberto com um pouco
   de eco, e o bumbo **seco**. **Não testado:** o send do RS e do OH é dedução (só o do SD
   foi ouvido no F2.2). Me diga quais ecoam.
3. **Desfazer.** **Esperado:** os sends voltam ao que eram (o eco some).

## F5.5 — O aviso do DIRECTION

1. No painel, ponha o **SD em R-L** (TRACK SETTING).
2. Escreva **Rockers (Channel One)**. **Esperado:** o quadro avisa `SD em R-L na A: toca
   diferente`. Desfaça e volte o SD para FWD.

## F5.6 — De ouvido

Escreva, ouça e desfaça cada um. Me diga se **algum soa errado para o estilo**:

1. **Steppers (Sly Dunbar)**: o bumbo em toda colcheia, a caixa no 2 e no 4.
2. **Ska (Lloyd Knibb)**: 120 BPM, o bumbo e o rim no 2 e no 4, o chimbal aberto.
3. **Funk (Cold Sweat)**: A e B são os dois compassos da figura.
4. **Jungle (amen)**: A, B e C são as barras do break.
5. **Bossa nova**: a clave no rim.

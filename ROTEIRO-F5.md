# F5 — a aba Ritmos na frente da máquina

Roteiro para o Luan. Testa a aba **Ritmos** revista em 15/10/2026 (REFERENCIA 7.10): o menu
de kits, o **▶ Play** e o **Restaurar**, e a correção do bloco 3 (o `[2]` é o kit, o `[3]` o
pattern). Faça um passo, me diga o que **ouviu e viu**, e siga para o próximo.

**Nada aqui grava na memória:** o WRITE do painel continua com você. Religar a máquina
descarta tudo.

**Antes:**
1. Confira com `python3 instalar_agente.py --estado` que o servidor já se atualizou.
2. Feche o TR-1000 App da Roland e aperte **ON** no Controller. No painel, deixe o
   **1-01**, tocando, num pattern que **pode ser sobrescrito na memória**.
3. Recarregue a página do Controller (Cmd+R) e abra a aba **Ritmos**.
4. Confira no painel (MENU > SYSTEM > MIDI) que o **Rx Program Change** está em ON, como
   no F4.4.

## F5.1 — O Play (o pattern, o BPM e o kit juntos)

1. Escolha **Steppers (Sly Dunbar)**. O menu mostra o kit sugerido, marcado como
   "(sugerido)". Deixe-o.
2. Clique em **▶ Play**. Cronometre de cabeça. **Esperado:**
   - o quadro "escrita" passa por: tirando a foto da sessão → trocando o kit → lendo o
     pattern → escrevendo (n/total) → pronto, **sem** "o pattern mudou no meio";
   - o **visor continua no 1-01**;
   - o **kit muda** para o do menu;
   - o ritmo entra (o bumbo em toda colcheia, a caixa no 2 e no 4);
   - o **BPM** vai para o do ritmo, no visor e no som;
   - o rodapé diz `kit N (bloco 3 [2..4] = [...])` e **não** diz `pattern 3-xx`.

   Me diga **quanto tempo levou** e se **algum item falhou**.
3. Gire um knob de kit na controladora, por exemplo o **LEVEL** ou o **PAN** do BD.
   **Esperado:** o som muda. Isso confirma que os knobs seguem o kit novo (o `[2]`).

## F5.2 — Restaurar

1. Clique em **Restaurar**. **Esperado:** "desfazendo… → desfeito", e voltam os steps, a
   Scale, o LAST, a chain, o **BPM** e o **kit** de antes.
2. Me diga se **algo não voltou**. Se o quadro mostrar "valor(es) antigo(s) fora do
   portao nao voltaram", copie a linha para mim.

## F5.3 — Outro kit pelo menu

1. Escolha **One drop (reto)**. No menu, troque o kit por um que você conhece, por exemplo
   o **TR-808-1000**.
2. **▶ Play.** **Esperado:** o kit que você escolheu, e não o sugerido. Me diga **qual
   kit o visor mostrou**. Se aparecer um vizinho (o 40 ou o 42), o número do PC está
   deslocado.
3. **Restaurar.**

## F5.4 — O pattern em `[3]` (a dedução que falta)

1. No painel, troque para o **1-03** (nele, o `[4]` do bloco 3 vem diferente).
   **Esperado:** o Controller vai para **1-03**, e a grade da tela bate com a do painel.
2. Volte ao 1-01.
3. Repita o **BPM digitado** do F4.8: `124.5` no topo, e depois de volta a `128`.
   **Esperado:** o painel e o som acompanham.

## F5.5 — Mix dub

1. Escolha **Dub roots (Tubby / Scientist)** e dê **▶ Play**. O mix dub vai junto, sempre.
2. **Esperado:** o **rim e a caixa com eco** (delay), o chimbal aberto com um pouco de eco,
   e o bumbo **seco**. **Não testado:** o send do RS e do OH é dedução (só o do SD foi ouvido
   no F2.2). Me diga quais ecoam.
3. **Restaurar.** **Esperado:** os sends voltam ao que eram (o eco some).

## F5.6 — O aviso do DIRECTION

1. No painel, ponha o **SD em R-L** (TRACK SETTING).
2. Dê Play no **Rockers (Channel One)**. **Esperado:** o quadro avisa `SD em R-L na A: toca
   diferente`. Restaure e volte o SD para FWD.

## F5.7 — De ouvido

Dê Play, ouça e restaure cada um. Me diga se **algum soa errado para o estilo**, ou se o
**kit sugerido** não combina (os kits foram escolhidos pelo nome, sem ouvir):

1. **One drop (Carlton Barrett, tercina)**: o bumbo e o rim juntos uma vez a cada meio
   compasso, o chimbal com swing de tercina (Scale 16th(T), LAST 12).
2. **Ska (Lloyd Knibb)**: 120 BPM, o bumbo e o rim no 2 e no 4, o chimbal aberto.
3. **Funk (Cold Sweat)**: A e B são os dois compassos da figura.
4. **Jungle (amen)**: A, B e C são as barras do break.
5. **Bossa nova**: a clave no rim.
6. **Dub techno**, **Two-step DnB** e **Trance (uplifting)**: os kits novos (Dub Techno
   Kit, Glitchy DnB Kit, Trance Kit).

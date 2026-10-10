# Fase 1b — as controladoras na frente da máquina

Roteiro para o Luan. É a **primeira vez** que um knob escreve na TR-1000; até aqui, todo
endereço veio do App escrevendo (REFERENCIA 7.5). Faça um passo, me diga o que **ouviu e
viu**, siga para o próximo.

**Como os knobs se comportam:**
- **pegar no caminho:** um knob só age depois de **passar pelo valor que a máquina tem**.
  Antes disso, girar não faz nada. É de propósito: sem pulo no som;
- trocou de pattern ou de kit: todos os knobs voltam a "pegar no caminho";
- os knobs que dependem do TYPE (DELAY 2–6, MFX 1–7) seguem o type **da máquina**. Num
  type sem aquele parâmetro, o knob fica parado;
- **não grava**: para guardar, WRITE no painel. Religar descarta.

**Antes:**
1. No **TR-1000 App normal**: ☰ → **Reload Kit**, se ainda não fez.
2. Ainda no App, no **MASTER FX**, aperte o **OFF** para ele ficar **ON**. Os knobs de
   MFX não escrevem esse botão, e com ele em OFF não se ouve nada.
3. **Feche o App** (Cmd+Q).
4. Os dois Launchpads e as duas controladoras na USB. No painel: **1-01**, parado.

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
python3 lp_tr1000.py run
```

**O que esperar no terminal:** além do `TR-1000 conectada` e do `pattern 1-01`, uma linha
`controladoras: MC-24, CM-MC50`. Se aparecer `(controladora ... nao achada)`, pare e me
conte.

Aperte **START** e deixe tocando durante todo o roteiro.

---

## F2.1 — GAIN do BD (o primeiro, e o pickup)

No CM-MC50, o knob **BD GAIN**:
1. Gire devagar até o fim **anti-horário**.
2. Depois, devagar, até o fim **horário**.
3. Volte para mais ou menos o meio.

**O que esperar:**
- no começo do giro, **talvez nada mude**: o knob ainda não passou pelo valor da máquina;
- **depois que passa**, o bumbo acompanha: no fim anti-horário **some** (−INF); no
  horário fica **mais alto** que o normal (+6 dB);
- **nenhum estalo** ou pulo de volume no momento em que ele "pega".

Me diga **em que ponto do giro** ele começou a agir.

## F2.2 — PAN, RVB SND, DLY SND

Um de cada vez, ponta a ponta e de volta ao meio:

| knob | o que ouvir |
|---|---|
| **SD PAN** | a caixa vai para a esquerda e para a direita |
| **SD RVB SND** | a caixa ganha reverb (no fim horário, bem molhada) |
| **SD DLY SND** | a caixa ganha eco |

## F2.3 — LFO DTH

**BD LFO DTH**: anti-horário, horário, meio.

**O que esperar:** depende do que o LFO do instrumento modula neste kit. Pode ser que
**não se ouça nada**, e isso não é defeito. O meio é zero, e as pontas são −/+ máximo.

Me diga se ouviu alguma oscilação. Ela se confere no App no F2.8.

## F2.4 — REVERB (MC-24)

1. **TIME** ponta a ponta: a cauda do reverb da caixa (o RVB SND do F2.2 ainda alto)
   fica curta e longa.
2. **TYPE** devagar, ponta a ponta. São 6 types (AMBI ROOM, HALL1, HALL2, PLATE, MOD), e
   cada um soa diferente.
3. **PREDELAY, LOWCUT, HIGHCUT, DENSITY:** mais sutis. Diga se ouviu algo.

## F2.5 — DELAY (MC-24)

1. **DELAY 1** (LEVEL) ponta a ponta: o eco da caixa some e volta.
2. **DELAY TYPE** devagar. São 4 types: DELAY, PAN, ECHO e PITCH.
3. Em **cada type**, gire **DELAY 2** e **DELAY 3**. No DELAY, PAN e PITCH são SYNC TIME
   e FEEDBACK; no ECHO, SYNC TIME e INTENSITY. O tempo do eco e a repetição devem mudar.
4. **RVB SEND:** o eco vai para o reverb.

Me diga se, ao trocar o TYPE, os DELAY 2–6 **passaram a mexer no type novo**.

## F2.6 — LFO do kit (MC-24)

**RATE** e **WAVEFORM**: o LFO do kit só se ouve se ele modula algo neste kit (RVB, DLY,
MFX…). Se não ouvir nada, tudo bem; confere-se no App (F2.8).

## F2.7 — MASTER FX (MC-24)

O **MASTER FX** precisa estar **ON** (o passo 2 do "Antes").

1. **MASTER FX TYPE** devagar: 19 posições, de BYPASS a DJFX DELAY. Pare no
   **FILTER+DRIVE** (o 3º).
2. **MFX 1** (CUTOFF) ponta a ponta: o filtro abre e fecha no som inteiro.
3. **MFX 3** (DRIVE): distorce.
4. Gire o TYPE para o **CRUSHER** (o 2º). **MFX 2** (SAMPLE) deve reduzir a taxa de
   amostragem; **MFX 4–7 não fazem nada**, porque o CRUSHER só tem 3 parâmetros.

## F2.8 — conferir no App

1. **Ctrl+C** no grid.
2. Abra o **TR-1000 App normal**. Não aperte Reload.
3. Confira se o que você deixou com os knobs aparece lá:
   - o BD GAIN e o SD PAN na tela INST › MIXER;
   - o TYPE e o TIME do REVERB, o TYPE do DELAY e o efeito do MASTER FX na tela KIT.
4. Me mande um print da tela **KIT**.
5. Para desfazer tudo: ☰ → **Reload Kit**. Feche o App.

## F2.9 — pickup depois de trocar de pattern

1. `python3 lp_tr1000.py run` de novo. No painel, 1-01, tocando.
2. Deixe o **SD PAN** do CM-MC50 todo à **esquerda**.
3. Troque para o pattern **1-02** no painel e espere 1 s.
4. Gire o **SD PAN** devagar para a direita.

**O que esperar:** nada muda até o knob passar pelo PAN que o 1-02 tem (provavelmente o
centro); daí em diante, a caixa acompanha, **sem pular** para a esquerda na hora da troca.

**Para sair:** Ctrl+C. Para descartar o que os knobs mudaram: religue a máquina sem WRITE,
ou use o Reload Kit no App.

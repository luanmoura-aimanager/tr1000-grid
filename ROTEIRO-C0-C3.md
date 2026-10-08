# Fase 0 — as sessões de hardware C0 a C3

Roteiro para o Luan, na frente da TR-1000. **Nada aqui escreve na máquina** até a C3, e a C3
só é escrita depois que a C1 e a C2 voltarem. O porquê de cada passo está na REFERENCIA 7.

Eu leio os arquivos que você gravar em `capturas/`. Faça um passo, me diga **o que viu e
ouviu** (o visor e os LEDs também contam), e vá para o próximo. Se algo sair diferente do
"o que esperar", pare e me conte: costuma ser o achado.

Antes de tudo, no terminal:

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
```

Troque `DD` pela data do dia nos nomes de arquivo.

---

## C0 — escuta passiva (~10 min)

**Feche o TR-1000 App** (Cmd+Q, não só a janela).

### C0.0 — anotar a configuração MIDI

Na TR-1000: **MENU > SYSTEM > MIDI**. Me mande o valor de cada um:
`Pattern Ch.`, `Kit Ch.`, `Tx Edit Data`, `Rx Edit Data`, `Tx Program Change`,
`TX Note`, `USB MIDI Through`, `MIDI Mode`. E no projeto: `Tempo Sync`.

**Não mude nada ainda.** Se `Tx Edit Data` ou `TX Note` estiverem OFF, me diga antes do C0.3.

### C0.1 — a máquina PARADA manda clock?

Confira no visor que ela está **parada**. Então:

```bash
python3 lp_tr1000.py escutar --segundos 15 --arquivo capturas/2026-10-DD-c0-parada.txt
```

Não toque em nada durante os 15 s.

**O que esperar:** a linha `autoteste:` e, no fim, um `── resumo ──`. A pergunta é a linha
`clock por segundo`: se vier com números (~51), **ela manda clock parada**, como a TR-8S
fazia. Se vier vazia ou com zeros, não manda. Me mande o resumo.

### C0.2 — start e stop

```bash
python3 lp_tr1000.py escutar --segundos 25 --arquivo capturas/2026-10-DD-c0-start-stop.txt
```

Conte uns 5 s, aperte **START**, deixe tocar ~10 s, aperte **STOP**, espere o comando acabar.

**O que esperar:** uma linha `start` e uma `stop` com horário. Se o clock por segundo
**muda** entre parada e tocando (aparece, some, ou muda de valor), isso também é achado.

### C0.3 — o painel transmite?

```bash
python3 lp_tr1000.py escutar --segundos 60 --arquivo capturas/2026-10-DD-c0-painel.txt
```

Com a máquina **parada**, faça na ordem, com ~3 s entre cada gesto:

1. Gire o **BD TUNE** de ponta a ponta e volte
2. Suba e desça o **fader BD**
3. Em INST PLAY, bata no pad do **BD** duas vezes
4. Troque de **pattern** (1-01 → 1-02) e volte
5. Troque de **variação** (A → B) e volte
6. **MUTE + BD** liga, e de novo desliga
7. **MFX ON** liga e desliga

**O que esperar** (pelo manual, não medido): o knob como CC 22 (`<- BD TUNE`), o fader como
CC 28, o pad como nota 36, o pattern como program change. Mute e variação **não têm** mensagem
na chart — se aparecer alguma coisa neles, é ouro. Me diga a ordem exata em que você fez,
se fugiu da lista.

### C0.4 — a CTRL fala sozinha com a máquina tocando?

Aperte **START**. Então:

```bash
python3 lp_tr1000.py sniff --arquivo capturas/2026-10-DD-c0-ctrl-tocando.txt
```

Deixe ~15 s, troque de variação uma vez no painel, espere mais ~5 s, **Ctrl+C**. Pare a máquina.

**O que esperar:** o autoteste vai dizer que a CTRL **não** respondeu ao Identity Request —
isso já sabemos (REFERENCIA 2.1), então silêncio aqui é ambíguo. Se aparecer **qualquer**
linha `SysEx Roland`, ela traz o model ID de presente: me mande na hora.

---

## C1 — espiar a serial do App (~30 min)

> **Mudou em 08/10/2026.** O App não fala MIDI com a máquina: fala por uma serial USB, e o
> MIDI Monitor não vê nada (REFERENCIA 2.1b). A versão com MIDI Monitor deste roteiro
> morreu. A captura de prova está em `capturas/2026-10-08-boot-app-serial-vazio.mmon`.

O que se usa agora é o **espião**: uma cópia do App (a original fica intocada) com uma
biblioteca que grava cada byte da serial. **Use sempre `python3 espiao.py rodar <nome>`**
— ele abre a cópia; você faz o gesto; **fecha a cópia com Cmd+Q**, e a captura fica em
`capturas/AAAA-MM-DD-<nome>.serlog`.

**Proibido nestas sessões**: WRITE (KIT), OVERWRITE (PTN/KIT), Write Inst, Transfer
Backup **To TR-1000**, Transfer Project, Import Sample. E se a cópia oferecer atualização
de firmware, **ignore**.

### C1.0 — preparar a cópia (uma vez)

**Feche o TR-1000 App** (Cmd+Q). No terminal, na pasta do projeto:

```bash
python3 espiao.py preparar
```

**O que esperar:** cinco comandos (`ditto`, `rm`, `xattr`, `codesign`, `clang`), depois:
- `copia:` com uma linha `flags=` **sem** a palavra `runtime`
- `original: assinatura VALIDA (intocado)`

Se aparecer `(!) a copia AINDA tem hardened runtime`, pare e me mande a saída.

### C1-S0 — o autoteste

TR-1000 ligada, na USB, **parada**. App original **fechado**.

```bash
python3 espiao.py rodar s0-autoteste
```

Abre uma janela do App igual à de sempre. Espere **"Connected"** e o kit aparecer. **Cmd+Q**.

**O que esperar** no terminal: `autoteste: espiao carregou = sim, abriu a serial = sim`.
Se qualquer um for `NAO`, pare e me mande a saída — captura sem autoteste não prova nada.
Um caso especial: `carregou = sim` e `abriu a serial = NAO` com o App mostrando
"Connected" quer dizer que o App passou a falar **MIDI** (o `ctrlPort` está em 1 desde
14:36 de 08/10, REFERENCIA 2.1b). Seria boa notícia — aí voltamos ao MIDI Monitor.
Se o macOS disser que o App "está danificado" ou não pode ser aberto, me avise antes de
mexer em qualquer configuração de segurança.

### C1-S1 — `boot-app` ← a mais importante

Mesmo do S0, com a máquina **parada**, e mais **10 s** parado depois do "Connected":

```bash
python3 espiao.py rodar boot-app
```

Me avise. Eu rodo o `estatisticas` e o `resumo` e respondo **antes** de você seguir — o boot
decide o resto do roteiro (se a serial é SysEx Roland, a hipótese H1, ou outra coisa).

### C1-S2 — `boot-tocando`

Aperte **START** na máquina. Então `python3 espiao.py rodar boot-tocando`, espere conectar,
mais 10 s, **Cmd+Q**. Pare a máquina.

### C1-S3 — `knob-bd-tune`

`python3 espiao.py rodar knob-bd-tune`. Depois de conectar, espere 5 s; na tela **INST**,
Bass Drum, gire o **TUNE** do GENERATOR de ponta a ponta e volte. Espere 5 s. **Cmd+Q**.

### C1-S4 — `mixer-mute-bd`

`python3 espiao.py rodar mixer-mute-bd`. No **MIXER** da cópia, **mute do BD** liga, 2 s,
desliga. **Cmd+Q**.

### C1-S5 — `painel-ptn` e `painel-var`

`python3 espiao.py rodar painel-ptn`: com a cópia conectada, **no painel da máquina** troque
de pattern 1-01 → 1-02 → 1-01. **Cmd+Q**. Depois `rodar painel-var`: variação A → B → A.

**O que esperar:** se a tela do App acompanhar sozinha, a máquina avisa de algum jeito — e a
captura mostra como.

### C1-S6 — `backup-to-pc` (só leitura, demorada)

1. **Na máquina**, crie um backup em **INTERNAL** (Reference Manual p.51): **[MENU]** →
   C6 em **FILE** → [ENTER] → C6 em **BACKUP** → [ENTER] → destino **INTERNAL** → um nome
   (ex.: `C1S6`) → [ENTER]. Não desligue enquanto aparecer "Executing". O backup **não**
   inclui pattern/kit com asterisco (editado e não salvo). A transferência do App leva
   arquivos de backup que já estão na máquina (manual do App p.19).
2. `python3 espiao.py rodar backup-to-pc`. No ☰ da cópia: **Transfer Backup → To PC**,
   escolha uma pasta do Mac. Espere terminar. **Cmd+Q**.
3. Me diga quanto tempo levou e o tamanho do arquivo de backup.

**Nunca "To TR-1000"**: isso grava por cima da memória da máquina.

## C2 — decodificar o pattern (roteiro a escrever depois da C1)

Leituras apenas, e **só nos endereços que o App leu na C1.1** (a lista branca). O `snap` e o
`snapdiff` do tr8s-grid serão portados com essa trava. Gestos previstos, um por vez e com o
inverso logo em seguida (Método, regra 3): um step do BD liga/desliga; weak beat; PROB;
cada SUBSTEP; CYCLE; **LAYER A/B**; **ALT** do RS; ACCENT; TRG; LAST STEP da variação e do
track; habilitar variações; trocar pattern (para o endereçamento pattern × variação); Fill
1–4. E, tocando: `cur_step*`, `cur_vari*`, `seq_run`.

## C3 — a primeira escrita nossa (o portão, REFERENCIA 3.1)

**Antes:** TR-1000 App — o original **e** a cópia do espião — **fechados** (Cmd+Q). Máquina
no pattern **Dub Techno**, var **A**, BD com o step 2 aceso (como ficou do `step-bd2`).
Rode tudo no **seu Terminal**, na pasta do projeto:

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages
```

Cada escrita mostra os bytes e pede **`sim`**. Qualquer outra resposta não manda nada.
Nada aqui é WRITE: fica no buffer de edição, e religar a máquina descarta.

### C3.0 — só leitura

```bash
python3 sessao_c3.py ler
```

**O que esperar:**
- `aperto de mao: versao '1.22'`
- `BD var A step 2, slots A/B: A503C A503C`
- `TUNE do BD: 1000`

**Se qualquer um vier diferente, ou der `(!)`, pare** e me mande a saída.

### C3.1 — desligar o step 2 (ouvindo)

1. Aperte **START**. Com o BD selecionado, você ouve o bumbo extra no step 2.
2. `python3 sessao_c3.py step2 desligar` → confira que são **dois** pacotes →
   digite `sim`.

**O que esperar:**
- `ok (03)` duas vezes e `depois: FF FF`
- **o bumbo do step 2 some**, sem parar a máquina
- o LED do step 2 apaga

Me diga o que **ouviu e viu**.

### C3.2 — ligar de novo

`python3 sessao_c3.py step2 ligar` → `sim`.
- **O que esperar:** `depois: A503C A503C` e **o bumbo do step 2 volta**.

### C3.3 — o TUNE de volta ao original

`python3 sessao_c3.py tune 509` → `sim`.

**O que esperar:**
- `depois: 509`
- tocando o BD, a afinação **cai** em relação ao máximo de agora

Depois: **STOP**. Não aperte WRITE.

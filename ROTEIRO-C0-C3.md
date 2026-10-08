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

## C1 — sniff do App com o MIDI Monitor (~30 min)

O rtmidi não enxerga o que **outro** programa manda; o MIDI Monitor enxerga.

### C1.0 — preparar o MIDI Monitor

1. Abra o **MIDI Monitor**. Em **Sources**, marque:
   - em *Spy on output to destinations*: **TR-1000 CTRL** (e também **TR-1000**)
   - em *MIDI sources*: **TR-1000 CTRL** (e também **TR-1000**)
   Se o macOS pedir permissão para o driver de spy, aceite. Sem ele, só metade do diálogo aparece
2. Em **Filter**, deixe passar *System Exclusive*; **desmarque Clock** (senão o clock afoga tudo)
3. Aumente o *Remember* para o máximo (o boot do App deve gerar milhares de mensagens)

Cada captura: **Clear** antes, faça o gesto, **File > Save As** em `capturas/` com o nome
indicado (`.mmon`). Me avise a cada uma; eu rodo o `tr1000_sysex.py resumo` e respondo antes
de você seguir para a próxima, porque o boot pode mudar o resto do roteiro.

### C1.1 — `2026-10-DD-boot-app.mmon` ← a mais importante

TR-1000 **parada**, App **fechado**. **Clear** no MIDI Monitor. Abra o **TR-1000 App** e espere ele
terminar de carregar (a tela mostrando o kit), mais **10 s** sem tocar em nada. Salve.

**O que esperar:** centenas ou milhares de linhas SysEx. Não precisa olhar — me avise.

### C1.2 — `2026-10-DD-boot-app-tocando.mmon`

Feche o App. Aperte **START** na máquina. **Clear**. Abra o App, espere carregar, mais 10 s. Salve.
Pare a máquina.

### C1.3 — `mixer-level-bd` e `mixer-mute-bd`

Com o App aberto, **Clear** depois que ele terminou de carregar. No **MIXER** do App:
- suba o nível do **BD** do mínimo ao máximo devagar, uma vez. Salve como `2026-10-DD-mixer-level-bd.mmon`
- **Clear**. Clique no **mute do BD**, espere 2 s, clique de novo. Salve como `2026-10-DD-mixer-mute-bd.mmon`

### C1.4 — `2026-10-DD-kit-bd-tune.mmon`

**Clear**. Na tela **INST** do App, BD, gire o **TUNE** de ponta a ponta e volte. Salve.

### C1.5 — `painel-ptn` e `painel-var`

App aberto. **Clear**. **No painel da máquina**, troque de pattern 1-01 → 1-02 → 1-01. Salve como
`2026-10-DD-painel-ptn.mmon`. **Clear**. Troque de variação A → B → A. Salve como
`2026-10-DD-painel-var.mmon`.

**O que esperar:** se o App atualizar a tela sozinho, a máquina avisa de alguma forma — e
a captura mostra como.

### C1.6 — `2026-10-DD-backup.mmon` (só leitura, mas demorada)

**Clear**. No App, **Export Backup** para uma pasta qualquer do Mac. Espere terminar. Salve a
captura e me diga **quanto tempo levou** e **o tamanho do arquivo** de backup gerado.

**O que esperar:** é aqui que o pattern inteiro deve passar, se o boot não o leu.

> **Não faça** WRITE KIT nem OVERWRITE nesta sessão. Eles gravam na memória da máquina; entram
> numa sessão própria, com um kit e um pattern descartáveis, depois que o boot mostrar o
> formato.

---

## C2 — decodificar o pattern (roteiro a escrever depois da C1)

Leituras apenas, e **só nos endereços que o App leu na C1.1** (a lista branca). O `snap` e o
`snapdiff` do tr8s-grid serão portados com essa trava. Gestos previstos, um por vez e com o
inverso logo em seguida (Método, regra 3): um step do BD liga/desliga; weak beat; PROB;
cada SUBSTEP; CYCLE; **LAYER A/B**; **ALT** do RS; ACCENT; TRG; LAST STEP da variação e do
track; habilitar variações; trocar pattern (para o endereçamento pattern × variação); Fill
1–4. E, tocando: `cur_step*`, `cur_vari*`, `seq_run`.

## C3 — primeiras escritas (o portão, REFERENCIA 3.1)

Um DT1 por vez, num pattern descartável, e **você ouvindo** — reler o que foi escrito prova que a
máquina aceitou, não que obedeceu (Método, regra 9). Ordem: um step on/off → velocity → mute →
variações habilitadas → WRITE, e então **desligar e religar** a máquina para ver se sobreviveu.

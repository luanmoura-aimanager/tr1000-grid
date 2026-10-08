# TR-1000 Grid — Referência

Base de conhecimento do projeto: o que se sabe do protocolo da TR-1000, de onde veio cada
coisa, e o que falta. **Ler antes de mexer em qualquer coisa** — a seção 3 separa o que
está provado do que é só dedução, e essa distinção é o que impede retrabalho caro.

Estrutura e método herdados do `../tr8s-grid/REFERENCIA.md`, onde a TR-8S foi decifrada
entre 08 e 18/08/2026. **Nada medido na TR-8S é fato aqui** — entra como hipótese.

Etiquetas usadas em todo o documento (e nos comentários do código):

| etiqueta | significa |
|---|---|
| **(medido DD/MM)** | visto nesta TR-1000, com o método da 3.2 |
| **(manual X p.N)** | está no manual da Roland. Diz o que a máquina *pode*, não o que *faz* aqui |
| **(catálogo)** | ordem de nomes no binário do TR-1000 App 1.10 (2.2). Hipótese forte de ordem, nunca endereço |
| **(TR-8S)** | era assim na TR-8S. Hipótese fraca |
| **(deduzido)** | inferência nossa |

---

## 1. Objetivo do projeto

Dois Launchpad Mini MK3 lado a lado (16×8) editando **o pattern interno da TR-1000** por
SysEx, em tempo real, como o tr8s-grid faz com a TR-8S. Decisão de 07/10/2026: **só SysEx no
pattern interno** — nada de sequenciador externo mandando notas. A máquina toca sozinha, e o
pattern sobrevive com o Mac desligado.

O que a TR-1000 traz e o grid quer aproveitar (manual RM p.12–31):

- **10 tracks** (BD SD LT HT RS HC CH OH CC RC — não há MT) **+ ACCENT + TRG**: 12 linhas
- **Layer A/B** nos quatro primeiros (dois GEN misturados pelo MIX); **ALT** nos outros seis
- **8 variações + 4 fills** (a TR-8S tinha 2 fills), FIRST/LAST STEP por variação **e por
  track** (polimetria), DIRECTION por track (FWD, BWD, P-P, RND...)
- Por step: VELOCITY, START (micro-timing), SUBSTEP (1/2, 1/3, 1/4, Flam, tercinas 1–4,
  quiálteras 1–5), PROB, **CYCLE** (1/1, 2/2, 1/3, 5/8, "1st Only"...), slice
- STEP LOOP, ROLL, snapshots, MORPH, motion

Prioridades combinadas: linhas com layer A/B e ALT; variação e step **por track**;
parâmetros de step; página de performance.

---

## 2. Protocolo

### 2.1 Portas — (medido 07/10/2026)

`lp_tr1000.py ports`, TR-1000 na USB, App fechado:

| direção | nome | uso |
|---|---|---|
| in/out | `TR-1000` | clock, notas, CC (manual) |
| in/out | `TR-1000 CTRL` | onde o App fala — candidata ao SysEx, como a `TR-8S CTRL` |
| in | `TR-1000 MIDI IN` | a DIN de entrada vista pela USB (deduzido) |
| out | `TR-1000 MIDI OUT 1`, `TR-1000 MIDI OUT 2` | as DIN de saída (deduzido) |

`TR-1000` é prefixo de `TR-1000 CTRL`: abrir por trecho de nome pega as duas. O código usa
`portas.porta_exata`.

**Formato SysEx: desconhecido.** O `roland.py` assume a família moderna da Roland
(`F0 41 <dev> <model> <cmd> <addr 4B> <dados> <chk> F7`, RQ1 = 11, DT1 = 12) porque era o da
TR-8S e é o que o App de uma máquina Roland de 2025 quase certamente usa — mas o **model
ID** e o próprio formato só ficam provados na sessão C1. O decodificador não precisa saber o
model ID: ele acha o tamanho pelo checksum.

**Identity Request universal (`F0 7E 7F 06 01 F7`): sem resposta** (medido 07/10/2026),
mandado na CTRL e na comum, escutando as três entradas por 1,5 s cada, App fechado. Isso só
diz que a TR-1000 não responde a *este* pedido — **não** que ela não tem SysEx (regra 7 do
Método). Consequência prática: o autoteste do `sniff` não tem como provar o listener na
CTRL antes da C1; até lá, silêncio na CTRL é ambíguo.

### 2.1b O App NÃO fala MIDI por padrão — fala serial USB (medido 08/10/2026)

A primeira tentativa da C1 não viu **nada** no MIDI Monitor, e não era o filtro: com o App
reiniciando sob escuta (`rtmidi` cru nas três entradas `TR-1000*`, clock filtrado, 3 min, o
PID do App trocando no meio), **zero** mensagens. O `lsof` do processo do App mostrou o
motivo:

```
12u CHR /dev/tty.usbmodem31101
```

A TR-1000 expõe, além do USB MIDI e do áudio, uma **interface serial USB (CDC ACM)**:
`ioreg` mostra `Roland TR-1000` → `AppleUSBCDCCompositeDevice` → `AppleUSBACMControl`/
`AppleUSBACMData` → `IOSerialBSDClient` = `/dev/cu.usbmodem31101`. O App 1.10 usa essa porta
por padrão. O App não abre o USB direto (os únicos IOUserClient dele são de GPU), não usa
rede e não tem endpoint MIDI privado (a enumeração CoreMIDI com `kMIDIPropertyPrivate` só
mostra `TR-1000`, `CTRL`, `MIDI OUT 1/2`, `MIDI IN`, todos públicos).

**"Use CTRL Port" não troca o transporte com o App aberto, e a UI não tem a opção**
(medido 08/10/2026). O `~/TR1000 User/settings.xml` tem `<ctrlPort user="…"/>`, e a string
"Use CTRL Port" está no binário. A sequência observada:

| hora | o que aconteceu | `ctrlPort` no arquivo |
|---|---|---|
| antes de 14:00 | eu troquei 0 → 1 com o App fechado | 1 |
| 14:00:22 | App aberto (pid 16057); abriu a serial; 120 s de escuta `rtmidi`: zero MIDI | **0** às 14:00:40 (mtime 14:00) |
| 14:36:22 | o Luan abriu a ⚙ do App (só tem *Scale Factor*) e o App regravou o arquivo | **1** |
| 15:04 | o mesmo App segue na serial: `lsof` mostra o fd em `0t2394308` (~2,4 MB trafegados desde 14:00) | 1 |

Ou seja: o valor em memória parece ser 1 (foi o que ele gravou às 14:36), e mesmo assim o
App fala pela serial. O que **não** se sabe: se um App aberto **do zero** com `1` já salvo
troca de transporte. A C1-S0 responde de graça (a cópia lê o mesmo arquivo): se o
autoteste disser "abriu a serial = NAO", é isso. A interface não tem a opção — a ⚙ só
oferece *Scale Factor*, e o ☰ é Import/Export Sample, Transfer Backup/Project, Reload/Write
Inst, Init Generator, About. É código herdado do app do SP-404MKII (as strings estão no
mesmo binário).

**O App conversa o tempo todo**, não só no boot: ~2,4 MB em ~65 min, uns 600 B/s. Ou seja,
ele faz polling — provável fonte do `cur_step`/`cur_vari` (2.2).

**Plano B — espiar a serial (implementado em 08/10/2026):**
- **`espiao/espiao_serial.c`:** biblioteca que entra no processo do App por
  `DYLD_INSERT_LIBRARIES` e grava cada byte lido e escrito em `/dev/tty.*`/`/dev/cu.*`,
  com hora em ns. **Só observa**: chama a função real e devolve o que ela devolveu.
  - Intercepta: `open`, `openat`, `close`, `read`, `write`, `readv`, `writev`, `ioctl` e
    `tcsetattr`.
  - É exatamente o que o App importa para a serial: `nm -u` mostra também `poll`, `fcntl`,
    `tcgetattr` e `cfsetspeed`. A porta é achada por IOKit (`IOServiceGetMatchingServices`).
- **A cópia do App:** o App tem hardened runtime (`flags=0x10000(runtime)`), e com ele o
  dyld ignora `DYLD_INSERT_LIBRARIES`.
  - `espiao.py preparar` faz uma **cópia** em `~/Library/Caches/tr1000-grid/` e a re-assina
    ad hoc, sem a flag.
  - O App não confere a própria assinatura: não importa `SecCode`, não tem entitlements nem
    segmento `__RESTRICT`.
  - O original em `/Applications` não é tocado.
- **Formato `.serlog`:** cabeçalho `TR1KSER1` + versão u32. Cada registro é
  `t_ns u64 | tipo u8 | fd u32 | n u32 | n bytes`.
  - Tipos: `S` início (o pid vai no campo fd), `O` open, `C` close, `R` read, `W` write,
    `I` ioctl, `T` tcsetattr.
  - Leitor: `tr1000_serial.py` (`bruto`, `estatisticas`). Todos os comandos do
    `tr1000_sysex.py` aceitam `.serlog`, que passa pelo mesmo caminho do `.mmon`.
- **Hipótese H1** **(deduzido)**: a serial carrega SysEx Roland (RQ1/DT1).
  - Por quê: o `ReadAllParametersReq` do App e a TR-8S.
  - O leitor remonta os quadros `F0..F7` sobre o fluxo, porque `read()` corta onde quiser,
    e conta os bytes que caem **fora** de quadro: muita sobra = H1 errada.
- **Conferido de mesa, sem o App** (08/10/2026): um programa de teste numa pty com caminho
  `.../dev/tty.teste`, rodando com o espião injetado.
  - Um DT1 escrito em dois `write` voltou como um quadro.
  - Dois quadros lidos num `readv` só saíram separados.
  - O `tcsetattr` mostrou 115200.
  - O `tr1000_sysex.py parse` leu o `.serlog` direto.
- **Ainda não rodou com o App**: o `preparar` (a re-assinatura da cópia) fica para o Luan
  rodar. A sessão C1-S0 é o teste de verdade.

Outras coisas na pasta `~/TR1000 User/`: `update.zip` (27 MB, o firmware baixado pelo App) e
`app_version.xml`. O firmware fica **intocado**.

### 2.1c O protocolo da serial — C1-S0, 08/10/2026 (medido, salvo onde marcado)

Captura: `capturas/2026-10-08-s0-autoteste.serlog` (1,77 MB, 14 886 registros). O App foi aberto
pela cópia do espião, esperou "Connected", e foi fechado com Cmd+Q. Máquina parada.
Autoteste: espião carregou, abriu `/dev/tty.usbmodem31101`.

**A porta:** `tcsetattr` a 9600 e logo depois a **230400** baud.

**H1 caiu.** Não é SysEx Roland: só 0,2–0,3% dos bytes caem em quadros `F0..F7`, e por
acaso. É um protocolo binário próprio, little-endian, em **pacotes**:

| tipo (`& 0x7F`) | tamanho | forma |
|---|---|---|
| `0x14` | 12 B fixos | `[tipo][canal][orig][dest][u32][u32]` |
| `0x15` | 16 + n | `[tipo][canal][orig][dest][u32][u32][u32 n]` + n bytes de carga |

Essa regra enquadra a captura **inteira**, nas duas direções, com **zero** byte sobrando:
- App → máquina: 86 KB em 5963 pacotes
- máquina → App: 1,43 MB em 9141 pacotes

`tr1000_serial.py pacotes` mostra a conversa.

O resto da forma dos pacotes:
- **Bit 7 do tipo** (`0x94`/`0x95`) aparece só no **canal `02`**: o aperto de mão inicial e
  um tráfego periódico de 160 B. O canal `08` leva todo o resto.
- **orig/dest** **(deduzido)**:
  - O App manda `40 F0` (o poll) e `41 F2` (os pedidos).
  - A máquina responde `F0 00`.
  - Parecem endereços de origem/destino de dois "serviços" de cada lado.

**O aperto de mão:**
- O App manda `94 02 40 F0 FE C0 00 00 00 84 03 03`.
- A máquina responde 43 B terminando em ASCII `"1.22"`, provavelmente a versão do
  firmware **(deduzido)**.

**O poll:**
- O App manda `14 08 40 F0 9B 00 00 00 00 00 00 05` a cada ~100 ms: 4680 vezes.
- A resposta foi **sempre** `14 08 F0 00 1B 00 00 01 00 00 00 07`.
- Hipótese: "nada mudou"; a C1-S5 (mexer no painel com o App aberto) testa.

**Listas** (pedido `14 08 41 F2 <cmd> … 01` → um `14` de cabeçalho + um `0x15` por item, a carga
começando por `<id da lista> <índice u16>`):

| cmd | id | itens | conteúdo |
|---|---|---|---|
| `87` | `08` | 104 | categorias ("ALL", "BD E", "BD A", "SD E", …) |
| `85` | `06` | 442 | GENs ("808 Bass Drum", "909 Snare Drum", "8X Conga", …) |
| — | `06` (282 B) | 2121 | caminhos de sample (`A:/Roland/TR-1000/SAMPLE…`) |
| `8D` | `0e` | 331 | INST ("TR-808-1000 BD", …) — bate com as 331 da INST List |
| `8B`? | `0c` | 128 | nomes de kit ("Dub Techno Kit", …) |

**O endereço, corrigido em 08/10/2026 (knob-bd-tune):** toda carga de parâmetro é
`<cmd u8> <bloco u16> <x u16> <y u16> <índice u16> …`. O que eu tinha lido como "instância
u32 nos 16 bits de cima" são **dois u16**:
- **y** = track (0..9 = BD..RC) ou layer (0/1);
- **x** = slot de sample (0..499), no bloco 156.

**A ESCRITA — medida em 08/10/2026, captura `knob-bd-tune`** (o Luan girou o TUNE do
GENERATOR do BD no App, ~28 s):

```
App → máquina   01 <bloco> <x> <y> <índice> <u32 valor>        escrita
máquina → App   03 <bloco> <x> <y> <índice> <índice>           confirmação (857 das 864)
```

- 864 escritas, **todas** no mesmo endereço: bloco **156**, x **126**, y 0, índice **962**.
- O BD do kit usa o GEN de sample "Hybrid Kick 03", então o TUNE do GENERATOR mexe no **slot
  de sample** 126, e não num parâmetro do track — o mesmo bloco 156 que o boot lê
  (índices 718..987 por slot).
- Valores: começou em **509**, foi até **0** e até **1000**, terminou em 1000. Faixa
  0..1000, centro ~500 **(deduzido)**.
- Antes de escrever, o App releu só esse parâmetro: `82 9C 00 7E 00 00 00 C2 03 01 00` (n = 1).
- **A máquina guardou o valor (medido, round-trip):** o Luan abriu o App original de novo
  depois da captura, e o TUNE do BD apareceu no **máximo** — o App lê os valores da máquina
  ao abrir, então o 1000 estava nela. Isso prova que a máquina **aceitou**, não que o som
  mudou (Método, regra 9): o Luan não sabia como soava antes. O kit é o 001 "Dub Techno
  Kit", BD "DubTechno Kit BD". **Deixado em 1000; o original era 509.**
- `tr1000_serial.py escritas` lista as escritas de uma captura.

O que isso destrava: o mesmo `01` deve escrever **qualquer** índice, inclusive os steps.
Ex.: BD var A step 2 layer A = bloco 118, x 0, y 0, índice 1249 + 4·1 + 0 = 1253.
**Hipótese — nenhum byte nosso foi mandado à máquina** (portão da fase 0, 3.1).

**Os parâmetros — o achado principal:**
- **Pedido** do App (carga de um `0x15`):
  `82 <bloco u16> <instância u32> <índice u16> <n u16>`
- **Resposta** da máquina:
  `02 <bloco u16> … <índice u16> <n u16>` + **n valores u32**
- O tamanho fecha sempre. O bloco 3, por exemplo, volta com n = 292 → 1168 B de valores.
- A instância anda de 65536 em 65536: o número está nos 16 bits de cima.
- **O índice parece global**: um número único por parâmetro, de 112 a ~2880. Ele é
  candidato a casar com o catálogo do App, 2.2 **(deduzido)**. Mas o catálogo foi
  deduplicado pelo linker, então a posição na lista de strings ≠ índice. A ponte certa é
  a tabela de descritores do binário, ainda não lida.

O App leu **139 blocos, 438 leituras (bloco × instância)** no boot (`tr1000_serial.py
blocos`). A estrutura que salta aos olhos — **dedução** sobre números medidos, a confirmar
com gestos (C1-S3/S4, C2):

| blocos | índice / n | instâncias | leitura provável |
|---|---|---|---|
| 3 | 112 / 292 | 1 | sistema/projeto |
| 4–13 | vários, pequenos | 1 (o 13: 10) | kit (o 13 por track?) |
| 16–24, 26–34, …, 106–114 | os mesmos 9 subblocos (565/27, 2856/30, 2651/15, 2628/11, 2690/11, 2715/27, 602/22, 592/10, 624/40), 10 grupos de 10 em 10 | **2** nos grupos 16, 26, 36, 46; **1** nos outros 6 | **os 10 instrumentos**. Os 4 primeiros têm **layer A/B**, exatamente BD SD LT HT (manual) |
| 116 | 988 / 248 | 1 | **cabeçalho do pattern** |
| 117–152 | 12 grupos de 3: 1236/13, 1249/131 (×10), 1380/144 (×10) | | **8 variações + 4 fills**: cabeçalho da variação (13), parâmetros do track na variação (131, ×10 tracks), **steps** (144, ×10 tracks) |
| 156 | 718 / 270 | 500 | os 500 slots de sample (strings em u32) |

**Correção da primeira leitura:** os steps estão no bloco **118 + 3v** (n = 131), não no
119. O 119 + 3v (144) estava vazio e casa com `motion0..95` + `motion_valid0..47` = 144 do
catálogo.

#### A leitura do pattern CONFERIDA NO PAINEL (08/10/2026)

`tr1000_serial.py pattern capturas/2026-10-08-s0-autoteste.serlog` contra o que o Luan viu
na máquina parada:

| o que se leu na captura | o painel |
|---|---|
| bloco 116: nome `"Dub Techno"` (um caractere ASCII por u32), depois `0x3200` = 12800 → **128,00 BPM** | ✅ "Dub Techno", 128 |
| var A, BD: steps 1, 5, 9, 13 | ✅ LEDs vermelhos em 1 5 9 13 |
| var A, OH: 3, 7, 11, 15 | ✅ |
| var A, SD: nota no 1º slot em 4 e 12; nota só em slot posterior em 2 7 9 10 13 15 16; o resto sem nota | ✅ **vermelho** em 4 e 12, **verde** em 2 7 9 10 13 15 16, apagado/cinza no resto |
| var H, BD: os 16 steps só com `FF` | ✅ todos apagados |

**Layout do bloco de steps** (n = 131, instância = track 0..9 = BD..RC) — **medido** onde o
painel conferiu, **deduzido** no resto:

- `[0..63]`: 16 steps × **4 slots** (`[step*4 + slot]`). **Os slots são LAYERS, não
  sub-steps.**
  - **Medido** em 08/10 nos 12 bancos do Dub Techno: os tracks de layer (BD SD LT HT) só
    usam os slots 0 e 1; os simples (RS…RC) só o slot 0.
  - Slot 0 = **layer A** (ou o som normal), slot 1 = **layer B**. Slots 2–3 sem uso visto;
    o ALT dos tracks simples é o candidato **(deduzido)**.
  - `0x00` = vazio; `0xFF` = pausa; outro valor = **nota**.
  - Um step ligado e desligado de novo vira `FF`, não `0`: visto na var H do BD entre a S0
    e o ruido-1.
  - **O step toca se algum slot tem nota (medido).**
  - **Cores no painel (medido no SD da var A):** layer A tocando (com ou sem o B) =
    **vermelho**; só o layer B (`FF nota`) = **verde**.
  - **Step ligado no painel (medido, `step-bd2`):** var A, BD, step 2: slots `0 0 0 0` →
    `A503C A503C 0 0`, os dois layers — igual aos outros BD do pattern. Contra o
    `ruido-2`, só isso mudou no pattern. Fora dele, o bloco 3 `[128]` foi de 8 para 1.
- O valor da nota, ex.: `0xA503C` = `A` `50` `3C`.
  - O byte do meio parece a **velocity**: `0x50` = 80, a "Normal Velocity" do manual;
    `0x5A` = 90; os CH variam `0x32`…`0x68`, como chimbal humanizado **(deduzido)**.
  - `0x3C` = 60 e o nibble `A` sem leitura ainda.
- `[64..79]`: todos `0x64` = 100 — **probability 100%** **(deduzido)**.
- `[80..130]`: zeros quase sempre; um `3` no step 1 do SD (`[96]`). Candidatos: sub_step,
  cycle, shift **(deduzido)**.

Parece que **o App lê o pattern inteiro ao abrir** — o obstáculo da TR-8S ("não há editor
de pattern para sniffar") não existe aqui. A **leitura** do pattern está provada contra o
painel. **Escrita: nada provado** — o App só leu; o comando de escrita ainda não apareceu
(C1-S3).

 — (catálogo, 07/10/2026)

O binário do App (`/Applications/Roland/TR-1000 App.app`, versão 1.10, framework JUCE —
código compartilhado com o app do SP-404MKII, cujas strings aparecem junto) tem uma tabela
**contígua** de 2400 nomes de parâmetro, em ordem. `python3 catalogo_app.py` a extrai e a
fatia em blocos pelas âncoras abaixo (os nomes dos blocos e as fronteiras são nossos):

| bloco | começa em | o que tem (resumo) |
|---|---|---|
| sistema | `Bright` | display, Auto Save, Project Num, atenuações das saídas |
| midi | `Device ID` | Omni, Pattern Ch., Kit Ch., Inst Note (normal, A, B, Alt) de cada track, Through, **Tx/Rx Bank Select**, Tx/Rx Edit Data, Tx Nudge, Tx Shuffle, MIDI Out 1/2, MIDI Mode |
| performance | `KIT_NUM` | `KIT_NUM`, `PTN_NUM`, `NEXT_PTN_NUM`, VOLUME, SEQ_TRIG, SEQ_START, `LAST_STEP`, `MUTE_BTN`, ACCENT, SUB_BTN, Shuffle, MOTION_REC, Nudge, RANDOM_PTN, `SUB_STEP_MODE`, PTN_SEL, CTRL_KNOB1..11, `FILLIN_SEL_BTN`, MANUAL_TRIG_BTN, CurTempo, LEVEL SLIDER1..11, `seq_run`, **`cur_step_master`, `cur_step0..10`, `cur_vari_master`, `cur_vari0..10`**, `vari_req`, `sw_fill`, seq_song_mode, `fillin_state`, `loop_step_sw`, `loop_step0..15`, `roll_sw`, motion_knob_tmp0..53 |
| projeto | `Tempo Source` | Tempo Sync, TR-REC Mode, Fill In Trigger, Pattern Lock, Normal/Weak Velocity, Mute Mode, Track Sync, Sync Delay, Ext In, Trig In/Out |
| kit | `CUSTOM LED` | cores, nomes, sends, side chain, mods, layers, níveis A/B, nomes de sample |
| pattern | `Name1` | nome (16), **Tempo, Variation**, Flam Space, MOTION SW, Accent, Accent Depth, KIT Ref SW, Master Prob, Pattern Gain, TRK GAIN1..10, Scale, Scale Trk1..11, Shuffle Trk1..11, **Begin/End Step A..H, Fill 1..4, Track1..11**, End Step Track SW1..11, AUTO SW/CYC, grooves, QUANTIZE |
| step | `Accent Weak` | Trigger, **`note0..`, `probability0..`, `sub_step`, `cycle`, `shift`, `trk_shift`**, motion, param, valid, pattern, mode, loop, variation, grv_timing, grv_velo |
| hardware | `ANA DEBUG` | calibração e detecção dos circuitos analógicos — **nunca tocar** |
| efeitos_inst | `PRE DLY` | parâmetros de reverb/delay/MFX/IFX e dos GEN |

O que isso muda em relação à TR-8S:

- **A variação que toca é legível, por track** (`cur_vari0..10`), se esse bloco for o que
  parece. Na TR-8S não estava em lugar nenhum que a gente lesse, e o grid deduzia contando
  clock (`CicloVars`), com "?" quando não sabia. Aqui o playhead pode ser exato e polimétrico.
- **`ServerApp::ReadAllParametersReq`** existe: o App lê tudo ao abrir. Na TR-8S, o
  obstáculo registrado era "o App da TR-1000 edita só kits, não há editor de pattern para
  sniffar" (tr8s REFERENCIA 8). O catálogo mostra que o App **conhece** o pattern e o step,
  e o boot deve ler ao menos o cabeçalho do pattern — a C1 diz.
- A performance tem a mesma cara do bloco `01 00 00 00` da TR-8S (kit, pattern atual,
  próximo pattern...) **(TR-8S)**.

**Ressalva principal — é vocabulário, não layout** (achado na revisão de 07/10/2026): a
tabela sai da seção de strings do binário, onde o linker guarda cada string idêntica **uma
vez só**. Os 2400 nomes têm **zero** repetidos, o que já denuncia a deduplicação: o `CTRL1`
de cada instrumento, os `PRM1..`, os `LEVEL` aparecem só na primeira ocorrência, e um bloco
de 10 instrumentos vira um conjunto de nomes. A ordem só é candidata a ordem de offset onde
os nomes são únicos por natureza — a performance (`cur_step0..10`) e o cabeçalho do pattern
(`Begin Step A..H`) — e mesmo ali é hipótese.

Outras ressalvas: a ordem dos nomes **não** é prova de ordem de offset — parâmetros de 2 bytes,
reservas e alinhamento quebram a correspondência um-para-um. E as contagens das séries
(`note0..63`; `probability`, `sub_step`, `cycle`, `shift` e `valid` em `0..15`; `motion0..95`;
`variation`, `grv_timing` e `grv_velo` em `0..127`) ainda não têm interpretação. Os de 16
casam com 16 steps; `note0..63` pode ser 16 steps × 4 sub-steps; 128 pode ser 8 variações × 16.
Hipóteses, nada mais.

### 2.3 O MIDI documentado — (manual MIC p.1–2, RM p.46–48)

Vale como plano B de leitura e para a página de performance, não como caminho de escrita
do pattern:

- **Canais:** Pattern Ch. 10 (troca pattern e kit), Kit Ch. 1 (só kit)
- **Notas** (Single Ch.): BD 36 (A 35, B 99), SD 38 (40, 104), LT 43 (41, 105), HT 50 (48, 112),
  RS 37 (ALT 56), HC 39 (54), CH 42 (44), OH 46 (58), CC 49 (61), RC 51 (63), TRG 84. Em
  `tr1000.NOTAS_PADRAO`. Mudáveis em MENU > SYSTEM > MIDI > Inst Note
- **66 CCs**, Tx e Rx (`tr1000.CC`), com `Rx/Tx Edit Data` = ON. MORPH = 89, MFX ON = 15,
  AFX ON = 19. **Sem CC:** mute, variação, fill, steps, accent level, volume, tempo
- **Program Change** 0–127, sem Bank Select na chart (mas o catálogo tem `Tx/Rx Bank
  Select` — divergência a medir)
- **Clock, Start, Continue, Stop**; **SPP** só em Song Mode
- **SysEx:** ✗ na chart. A da TR-8S também era ✗ — a chart não é evidência de ausência

**Falta no `manuals/`:** o documento *MIDI Implementation* (Owner's Manual p.1), separado
da Chart. Se a Roland publicou algum mapa SysEx, é lá. Baixar antes da C1.

---

## 3. O que está provado vs. deduzido vs. desconhecido

| item | estado | onde |
|---|---|---|
| nomes e quantidade das portas | **medido 07/10** | 2.1 |
| clock contínuo na `TR-1000`, ~51 pulsos/s (≈128 bpm) | **medido 07/10** — se parada ou tocando, **desconhecido** | 7.2 |
| sem resposta ao Identity Request | **medido 07/10** | 2.1 |
| nada chegou na CTRL nem na MIDI IN em 8 s parados | **medido 07/10** (sem autoteste na CTRL — ambíguo) | 7.2 |
| formato Roland RQ1/DT1 na CTRL | **(deduzido)** da TR-8S e da existência da porta | 2.1 |
| o App fala por **serial USB** (`/dev/tty.usbmodem*`), não MIDI, com `ctrlPort` = 0 | **medido 08/10** | 2.1b |
| "Use CTRL Port" = 1 com o App já aberto: segue na serial; a UI não tem a opção | **medido 08/10** | 2.1b |
| "Use CTRL Port" = 1 num App aberto do zero | **desconhecido** — a C1-S0 diz | 2.1b |
| o App fala com a máquina continuamente (~600 B/s) | **medido 08/10** (`lsof`, offset do fd) | 2.1b |
| a serial carrega SysEx Roland (H1) | **falso — medido 08/10** (C1-S0: 0,2% em quadros) | 2.1c |
| transporte: serial USB a 230400, pacotes `0x14` (12 B) / `0x15` (16 + n), enquadramento sem sobra | **medido 08/10** | 2.1c |
| leitura de parâmetros: `82 bloco inst índice n` → `02 …` + n × u32 | **medido 08/10** | 2.1c |
| ler o pattern pela serial (nome, tempo, steps 118+3v, slots 0/FF/nota) | **medido 08/10**, conferido no painel | 2.1c |
| slots 0/1 do step = layer A/B; vermelho = A, verde = só B | **medido 08/10** | 2.1c |
| piso de ruído entre dois boots sem gesto: zero (139 blocos iguais) | **medido 08/10** (`ruido-1`/`ruido-2`) | 2.1c |
| bloco 3 `[128]` = variação selecionada no painel (8 = H, 1 = A) | **(deduzido)** de dois diffs | 2.1c |
| velocity no byte do meio da nota; `[64..79]` = probability | **(deduzido)** | 2.1c |
| comando de escrita: `01 bloco x y índice u32` → `03 …` | **medido 08/10** (App escrevendo; nunca por nós) | 2.1c |
| o mesmo `01` escreve steps (bloco 118+3v) | **(deduzido)** — é o teste C3 | 2.1c |
| espião grava `read`/`write` da serial, quadros remontados | **medido 08/10** (pty e com o App) | 2.1b |
| **escrita nossa de um step (`01`) obedecida: bumbo some/volta, LED apaga/acende vermelho** | **medido 08/10, OUVIDO** (C3.1, C3.2) | 3.1 |
| model ID | **não se aplica** à serial (não é SysEx); a versão `"1.22"` vem no aperto de mão | 2.1c |
| ordem dos parâmetros por bloco | **(catálogo)** | 2.2 |
| endereços de qualquer coisa | **desconhecido** | |
| RQ1 inválido envenena a CTRL? | **desconhecido** — tratar como sim | CLAUDE.md |
| a máquina empurra estado sozinha? | **desconhecido** (a TR-8S empurrava o step atual) | C0/C1 |
| o painel transmite nota/CC/PC? | **desconhecido** (a TR-8S não transmitia CC) | C0 |

### 3.1 Critério de saída da fase 0 (o portão)

Reescrito em 08/10/2026 para a realidade da serial (2.1b/2.1c): não há SysEx nem model ID.
A fase 1 (o grid escrevendo) só começa quando **todos** estes forem **medidos**:

| # | critério | estado |
|---|---|---|
| 1 | Formato da mensagem provado em captura real (enquadramento sem sobra, aperto de mão com versão) | ✅ 08/10 (C1-S0) |
| 2 | Ler o pattern pela serial e conferir no painel | ✅ 08/10 (Dub Techno, var A/H) |
| 3 | **Um step desligado e ligado por escrita NOSSA (`01`), ouvido pelo Luan** | ✅ **08/10 — desligar (C3.1) e ligar (C3.2), ouvidos** |
| 4 | Endereçamento pattern × variação provado em **3 patterns** diferentes (o bloco 118+3v muda de conteúdo ao trocar de pattern) | ⏳ |
| 5 | Step atual / variação que toca lidos com a máquina tocando, conferidos no visor | ⏳ (candidato: bloco 3) |
| 6 | WRITE (gravar o pattern) seguido de religar a máquina, e o step sobrevivendo | ⏳ |

**C3.1 — 08/10/2026, a primeira escrita nossa, OUVIDA:**
- **O que saiu:** `sessao_c3.py step2 desligar`, máquina tocando só a var A do Dub Techno.
  Dois pacotes `01` byte a byte iguais ao formato do App: bloco 118, x 0, y 0, índices 1253
  e 1254, valor `FF`.
- **O que voltou:** `03` para os dois; releitura `FF FF`.
- **O Luan, na frente da máquina:** o bumbo do step 2 **sumiu**, o LED do step 2 **apagou**,
  e a máquina **seguiu tocando** sem parar nem engasgar.
- **Captura:** `capturas/2026-10-08-c3-step2-desligar.serlog`.
- **Uma lição:** a primeira tentativa não mandou nada, nem pelo Terminal (Enter vazio) nem
  pelo `!` (sem teclado). A trava do `sim` segurou as duas, e daí veio o `--sim`.
- **Para ouvir o step é preciso que a máquina toque SÓ a variação editada.** Ela estava
  encadeando A → B…, e o step 2 só soava em parte do tempo.

**C3.2 — 08/10/2026, ligar de novo, OUVIDO:**
- **O que saiu:** `sessao_c3.py step2 ligar`, o valor `0xA503C` (o que o painel tinha posto
  em `step-bd2`) nos dois slots.
- **O que voltou:** `03` nos dois, releitura `A503C A503C`.
- **O Luan, na frente da máquina:** o bumbo do step 2 **voltou**, o LED acendeu
  **vermelho** (layer A tocando, como a 2.1c previa), e a máquina seguiu tocando.
- **Captura:** `capturas/2026-10-08-c3-step2-ligar.serlog`.

**Com C3.1 + C3.2 o critério 3 do portão está cumprido:** lemos e escrevemos steps do
pattern interno da TR-1000 pela serial, e a máquina obedece de ouvido. Faltam os critérios
4–6 (três patterns, step atual tocando, WRITE + religar).

A escrita da C3 passa só por `sessao_c3.py` → `conexao_serial.py`, com **lista de 3
endereços** no código (`ESCRITAS_PERMITIDAS`: os dois slots do step 2 do BD na var A e o
TUNE do sample do BD), os bytes mostrados e `sim` digitado antes de cada uma. Os pacotes
são **byte a byte** iguais aos que o App mandou e a máquina aceitou (`TesteEscritaC3`).

### 3.2 Método: como descobrir coisas nesta máquina

> Copiado **sem mudança** do tr8s-grid (REFERENCIA 3.2 de lá). Os exemplos são da TR-8S;
> as regras valem iguais aqui, e foi por isso que vieram inteiras.

Destilado da sessão de 14/08/2026, que decodificou o mute, o ALT e o step atual em algumas
horas depois de meses de itens parados. O que mudou não foi a sorte — foram estas regras.
Elas custaram caro para aprender e são baratas de seguir.

**1. Autoteste sempre, e periódico.** Sem ele, "não apareceu nada" é ambíguo entre a
máquina calada e o listener surdo, e a leitura errada vira achado no documento. Foi o
autoteste que tornou confiável o resultado negativo do `sniff`, e foi a falta dele que
produziu os 15 endereços fantasma da 3.1 — a primeira versão do `varrer` conferia se a
máquina respondia **uma vez, no começo**, e não viu que ela morreu no meio.

**2. Piso de ruído antes de qualquer diff.** Dois snapshots sem tocar em nada, e compare.
Custa 10 segundos. Sem essa medida, um byte que muda sozinho — e existem, como o offset 90
do nó de pattern — vira "achado" no primeiro diff que você olhar.

**3. Um gesto por vez, e o inverso logo em seguida.** O valor tem que voltar. Mutar o BD e
desmutar o BD prova mais que mutar cinco instrumentos, porque o retorno elimina
coincidência.

**4. Segundo passe em todo achado.** Endereço de verdade responde duas vezes; falso
positivo não. É uma linha de código e teria matado os 15 fantasmas sozinha.

**5. Ler blocos, não sondar bytes.** Uma leitura de 128 bytes cobre o que 128 sondas
cobririam, é ~100× mais rápida e **não envenena a porta** (3.1). A varredura byte a byte
existe para mapear fronteiras de região, e é o último recurso, não o primeiro.

**6. O que muda sem motivo aparente merece uma pergunta antes de virar ruído.** O byte de
step atual (2.8) apareceu como "ruído que muda sozinho" num diff de mute e quase foi
descartado. Ele acabou consertando dois bugs do playhead.

**7. Teste negativo não vira afirmação geral.** O CC de LEVEL não silenciar virou "não dá
para silenciar por software", e essa frase ficou errada no documento por um dia — tempo em
que um recurso funcionando parecia impossível (seção 10). Registre o que **foi** testado,
não a generalização que ele sugere.

**8. A ordem certa é do barato para o caro.** `snap`/`snapdiff` nos endereços conhecidos →
leitura em bloco de regiões novas → varredura → MIDI Monitor. Cada degrau só se justifica
quando o anterior não alcança; a sessão de 14/08 quase começou pelo caro e teria gasto
várias religadas da máquina à toa.

**9. O que o hardware confirma vale mais que o que o round-trip confirma.** Escrever um
valor e reler prova que a máquina *aceitou*, não que ela *obedeceu*. O mute só virou fato
quando o Luan ouviu os chimbais sumirem.

---

## 5. Launchpad Mini MK3

Mesmo hardware do tr8s-grid, medido aqui em 07/10/2026: quatro portas com nomes idênticos
(`LPMiniMK3 DAW` e `LPMiniMK3 MIDI`, ×2). Toda a seção 5 da REFERENCIA de lá vale: programmer
mode (`F0 00 20 29 02 0D 0E 01 F7`), notas = linha×10+coluna (11–88), CC 91–98 na fileira de
cima e 89…19 na coluna de cena, cor RGB por SysEx `F0 00 20 29 02 0D 03 ...`, `learn` com três
pads por aparelho para descobrir a rotação. A camada entra como `launchpad.py` na fase 1, sem
mudança de lógica.

---

## 6. Configurações da TR-1000 que importam — (manual RM p.47–48)

MENU > SYSTEM > MIDI. A anotar como estão na máquina do Luan durante a C0:

| parâmetro | por que importa |
|---|---|
| Pattern Ch. / Kit Ch. | onde o program change age |
| Tx/Rx Edit Data | sem ON, nenhum CC passa (página de performance) |
| Tx/Rx Program Change | |
| Rx Start Stop Cont | |
| TX Note / RX Note | se o painel manda nota quando toca — útil para a C0 |
| USB MIDI Through / Soft Through | eco que pode confundir uma captura |
| MIDI Mode | Single Ch. ou Each Track Ch. (muda o mapa de notas) |
| Tempo Sync (projeto) | Auto/MIDI/USB/INT — o Mac **não** deve virar mestre de clock sem querer |

---

## 7. Fase 0 — o plano de captura

Do barato para o caro (regra 8 do Método). O passo a passo para o Luan está no
`ROTEIRO-C0-C3.md`; aqui fica o porquê e o que cada um responde.

### 7.1 As sessões

| sessão | ferramenta | responde |
|---|---|---|
| **C0** escuta passiva | `lp_tr1000.py escutar` | clock parada × tocando; o painel transmite nota/CC/PC?; a máquina empurra SysEx? |
| **C1** sniff do App | ~~MIDI Monitor~~ → **espião da serial** (`espiao.py` + `tr1000_serial.py`, 2.1b) + `tr1000_sysex.py resumo/fx/diff` | **model ID**, formato, **mapa de endereços e tamanhos** (boot), lista branca de RQ1, keep-alive, mute, WRITE, formato de bulk |
| **C2** decodificar o pattern | `snap`/`snapdiff` (a portar do tr8s-grid), **só em endereços da lista branca** | layout do step, layer A/B, ALT, prob, sub, cycle, last step, máscara de variações, `cur_step`/`cur_vari` |
| **C3** primeiras escritas | um DT1 por vez, ouvido | o portão (3.1) |

Regra que atravessa todas: **nunca RQ1 em endereço que o App não pediu**.

### 7.2 Medições de 07/10/2026 (sessão zero, sem o Luan mexer)

- `ports`: tabela da 2.1
- `identidade`: ninguém respondeu (2.1)
- `escutar --segundos 8`: `TR-1000` mandou **409 clocks** (51 51 51 51 52 51 51 51 por
  segundo ≈ 127,5 bpm) e nada mais; CTRL e MIDI IN mudas. **O estado da máquina (parada ou
  tocando) não foi anotado**, então isto ainda não responde à armadilha 2. É a primeira
  pergunta da C0.

---

## 8. Ideias registradas, não implementadas

- **Leitura por CC como plano B:** se `Tx Edit Data` funcionar de verdade (a TR-8S não
  transmitia), os knobs do painel chegam de graça para a página de mixer
- **Polimetria visível:** com FIRST/LAST STEP por track, pintar fora da janela de cada
  track em cinza, e o playhead de cada linha andando no seu próprio passo

---

## 9. Referências

- `../tr8s-grid/REFERENCIA.md` — a TR-8S decifrada; seções 2.9 (mapa oficial via ARIA),
  3.1 (envenenamento da CTRL), 3.2 (Método), 5 (Launchpad), 7 (portas)
- `../TR-8S-SysEx/` (compuphonic) — o mapa oficial da TR-8S em `js/Tr8s/Tr8sData.js`; vale
  procurar se a Roland publicou algo equivalente para a TR-1000 (ARIA, Roland Cloud)
- Manuais em `manuals/` (fora do git) — ver README
- Launchpad Mini MK3 Programmer's Reference (Novation)

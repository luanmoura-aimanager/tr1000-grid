# TR-1000 Grid

Dois **Launchpad Mini MK3** viram um grid 16×8 que liga e desliga steps **no sequenciador
interno da Roland TR-1000**, em tempo real, por SysEx — o mesmo gesto do
[tr8s-grid](https://github.com/luanmoura-aimanager/tr8s-grid), agora para a máquina maior.

Não é um sequenciador externo disparando notas: o que se edita é o pattern dela, e o que
soa é a TR-1000 tocando sozinha. Desligue o computador e o pattern continua lá.

```
launchpads (nota/CC via USB) → Mac (Python + rtmidi) → SysEx (porta TR-1000 CTRL) → TR-1000
Mac (velocity = cor)         → launchpads (LEDs)
```

## Onde o projeto está: fase 0, captura

**Nada aqui escreve na máquina ainda.** A Roland documenta só notas, 66 CCs, program change
e clock (a *MIDI Implementation Chart* marca SysEx como não suportado — a da TR-8S também
marcava, e o SysEx dela funciona). O mapa de endereços tem que ser levantado, e a fase 0
existe para isso, com o método que deu certo na TR-8S (REFERENCIA 3.2).

A diferença em relação à TR-8S é a que torna isto viável: o **TR-1000 App** carrega dentro
do binário o catálogo **ordenado** de todos os parâmetros da máquina — inclusive o step
atual e a **variação que toca por track**, que a TR-8S nunca expôs — e lê tudo da máquina ao
abrir. Um sniff do App abrindo deve entregar endereços e tamanhos; o catálogo dá nome a eles.

| Fase | O quê | Estado |
|---|---|---|
| 0 | captura: catálogo do App, sniff do boot, decodificar pattern, primeira escrita ouvida | **em andamento** — ferramentas prontas, sessões C0–C3 pendentes |
| 1 | o grid: 12 linhas (10 tracks + ACC + TRG), layer A/B e ALT, playhead por track | depois do portão da fase 0 |
| 2 | parâmetros do step: probability, CYCLE, sub steps (tercinas, quiálteras), micro-timing | |
| 3 | página de performance: mute/cue, fill 1–4, step loop, roll, morph | |
| 4 | a tela web e o empacotamento (LaunchAgent, `.app`) | |

O roteiro detalhado está em [`REFERENCIA.md`](REFERENCIA.md) (seção 7) e o passo a passo
das sessões de hardware em [`ROTEIRO-C0-C3.md`](ROTEIRO-C0-C3.md).

## Uso (fase 0)

```bash
export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages

python3 lp_tr1000.py ports                    # portas MIDI com índice
python3 lp_tr1000.py escutar --segundos 20    # tudo que a máquina manda, em todas as portas
python3 lp_tr1000.py identidade               # Identity Request universal (não é RQ1)
python3 lp_tr1000.py sniff --arquivo x.txt    # SysEx da porta CTRL

python3 catalogo_app.py                       # catálogo do App -> capturas/ (fora do git)
python3 tr1000_sysex.py resumo boot-app.mmon  # lista branca de endereços de uma captura
python3 tr1000_sysex.py parse|diff|fx ...     # o resto da análise de capturas

python3 testes.py                             # testes de mesa, sem porta MIDI
python3 instalar_hooks.py                     # uma vez por clone
```

**Feche o TR-1000 App** antes de rodar qualquer coisa que use a porta CTRL ou a serial. O
CoreMIDI deixa os dois abrirem a porta ao mesmo tempo, e na TR-8S isso trocava as respostas
entre os dois sem erro nenhum aparecendo.

**O App não fala MIDI com a máquina**: fala por uma serial USB (REFERENCIA 2.1b). Para
capturar o que ele diz, use o espião:

```bash
python3 espiao.py preparar                 # uma vez: cópia re-assinada do App + espião
python3 espiao.py rodar boot-app           # abre a cópia; Cmd+Q grava capturas/AAAA-MM-DD-boot-app.serlog
python3 tr1000_serial.py estatisticas capturas/AAAA-MM-DD-boot-app.serlog
python3 tr1000_sysex.py resumo capturas/AAAA-MM-DD-boot-app.serlog
```

## Os manuais não estão no repositório

São obra da Roland. Baixe em [roland.com/support](https://www.roland.com/support/) (TR-1000)
e ponha em `manuals/` — o `.gitignore` já os deixa de fora:

| Arquivo | Documento |
|---|---|
| `TR-1000_eng02_W.pdf` | Owner's Manual |
| `TR-1000_reference_eng03_W.pdf` | Reference Manual (firmware 1.20+) |
| `TR-1000_MIDIImpleChart_eng02_W.pdf` | MIDI Implementation Chart (1.20) |
| `TR-1000_APP_eng01_W.pdf` | manual do TR-1000 App |
| `TR-1000_GEN_INST_List_eng02_W.pdf` | GEN/INST List (1.20) |
| ***MIDI Implementation*** | **ainda não baixado** — o Owner's Manual p.1 diz que existe, separado da Chart. Se houver mapa SysEx oficial, é lá |

## Requisitos

- macOS, Python 3.9 com `mido` e `python-rtmidi`
- Dois Launchpad Mini MK3 e uma TR-1000
- [MIDI Monitor](https://www.snoize.com/midimonitor/) para as sessões de sniff

**Armadilha do mido:** ele deduplica portas por nome e sempre abre a primeira ocorrência,
então os dois Launchpad viram um só. Toda enumeração e abertura usa `rtmidi` cru **por
índice** (`portas.py`); o `mido` fica só para montar e parsear mensagens.

## Arquivos

| Arquivo | O que é |
|---|---|
| `lp_tr1000.py` | A CLI. Na fase 0: `ports`, `escutar`, `identidade`, `sniff` — nenhuma escreve endereço |
| `roland.py` | Camada SysEx Roland genérica: checksum, endereço com carry de 7 bits, e um decodificador que **descobre o model ID pelo checksum** |
| `portas.py` | Portas MIDI por índice (herdado do tr8s-grid) |
| `tr1000.py` | O modelo da máquina, cada constante com a fonte: manual, catálogo, medido ou deduzido |
| `tr1000_sysex.py` | Parser/diff de capturas do MIDI Monitor; `resumo` tira a lista branca de endereços |
| `catalogo_app.py` | Extrai o catálogo ordenado de parâmetros do binário do TR-1000 App |
| `espiao.py` + `espiao/espiao_serial.c` | O App fala com a máquina por **serial USB**, não MIDI: o espião roda uma cópia do App gravando cada byte da serial em `capturas/*.serlog` |
| `tr1000_serial.py` | O protocolo da serial: lê os `.serlog` (`bruto`, `pacotes`, `blocos`, `pattern`, `escritas`, `diffblocos`) e monta pacotes byte a byte iguais aos do App |
| `conexao_serial.py` | Abre a serial da TR-1000 como o App abre; lê (`82`) e escreve (`01`) — escrita só na lista de 3 endereços da C3 |
| `sessao_c3.py` | A sessão C3: a primeira escrita nossa, um endereço por vez, com `sim` digitado |
| `sessao_c4.py` | Só leitura, ao vivo: o pattern inteiro (`pattern`) e o que muda nos blocos de estado (`estado`) |
| `testes.py` | Testes de mesa (`unittest`) |
| `REFERENCIA.md` | Fonte da verdade: o que está provado, deduzido e desconhecido |
| `ROTEIRO-C0-C3.md` | As sessões de hardware da fase 0, passo a passo |

## Licença

Sem licença definida ainda — pergunte antes de reutilizar.

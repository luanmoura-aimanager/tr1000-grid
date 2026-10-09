# TR-1000 Grid — contexto para o agente

## Leia a `REFERENCIA.md` antes de agir

Ela é a fonte da verdade do projeto e **separa o que está provado do que é dedução**. O
protocolo SysEx da TR-1000 não é documentado pela Roland; tudo o que soubermos vai ser
levantado empiricamente e registrado lá, com a seção 3 dizendo o que foi testado com
hardware e o que não foi.

Este projeto é um **fork adaptado do `../tr8s-grid`**. Lá está a história inteira da
engenharia reversa da TR-8S — a `REFERENCIA.md` de lá é leitura obrigatória quando a dúvida
for "como a gente descobriu X na TR-8S". Mas **nada medido na TR-8S vale como fato aqui**:
entra como hipótese a remedir.

A seção **"Método"** (3.2) vale ler mesmo para tarefas que não são de engenharia reversa.

## Quem opera o hardware

**O Luan.** Eu não aperto pad, não vejo LED e não escuto a caixa. Isso muda como o
trabalho é entregue:

- Passos **exatos** para ele executar, um por vez, com o que esperar de cada um
  (`ROTEIRO-C0-C3.md` é o modelo)
- Dizer sempre, e sem ser perguntado, **o que não foi testado em hardware**
- Quando algo depende de julgamento visual ou auditivo, pedir a observação em vez de
  afirmar que está certo
- "Compila" e "roda sem exceção" **não** são "funciona"

## Fase 0: nada escreve na máquina

Até o portão da fase 0 (REFERENCIA 3, "critério de saída"), **nenhum código manda DT1 nem
RQ1**. O `TestePortaoDaFase0` garante isso no `lp_tr1000.py`. O único SysEx que sai é o
Identity Request universal, que não toca no mapa de endereços.

Quando a fase 0 liberar leituras: **só RQ1 em endereço que o próprio TR-1000 App pediu**
(a lista branca que o `tr1000_sysex.py resumo` tira do boot do App).

**A exceção da C3 (08/10/2026):** a máquina fala por serial, não SysEx (REFERENCIA 2.1c), e a
primeira escrita nossa passa **só** por `sessao_c3.py` → `conexao_serial.py`, com a lista de
3 endereços `ESCRITAS_PERMITIDAS`, os bytes mostrados e `sim` digitado pelo Luan. Ampliar
essa lista é decisão dele, não detalhe de código.

- O **`--sim`** existe porque o `!` do Claude Code não tem teclado. Ele é o Luan digitando a
  confirmação na linha de comando. **O agente nunca roda uma escrita na máquina por conta
  própria**, com ou sem `--sim`: ele entrega o comando, e quem roda é o Luan.
- **Toda saída da serial passa por `conexao_serial.conferir_pacote`.**
  - Escrita só na lista.
  - Leitura (`82`) só dentro das faixas que o **próprio App** leu no boot da C1-S0 (a
    armadilha 1, versão serial).
  - Fora isso, só o aperto de mão.

## As armadilhas da TR-8S, a remedir aqui

1. **RQ1 em endereço inválido derrubava a porta CTRL** da TR-8S depois de ~60–75 sondas;
   só voltava religando. Não descobrir se a TR-1000 faz o mesmo do jeito caro — por isso
   a lista branca.
2. **A TR-1000 manda MIDI clock mesmo PARADA**, como a TR-8S. Medido em 08/10/2026:
   66/s a 165 BPM, parada e tocando. Só `start`/`stop` (que chegam) dizem se está tocando
   (REFERENCIA 7.3). O step atual **não** existe pela serial; vem de contar clock desde o
   `start`.
3. **O mido não enxerga os quatro Launchpad.** Ele deduplica portas por nome. Toda
   enumeração e abertura usa **rtmidi cru por índice** (`portas.py`); não "simplificar"
   isso de volta. Medido aqui também em 07/10/2026.
4. **`TR-1000` e `TR-1000 CTRL` casam pelo mesmo trecho de nome.** Use `porta_exata`.
5. **O TR-1000 App não fala MIDI com a máquina** — fala por uma serial USB
   (`/dev/tty.usbmodem*`), e o MIDI Monitor não vê nada (REFERENCIA 2.1b, medido em
   08/10/2026). O "Use CTRL Port" do `settings.xml` não muda isso. Captura do App é com o
   **espião**: `espiao.py rodar <nome>` → `.serlog` → `tr1000_serial.py` /
   `tr1000_sysex.py`.
6. **Feche o MIDI Monitor depois de salvar uma captura.** Documento aberto continua se
   salvando sozinho. Em 08/10/2026 ele gravou três vezes por cima da prova
   `2026-10-08-boot-app-serial-vazio.mmon`, e o `git add -A` levou as versões erradas para
   os commits. A original foi restaurada do histórico, e o `TesteRevisaoPR2` agora trava o
   conteúdo dela.
7. **O espião roda numa CÓPIA do App** em `~/Library/Caches/tr1000-grid/`, re-assinada sem
   hardened runtime. O App em `/Applications` nunca é escrito (`TesteEspiaoPreparo`), e o
   original fica **fechado** enquanto a cópia roda: dois Apps na mesma serial cruzariam as
   respostas.

## Ambiente

- Python 3.9 do Command Line Tools, com `mido` + `python-rtmidi` em `~/Library/Python/3.9`
- `export PYTHONPATH=~/Library/Python/3.9/lib/python/site-packages` antes de rodar
- **Não usar `--break-system-packages`**: o pip é 21.2.4 e não suporta
- PDFs: `pdftotext` não existe aqui. Usar `fitz` (PyMuPDF), que já está instalado — e
  **não** rodar com `python3 -I`, que ignora o `PYTHONPATH` e o `fitz` some
- O TR-1000 App está em `/Applications/Roland/TR-1000 App.app` (versão 1.10 em 07/10/2026)

## Fluxo de trabalho

**Toda edição sai de uma branch e entra na `main` por PR.** Nunca commitar direto na
`main`.

```bash
python3 instalar_hooks.py   # uma vez por clone; liga os hooks de .githooks/
```

- `pre-commit` recusa commit na `main`
- `pre-push` roda `python3 testes.py`; falhou, não empurra
- Para escapar de um deles, quando você sabe o que está fazendo: `--no-verify`

O CI (`.github/workflows/testes.yml`) roda os mesmos testes. **Verde não significa
"funciona"**: significa "não quebrou o que já estava provado".

## Capturas

- `capturas/*.mmon` (MIDI Monitor) e `capturas/*.txt` (sniff/escutar) são versionados: é o
  tráfego da máquina do Luan, a matéria-prima de toda conclusão
- `capturas/catalogo-app-*.json` **não** é versionado: é derivado do binário da Roland.
  Regenera com `python3 catalogo_app.py`
- Os manuais (`manuals/*.pdf`) também ficam fora: baixam-se da Roland

## Formatação

**Os `.py` não são formatados automaticamente, e isso é deliberado.** O estilo é
alinhamento manual: comentários alinhados à direita, tabelas de constantes em coluna, e a
coluna de fonte (`(manual ...)`, `(catalogo)`, `(medido)`, `(deduzido)`) que carrega a
distinção que este projeto trata como fundamental. Não rodar `black`.

## Idioma

Código, comentários e documentação em **português**, sem acento nos identificadores e nos
comentários do código. A documentação em `.md` usa acento normalmente.

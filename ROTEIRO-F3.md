# F3 — o TR-1000 Controller na frente da máquina

Roteiro para o Luan. É a **primeira vez** que vários endereços aprendidos pelo **painel** (C5,
REFERENCIA 7.6) são escritos por nós: os parâmetros do step, o cabeçalho, o MUTE e o STEP
LOOP. Faça um passo, me diga o que **ouviu e viu**, siga para o próximo.

**Antes:**
1. TR-1000 App da Roland **fechado**.
2. `lp_tr1000.py run` **fechado**: a serial é de um processo só.
3. Os Launchpads e as controladoras na USB.
4. No painel: **1-01**, var **A**.

```bash
cd ~/Documents/Claude/Projects/tr1000-grid
python3 instalar_agente.py      # o servidor sempre no ar (uma vez; de novo depois de editar)
python3 criar_app.py            # o "TR-1000 Controller.app" no Desktop
```

No **Safari**, abra `http://127.0.0.1:8734/` e use **Arquivo › Adicionar ao Dock**. É o app
igual ao do TR-8S.

---

## F3.1 — ON / OFF

1. Abra o App da Roland, e então aperte **ON** no Controller.
   **Esperado:** não liga; o rodapé diz que o App está aberto.
2. Feche o App e aperte **ON**.
   **Esperado:** os LEDs **TR-1000**, **Launchpads**, **MC-24** e **CM-MC50** acendem, e o
   PTN mostra 1-01.

## F3.2 — Pattern

1. Clique num step vazio do BD. **Esperado:** acende na tela, no Launchpad e no painel.
2. **Shift-clique** num step do SD que toca. No editor, **PROB 50%**, com a máquina tocando.
   **Esperado:** o step soa mais ou menos metade das vezes; no painel, segurando o step, o
   PROB mostra 50%.
3. **SUB** = 1/2: o step vira dois toques. **START** +50: ele atrasa.
4. Num step do **RS**, ligue **ALT**. **Esperado:** roxo na tela, no Launchpad e no painel.
5. No Launchpad, **▼**: as linhas 5 e 6 viram **CC** e **RC**. **▲** volta para RS e HC.

## F3.3 — Mixer e Efeitos

1. **Mixer**: mova o **PAN do SD**. A caixa anda. Depois gire o knob **SD PAN** do CM-MC50:
   ele "pega no caminho" a partir do valor novo.
2. **Efeitos**:
   - **MASTER FX TYPE** = ISOLATOR, depois **MFX 1** (LOW). Precisa do MASTER FX **ON no
     painel**.
   - **Routing**: o **SD** em THROUGH. A caixa sai do master FX.
   - **SIDE CHAIN**: SOURCE = BD A&B, MSTR DEP alto. O BD "abaixa" o resto.

## F3.4 — Performance

1. **MUTE** do HT: some, e a tecla lateral do Launchpad fica rosa.
2. **Variações** A e B acesas (a chain): com a máquina tocando, alterna A → B.
3. **FILL 2**: o FILL IN TRIG do painel toca a Fill 2.
4. **Scale** 32nd: o pattern corre no dobro. Volte para 16th.
5. **FIRST/LAST**: LAST da variação = 12, e o pattern dá a volta no 12.
6. **STEP LOOP**: ligue e segure o **5**. **É o menos certo:** no painel ele depende da tecla
   segurada. Me diga o que acontece.

## F3.5 — OFF

Aperte **OFF** e abra o App da Roland. **Esperado:** ele conecta normalmente.

**No fim:** se quiser desfazer, **[SHIFT]+[MENU]** (RELOAD) do pattern e do kit.

**Não testado até este roteiro:** tudo acima. Os testes de mesa (168) só dizem que nada
quebrou o que já estava provado.

#!/usr/bin/env python3
"""
portas.py - portas MIDI por INDICE, via rtmidi cru

Herdado sem mudanca de logica do tr8s-grid (lp_tr8s.py :854-962, REFERENCIA 7
de la). O motivo continua o mesmo, e continua valendo aqui porque o hardware e
o mesmo: dois Launchpad Mini MK3 expoem quatro portas com nomes IDENTICOS
(medido 07/10/2026: "Launchpad Mini MK3 LPMiniMK3 DAW Out" duas vezes,
"... MIDI Out" duas vezes), e o mido
  - deduplica por nome em get_input_names()  (backends/rtmidi.py), e
  - abre pelo nome casando sempre a PRIMEIRA ocorrencia,
entao os dois aparelhos virariam um. Toda enumeracao e abertura e por indice;
o mido fica so para montar e parsear mensagens. NAO "simplificar" de volta.
"""
import collections

import mido
import rtmidi


class EntradaMIDI:
    """Entrada aberta por indice, com a interface do mido (iter_pending).

    callback=True: o rtmidi entrega cada mensagem num deque ilimitado em vez da
    fila interna de 1024, que descarta em silencio quando enche (medido no
    tr8s-grid em 16/08/2026: 657 avisos num log, cada um um pulso de clock
    perdido). Use em toda porta que recebe clock."""

    def __init__(self, idx, nome=None, ignorar_sense=True, callback=False):
        self._rt = rtmidi.MidiIn()
        self._rt.open_port(idx)
        # NAO ignorar sysex nem timing (clock); active sensing so quando pedido
        self._rt.ignore_types(False, False, ignorar_sense)
        self._parser = mido.Parser()
        self.idx, self.name = idx, nome or "?"
        self._buf = None
        if callback:
            # append de um lado e popleft do outro sao atomicos sob o GIL
            self._buf = collections.deque()
            self._rt.set_callback(lambda par, d=None: self._buf.append(par[0]))

    def iter_pending(self):
        if self._buf is not None:
            while self._buf:
                self._parser.feed(self._buf.popleft())
        else:
            while True:
                r = self._rt.get_message()
                if r is None:
                    break
                self._parser.feed(r[0])
        return list(self._parser)          # lista, nao generator: drenar e seguro

    def close(self):
        try:
            if self._buf is not None:
                self._rt.cancel_callback()
            self._rt.close_port(); self._rt.delete()
        except Exception: pass

    def __enter__(self): return self
    def __exit__(self, *e): self.close()


class SaidaMIDI:
    """Saida aberta por indice."""
    def __init__(self, idx, nome=None):
        self._rt = rtmidi.MidiOut()
        self._rt.open_port(idx)
        self.idx, self.name = idx, nome or "?"

    def send(self, msg):
        self._rt.send_message(msg.bytes())

    def send_bytes(self, b):
        """Bytes crus - para SysEx montado pelo roland.py, sem passar pelo mido."""
        self._rt.send_message(list(b))

    def close(self):
        try: self._rt.close_port(); self._rt.delete()
        except Exception: pass

    def __enter__(self): return self
    def __exit__(self, *e): self.close()


def listar_portas(entradas=True):
    """Todas as portas como [(indice, nome)] - sem deduplicar."""
    rt = rtmidi.MidiIn() if entradas else rtmidi.MidiOut()
    try:
        return list(enumerate(rt.get_ports()))
    finally:
        rt.delete()


def achar_portas(trecho, entradas=True):
    """[(indice, nome)] das portas cujo nome contem 'trecho'."""
    return [(i, n) for i, n in listar_portas(entradas)
            if trecho.lower() in n.lower()]


def porta_exata(nome, entradas=True, portas=None):
    """(indice, nome) da porta com este nome EXATO, ou None.

    A TR-1000 tem "TR-1000" e "TR-1000 CTRL": casar por trecho pegaria as duas,
    e abrir a CTRL achando que e a comum foi exatamente o tipo de troca que no
    tr8s-grid custou leituras cruzadas sem erro nenhum (README de la)."""
    portas = listar_portas(entradas) if portas is None else portas
    achadas = [(i, n) for i, n in portas if n == nome]
    return achadas[0] if achadas else None

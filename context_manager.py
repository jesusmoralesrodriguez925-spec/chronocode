#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_manager.py - Historial de la conversación y compactación (Fase 2).
"""
import json

LIMITE_TOKENS_DEFAULT = 24000   # presupuesto aproximado del historial
UMBRAL = 0.8                    # compacta al llegar al 80 % del límite
MANTENER_RECIENTES = 6          # mensajes recientes que nunca se resumen


class ContextManager:
    def __init__(self, limite_tokens=LIMITE_TOKENS_DEFAULT):
        self.limite_tokens = limite_tokens
        self.mensajes = []

    def add_message(self, role, content):
        self.mensajes.append({"role": role, "content": content})
        return self.mensajes[-1]

    def as_list(self):
        return list(self.mensajes)

    def clear(self):
        self.mensajes.clear()

    def estimate_tokens(self):
        """Estimación aproximada: unos 4 caracteres por token."""
        return sum(len(json.dumps(m, ensure_ascii=False)) for m in self.mensajes) // 4

    def needs_compaction(self):
        return self.estimate_tokens() > self.limite_tokens * UMBRAL

    def compact_history(self, llm_client, keep_last=MANTENER_RECIENTES):
        """
        Resume los mensajes viejos con llm_client(prompt) -> str.
        El corte siempre empieza en un mensaje del usuario, para no partir un turno.
        Devuelve True si compactó.
        """
        if keep_last < 1 or len(self.mensajes) <= keep_last:
            return False
        corte = len(self.mensajes) - keep_last
        while corte > 0 and self.mensajes[corte]["role"] != "user":
            corte -= 1
        if corte <= 0:
            return False
        viejos = self.mensajes[:corte]
        recientes = self.mensajes[corte:]
        texto = "\n".join(f"{m['role']}: {m.get('content') or ''}" for m in viejos)
        prompt = ("Resume de forma concisa esta conversación de programación: decisiones tomadas, "
                  "archivos modificados, objetivos pendientes y datos importantes. "
                  "Responde solo con el resumen.\n\n" + texto)
        resumen = (llm_client(prompt) or "").strip()
        if not resumen:
            return False
        self.mensajes = [{"role": "user",
                          "content": "Resumen de la conversación anterior:\n" + resumen}] + recientes
        return True

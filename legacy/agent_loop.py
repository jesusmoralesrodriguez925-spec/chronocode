#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_loop.py - Bucle agéntico de ChronoCode (Fase 2).
Pide al modelo, ejecuta las herramientas de tools.py y repite hasta obtener texto final.
Solo para proveedores compatibles con la API de OpenAI (tool calling).
"""
import json

import requests

import tools

MAX_PASOS = 8          # límite de pasos con herramientas por turno
TIMEOUT = 120          # segundos por petición

GUIA_HERRAMIENTAS = (
    "Tienes herramientas para trabajar en el proyecto del usuario: read_file, glob, grep, "
    "edit_file, write_file y run_command. Lee un archivo antes de editarlo. Usa edit_file para "
    "cambios pequeños y write_file solo para archivos nuevos. Cuando termines, responde con un "
    "resumen corto en español."
)


def _propiedad(descripcion):
    return {"type": "string", "description": descripcion}


OPENAI_TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Lee un archivo de texto.",
        "parameters": {"type": "object", "properties": {"path": _propiedad("Ruta del archivo")},
                       "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file", "description": "Crea o sobrescribe un archivo (el usuario debe aprobarlo).",
        "parameters": {"type": "object", "properties": {
            "path": _propiedad("Ruta del archivo"),
            "content": _propiedad("Contenido completo del archivo")},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "edit_file", "description": "Reemplaza un texto exacto y único en un archivo.",
        "parameters": {"type": "object", "properties": {
            "path": _propiedad("Ruta del archivo"),
            "old_string": _propiedad("Texto exacto a reemplazar"),
            "new_string": _propiedad("Texto nuevo")},
            "required": ["path", "old_string", "new_string"]}}},
    {"type": "function", "function": {
        "name": "glob", "description": "Lista archivos que coinciden con un patrón, p. ej. **/*.py.",
        "parameters": {"type": "object", "properties": {
            "pattern": _propiedad("Patrón glob"),
            "root": _propiedad("Carpeta base (opcional)")},
            "required": ["pattern"]}}},
    {"type": "function", "function": {
        "name": "grep", "description": "Busca un patrón (regex) dentro de archivos.",
        "parameters": {"type": "object", "properties": {
            "pattern": _propiedad("Expresión regular"),
            "path": _propiedad("Carpeta o archivo (opcional)")},
            "required": ["pattern"]}}},
    {"type": "function", "function": {
        "name": "run_command", "description": "Ejecuta un comando de terminal (el usuario debe aprobarlo).",
        "parameters": {"type": "object", "properties": {"cmd": _propiedad("Comando a ejecutar")},
                       "required": ["cmd"]}}},
]


def _llamar(url, headers, payload):
    r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]


def _argumentos(llamada):
    try:
        return json.loads(llamada["function"].get("arguments") or "{}")
    except json.JSONDecodeError:
        return None


def responder(url, headers, modelo, mensajes, validar_ruta=None, on_tool=None):
    """
    mensajes: lista [system, ..., user] con role/content.
    validar_ruta(path) -> motivo o None: se aplica a write_file y edit_file.
    Devuelve el texto final del asistente.
    """
    turno = []
    for _ in range(MAX_PASOS):
        payload = {"model": modelo, "messages": mensajes + turno,
                   "tools": OPENAI_TOOLS, "tool_choice": "auto", "temperature": 0.2}
        msg = _llamar(url, headers, payload)
        llamadas = msg.get("tool_calls") or []
        if not llamadas:
            return (msg.get("content") or "").strip()

        turno.append({"role": "assistant", "content": msg.get("content") or "",
                      "tool_calls": llamadas})
        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            if on_tool:
                on_tool(nombre)
            args = _argumentos(llamada)
            if args is None:
                resultado = "ERROR: argumentos JSON inválidos."
            elif nombre in ("write_file", "edit_file") and validar_ruta:
                problema = validar_ruta(args.get("path", ""))
                resultado = (f"BLOQUEADO: {problema}" if problema
                             else tools.ejecutar_herramienta(nombre, args))
            else:
                resultado = tools.ejecutar_herramienta(nombre, args)
            turno.append({"role": "tool", "tool_call_id": llamada["id"], "content": resultado})

    return "Se alcanzó el máximo de pasos con herramientas. Pide que continúe si lo necesitas."


def llamada_simple(url, headers, modelo, prompt):
    """Petición sin herramientas (la usa la compactación del historial)."""
    payload = {"model": modelo, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
    return _llamar(url, headers, payload).get("content") or ""

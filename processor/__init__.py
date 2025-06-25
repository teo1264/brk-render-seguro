#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: processor/__init__.py
💾 ONDE SALVAR: brk-monitor-seguro/processor/__init__.py
📦 FUNÇÃO: Inicializador do módulo de processamento
🔧 DESCRIÇÃO: Centraliza acesso aos módulos de processamento de emails
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar da tesouraria
"""

from .email_processor import EmailProcessor

__version__ = "1.0.0"
__author__ = "Sidney Gubitoso, auxiliar da tesouraria"
__all__ = ["EmailProcessor"]

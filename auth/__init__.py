#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 ARQUIVO: auth/__init__.py
💾 ONDE SALVAR: brk-monitor-seguro/auth/__init__.py
📦 FUNÇÃO: Inicializador do módulo de autenticação
🔧 DESCRIÇÃO: Centraliza acesso aos módulos de autenticação Microsoft
👨‍💼 AUTOR: Sidney Gubitoso, auxiliar da tesouraria
"""

from .microsoft_auth import MicrosoftAuth

__version__ = "1.0.0"
__author__ = "Sidney Gubitoso, auxiliar da tesouraria"
__all__ = ["MicrosoftAuth"]
